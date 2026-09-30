"""
Fetching and installing a new release of the plugin.

Everything that touches the network or the filesystem lives here, and
nothing here touches Qt: an update runs on a worker thread and reports
back through plain callables, so this module can be exercised without
Painter at all.

A *source* is one place where releases of the plugin are published - a
GitHub repository, a GitLab project, a mirror of either - listed in
config.UPDATE_SOURCES. Sources are asked in turn, so a host that is
down, rate-limited or simply not there costs a delay rather than the
update itself.

Failures are reported as an UpdateError carrying a reason rather than a
sentence: this module needs no localization, and the reason is what the
UI turns into words.
"""

import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from . import config
from . import settings
from .version import from_tag, is_newer

# Why an update did not happen. Identifiers, not sentences - see the
# module docstring. Each one is named after the locale key that words
# it, "update_error_<reason>", so the UI never has to map them.
REASON_NETWORK = "network"
REASON_DOWNLOAD = "download"
REASON_CHECKSUM = "checksum"
REASON_ARCHIVE = "archive"
REASON_NO_ASSET = "no_asset"
REASON_INSTALL = "install"
REASON_CANCELLED = "cancelled"
REASON_UNKNOWN = "unknown"

# Fallback host per source kind, so the usual entry in config.py is two
# keys long.
_DEFAULT_HOSTS = {"github": "github.com", "gitlab": "gitlab.com"}

# Read in chunks so the download can report progress and be cancelled
# part-way through, rather than arriving in one lump at the end.
_CHUNK = 64 * 1024

# A checksum file is a single line; anything longer is not one.
_CHECKSUM_LIMIT = 64 * 1024

_HEX64 = re.compile(r"\b[0-9a-fA-F]{64}\b")


class UpdateError(Exception):
    """An update that did not happen.

    `reason` is one of the REASON_* constants above and is what the UI
    localizes. `status` carries an HTTP status when there was one, which
    the GitLab provider needs in order to know that an endpoint is
    missing rather than broken.
    """

    def __init__(self, reason, detail="", status=None):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail
        self.status = status


class Release:
    """One published version, and where its archive can be fetched."""

    __slots__ = ("version", "page_url", "archive_url")

    def __init__(self, version, page_url, archive_url):
        self.version = version
        self.page_url = page_url
        self.archive_url = archive_url


class Source:
    """One place where releases are published.

    Built from a plain dict in config.UPDATE_SOURCES, which documents
    what each key means. Anything left out falls back to the default for
    the kind, so the common case is two keys.
    """

    def __init__(self, spec: dict):
        self.kind = str(spec.get("kind", "")).strip().lower()
        self.path = str(spec.get("path", "")).strip("/")
        self.host = str(spec.get("host") or _DEFAULT_HOSTS.get(self.kind, "")).strip("/")
        self.scheme = str(spec.get("scheme") or "https")

        # An explicit API base URL, for hosts that do not follow the
        # usual layout - a self-hosted GitLab under a sub-path, or a
        # GitHub Enterprise instance, whose API lives at /api/v3 on the
        # same host rather than on an api. subdomain.
        self.api = str(spec.get("api") or "")

        # What to call this source in the progress line: a repository
        # the user can recognise beats "GitHub" when there are mirrors.
        self.name = str(spec.get("name") or self.path or self.host)

    def api_base(self) -> str:
        """Where this host's API lives, with no trailing slash."""
        return (self.api or "").rstrip("/")

    def __repr__(self):
        return "<Source {} {}>".format(self.kind, self.path)


def sources(specs) -> list:
    """Every configured source, as Source objects.

    Entries that name a kind nothing implements are dropped with a note
    rather than raising: one bad line in config.py must not take the
    whole update feature down with it.
    """
    usable = []

    for spec in specs:
        try:
            source = Source(spec)
        except Exception as err:  # a malformed entry is a typo, not a crash
            print("[DiscordRPC] Ignoring malformed update source {!r}: {}".format(spec, err))
            continue

        if source.kind not in _PROVIDERS or not source.path:
            print(
                "[DiscordRPC] Ignoring update source with unknown kind "
                "'{}' - expected one of: {}".format(
                    source.kind, ", ".join(sorted(_PROVIDERS))
                )
            )
            continue

        usable.append(source)

    return usable


