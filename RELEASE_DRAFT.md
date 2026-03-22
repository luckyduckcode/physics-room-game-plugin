# Release v0.1.0 — Game plugin milestone (Draft)

Branch: `main`

## PR Title

feat(release): v0.1.0 — game-plugin milestone

## PR Body

This release collects the initial game-plugin work enabling export and
visualization of Gaussian "splats" in game engines. Changes included in
this milestone:

- `physics engine/src/physics_engine/exporter.py` — `SplatExporter.save_ply()` to write ASCII PLY point clouds.
- `physics engine/examples/export_splats_example.py` — example that emits JSON + PLY (`physics engine/examples/out/`).
- Godot add-on scaffold: `godot_scene_bundle/addons/physics_room_splats/` (`plugin.cfg`, editor helper, runtime loader).
- Godot runtime loader: `godot_scene_bundle/addons/physics_room_splats/runtime_loader.gd` and example scene `godot_scene_bundle/scenes/example_splat_scene.tscn`.
- Unity UPM stub: `unity_plugin/package.json`, `unity_plugin/Runtime/SplatLoader.cs` to load PLY into a ParticleSystem.

See `GAME_PLUGIN_QUICKSTART.md` for run steps and notes.

## Release Notes (summary)

Initial game-plugin milestone:
- Export splats from the physics engine to PLY/JSON
- Minimal Godot add-on + runtime loader for quick visualization
- Unity stub to demonstrate cross-engine import pattern

## Post-merge steps

1. Create a Git tag `v0.1.0` and push it:

```bash
git tag -a v0.1.0 -m "v0.1.0: game-plugin milestone — Godot add-on, exporter, examples"
git push origin v0.1.0
```

2. Publish a GitHub release (draft) using the content above (attach `GAME_PLUGIN_QUICKSTART.md`/`CHANGELOG.md` as desired).
