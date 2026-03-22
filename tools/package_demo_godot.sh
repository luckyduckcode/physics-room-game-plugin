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
  files=(
    "godot_scene_bundle/scenes/example_splat_scene.tscn"
    "godot_scene_bundle/scenes/entity.tscn"
    "godot_scene_bundle/scripts/entity.gd"
  )
  found=()
  for f in "${files[@]}"; do
    if [ -e "$f" ]; then
      found+=("$f")
    else
      echo "Warning: missing file $f — skipping"
    fi
  done
  if [ ${#found[@]} -eq 0 ]; then
    echo "No demo files found; creating empty zip with README" >/dev/stderr
    echo "Demo files not present" > demo-README.txt
    zip -r "$ZIP_PATH" demo-README.txt >/dev/null
    rm -f demo-README.txt
  else
    zip -r "$ZIP_PATH" "${found[@]}"
  fi
)

echo "Created $ZIP_PATH"
