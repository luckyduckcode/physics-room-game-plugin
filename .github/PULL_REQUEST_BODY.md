Title: Refactor Godot runtime loader into reusable `SplatLoader` class

Summary
-------
This PR moves the PLY parsing, selection, and MultiMesh-building logic out of
`runtime_loader.gd` into a small reusable Reference class `SplatLoader` under
`addons/physics_room_splats/runtime/loader.gd` and updates
`runtime_loader.gd` to use that helper. The change preserves the existing
exported properties and runtime behavior while making the core logic easier to
reuse and test.

Files changed (high-level)
- Added: `godot_scene_bundle/addons/physics_room_splats/runtime/loader.gd` (new)
- Updated: `godot_scene_bundle/addons/physics_room_splats/runtime_loader.gd`
- Added: `godot_scene_bundle/addons/physics_room_splats/runtime/README.md`

Why
---
- Improves separation of concerns: parsing & selection logic is decoupled from
  scene/node lifecycle.
- Enables reusing `SplatLoader` from editor tools or other scripts.
- Prepares the codebase for unit tests around parsing/selection.

Behavioral notes
----------------
- The public `RuntimeSplatLoader` API is unchanged: exported properties,
  auto-update behavior, and shader/material selection are preserved.
- The `SplatLoader` class returns arrays and builds `MultiMeshInstance3D`
  children under a provided owner node when requested.

Testing
-------
1. Open Godot project and enable the `Physics Room Splats` plugin.
2. Open `res://addons/physics_room_splats/example_splat_scene.tscn` and run.
3. Confirm splats load, LOD auto-updates, and materials/shader apply.

Follow-ups
----------
- Add unit tests for `SplatLoader.load_ply()` parsing behavior.
- Add editor API to preview subsets in the editor and a small tool script.

If you want me to create the PR on GitHub, I can do so if you provide a
Personal Access Token with `repo` scope, or you can create the pull request via
the UI using this URL:

https://github.com/luckyduckcode/physics-room/compare/main...feat/godot-loader-refactor?expand=1
