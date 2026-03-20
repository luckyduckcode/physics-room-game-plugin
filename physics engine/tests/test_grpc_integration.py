import time
from concurrent import futures
from typing import Iterator

import pytest


grpc = pytest.importorskip("grpc")

from physics_engine.grpc import physics_room_pb2 as pb2  # type: ignore[import-not-found]
from physics_engine.grpc import physics_room_pb2_grpc as pb2_grpc  # type: ignore[import-not-found]
from physics_engine.grpc.client import call_with_retry  # type: ignore[import-not-found]
from physics_engine.grpc.server import ApiKeyAuthInterceptor, PhysicsRoomGrpcService  # type: ignore[import-not-found]


@pytest.fixture
def grpc_server() -> Iterator[tuple[str, int]]:
    host = "127.0.0.1"
    port = 7006
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    pb2_grpc.add_PhysicsRoomServiceServicer_to_server(PhysicsRoomGrpcService(), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    time.sleep(0.1)
    try:
        yield host, port
    finally:
        server.stop(0)


@pytest.fixture
def grpc_server_auth() -> Iterator[tuple[str, int]]:
    host = "127.0.0.1"
    port = 7007
    key_map = {"alpha-secret": "team-alpha", "beta-secret": "team-beta"}
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        interceptors=[ApiKeyAuthInterceptor(key_map)],
    )
    pb2_grpc.add_PhysicsRoomServiceServicer_to_server(PhysicsRoomGrpcService(key_map), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    time.sleep(0.1)
    try:
        yield host, port
    finally:
        server.stop(0)


def test_grpc_roundtrip(grpc_server: tuple[str, int]) -> None:
    host, port = grpc_server
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb2_grpc.PhysicsRoomServiceStub(channel)

        start = call_with_retry(
            stub.StartSession,
            pb2.StartSessionRequest(
                config=pb2.SessionConfig(
                    session_id="grpc-it",
                    system_name="Double Pendulum",
                    N=12,
                    dt=0.02,
                    hbar=1.0,
                    omega=1.0,
                    phi=2.718281828,
                    lam=0.05,
                    kappa=0.01,
                    enable_ai=False,
                    use_real_modules=False,
                    seed=42,
                    grid_x=32,
                    grid_y=32,
                    grid_z=32,
                )
            ),
        )
        assert start.ok is True
        assert start.session_id.endswith(":grpc-it")
        assert start.metadata.config_hash
        assert start.taxonomy.fields["status"].string_value == "matched"
        assert start.taxonomy.fields["system"].string_value == "Double Pendulum"
        assert start.state.taxonomy.fields["status"].string_value == "matched"

        run = call_with_retry(stub.TickRun, pb2.TickRunRequest(session_id=start.session_id, steps=3))
        assert run.ok is True
        assert run.final_tick == 3
        assert len(run.events) >= 3

        state = call_with_retry(stub.GetSessionState, pb2.GetSessionStateRequest(session_id=start.session_id))
        assert state.ok is True
        assert state.state.tick == 3
        assert state.state.taxonomy.fields["status"].string_value == "matched"

        events = call_with_retry(
            stub.GetSessionEvents,
            pb2.GetSessionEventsRequest(session_id=start.session_id, after_sequence=0, limit=5),
        )
        assert events.ok is True
        assert len(events.events) >= 1
        first = events.events[0]
        assert first.event_type == "session.lifecycle"
        taxonomy = first.payload.fields["taxonomy"].struct_value
        assert taxonomy.fields["status"].string_value == "matched"
        assert taxonomy.fields["system"].string_value == "Double Pendulum"


def test_grpc_rejects_missing_api_key(grpc_server_auth: tuple[str, int]) -> None:
    host, port = grpc_server_auth
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb2_grpc.PhysicsRoomServiceStub(channel)
        with pytest.raises(grpc.RpcError) as exc:
            stub.StartSession(
                pb2.StartSessionRequest(
                    config=pb2.SessionConfig(
                        session_id="no-key",
                        N=12,
                        dt=0.02,
                        hbar=1.0,
                        omega=1.0,
                        phi=2.7,
                        lam=0.0,
                        kappa=0.0,
                        enable_ai=False,
                        use_real_modules=False,
                        seed=1,
                        grid_x=16,
                        grid_y=16,
                        grid_z=16,
                    )
                )
            )
        assert exc.value.code() == grpc.StatusCode.UNAUTHENTICATED


def test_grpc_namespace_isolation(grpc_server_auth: tuple[str, int]) -> None:
    host, port = grpc_server_auth
    alpha_md = [("x-api-key", "alpha-secret"), ("x-namespace", "team-alpha")]
    beta_md = [("x-api-key", "beta-secret"), ("x-namespace", "team-beta")]

    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = pb2_grpc.PhysicsRoomServiceStub(channel)
        start = call_with_retry(
            stub.StartSession,
            pb2.StartSessionRequest(
                config=pb2.SessionConfig(
                    session_id="shared-id",
                    N=12,
                    dt=0.02,
                    hbar=1.0,
                    omega=1.0,
                    phi=2.7,
                    lam=0.05,
                    kappa=0.01,
                    enable_ai=False,
                    use_real_modules=False,
                    seed=42,
                    grid_x=32,
                    grid_y=32,
                    grid_z=32,
                )
            ),
            metadata=alpha_md,
        )
        assert start.session_id.startswith("team-alpha:")

        call_with_retry(
            stub.TickRun,
            pb2.TickRunRequest(session_id=start.session_id, steps=2),
            metadata=alpha_md,
        )

        with pytest.raises(grpc.RpcError) as exc:
            call_with_retry(
                stub.GetSessionState,
                pb2.GetSessionStateRequest(session_id=start.session_id),
                metadata=beta_md,
                retries=0,
            )
        assert exc.value.code() == grpc.StatusCode.PERMISSION_DENIED
