"""Adapter to run the project's `physics_engine` simulations from the
`game_module` environment.

This provides a small, testable interface that maps simple experiment
parameters into `EngineConfig` and invokes `PhysicsEngine.simulate`.

It is intentionally defensive: if the `physics_engine` package is not
importable, it raises a clear error so callers can fallback to other
behaviour (e.g., placeholder integration).
"""
from __future__ import annotations

from typing import Optional, Callable, Any

try:
    from physics_engine.config import EngineConfig, SimulationResult  # type: ignore
    from physics_engine.engine import PhysicsEngine  # type: ignore
    import numpy as np  # type: ignore
except Exception as exc:  # pragma: no cover - environment may not have package
    EngineConfig = None  # type: ignore
    PhysicsEngine = None  # type: ignore
    SimulationResult = None  # type: ignore
    np = None  # type: ignore


class PhysicsEngineAdapter:
    """Wraps `PhysicsEngine` to run experiments from the game module.

    Example usage:
        adapter = PhysicsEngineAdapter()
        res = adapter.run_experiment(psi0=psi0, times=times, overrides={"N":64, "dt":0.02})

    The `overrides` dict maps to fields on `EngineConfig`.
    """

    def __init__(self, config_overrides: Optional[dict] = None):
        self.config_overrides = config_overrides or {}

    def _build_config(self, overrides: Optional[dict] = None) -> Any:
        if EngineConfig is None:
            raise RuntimeError("physics_engine package not available")
        cfg_vals = dict()
        cfg_vals.update(self.config_overrides)
        if overrides:
            cfg_vals.update(overrides)
        # Accept lists for array fields and convert to numpy arrays when present
        if "F" in cfg_vals and cfg_vals["F"] is not None:
            cfg_vals["F"] = np.asarray(cfg_vals["F"], dtype=float)
        if "g" in cfg_vals and cfg_vals["g"] is not None:
            cfg_vals["g"] = np.asarray(cfg_vals["g"], dtype=float)
        if "h" in cfg_vals and cfg_vals["h"] is not None:
            cfg_vals["h"] = np.asarray(cfg_vals["h"], dtype=float)

        return EngineConfig(**cfg_vals)

    def run_experiment(
        self,
        psi0: Any,
        times: Any,
        overrides: Optional[dict] = None,
        forcing: Optional[Callable[[float], float]] = None,
        simulate_with_logs: bool = False,
    ) -> Any:
        """Run a simulation and return the SimulationResult.

        Parameters:
            psi0: complex numpy array-like initial state
            times: array-like of time points
            overrides: dict of EngineConfig overrides (N, dt, lam, etc.)
            forcing: optional callable forcing(t) passed to engine
            simulate_with_logs: if True use `simulate_with_logs` to collect logs
        """
        if PhysicsEngine is None:
            raise RuntimeError("physics_engine package not available")

        cfg = self._build_config(overrides)
        engine = PhysicsEngine(cfg)

        psi0_arr = np.asarray(psi0)
        times_arr = np.asarray(times)

        if simulate_with_logs and hasattr(engine, "simulate_with_logs"):
            return engine.simulate_with_logs(psi0=psi0_arr, times=times_arr, forcing=forcing)
        return engine.simulate(psi0=psi0_arr, times=times_arr, forcing=forcing)


def quick_smoke_test() -> bool:
    """Return True if the physics engine adapter can be imported and a
    config object can be constructed. This is a lightweight smoke test used
    by automation to verify integration without running expensive sims.
    """
    if EngineConfig is None:
        return False
    cfg = EngineConfig()
    return cfg.N > 0
