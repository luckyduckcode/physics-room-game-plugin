from __future__ import annotations

from concurrent import futures
import os
import time
from typing import Callable, Mapping, cast

import grpc
from google.protobuf import struct_pb2

from physics_engine.config import EngineConfig
from physics_engine.coordinator import PhysicsRoomCoordinator
from physics_engine.contracts import StartSessionRequest as StartSessionDTO

from . import physics_room_pb2 as pb2
from . import physics_room_pb2_grpc as pb2_grpc


def _metadata_to_dict(metadata) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in metadata or []:
        key = str(getattr(item, "key", "")).lower()
        value = str(getattr(item, "value", ""))
        if key:
            out[key] = value
    return out


def parse_api_key_namespace_map(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    mapping: dict[str, str] = {}
    for token in [t.strip() for t in raw.split(",") if t.strip()]:
        if ":" not in token:
            continue
        api_key, namespace = token.split(":", 1)
        api_key = api_key.strip()
        namespace = namespace.strip()
        if api_key and namespace:
            mapping[api_key] = namespace
    return mapping


class ApiKeyAuthInterceptor(grpc.ServerInterceptor):
    def __init__(self, api_keys_to_namespaces: Mapping[str, str] | None = None) -> None:
        self._api_keys = dict(api_keys_to_namespaces or {})

    def _validate(self, metadata) -> tuple[bool, grpc.StatusCode, str]:
        if not self._api_keys:
            return True, grpc.StatusCode.OK, "ok"

        md = _metadata_to_dict(metadata)
        api_key = md.get("x-api-key")
        if not api_key or api_key not in self._api_keys:
            return False, grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid x-api-key"

        requested_ns = md.get("x-namespace")
        mapped_ns = self._api_keys[api_key]
        if requested_ns and requested_ns != mapped_ns:
            return False, grpc.StatusCode.PERMISSION_DENIED, "x-namespace does not match api-key scope"

        return True, grpc.StatusCode.OK, "ok"

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None:
            return None

        ok, status, message = self._validate(handler_call_details.invocation_metadata)
        if ok:
            return handler

        def _abort(request, context):
            context.abort(status, message)

        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                _abort,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.unary_stream:
            def _abort_stream(request, context):
                context.abort(status, message)
                yield from ()
            return grpc.unary_stream_rpc_method_handler(
                _abort_stream,
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )

        return handler


class PhysicsRoomGrpcService(pb2_grpc.PhysicsRoomServiceServicer):
    def __init__(self, api_keys_to_namespaces: Mapping[str, str] | None = None, default_namespace: str = "public") -> None:
        self._sessions: dict[str, PhysicsRoomCoordinator] = {}
        self._session_namespace: dict[str, str] = {}
        self._api_keys = dict(api_keys_to_namespaces or {})
        self._default_namespace = default_namespace

    def _get_namespace(self, context) -> str:
        md = _metadata_to_dict(context.invocation_metadata())
        requested_ns = md.get("x-namespace")

        if not self._api_keys:
            return requested_ns or self._default_namespace

        api_key = md.get("x-api-key")
        if not api_key or api_key not in self._api_keys:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing or invalid x-api-key")
        assert api_key is not None

        mapped_ns = self._api_keys[api_key]
        if requested_ns and requested_ns != mapped_ns:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "x-namespace does not match api-key scope")
        return mapped_ns

    def _qualified_session_id(self, namespace: str, requested_id: str) -> str:
        if requested_id.startswith(f"{namespace}:"):
            return requested_id
        if ":" in requested_id:
            raise ValueError("Cross-namespace session id not allowed")
        return f"{namespace}:{requested_id}"

    def _resolve_owned_session(self, context, session_id: str) -> PhysicsRoomCoordinator:
        namespace = self._get_namespace(context)
        coordinator = self._sessions.get(session_id)
        if coordinator is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "Session not found")
        assert coordinator is not None

        owner_ns = self._session_namespace.get(session_id)
        if owner_ns != namespace:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, "Session belongs to different namespace")
        return coordinator

    @staticmethod
    def _meta_to_proto(meta):
        run_meta_cls = getattr(pb2, "RunMetadata")
        return run_meta_cls(
            config_hash=meta.config_hash,
            code_version=meta.code_version,
            seed=meta.seed,
            created_at_ns=meta.created_at_ns,
        )

    @staticmethod
    def _taxonomy_to_proto(taxonomy: dict[str, object] | None):
        payload = struct_pb2.Struct()
        payload.update(taxonomy or {})
        return payload

    @classmethod
    def _state_to_proto(cls, state, taxonomy: dict[str, object] | None = None):
        state_cls = getattr(pb2, "SessionState")
        return state_cls(
            session_id=state.session_id,
            tick=max(0, int(state.tick)),
            active_voxels=max(0, int(state.active_voxels)),
            stable_voxels=max(0, int(state.stable_voxels)),
            last_energy=float(state.last_energy),
            metadata=cls._meta_to_proto(state.metadata),
            taxonomy=cls._taxonomy_to_proto(taxonomy),
        )

    @staticmethod
    def _event_to_proto(event):
        payload = struct_pb2.Struct()
        payload.update(event.payload)
        event_cls = getattr(pb2, "EventEnvelope")
        return event_cls(
            timestamp=event.timestamp,
            session_id=event.session_id,
            source=event.source,
            event_type=event.event_type,
            sequence=max(1, int(event.sequence)),
            payload=payload,
        )

    def StartSession(self, request, context):
        cfg = request.config
        namespace = self._get_namespace(context)
        dto = StartSessionDTO(
            session_id=(cfg.session_id or None),
            system_name=(cfg.system_name or None),
            N=max(int(cfg.N), 3),
            dt=float(cfg.dt) if cfg.dt > 0 else 0.01,
            hbar=float(cfg.hbar) if cfg.hbar > 0 else 1.0,
            omega=float(cfg.omega) if cfg.omega > 0 else 1.0,
            phi=float(cfg.phi) if cfg.phi > 0 else 2.718281828,
            lam=max(float(cfg.lam), 0.0),
            kappa=max(float(cfg.kappa), 0.0),
            grid_shape=(
                max(int(cfg.grid_x), 1) or 32,
                max(int(cfg.grid_y), 1) or 32,
                max(int(cfg.grid_z), 1) or 32,
            ),
            enable_ai=bool(cfg.enable_ai),
            use_real_modules=bool(cfg.use_real_modules),
            seed=(int(cfg.seed) if cfg.seed > 0 else None),
        )

        requested_id = dto.session_id or PhysicsRoomCoordinator.new_session_id()
        try:
            session_id = self._qualified_session_id(namespace, requested_id)
        except ValueError as exc:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
            raise

        if session_id in self._sessions:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, "Session id already exists in namespace")

        coordinator = PhysicsRoomCoordinator(
            session_id=session_id,
            config=EngineConfig(
                N=dto.N,
                dt=dto.dt,
                hbar=dto.hbar,
                omega=dto.omega,
                phi=dto.phi,
                lam=dto.lam,
                kappa=dto.kappa,
            ),
            system_name=dto.system_name,
            grid_shape=dto.grid_shape,
            enable_ai=dto.enable_ai,
            use_real_modules=dto.use_real_modules,
            seed=dto.seed,
        )

        self._sessions[session_id] = coordinator
        self._session_namespace[session_id] = namespace
        state = coordinator.state()
        start_resp_cls = getattr(pb2, "StartSessionResponse")
        return start_resp_cls(
            ok=True,
            session_id=session_id,
            state=self._state_to_proto(state, coordinator.dynamics_taxonomy),
            metadata=self._meta_to_proto(coordinator.metadata),
            taxonomy=self._taxonomy_to_proto(coordinator.dynamics_taxonomy),
        )

    def TickRun(self, request, context):
        coordinator = self._resolve_owned_session(context, request.session_id)

        result = coordinator.run_steps(max(1, int(request.steps)))
        tick_resp_cls = getattr(pb2, "TickRunResponse")
        return tick_resp_cls(
            ok=True,
            session_id=result.session_id,
            steps=result.steps,
            final_tick=result.final_tick,
            events=[self._event_to_proto(e) for e in result.events],
            metadata=self._meta_to_proto(result.metadata),
        )

    def GetSessionState(self, request, context):
        coordinator = self._resolve_owned_session(context, request.session_id)

        state_resp_cls = getattr(pb2, "GetSessionStateResponse")
        return state_resp_cls(ok=True, state=self._state_to_proto(coordinator.state(), coordinator.dynamics_taxonomy))

    def GetSessionEvents(self, request, context):
        coordinator = self._resolve_owned_session(context, request.session_id)

        limit = max(1, int(request.limit or 500))
        selected = [
            e for e in coordinator.events
            if int(e.sequence) > int(request.after_sequence)
        ][:limit]

        events_resp_cls = getattr(pb2, "GetSessionEventsResponse")
        return events_resp_cls(
            ok=True,
            session_id=request.session_id,
            events=[self._event_to_proto(e) for e in selected],
        )

    def StreamEvents(self, request, context):
        coordinator = self._resolve_owned_session(context, request.session_id)

        last_seq = int(request.after_sequence)
        while context.is_active():
            pending = [e for e in coordinator.events if int(e.sequence) > last_seq]
            for event in pending:
                yield self._event_to_proto(event)
                last_seq = int(event.sequence)
            time.sleep(0.2)


def serve_grpc(host: str = "127.0.0.1", port: int = 7005) -> None:
    api_key_map = parse_api_key_namespace_map(os.getenv("PHYSICS_GRPC_API_KEYS"))
    interceptors = [cast(grpc.ServerInterceptor, ApiKeyAuthInterceptor(api_key_map))] if api_key_map else []
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=8), interceptors=interceptors)
    pb2_grpc.add_PhysicsRoomServiceServicer_to_server(PhysicsRoomGrpcService(api_key_map), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    server.wait_for_termination()