# -- providers -------------------------------------------------------------------
#
# Each one turns a source into a Release, or raises UpdateError. They
# share nothing but that interface, which is what lets GitHub and GitLab
# be listed side by side in the same config.


class _Provider:
    """Common plumbing: HTTP, headers, and picking the asset out of a
    release."""

    kind = ""

    def __init__(self, source: Source):
        self.source = source

    def latest(self, token):
        """The newest published release for this source."""
        raise NotImplementedError

    # -- helpers

    def _request(self, url, token=""):
        headers = {
            "Accept": "application/json",
            # GitHub rejects a request without one outright.
            "User-Agent": "drp-as3dp/{}".format(config.PLUGIN_VERSION),
        }

        if token:
            headers[self._auth_header()] = token

        return urllib.request.Request(url, headers=headers)

    def _auth_header(self):
        raise NotImplementedError

    def _get_json(self, url, token):
        try:
            with urllib.request.urlopen(
                self._request(url, token), timeout=config.UPDATE_REQUEST_TIMEOUT
            ) as response:
                payload = response.read()
        except urllib.error.HTTPError as err:
            raise UpdateError(
                REASON_NETWORK, "{}: HTTP {}".format(url, err.code), status=err.code
            ) from err
        except (urllib.error.URLError, OSError) as err:
            raise UpdateError(REASON_NETWORK, "{}: {}".format(url, err)) from err

        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as err:
            raise UpdateError(REASON_NETWORK, "{}: not JSON".format(url)) from err

    def _release(self, tag, page_url, assets):
        """Pick the plugin archive out of a release's asset list.

        A release that does not carry the archive is a release we
        cannot install from, which is worth saying out loud rather than
        silently skipping - it usually means the zip was forgotten when
        the release was cut.
        """
        wanted = config.UPDATE_ASSET_NAME

        for name, url in assets:
            if name == wanted and url:
                return Release(from_tag(tag), page_url, url)

        raise UpdateError(
            REASON_NO_ASSET,
            "{}: release {} has no {}".format(self.source.path, tag, wanted),
        )


class GitHubProvider(_Provider):
    """GitHub, and GitHub Enterprise.

    The public API serves a public repository without a token, so one is
    only needed to lift the request limit on a busy network or to reach
    a private repository.
    """

    kind = "github"

    def _auth_header(self):
        return "Authorization"

    def _endpoint(self):
        base = self.source.api_base()

        if not base:
            # api.github.com for the hosted service. A self-hosted
            # instance wants its own api= entry instead, since it serves
            # the API from a path on the same host.
            base = "{scheme}://api.{host}".format(
                scheme=self.source.scheme, host=self.source.host
            )

        return "{}/repos/{}/releases/latest".format(base, self.source.path)

    def latest(self, token):
        data = self._get_json(self._endpoint(), token)
        if not isinstance(data, dict):
            raise UpdateError(REASON_NETWORK, "unexpected release payload")

        assets = [
            (asset.get("name"), asset.get("browser_download_url"))
            for asset in data.get("assets", [])
        ]

        # releases/latest already excludes drafts and prereleases.
        return self._release(
            data.get("tag_name", ""), data.get("html_url", ""), assets
        )


