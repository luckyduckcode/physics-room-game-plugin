# Physics Room Splats — Unity stub

This folder contains a minimal Unity package stub that demonstrates how to
load ASCII PLY exports produced by the physics engine into Unity using a
ParticleSystem. It's intended as a starting point for a full Unity package.

Usage
1. Copy `unity_plugin` into `Packages/` or use `manifest.json` to reference it.
2. Add the `SplatLoader.cs` script to a GameObject with a ParticleSystem.
3. Set `plyPath` to the exported PLY (relative to `Application.dataPath` or an absolute path).

Notes
- This is a simple, synchronous loader for small point clouds. For large datasets use streaming or GPU instancing.
