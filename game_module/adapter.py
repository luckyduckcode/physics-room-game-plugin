from typing import Optional, Any
from dataclasses import dataclass
import threading
import json
import time

try:
    # Best-effort import of existing physics engine API in workspace
    from physics_engine import engine as pe_engine  # type: ignore
except Exception:
    pe_engine = None


class PhysicsAdapter:
    """Adapter that exposes a tiny API suitable for game loops.

    Methods are intentionally generic/stubbed so you can wire them to your
    actual physics engine objects (World, Body, etc.).
    """

    def __init__(self, engine: Optional[Any] = None):
        self.engine = engine or pe_engine
        self.world = None
        self._bodies = {}

    def init_world(self, **kwargs):
        """Initialize or reset the physics world using the engine API."""
        if self.engine is None:
            raise RuntimeError("Physics engine not available in environment")
        # Example placeholder call; adapt to your engine's constructor
        if hasattr(self.engine, "World"):
            self.world = self.engine.World(**kwargs)
        else:
            # keep a generic placeholder if engine shape is unknown
            self.world = object()
        return self.world

    def add_entity(self, entity, **body_opts):
        """Add an `Entity` to the physics world and return a body handle.

        `entity` is expected to have `x`, `y`, `mass` attributes — see
        `game_module.entity.Entity`.
        """
        if self.world is None:
            self.init_world()

        # If engine provides a body creation API, call it; otherwise store a stub
        if self.engine and hasattr(self.world, "create_body"):
            body = self.world.create_body(x=entity.x, y=entity.y, mass=entity.mass, **body_opts)  # type: ignore
        else:
            body = {"id": entity.id, "x": entity.x, "y": entity.y, "vx": getattr(entity, "vx", 0.0), "vy": getattr(entity, "vy", 0.0)}
        self._bodies[entity.id] = body
        return body

    def apply_force(self, entity_id, fx: float, fy: float):
        """Apply a force to a body identified by `entity_id`.

        Adapter will call into engine-specific API when available.
        """
        body = self._bodies.get(entity_id)
        if body is None:
            raise KeyError(entity_id)

        if self.engine and hasattr(body, "apply_force"):
            body.apply_force(fx, fy)  # type: ignore
        else:
            # simple Euler-ish velocity update for placeholder bodies
            body.setdefault("vx", 0.0)
            body.setdefault("vy", 0.0)
            body["vx"] += fx / (body.get("mass", 1.0) or 1.0)
            body["vy"] += fy / (body.get("mass", 1.0) or 1.0)

    def step(self, dt: float):
        """Advance the simulation by `dt` seconds."""
        if self.world is None:
            self.init_world()

        if self.engine and hasattr(self.world, "step"):
            return self.world.step(dt)  # type: ignore

        # fallback: integrate placeholder bodies
        for b in self._bodies.values():
            b.setdefault("x", 0.0)
            b.setdefault("y", 0.0)
            b.setdefault("vx", 0.0)
            b.setdefault("vy", 0.0)
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
        return self._bodies

    # --- gRPC splat streaming helper ---
    def start_splat_listener(self, host: str = 'localhost', port: int = 50051):
        """Start a background thread that runs a local gRPC server to accept SplatClouds
        and write them to a JSON file that Godot can load from the project.

        This is a minimal convenience: for production you may want a proper IPC
        channel into the Godot runtime or a socket-based bridge.
        """
        try:
            from physics_engine.grpc._generated import splats_pb2, splats_pb2_grpc
            import grpc
            from concurrent import futures
        except Exception:
            raise RuntimeError('gRPC bindings not generated; run physics engine/scripts/generate_protos.sh')

        adapter = self

        class _Servicer(splats_pb2_grpc.VisualizerServicer):
            def SendSplatCloud(self, request, context):
                # Convert request to JSON and write to shared file
                splats = []
                for s in request.splats:
                    splats.append({
                        'atom': s.atom,
                        'center': list(s.center),
                        'alpha': float(s.alpha),
                        'coeff': float(s.coeff),
                        'color': [float(c) for c in s.color],
                    })
                out = {'splats': splats, 'source': request.source_id}
                # write into godot project's res:// by using project path relative copy
                path = 'godot_scene_bundle/splats_received.json'
                with open(path, 'w') as f:
                    json.dump(out, f)
                return splats_pb2.Ack(ok=True, message='written')

        def _serve():
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
            splats_pb2_grpc.add_VisualizerServicer_to_server(_Servicer(), server)
            addr = f'{host}:{port}'
            server.add_insecure_port(addr)
            server.start()
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                server.stop(0)

        t = threading.Thread(target=_serve, daemon=True)
        t.start()
        return t

    def start_file_watcher(self, path: str = 'godot_scene_bundle/splats_received.json', notify_path: str = None, interval: float = 0.5, command: str = None, callback=None):
        """Start a background thread that watches `path` for modifications.

        On change the watcher will optionally:
        - write a small notify file at `notify_path` (if provided),
        - run a shell `command` (if provided),
        - call a Python `callback(path)` (if provided).

        This lets Godot poll a lightweight signal file or you can provide a
        callback to push notifications into your runtime.
        """
        import os

        def _watch():
            last_mtime = None
            while True:
                try:
                    if os.path.exists(path):
                        mtime = os.path.getmtime(path)
                        if last_mtime is None:
                            last_mtime = mtime
                        elif mtime != last_mtime:
                            last_mtime = mtime
                            # write notify file
                            if notify_path:
                                try:
                                    with open(notify_path, 'w') as nf:
                                        nf.write(str(mtime))
                                except Exception:
                                    pass
                            # run command
                            if command:
                                try:
                                    import subprocess

                                    subprocess.Popen(command, shell=True)
                                except Exception:
                                    pass
                            # call callback
                            if callback:
                                try:
                                    callback(path)
                                except Exception:
                                    pass
                    time.sleep(interval)
                except Exception:
                    time.sleep(interval)

        t = threading.Thread(target=_watch, daemon=True)
        t.start()
        return t
