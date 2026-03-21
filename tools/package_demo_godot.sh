#!/usr/bin/env bash
set -euo pipefail

# Package a small Godot demo scene and supporting scripts into release/demo-godot.zip
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/release"
mkdir -p "$OUT_DIR"

ZIP_PATH="$OUT_DIR/demo-godot.zip"
rm -f "$ZIP_PATH"

echo "Creating demo zip: $ZIP_PATH"
(
  cd "$ROOT"
  zip -r "$ZIP_PATH" \
    godot_scene_bundle/scenes/example_splat_scene.tscn \
    godot_scene_bundle/scenes/entity.tscn \
    godot_scene_bundle/scripts/entity.gd 2>/dev/null || true
)

echo "Created $ZIP_PATH"
