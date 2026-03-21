# The Physics Room Workspace

This workspace contains a complete local simulation stack for quantum-classical experiments.

## Workspace Contents
- elements table/
- physics engine/
- room:mainfold/
- tools/

## Core Capabilities
- Hamiltonian-based quantum simulation.
- Chemical formula parsing and molar mass computation.
- Virtual STM and spectroscopy probing.
- AI anomaly event generation.
- Unified session/tick/event API.
- gRPC contract and service implementation.
- Benchmark scenarios for model credibility.
- Notebook-based post-run analysis.

## Start Here
1. Read [physics engine/README.md](physics%20engine/README.md)
2. Read [HOW_TO_USE.md](HOW_TO_USE.md)
3. Review [WHITE_PAPER_PHYSICS_ROOM.md](WHITE_PAPER_PHYSICS_ROOM.md)

## Quick Validation
From [physics engine](physics%20engine):
- Run tests with `PYTHONPATH=src <python> -m pytest`

## Unified API Endpoints
- `POST /session/start`
- `POST /tick/run?session_id=<id>`
- `GET /session/{session_id}/state`
- `GET /session/{session_id}/events`
- `WS /ws/sessions/{session_id}/events`

## Additional Runtime Interfaces
- gRPC proto: [physics engine/src/physics_engine/grpc/physics_room.proto](physics%20engine/src/physics_engine/grpc/physics_room.proto)
- gRPC server launcher: [physics engine/run_grpc_server.py](physics%20engine/run_grpc_server.py)
- Benchmarks: [physics engine/benchmarks/run_benchmarks.py](physics%20engine/benchmarks/run_benchmarks.py)
- Notebook analysis: [notebooks/results_analysis.ipynb](notebooks/results_analysis.ipynb)

## Notes
- `use_real_modules=false` gives stable local fallback behavior.
- `enable_ai=true` enables `ai.anomaly` event emission.

## Benchmarks & Notebooks

- See the harmonic oscillator benchmark summary: [physics engine/notebooks/BENCHMARK_RESULTS.md](physics%20engine/notebooks/BENCHMARK_RESULTS.md)
- Notebook with runnable cell: [physics engine/notebooks/benchmark_results.ipynb](physics%20engine/notebooks/benchmark_results.ipynb)


## Godot Add-on (Quick Install)

Install the packaged Godot add-on to a Godot project:

1. Download `physics_room_splats-godot.zip` from the release assets (see the Releases page).
2. In your Godot project directory, create `addons/` if it doesn't exist and unzip the package there:

```bash
mkdir -p /path/to/your-godot-project/addons
unzip physics_room_splats-godot.zip -d /path/to/your-godot-project/addons/
```

3. Open the project in Godot, go to `Project -> Project Settings -> Plugins`, and enable `Physics Room Splats`.

4. Open the example scene `res://addons/physics_room_splats/example_splat_scene.tscn` or add a `RuntimeSplatLoader` node and point it at a `.ply` splat file to load.

Notes: the add-on includes `runtime_loader.gd` (MultiMesh loader with LOD/chunking) and `shaders/gaussian_splat.shader` for simple GPU splatting.

