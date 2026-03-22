Runtime utilities for the Physics Room Splats Godot add-on.

`SplatLoader` is a small reusable Reference class that handles parsing
ASCII PLY splat files, selecting nearest splats to a camera, and building
`MultiMeshInstance3D` chunks you can add to a scene node.

Usage (in GDScript):

```
var loader = SplatLoader.new()
loader.load_ply("res://path/to/splats.ply")
var indices = loader.selected_indices_nearest(get_viewport().get_camera_3d(), 20000)
var instances = loader.build_multimesh_instances(self, indices, 0.06, "res://addons/physics_room_splats/shaders/gaussian_splat.shader")
```

Tests
-----
There's a small test runner and sample PLY under `tests/` you can run in the
Godot editor or via the command line. To run in-editor, open
`res://addons/physics_room_splats/tests/test_loader.gd` as a scene and run it —
it will print `TEST PASSED` or `TEST FAILED` in the output panel.

