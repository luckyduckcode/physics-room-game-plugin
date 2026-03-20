# Release v0.2.0 Draft

Branch: `release/v0.2.0`

## PR Title

chore(release): v0.2.0

## PR Body

This release collects the following changes:

- Pluggable Hamiltonian registry and runtime APIs for adding extra Hamiltonian terms.
- Optional QuTiP backend support and SymPy symbolic-check hooks.
- Open-system helpers: thermal noise, Lindblad-like damping, and collapse operator plumbing.
- `chem_visualizer` utilities: `AtomicGaussianSplat`, STO-3G effective-alpha proxy, mesh-to-splats sampler, KDTree vertex mapping, and helpers to update splat coefficients.
- gRPC proto for SplatCloud messages and example client/server/streaming scripts.
- Godot MultiMesh splat renderer and auto-reload script for live visualization.
- Benchmarks and example scripts demonstrating harmonic convergence and splat export/streaming.
- CI improvements: `ruff` lint step and pip caching; various lint fixes across the repo.

See `CHANGELOG.md` for details.

## Release Notes (summary)

See `CHANGELOG.md` for the full set of notes. Key highlights:
- Modular Hamiltonian and open-system features for the physics engine.
- Visualization pipeline: splat generator, gRPC proto, Godot renderer and file-watcher.
- Linting fixes and CI improvements to keep the tree healthy.

## Post-merge steps

1. Create a Git tag `v0.2.0` and push it:

```bash
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

2. Create a GitHub release (draft) and attach `CHANGELOG.md` as release notes.
