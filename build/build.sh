#!/usr/bin/env bash
# Packages src/drp into dist/DRP_AS3DP-python.zip
#
# Usage:
#   ./build/build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$ROOT_DIR/src/drp"
DIST_DIR="$ROOT_DIR/dist"

ZIP_NAME="DRP_AS3DP-python.zip"

if [ ! -d "$SRC_DIR" ]; then
    echo "error: source folder not found at $SRC_DIR" >&2
    exit 1
fi

echo "Building DRP_AS3DP-python"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/staging"

# Copy the plugin package, then strip anything that shouldn't ship:
# caches, bytecode, and OS cruft. Plain cp+find instead of rsync so
# this doesn't depend on rsync being installed.
cp -r "$SRC_DIR" "$DIST_DIR/staging/"
find "$DIST_DIR/staging" -type d -name '__pycache__' -exec rm -rf {} +
find "$DIST_DIR/staging" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete

cd "$DIST_DIR/staging"
zip -r -q "../$ZIP_NAME" drp
cd "$ROOT_DIR"

rm -rf "$DIST_DIR/staging"

echo "Done: dist/${ZIP_NAME}"
echo "Extract '$ZIP_NAME' directly into your Painter python/plugins folder."
