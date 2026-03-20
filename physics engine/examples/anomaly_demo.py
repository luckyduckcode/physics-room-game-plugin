"""Demo: run a small loop and emit splats + anomaly events to JSON for Godot.

Writes to `examples_output/splats.json` and `examples_output/events.json`.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import sys
from pathlib import Path

# Ensure local package `physics_engine` is importable when running this script
here = Path(__file__).resolve()
srcdir = here.parent.parent / "src"
sys.path.insert(0, str(srcdir))

from physics_engine.chem_visualizer import build_molecule_splats, write_splats_json, apply_game_effect
from physics_engine.gameplay import AnomalyManager


OUT_DIR = Path(__file__).resolve().parent / "examples_output"
OUT_DIR.mkdir(exist_ok=True)


def write_events(path: Path, events, score: int = 0):
    with open(path, "w") as f:
        json.dump({"events": events, "score": int(score)}, f, indent=2)


def run_demo(formula: str = "H2O", duration: float = 6.0, interval: float = 0.5):
    mgr = AnomalyManager(chance_per_second=0.5, seed=123)
    t0 = time.time()
    last = t0
    while time.time() - t0 < duration:
        now = time.time()
        splats = build_molecule_splats(formula)
        evt = mgr.maybe_trigger(now)
        if evt is not None:
            # apply a pulse effect when anomaly occurs
            apply_game_effect(splats, "anomaly_pulse", engine_time=now, params={"freq": 8.0, "amp": 0.6, "base": 1.0})
            mgr.award_points(100)

        # write out current splats and events for Godot to pick up
        write_splats_json(str(OUT_DIR / "splats.json"), splats)
        write_events(OUT_DIR / "events.json", mgr.export_events(), mgr.score)

        # simple throttling
        time.sleep(interval)

    print("Demo complete. Events:", mgr.export_events())


if __name__ == "__main__":
    run_demo()
