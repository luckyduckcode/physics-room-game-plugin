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



## Game Plugin Integration (Godot, Unity, Unreal)

Physics Room now supports direct export and visualization of Gaussian "splats" in popular game engines:

- **Godot**: Add-on for loading and rendering splat point clouds. Includes runtime loader, example scene, and shader scaffold.
- **Unity**: Minimal loader stub for importing PLY splats into a ParticleSystem.
- **Unreal**: Plugin scaffold for teams to implement a native or Blueprint-based PLY loader.

### Quickstart

See [GAME_PLUGIN_QUICKSTART.md](GAME_PLUGIN_QUICKSTART.md) for step-by-step instructions to export splats and use the Godot add-on. Example:

1. Export splats from the physics engine (see exporter example in `physics engine/examples/export_splats_example.py`).
2. For Godot, download `physics_room_splats-godot.zip` from the release assets and unzip to your project's `addons/` folder.
3. Enable the plugin in Godot and open the example scene or add the loader to your own scene.
4. For Unity/Unreal, see the respective plugin folders for usage and extension notes.

Release assets include:
- `physics_room_splats-godot.zip` (Godot add-on)
- `unity_plugin-0.1.0.zip` (Unity stub)
- `demo-godot.zip` (Godot demo project)

For more, see:
- [GAME_PLUGIN_QUICKSTART.md](GAME_PLUGIN_QUICKSTART.md)
- [CHANGELOG.md](CHANGELOG.md)
- [RELEASE_DRAFT.md](RELEASE_DRAFT.md)

---

