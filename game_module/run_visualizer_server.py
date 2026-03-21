"""Run the gRPC Visualizer server (convenience runner).

Usage:
  PYTHONPATH="physics engine/src" .venv/bin/python game_module/run_visualizer_server.py

"""
from __future__ import annotations

import argparse
from game_module import grpc_visualizer


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=50051)
    p.add_argument("--out", type=str, default="godot_scene_bundle/examples/out/streamed_splats.ply")
    args = p.parse_args()
    grpc_visualizer.serve(port=args.port, out_ply_path=args.out)


if __name__ == "__main__":
    main()
