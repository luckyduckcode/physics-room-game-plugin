"""Deterministic game-loop helper for integrating `PhysicsEngine` into a game loop.

Provides `GameLoop` which manages `psi` state, accumulates wall-clock delta,
and advances the physics engine using `PhysicsEngine.game_update`. It also
exposes a simple input binding map and update callbacks for downstream systems
(e.g., visualizers that want to receive splat updates).
"""
from __future__ import annotations

from typing import Callable, Dict, Any, Optional
import time

try:
    from physics_engine.config import EngineConfig  # type: ignore
    from physics_engine.engine import PhysicsEngine  # type: ignore
    import numpy as np  # type: ignore
except Exception:
    PhysicsEngine = None
    EngineConfig = None
    np = None


class GameLoop:
    def __init__(self, engine: Optional[PhysicsEngine] = None, config_overrides: Optional[dict] = None):
        if engine is None:
            if PhysicsEngine is None:
                raise RuntimeError("PhysicsEngine not available")
            cfg = EngineConfig(**(config_overrides or {}))
            engine = PhysicsEngine(cfg)

        self.engine: PhysicsEngine = engine
        self.inputs: Dict[str, Any] = {}
        self._callbacks: list[Callable[[Any], None]] = []
        # initial psi (caller should set) — default to ground state if available
        self.psi = None
        # internal accumulator for wall-clock dt handling
        self._accumulator = 0.0

    def set_psi(self, psi_array) -> None:
        if np is not None:
            self.psi = np.asarray(psi_array, dtype=complex)
        else:
            self.psi = psi_array

    def set_input(self, name: str, value: Any) -> None:
        self.inputs[name] = value

    def register_update_callback(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback called after each game_update step.

        Callback receives a dict: { 'psi': psi, 'steps': steps, 'time': t, 'inputs': inputs }
        """
        self._callbacks.append(fn)

    def tick(self, delta_time: float) -> int:
        """Advance the game loop by `delta_time` seconds using engine.game_update.

        Returns the number of physics steps taken.
        """
        if not hasattr(self.engine, "game_update"):
            raise RuntimeError("Engine missing game_update helper")
        if self.psi is None:
            raise RuntimeError("psi state not set (use set_psi)")

        # pass accumulator via inputs so engine can reuse it if desired
        local_inputs = dict(self.inputs)
        local_inputs.setdefault("_accumulator", self._accumulator)

        new_psi, steps = self.engine.game_update(self.psi, float(delta_time), inputs=local_inputs)
        # store psi and leftover accumulator
        self.psi = new_psi
        # engine.game_update does not return accumulator; caller should manage if needed
        # For compatibility, we preserve accumulator semantics via inputs if engine mutates it.

        info = {"psi": self.psi, "steps": steps, "delta_time": float(delta_time), "inputs": dict(self.inputs)}
        for cb in self._callbacks:
            try:
                cb(info)
            except Exception:
                # swallow callback exceptions
                continue

        return int(steps)

    def run_forever(self, tick_interval: float = 1.0 / 60.0) -> None:
        """Simple blocking loop that calls `tick` at `tick_interval` wall-clock.

        Use for local testing only — a real game integrates this into the engine
        main loop instead.
        """
        last = time.time()
        try:
            while True:
                now = time.time()
                dt = now - last
                last = now
                self.tick(dt)
                time.sleep(max(0.0, tick_interval - (time.time() - now)))
        except KeyboardInterrupt:
            return
