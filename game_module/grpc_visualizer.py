"""gRPC Visualizer server for receiving SplatCloud messages and exporting PLY.

Starts a simple gRPC server implementing the `Visualizer` service defined in
`physics_engine/src/physics_engine/grpc/splats.proto`. Received splats are
written to disk as ASCII PLY using `physics_engine.exporter.SplatExporter`.
"""
from concurrent import futures
import logging
import os

import grpc

from physics_engine.grpc._generated import splats_pb2_grpc, splats_pb2
from physics_engine.exporter import SplatExporter


class VisualizerServicer(splats_pb2_grpc.VisualizerServicer):
    def __init__(self, out_ply_path: str):
        self.out_ply_path = os.path.abspath(out_ply_path)

    def SendSplatCloud(self, request, context):
        # Convert proto splats to dicts compatible with SplatExporter
        objs = []
        for s in request.splats:
            center = list(s.center) if s.center else [0.0, 0.0, 0.0]
            color = list(s.color) if s.color else [200, 200, 200]
            # proto color may be floats 0..1 or 0..255; normalize if >1
            if any(c > 1.01 for c in color):
                color = [c / 255.0 for c in color]
            objs.append({
                "atom": s.atom or "X",
                "center": center,
                "alpha": float(s.alpha or 1.0),
                "coeff": float(s.coeff or 1.0),
                "color": color,
            })

        # Ensure output dir exists
        os.makedirs(os.path.dirname(self.out_ply_path), exist_ok=True)
        try:
            SplatExporter.save_ply(self.out_ply_path, objs)
            return splats_pb2.Ack(ok=True, message=f"Wrote {len(objs)} splats to {self.out_ply_path}")
        except Exception as e:
            logging.exception("Failed to write PLY")
            return splats_pb2.Ack(ok=False, message=str(e))


def serve(port: int = 50051, out_ply_path: str = "godot_scene_bundle/examples/out/streamed_splats.ply"):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    servicer = VisualizerServicer(out_ply_path=out_ply_path)
    splats_pb2_grpc.add_VisualizerServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info("Visualizer gRPC server started on port %d, writing to %s", port, out_ply_path)
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutting down server")
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
