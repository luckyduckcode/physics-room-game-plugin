#!/usr/bin/env bash
# Create a zip of the `unity_plugin` folder for distribution/import.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
PKG_DIR="$ROOT_DIR/unity_plugin"
OUT_DIR="$ROOT_DIR/release"
OUT_ZIP="$OUT_DIR/unity_plugin-0.1.0.zip"

mkdir -p "$OUT_DIR"
if [ ! -d "$PKG_DIR" ]; then
  echo "Unity plugin directory not found: $PKG_DIR" >&2
  exit 1
fi

pushd "$PKG_DIR" >/dev/null
zip -r "$OUT_ZIP" . >/dev/null
popd >/dev/null

echo "Created Unity package zip: $OUT_ZIP"
