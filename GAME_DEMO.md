Game-friendly demo (Godot integration)
====================================

Quick steps to run the Python demo and view splats/events from Godot:

1. Create and activate a Python virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r "physics engine/requirements-dev.txt"
```

2. Run the anomaly demo which writes JSON files for Godot to consume:

```bash
.venv/bin/python "physics engine/examples/anomaly_demo.py"
# Output files: physics engine/examples/examples_output/splats.json
#               physics engine/examples/examples_output/events.json
```

3. In Godot (4.x):
   - Open `godot_scene_bundle/project.godot` as a project.
   - Instance or open `godot_scene_bundle/scenes/GameBridge.tscn`.
   - Configure the `GameBridge` node exported paths to point to the demo output (or copy files to `user://` path).
   - Run the scene; `GameBridge` will reload `splats.json` and `events.json` periodically and display score/flash on anomalies.

Notes:
- Use the MultiMesh renderer (`godot_scene_bundle/AtomicSplatMultimeshRenderer.tscn`) for per-instance color/alpha (supported by the example scene).
- To stream splats to an external visualizer instead of JSON, see `physics engine/examples/grpc_send_splats.py` and `physics engine/examples/grpc_splat_server.py`.
