# Changelog

All notable changes to this repository will be documented in this file.

## [0.1.2] - 2026-03-21
### Added
- Packaged Godot demo scene (`demo-godot.zip`) and smaller Godot/Unity plugin zips uploaded to release v0.1.2.

### Notes
- Release assets include `physics_room_splats-godot.zip`, `unity_plugin-0.1.0.zip`, and `demo-godot.zip`.

## [0.1.0] - 2026-03-21
### Added
- Initial game-plugin milestone: PLY `SplatExporter`, Godot add-on (editor + runtime loader), example exporter script, Godot shader scaffold, Unity and Unreal stubs, deterministic `GameLoop` helper, and gRPC Visualizer server.

### Notes
- Tagged and published releases: `v0.1.0` and `v0.1.2` (packaged artifacts).

## [0.2.0] - 2026-03-20
### Added
- Pluggable Hamiltonian registry and runtime APIs for adding extra Hamiltonian terms.
- Optional QuTiP backend support and SymPy symbolic-check hooks.
- Simple open-system helpers: thermal noise, Lindblad-like damping, and collapse operator plumbing.
- `chem_visualizer` utilities: `AtomicGaussianSplat`, STO-3G effective-alpha support, mesh-to-splats sampler, KDTree vertex mapping, and helpers to update splat coefficients.
- gRPC proto for SplatCloud messages and example client/server/streaming scripts.
- Godot MultiMesh splat renderer and auto-reload script for live visualization.
- Benchmark and example scripts demonstrating harmonic convergence and splat export/streaming.

### Changed
- Bumped package version to `0.2.0`.

### Fixed
- Cleaned duplicate imports and adjusted optional-dependency fallbacks.

### Notes
- Some optional features (QuTiP, SymPy, trimesh, matplotlib) are gated behind optional dependencies; see `pyproject.toml` optional-dependencies for details.
