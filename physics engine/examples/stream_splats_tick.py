"""Stream splats periodically from the engine by calling `build_molecule_splats`
and sending via gRPC to a Visualizer service.

Usage:
  python stream_splats_tick.py H2O --interval 0.5
"""
from __future__ import annotations
import time
import argparse

try:
    from physics_engine.chem_visualizer import build_molecule_splats
except Exception:
    print('chem_visualizer not available')
    raise


def send_cloud(splats, addr='localhost:50051'):
    try:
        from physics_engine.grpc._generated import splats_pb2, splats_pb2_grpc
        import grpc
    except Exception:
        print('gRPC bindings not generated; run physics engine/scripts/generate_protos.sh')
        raise

    cloud = splats_pb2.SplatCloud(source_id='stream-splats')
    for s in splats:
        cloud.splats.append(splats_pb2.Splat(atom=s.atom, center=s.center.tolist(), alpha=float(s.alpha), coeff=float(s.coeff), color=list(s.color)))

    with grpc.insecure_channel(addr) as ch:
        stub = splats_pb2_grpc.VisualizerStub(ch)
        resp = stub.SendSplatCloud(cloud)
        print('sent', len(splats), 'splats ->', resp.message)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('formula')
    p.add_argument('--interval', type=float, default=1.0)
    p.add_argument('--addr', default='localhost:50051')
    args = p.parse_args()

    while True:
        splats = build_molecule_splats(args.formula)
        try:
            send_cloud(splats, addr=args.addr)
        except Exception as e:
            print('send failed:', e)
        time.sleep(args.interval)
