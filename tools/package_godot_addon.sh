#!/usr/bin/env bash
# Package the Godot add-on into a zip suitable for distribution.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
ADDON_DIR="$ROOT_DIR/godot_scene_bundle/addons/physics_room_splats"
OUT_DIR="$ROOT_DIR/release"
OUT_ZIP="$OUT_DIR/physics_room_splats-godot.zip"

mkdir -p "$OUT_DIR"
if [ ! -d "$ADDON_DIR" ]; then
  echo "Add-on directory not found: $ADDON_DIR" >&2
  exit 1
fi

pushd "$ADDON_DIR" >/dev/null
zip -r "$OUT_ZIP" . >/dev/null
popd >/dev/null

echo "Created Godot add-on package: $OUT_ZIP"
