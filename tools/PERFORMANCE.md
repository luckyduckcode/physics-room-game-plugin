Splat Export Performance

This document records a small micro-benchmark for `SplatExporter.save_ply`.

Run the benchmark:

```bash
python3 tools/benchmark_splats.py
```

This will generate `tools/out/splats_<N>.ply` files and print timings and sizes.

Notes
- The benchmark runs entirely in Python and measures exporter IO + formatting cost.
- For GPU/runtime rendering performance use the Godot demo and profile inside the engine.
 
Sample run (times will vary by machine):

```
Splat export benchmark
Output dir: tools/out
Wrote 1000 splats -> tools/out/splats_1000.ply in 0.03s (26205 bytes)
Wrote 5000 splats -> tools/out/splats_5000.ply in 0.01s (130205 bytes)
Wrote 20000 splats -> tools/out/splats_20000.ply in 0.06s (520206 bytes)
Wrote 50000 splats -> tools/out/splats_50000.ply in 0.05s (1300206 bytes)

Summary:
 1000 splats: 0.03s, 26205 bytes, 26.2 bytes/splat
 5000 splats: 0.01s, 130205 bytes, 26.0 bytes/splat
20000 splats: 0.06s, 520206 bytes, 26.0 bytes/splat
50000 splats: 0.05s, 1300206 bytes, 26.0 bytes/splat
```
