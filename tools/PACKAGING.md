# Packaging helper

This folder contains helper scripts to create distributable packages for the
game-plugin components.

Scripts
- `tools/package_godot_addon.sh`: zips `godot_scene_bundle/addons/physics_room_splats/` into `release/physics_room_splats-godot.zip`.
- `unity_plugin/package_unity_zip.sh`: zips `unity_plugin/` into `release/unity_plugin-0.1.0.zip`.

Usage (from repository root):
```bash
./tools/package_godot_addon.sh
./unity_plugin/package_unity_zip.sh
```

The scripts create a `release/` folder with the packaged artifacts.
