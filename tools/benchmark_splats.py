#!/usr/bin/env python3
"""Simple benchmark for SplatExporter.save_ply performance.

Generates random splat clouds of increasing size, writes PLY files, and
reports timing and file sizes. Run from the repo root:

  python3 tools/benchmark_splats.py

"""
import os
import sys
import time
import random


def ensure_path():
    # Add physics engine src to path (handles space in 'physics engine')
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pe_src = os.path.join(repo_root, "physics engine", "src")
    if pe_src not in sys.path:
        sys.path.insert(0, pe_src)


def make_splats(n):
    for i in range(n):
        yield {
            "center": (random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10)),
            "color": (random.random(), random.random(), random.random()),
            "alpha": 1.0,
            "coeff": random.random() * 2.0,
        }


def run():
    ensure_path()
    # Import exporter directly from source file to avoid importing heavy package deps
    try:
        import importlib.util
        exporter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "physics engine", "src", "physics_engine", "exporter.py")
        exporter_path = os.path.abspath(exporter_path)
        spec = importlib.util.spec_from_file_location("splat_exporter", exporter_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        SplatExporter = mod.SplatExporter
    except Exception as e:
        print("Could not load SplatExporter from file:", exporter_path, e)
        sys.exit(1)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out_dir, exist_ok=True)

    sizes = [1000, 5000, 20000, 50000]
    print("Splat export benchmark")
    print("Output dir:", out_dir)
    results = []
    for n in sizes:
        splats = list(make_splats(n))
        out = os.path.join(out_dir, f"splats_{n}.ply")
        t0 = time.time()
        SplatExporter.save_ply(out, splats, ascii=True)
        dt = time.time() - t0
        size = os.path.getsize(out)
        print(f"Wrote {n} splats -> {out} in {dt:.3f}s ({size} bytes)")
        results.append((n, dt, size))

    print("\nSummary:")
    for n, dt, size in results:
        print(f"{n:6d} splats: {dt:.3f}s, {size} bytes, {size/n:.1f} bytes/splat")


if __name__ == "__main__":
    run()