class GitLabProvider(_Provider):
    """GitLab, including self-hosted instances.

    GitLab identifies a project by its whole "group/subgroup/project"
    path, percent-encoded as a single URL segment - which is why the
    path cannot simply be pasted into the URL.
    """

    kind = "gitlab"

    def _auth_header(self):
        return "PRIVATE-TOKEN"

    def _endpoint(self, suffix):
        base = self.source.api_base()

        if not base:
            base = "{scheme}://{host}/api/v4".format(
                scheme=self.source.scheme, host=self.source.host
            )

        # GitLab names a project by its whole "group/subgroup/project"
        # path, percent-encoded as a single URL segment - which is why
        # the path cannot simply be pasted into the URL.
        return "{}/projects/{}/{}".format(
            base, urllib.parse.quote(self.source.path, safe=""), suffix
        )

    def latest(self, token):
        data = self._permalink(token)

        if data is None:
            # GitLab before 16.7 has no permalink. The ordered list is
            # the older way of asking the same question.
            data = self._newest_published(token)

        assets = [
            (link.get("name"), link.get("url"))
            for link in data.get("assets", {}).get("links", [])
        ]

        page_url = "{scheme}://{host}/{path}/-/releases/{tag}".format(
            scheme=self.source.scheme,
            host=self.source.host,
            path=self.source.path,
            tag=data.get("tag_name", ""),
        )

        return self._release(data.get("tag_name", ""), page_url, assets)

    def _permalink(self, token):
        """The latest release, or None if this GitLab cannot say."""
        try:
            data = self._get_json(self._endpoint("releases/permalink/latest"), token)
        except UpdateError as err:
            if err.status == 404:
                return None
            raise

        if not isinstance(data, dict):
            return None

        # An upcoming release has no release date yet: nobody can
        # install it, so it does not count as "latest" here either.
        return data if data.get("released_at") else None

    def _newest_published(self, token):
        listing = self._get_json(
            self._endpoint(
                "releases?per_page=5&order_by=released_at&sort=desc"
            ),
            token,
        )

        for entry in listing if isinstance(listing, list) else []:
            if entry.get("released_at"):
                return entry

        raise UpdateError(REASON_NETWORK, "{}: no published release".format(self.source.path))


_PROVIDERS = {
    GitHubProvider.kind: GitHubProvider,
    GitLabProvider.kind: GitLabProvider,
}


def build_provider(source: Source):
    """The provider class that knows how to read `source`."""
    return _PROVIDERS[source.kind](source)


# -- downloading -----------------------------------------------------------------


def _log(message):
    print("[DiscordRPC] {}".format(message))


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_symlink(entry) -> bool:
    """Whether a zip entry claims to be a symbolic link.

    Such an entry would be written out as a link pointing wherever it
    likes when the archive is unpacked, which is the same hole as a
    path escaping the destination - so it is refused outright.
    """
    return (entry.external_attr >> 16) & 0o170000 == 0o120000


def _extract_safely(archive: zipfile.ZipFile, destination: Path):
    """Unpack into `destination`, refusing anything that points outside it.

    An archive is an upload from somewhere else. A name like
    "../../somewhere/else" inside one is entirely possible and would
    otherwise let a release write over files the plugin has no business
    touching.
    """
    root = str(destination.resolve())

    for entry in archive.infolist():
        if _is_symlink(entry):
            raise UpdateError(
                REASON_ARCHIVE, "archive contains a link: {}".format(entry.filename)
            )

        target = str((destination / entry.filename).resolve())
        if target != root and not target.startswith(root + os.sep):
            raise UpdateError(
                REASON_ARCHIVE, "archive path escapes the plugin folder: {}".format(entry.filename)
            )

    try:
        archive.extractall(str(destination))
    except OSError as err:
        raise UpdateError(REASON_ARCHIVE, "could not unpack: {}".format(err)) from err


def _carried_files() -> tuple:
    """Files that belong to this installation rather than to a release.

    The user's settings are theirs: they are never in the release zip,
    and losing them on every upgrade would make the plugin unusable
    without ever re-entering them.
    """
    return (settings.FILE_NAME, settings.FILE_NAME + settings.BACKUP_SUFFIX)


# Most informative first: what these have in common is that they are all
# true, so the point is which one the user could do anything about.
_FINAL_REASONS = (REASON_CHECKSUM, REASON_DOWNLOAD, REASON_NO_ASSET, REASON_NETWORK)


def _final_reason(reasons: set) -> str:
    for reason in _FINAL_REASONS:
        if reason in reasons:
            return reason
    return REASON_DOWNLOAD


# -- the updater -----------------------------------------------------------------


