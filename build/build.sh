#!/usr/bin/env bash
# Builds the distributable plugin zip and its checksum:
#   dist/DRP_AS3DP-python.zip
#   dist/DRP_AS3DP-python.zip.sha256
#
# Usage:
#   ./build/build.sh                     (Linux, macOS)
#   bash build/build.sh                  (Windows, from a Git Bash shell)
#   bash build/build.sh --verify-tag v1.0.0
#
# --verify-tag builds *and* insists that the release being cut is tagged
# exactly v<PLUGIN_VERSION>; CI passes the tag it was triggered by. Left
# out, a tagged checkout verifies against its own tag instead, and an
# untagged one - most of development - skips the check.
#
# Third-party code is not kept in the repository. The one package the
# plugin needs is downloaded from PyPI here, at build time, and lands in
# the staging copy only. See "Building a distributable zip" in README.md
# for the tools this needs.

set -euo pipefail

# --- Dependencies --------------------------------------------------------------

# The one place a dependency version is changed. build.sh derives the
# download URL from the name and this value, so bumping a dependency is
# a one-line edit and nothing else has to know about it.
PYPRESENCE_VERSION="4.6.2"

# The name of the release asset that is the plugin. Not a constant of
# its own: read out of src/drp/config.py (UPDATE_ASSET_NAME) during the
# build, so the file produced here and the file an installed copy looks
# for are the same name by construction rather than by agreement.
ZIP_NAME=""

# --- Paths ---------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$ROOT_DIR/src/drp"
DIST_DIR="$ROOT_DIR/dist"
CONFIG_FILE="$SRC_DIR/config.py"

# Everything below is thrown away at the end of the build.
STAGING_DIR="$DIST_DIR/staging"          # the plugin, as it will be zipped
DOWNLOAD_DIR="$DIST_DIR/download"        # fetched archives and their unpacked form
VENDOR_DIR="$STAGING_DIR/drp/vendor"     # third-party code inside the package

# --- Helpers -------------------------------------------------------------------

die() {
    echo "error: $*" >&2
    exit 1
}

usage() {
    # The header comment above, minus its own line and its leading "# ".
    sed -n '2,/^$/p' "${BASH_SOURCE[0]}" | sed 's/^#\{1,\} \{0,1\}//'
}

# PyPI serves every source distribution from a predictable path that needs
# no content hash, so no JSON API and no JSON parser are required:
#   .../source/<first letter>/<name>/<name>-<version>.tar.gz
pypi_source_url() {
    local name="$1" version="$2"
    printf 'https://files.pythonhosted.org/packages/source/%s/%s/%s-%s.tar.gz' \
        "${name:0:1}" "$name" "$name" "$version"
}

# --- Version -------------------------------------------------------------------

# A release tag is exactly "v" + PLUGIN_VERSION, and nothing else.
# Publishing 1.1.0 under the tag 1.0.0 would leave every user on an old
# build forever, because that is the tag their updater compares against,
# so the mismatch is refused rather than reported afterwards.
verify_tag() {
    local tag="$1" version="$2"

    # Compared case-insensitively: this repository already carries both
    # "V0.1.0" and "v1.0.0", and which one a person types is not worth
    # failing a release over.
    local wanted="v$version"
    if [ "$(printf '%s' "$tag" | tr '[:upper:]' '[:lower:]')" != "$wanted" ]; then
        die "tag '$tag' does not match PLUGIN_VERSION '$version' in $CONFIG_FILE

  A release tag must be exactly $wanted. Either re-tag this commit, or
  change PLUGIN_VERSION in src/drp/config.py and commit it first."
    fi
}

# The tag to check against, if there is one. An explicit --verify-tag
# wins; otherwise the tag on the commit being built is used, which is
# what catches a local release built from the wrong commit. A commit
# that carries no tag is not a release and skips the whole thing.
current_tag() {
    local explicit="$1"

    if [ -n "$explicit" ]; then
        printf '%s' "$explicit"
        return
    fi

    if command -v git >/dev/null 2>&1 && git -C "$ROOT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
        git -C "$ROOT_DIR" describe --tags --exact-match 2>/dev/null || true
    fi
}

# --- Steps ---------------------------------------------------------------------

