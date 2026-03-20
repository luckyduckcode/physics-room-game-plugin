"""Example gRPC client that sends a SplatCloud to a Visualizer service.

Before running, generate the Python bindings with:

  cd "physics engine/scripts"
  ./generate_protos.sh

Then run the server (see grpc_splat_server.py) and run this client.
"""
import json
import sys
import time

try:
    from physics_engine.grpc._generated import splats_pb2, splats_pb2_grpc
    import grpc
except Exception:
    print("Protobuf bindings not generated. Run physics engine/scripts/generate_protos.sh first.")
    sys.exit(1)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def make_splat_message(d):
    return splats_pb2.Splat(
        atom=d.get('atom','X'),
        center=d.get('center', []),
        alpha=float(d.get('alpha', 0.1)),
        coeff=float(d.get('coeff', 1.0)),
        color=[float(x) for x in d.get('color', [0.8,0.8,0.8])]
    )


def send(path, addr='localhost:50051'):
    data = load_json(path)
    splats = data.get('splats', [])
    cloud = splats_pb2.SplatCloud(source_id='example-send')
    for s in splats:
        cloud.splats.append(make_splat_message(s))

    with grpc.insecure_channel(addr) as ch:
        stub = splats_pb2_grpc.VisualizerStub(ch)
        resp = stub.SendSplatCloud(cloud)
        print('Server response:', resp.ok, resp.message)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: grpc_send_splats.py <splats.json> [address]')
        sys.exit(1)
    path = sys.argv[1]
    addr = sys.argv[2] if len(sys.argv) > 2 else 'localhost:50051'
    send(path, addr)
