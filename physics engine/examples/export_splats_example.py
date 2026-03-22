"""Example: build a small molecule as Gaussian splats and export to PLY/JSON.

Run from repository root with PYTHONPATH pointing at the engine `src`:

  PYTHONPATH="physics engine/src" .venv/bin/python "physics engine/examples/export_splats_example.py"

"""
from __future__ import annotations

import os

from physics_engine.chem_visualizer import build_molecule_splats, write_splats_json
from physics_engine.exporter import SplatExporter


def main():
    # simple water geometry example
    geometry = [[0.0, 0.0, 0.0], [0.9572, 0.0, 0.0], [-0.2390, 0.9270, 0.0]]
    splats = build_molecule_splats("H2O", geometry=geometry, use_sto3g=False)

    out_dir = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(out_dir, exist_ok=True)

    ply_path = os.path.join(out_dir, "example_splats.ply")
    json_path = os.path.join(out_dir, "example_splats.json")

    write_splats_json(json_path, splats)
    SplatExporter.save_ply(ply_path, splats)

    print("Wrote:", json_path)
    print("Wrote:", ply_path)


if __name__ == "__main__":
    main()