# Checked up front so a missing tool is reported as such, instead of
# surfacing halfway through as an unrelated-looking failure.
require_tools() {
    local tool
    local missing=()

    for tool in curl tar zip; do
        command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
    done

    # The checksum is written with whatever the system provides: Linux
    # and Git Bash have sha256sum, macOS has shasum.
    if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
        missing+=("sha256sum or shasum")
    fi

    if [ ${#missing[@]} -eq 0 ]; then
        return
    fi

    die "missing required tool(s): ${missing[*]}

  Linux/macOS: install them with the system package manager.
  Windows:    install Git for Windows, which provides bash, curl and tar,
              then add zip itself - 'choco install zip', or 'pacman -S zip'
              from an MSYS2 shell. A WSL shell works as well."
}

# Note that the staging folder's contents do not exist yet: copy_plugin
# below creates the package folder, and adding it here first would make
# cp nest the plugin inside itself.
prepare_staging() {
    [ -d "$SRC_DIR" ] || die "source folder not found at $SRC_DIR"

    rm -rf "$DIST_DIR"
    mkdir -p "$STAGING_DIR" "$DOWNLOAD_DIR"
}

copy_plugin() {
    cp -r "$SRC_DIR" "$STAGING_DIR/drp"
}

# Downloads one source distribution and keeps only the importable package
# and its licence. The rest of the archive - tests, setup.py, packaging
# metadata - has no business inside the plugin.
fetch_vendored_package() {
    local name="$1" version="$2"
    local archive="$DOWNLOAD_DIR/$name-$version.tar.gz"
    local unpacked="$DOWNLOAD_DIR/$name-$version"

    echo "  $name $version"

    mkdir -p "$unpacked"
    curl -fsSL -o "$archive" "$(pypi_source_url "$name" "$version")" \
        || die "could not download $name $version - does that version exist?"

    # --strip-components=1 removes the <name>-<version>/ directory the
    # archive wraps its contents in.
    tar -xzf "$archive" -C "$unpacked" --strip-components=1 "$name-$version/$name" \
        || die "could not unpack $archive - is $name a source distribution?"

    mkdir -p "$VENDOR_DIR"
    mv "$unpacked/$name" "$VENDOR_DIR/$name"

    # The licence travels with the code: pypresence is MIT, and shipping
    # its terms is part of shipping it. It sits beside the package in the
    # archive rather than inside it, so the extraction above did not get
    # it and it has to be asked for by name. Not every distribution
    # ships one, and shipping third-party code without saying where it
    # came from is worth a warning rather than silence.
    local licence
    licence="$(tar -tzf "$archive" |
        grep -m1 -E "^$name-$version/[^/]*(LICENSE|LICENCE|COPYING)$" || true)"
    licence="${licence#"$name-$version/"}"

    if [ -n "$licence" ]; then
        tar -xzf "$archive" -C "$unpacked" --strip-components=1 \
            "$name-$version/$licence"
        cp "$unpacked/$licence" "$VENDOR_DIR/$name/LICENSE"
    else
        echo "  warning: $name $version ships no licence; add one to the zip" >&2
    fi
}

# The dependency list. Adding a third-party package is one line here and
# one version at the top - nothing else in the build changes.
fetch_vendors() {
    fetch_vendored_package pypresence "$PYPRESENCE_VERSION"
}

# The updater downloads the archive by the name in config.py, and the
# checksum from the same name plus config.UPDATE_CHECKSUM_SUFFIX. Both
# are read from there for exactly that reason.
read_config_value() {
    local name="$1"
    sed -n "s/^$name *= *\"\\(.*\\)\" *$/\\1/p" "$CONFIG_FILE"
}

strip_caches() {
    # The author's own settings must never ship: a release zip is unpacked
    # on top of an existing install, so everyone would silently inherit
    # the author's language and intervals.
    rm -f "$STAGING_DIR/drp/settings.json" "$STAGING_DIR/drp/settings.json.bak"

    find "$STAGING_DIR" -type d -name '__pycache__' -exec rm -rf {} +
    find "$STAGING_DIR" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete
}

create_archive() {
    # In a subshell so the build's own working directory stays put, and
    # with an absolute destination so the cd cannot break the output path.
    (cd "$STAGING_DIR" && zip -r -q "$DIST_DIR/$ZIP_NAME" drp)
}

# The plugin refuses to install an archive that does not match a
# published checksum, so the checksum is not an optional extra: without
# it the release this build produces cannot be installed at all.
create_checksum() {
    local suffix="$1"
    local output="$DIST_DIR/$ZIP_NAME$suffix"

    if command -v sha256sum >/dev/null 2>&1; then
        (cd "$DIST_DIR" && sha256sum "$ZIP_NAME" > "$(basename "$output")")
    else
        (cd "$DIST_DIR" && shasum -a 256 "$ZIP_NAME" > "$(basename "$output")")
    fi

    echo "  $(cat "$output")"
}

# --- Build ---------------------------------------------------------------------

main() {
    local version tag suffix

    version="$(read_config_value PLUGIN_VERSION)"
    ZIP_NAME="$(read_config_value UPDATE_ASSET_NAME)"
    suffix="$(read_config_value UPDATE_CHECKSUM_SUFFIX)"

    [ -n "$version" ] || die "cannot read PLUGIN_VERSION from $CONFIG_FILE"
    [ -n "$ZIP_NAME" ] || die "cannot read UPDATE_ASSET_NAME from $CONFIG_FILE"
    [ -n "$suffix" ] || die "cannot read UPDATE_CHECKSUM_SUFFIX from $CONFIG_FILE"

    tag="$(current_tag "${1:-}")"
    if [ -n "$tag" ]; then
        verify_tag "$tag" "$version"
        echo "Building $ZIP_NAME for $tag"
    else
        echo "Building $ZIP_NAME ($version)"
    fi

    require_tools
    prepare_staging
    copy_plugin
    fetch_vendors
    strip_caches
    create_archive
    create_checksum "$suffix"

    rm -rf "$STAGING_DIR" "$DOWNLOAD_DIR"

    echo "Done: dist/$ZIP_NAME"
    echo "      dist/$ZIP_NAME$suffix"
    echo "Extract the zip directly into Painter's python/plugins folder."
    echo "Publish both files as release assets; a release without the"
    echo "checksum cannot be installed."
}

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    --verify-tag)
        [ $# -ge 2 ] || die "--verify-tag needs a tag, e.g. --verify-tag v1.0.0"
        # An empty tag means the caller asked for verification and has
        # nothing to verify against - which is what CI passing an unset
        # $CI_COMMIT_TAG would look like. Refused rather than quietly
        # built, because "unverified" is the one outcome this option
        # exists to rule out.
        [ -n "$2" ] || die "--verify-tag was given an empty tag"
        main "$2"
        ;;
    "")
        main
        ;;
    *)
        die "unknown option: $1 (try --help)"
        ;;
esac
