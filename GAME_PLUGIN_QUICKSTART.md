# Physics Room — Game Plugin Quickstart

This file documents the minimal game-plugin scaffolding added to the repository.

What was added
- `godot_scene_bundle/addons/physics_room_splats/` — Godot add-on scaffold (editor button + runtime loader)
- `godot_scene_bundle/addons/physics_room_splats/runtime_loader.gd` — runtime PLY loader (MultiMesh)
- `godot_scene_bundle/scenes/example_splat_scene.tscn` — example scene that uses the loader
- `physics engine/src/physics_engine/exporter.py` — `SplatExporter.save_ply()` to write PLY files
- `physics engine/examples/export_splats_example.py` — example that writes JSON + PLY to `physics engine/examples/out/`

Quick run
1. Activate virtualenv and run the exporter example:
```bash
cd path/to/physics-room
PYTHONPATH="physics engine/src" .venv/bin/python "physics engine/examples/export_splats_example.py"
```

2. Open Godot, enable the plugin: Project → Project Settings → Plugins → `Physics Room Splats`.
3. Open `godot_scene_bundle/scenes/example_splat_scene.tscn` and run the scene.

Notes
- The loader expects an ASCII PLY with per-vertex: x y z r g b alpha coeff.
- The loader expects an ASCII PLY with per-vertex: x y z r g b alpha coeff.
- A simple Gaussian splat shader scaffold is included at `godot_scene_bundle/addons/physics_room_splats/shaders/gaussian_splat.shader` — use it as a starting point for a production GPU splat material (tweak `falloff` and `intensity`, or replace with a more advanced additive/LOD shader).
- To support Unity/Unreal, create `unity_plugin/` or `unreal_plugin/` stubs and implement runtime loaders that read the same PLY/JSON exported format.