class Updater:
    """Checks for, and installs, a newer release.

    Holds no state worth keeping between calls, so one instance can serve
    both the automatic check at startup and a manual one.
    """

    def __init__(self, source_specs=None, token="", attempts=None):
        self._sources = sources(
            config.UPDATE_SOURCES if source_specs is None else source_specs
        )
        self._token = token or ""
        self._attempts = config.UPDATE_ATTEMPTS if attempts is None else max(1, attempts)

        if not self._sources:
            _log("No usable update sources configured; updates are off.")

    @property
    def sources(self) -> list:
        return list(self._sources)

    # -- checking

    def find(self):
        """The newest release across all sources, if it is newer than
        the installed one. None means there is nothing to do.

        Raises UpdateError only when no source could be asked at all.
        A network problem is worth reporting to someone who pressed the
        button, and worth saying nothing about when the check was
        automatic - there is nothing the user could do about it either
        way.
        """
        newest = None
        last_error = None

        for source in self._sources:
            try:
                release = build_provider(source).latest(self._token)
            except UpdateError as err:
                _log("{}: {}".format(source.name, err.detail or err.reason))
                last_error = err
                continue

            if not is_newer(release.version, config.PLUGIN_VERSION):
                continue

            if newest is None or is_newer(release.version, newest.version):
                newest = release

        if newest is None and last_error is not None:
            raise last_error

        return newest

    # -- installing

    def install(self, report=None, cancelled=None):
        """Download, verify and unpack the newest release over the
        running plugin. Returns the Release that was installed.

        One *attempt* is a full pass over the sources: the first one that
        yields an archive whose checksum matches is unpacked and
        installed. A source that cannot be reached, or that serves an
        archive which fails verification, only moves the pass on to the
        next one - that is a problem with that mirror, not with this
        attempt. An archive that will not unpack does end the attempt,
        which is what config.UPDATE_ATTEMPTS bounds.

        `report(stage, **details)` is called as it goes, and
        `cancelled()` is polled so a user who changed their mind is not
        left waiting out a download. Neither is allowed to raise.
        """
        report = report or (lambda stage, **details: None)
        cancelled = cancelled or (lambda: False)

        attempts = self._attempts
        reasons = set()
        # An archive that arrived intact but is not the plugin is a
        # different kind of problem from a mirror being down, and the
        # answer to it is to try the whole thing again. It is kept here
        # so that whatever the retries went on to do, this is still the
        # error the user is finally told about.
        unusable = None

        while attempts > 0:
            attempts -= 1

            for source in self._sources:
                if cancelled():
                    raise UpdateError(REASON_CANCELLED)

                try:
                    # Asked per source, not per run: each mirror has its
                    # own releases and its own archive to hand out, so
                    # "try the next one" means asking the next one.
                    release = build_provider(source).latest(self._token)
                    if not is_newer(release.version, config.PLUGIN_VERSION):
                        continue

                    payload = self._fetch(
                        release.archive_url, report, cancelled, source.name
                    )

                    report("update_stage_verify")
                    if not self._checksum_matches(payload, release.archive_url):
                        _log(
                            "{}: archive does not match its checksum".format(source.name)
                        )
                        reasons.add(REASON_CHECKSUM)
                        continue

                    report("update_stage_unpack")
                    staging, package = self._unpack(payload)
                except UpdateError as err:
                    if err.reason == REASON_CANCELLED:
                        raise
                    if err.reason == REASON_ARCHIVE:
                        _log("{}: {}".format(source.name, err.detail or err.reason))
                        unusable = err
                        break

                    _log("{}: {}".format(source.name, err.detail or err.reason))
                    reasons.add(err.reason)
                    continue

                report("update_stage_install")
                self._replace(staging, package)
                return release

        # Every attempt is spent. An archive that is not the plugin wins
        # over a host we never reached, because it is the one thing that
        # came back and turned out to be wrong.
        if unusable is not None:
            raise unusable

        # Otherwise report the most informative thing that went wrong.
        raise UpdateError(
            _final_reason(reasons),
            "no source produced a verified archive after {} attempt(s)".format(
                self._attempts
            ),
        )

    def _fetch(self, url, report, cancelled, name=""):
        """Stream a URL into memory, reporting as it goes."""
        request = urllib.request.Request(
            url, headers={"User-Agent": "drp-as3dp/{}".format(config.PLUGIN_VERSION)}
        )

        try:
            with urllib.request.urlopen(
                request, timeout=config.UPDATE_REQUEST_TIMEOUT
            ) as response:
                declared = response.headers.get("Content-Length", "")
                total = int(declared) if declared.isdigit() else 0

                chunks = []
                received = 0

                while True:
                    if cancelled():
                        raise UpdateError(REASON_CANCELLED)

                    chunk = response.read(_CHUNK)
                    if not chunk:
                        break

                    chunks.append(chunk)
                    received += len(chunk)
                    report(
                        "update_stage_download",
                        source=name,
                        received=received,
                        total=total,
                    )

                    if received > config.UPDATE_MAX_DOWNLOAD:
                        raise UpdateError(
                            REASON_DOWNLOAD, "archive is larger than expected"
                        )

        except UpdateError:
            raise
        except (urllib.error.URLError, OSError) as err:
            raise UpdateError(REASON_DOWNLOAD, "{}: {}".format(url, err)) from err

        return b"".join(chunks)

    def _checksum_matches(self, payload, archive_url) -> bool:
        """Compare the archive against the checksum published with it.

        A checksum that cannot be read counts as a failure, not as a
        pass: the whole point of publishing it is that nothing is
        installed without it.
        """
        expected = self._expected_checksum(archive_url)

        if expected is None:
            return False

        return _digest(payload) == expected

    def _expected_checksum(self, archive_url):
        """The sha256 sitting next to the archive, or None if it cannot
        be read. Parsed out of the file rather than assumed, so both the
        bare hash and the full "sha256sum" output line are accepted."""
        try:
            payload = self._fetch(
                archive_url + config.UPDATE_CHECKSUM_SUFFIX,
                lambda stage, **details: None,
                lambda: False,
            )
        except UpdateError:
            return None

        match = _HEX64.search(payload.decode("utf-8", "replace"))
        return match.group(0).lower() if match else None

    def _unpack(self, payload):
        """Unpack into a temporary folder. Returns (temp folder, the
        single package directory found inside it)."""
        staging = Path(tempfile.mkdtemp(prefix="drp-update-"))

        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                _extract_safely(archive, staging)

            roots = [entry for entry in staging.iterdir() if entry.is_dir()]

            # One folder, and it is a package: that is what the build
            # produces and the only shape that can be installed. The
            # name is not checked, so a user who renamed their plugin
            # folder is not locked out of updating.
            if len(roots) != 1 or not (roots[0] / "__init__.py").is_file():
                raise UpdateError(
                    REASON_ARCHIVE, "archive does not contain a single plugin package"
                )

            return staging, roots[0]
        except zipfile.BadZipFile as err:
            raise UpdateError(REASON_ARCHIVE, "not a zip file") from err
        except Exception:
            shutil.rmtree(str(staging), ignore_errors=True)
            raise

    def _replace(self, staging: Path, package: Path):
        """Swap the running plugin's folder for the freshly unpacked one.

        Each direction is a rename rather than a copy, so there is never
        a half-written folder: the old one is moved aside first and only
        deleted once the new one is in place, and put back if that
        fails. Nothing is left behind afterwards - this is not a backup
        the user can restore from later, just an order of operations that
        makes a failed write recoverable.

        The swap itself is not a cancellation point: walking away
        halfway through would leave the plugin in a worse state than not
        updating at all.
        """
        target = Path(__file__).resolve().parent
        previous = target.with_name(target.name + ".old")

        try:
            shutil.rmtree(str(previous), ignore_errors=True)

            for name in _carried_files():
                carried = target / name
                if carried.is_file():
                    shutil.copy2(str(carried), str(package / name))

            target.rename(previous)

            try:
                shutil.move(str(package), str(target))
            except OSError as err:
                previous.rename(target)  # nothing installed, so undo
                raise UpdateError(REASON_INSTALL, str(err)) from err

            shutil.rmtree(str(previous), ignore_errors=True)
        finally:
            shutil.rmtree(str(staging), ignore_errors=True)
