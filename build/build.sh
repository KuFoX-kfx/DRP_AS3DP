#!/usr/bin/env bash
# Builds the distributable plugin zip: dist/DRP_AS3DP-python.zip
#
# Usage:
#   ./build/build.sh          (Linux, macOS)
#   bash build/build.sh       (Windows, from a Git Bash shell)
#
# Third-party code is not kept in the repository. The one package the
# plugin needs is downloaded from PyPI here, at build time, and lands in
# the staging copy only. See "Building a distributable zip" in README.md
# for the tools this needs.

set -euo pipefail

# --- Dependencies --------------------------------------------------------------

# The one place a version is changed. build.sh derives the download URL
# from the name and this value, so bumping a dependency is a one-line
# edit and nothing else has to know about it.
PYPRESENCE_VERSION="4.6.2"

ZIP_NAME="DRP_AS3DP-python.zip"

# --- Paths ---------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$ROOT_DIR/src/drp"
DIST_DIR="$ROOT_DIR/dist"

# Everything below is thrown away at the end of the build.
STAGING_DIR="$DIST_DIR/staging"          # the plugin, as it will be zipped
DOWNLOAD_DIR="$DIST_DIR/download"        # fetched archives and their unpacked form
VENDOR_DIR="$STAGING_DIR/drp/vendor"     # third-party code inside the package

# --- Helpers -------------------------------------------------------------------

die() {
    echo "error: $*" >&2
    exit 1
}

# PyPI serves every source distribution from a predictable path that needs
# no content hash, so no JSON API and no JSON parser are required:
#   .../source/<first letter>/<name>/<name>-<version>.tar.gz
pypi_source_url() {
    local name="$1" version="$2"
    printf 'https://files.pythonhosted.org/packages/source/%s/%s/%s-%s.tar.gz' \
        "${name:0:1}" "$name" "$name" "$version"
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
    # its terms is part of shipping it.
    if [ -f "$unpacked/LICENSE" ]; then
        cp "$unpacked/LICENSE" "$VENDOR_DIR/$name/LICENSE"
    fi
}

# The dependency list. Adding a third-party package is one line here and
# one version at the top - nothing else in the build changes.
fetch_vendors() {
    fetch_vendored_package pypresence "$PYPRESENCE_VERSION"
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

# --- Build ---------------------------------------------------------------------

main() {
    echo "Building $ZIP_NAME"

    require_tools
    prepare_staging
    copy_plugin
    fetch_vendors
    strip_caches
    create_archive

    rm -rf "$STAGING_DIR" "$DOWNLOAD_DIR"

    echo "Done: dist/$ZIP_NAME"
    echo "Extract it directly into Painter's python/plugins folder."
}

main "$@"
