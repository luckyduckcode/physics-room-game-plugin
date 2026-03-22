from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from scipy.linalg import expm

from .config import EngineConfig, SimulationResult
from .hamiltonian import build_H


class PhysicsEngine:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        # Pluggable operator terms: callables (ops, cfg, t) -> NxN operator
        self.operator_terms: list[Callable] = []
        # Non-unitary / dissipative callables: (psi, t) -> delta_psi contribution
        self.non_unitary_terms: list[Callable] = []
        # Optional collapse operators (static numpy matrices) for Lindblad solvers
        self.collapse_operators: list[np.ndarray] = []
        # Operator-form non-unitary terms (matrices). When using QuTiP these
        # are forwarded as collapse operators; when using the NumPy path they
        # are applied in a simple first-order damping approximation.
        self.non_unitary_ops: list[np.ndarray] = []

        # Optional RNG seeding for stochastic terms
        if getattr(self.config, "random_seed", None) is not None:
            import numpy as _np
            _np.random.seed(self.config.random_seed)

        # Register default operator terms if provided via config.extra_terms
        if self.config.extra_terms:
            for name, fn in (self.config.extra_terms or {}).items():
                self.add_operator_term(fn)

    def _build_H(self, t: float, forcing: Optional[Callable] = None) -> np.ndarray:
        f_t = float(forcing(t)) if forcing else 0.0
        c = self.config
        H = build_H(
            N=c.N, hbar=c.hbar, omega=c.omega, phi=c.phi,
            F=c.F, g=c.g, h=c.h,
            lam=c.lam, kappa=c.kappa, Vcosmo=c.Vcosmo, f_t=f_t,
            extra_terms=None,  # we'll add runtime-registered operator_terms below
            t=t,
        )

        # Prebuilt operators passed to operator term callables
        from .operators import ladder_ops, position_op, momentum_op
        A, Ad = ladder_ops(c.N)
        ops = {"A": A, "Ad": Ad, "x": position_op(c.N), "p": momentum_op(c.N)}

        for fn in self.operator_terms:
            try:
                add = fn(ops, dict(N=c.N, hbar=c.hbar, omega=c.omega, phi=c.phi), t)
                if add is not None:
                    H += add
            except Exception:
                # ignore optional operator errors at build time
                continue

        return 0.5 * (H + H.conj().T)

    def simulate(
        self,
        psi0: np.ndarray,
        times: np.ndarray,
        forcing: Optional[Callable] = None,
    ) -> SimulationResult:
        # If user requests QuTiP backend and it's available, prefer it for
        # validated solvers (but only for purely unitary problems here).
        if getattr(self.config, "use_qutip", False):
            try:
                import qutip as qt
            except Exception:
                qt = None

            if qt is not None:
                H_np = self._build_H(0.0, forcing)
                try:
                    H_q = qt.Qobj(H_np)
                    psi_q = qt.Qobj(psi0)
                    # If collapse operators registered, use master equation solver
                    if len(self.collapse_operators) > 0:
                        c_ops_q = [qt.Qobj(c) for c in self.collapse_operators]
                        result = qt.mesolve(H_q, psi_q, times, c_ops=c_ops_q)
                    else:
                        result = qt.sesolve(H_q, psi_q, times)

                    states = np.array([np.asarray(s.full()).ravel() for s in result.states], dtype=complex)
                    energies = np.array([float((s.conj().T @ H_np @ s).item()) for s in states])
                    norms = np.linalg.norm(states, axis=1)
                    return SimulationResult(times=times, states=states, energies=energies, norms=norms)
                except Exception:
                    # fallback to numpy implementation on any qutip error
                    pass
        N = self.config.N
        assert psi0.shape == (N,), f"psi0 must have shape ({N},)"
        psi = psi0.astype(complex).copy()
        psi /= np.linalg.norm(psi)

        states = np.zeros((len(times), N), dtype=complex)
        energies = np.zeros(len(times))
        norms = np.zeros(len(times))

        for i, t in enumerate(times):
            H = self._build_H(t, forcing)

            # Unitary propagation (base)
            psi = expm(-1j * H * self.config.dt / self.config.hbar) @ psi
            psi /= np.linalg.norm(psi)
            # Apply non-unitary / dissipative contributions (first-order)
            if self.non_unitary_terms or self.non_unitary_ops:
                delta = np.zeros_like(psi, dtype=complex)
                for fn in self.non_unitary_terms:
                    try:
                        part = fn(psi, t)
                        if part is not None:
                            delta += part
                    except Exception:
                        continue

                # Operator-form contributions: simple Lindblad-like term
                for (C, strength) in self.non_unitary_ops:
                    try:
                        K = C.conj().T @ C
                        delta += -0.5 * strength * (K @ psi)
                    except Exception:
                        continue

                psi = psi + (self.config.dt * delta)

            states[i] = psi
            energies[i] = float(np.real(psi.conj() @ H @ psi))
            norms[i] = float(np.linalg.norm(psi))

        return SimulationResult(times=times, states=states, energies=energies, norms=norms)

    # --- Pluggable API ---
    def add_operator_term(self, fn: Callable[[dict, dict, float], np.ndarray]) -> None:
        """Register an operator-style term: fn(ops, cfg_dict, t) -> NxN matrix"""
        self.operator_terms.append(fn)

    def add_potential_term(self, fn: Callable[[dict, dict, float], np.ndarray]) -> None:
        """Register a potential provider that returns a vector V(x) -> converted to diag operator."""
        def wrapper(ops, cfg, t):
            v = fn(ops, cfg, t)
            return np.diag(v)

        self.operator_terms.append(wrapper)

    def add_non_unitary(self, fn: Callable[[np.ndarray, float], np.ndarray]) -> None:
        """Register a non-unitary contribution function: fn(psi, t) -> delta_psi"""
        self.non_unitary_terms.append(fn)

    def add_non_unitary_operator(self, matrix: np.ndarray, strength: float = 1.0) -> None:
        """Register an operator-form non-unitary term.

        The matrix should be shape (N,N). For QuTiP backend it will be used
        directly as a collapse operator; for the NumPy integrator a simple
        Lindblad-like first-order contribution -0.5 * strength * (C^\\dag C) psi
        will be applied each step.
        """
        assert matrix.shape == (self.config.N, self.config.N)
        mat = matrix.astype(complex)
        self.non_unitary_ops.append((mat, float(strength)))
        # also register for QuTiP collapse operators
        self.collapse_operators.append(mat)

    def try_promote_callable_to_operator(self, fn: Callable) -> bool:
        """Try to detect if `fn` is an operator-form callable and promote it.

        Detection heuristic:
        - Inspect the callable signature: if it accepts (ops, cfg, t) or similar,
          call it with a small ops dict and cfg dict and see if it returns a
          2D ndarray of shape (N,N). If so, register it via
          `add_non_unitary_operator` with default strength 1.0 and return True.
        - Otherwise return False.
        """
        import inspect

        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        # Prepare small ops and cfg
        from .operators import ladder_ops, position_op, momentum_op
        A, Ad = ladder_ops(self.config.N)
        ops = {"A": A, "Ad": Ad, "x": position_op(self.config.N), "p": momentum_op(self.config.N)}
        cfg = dict(N=self.config.N, hbar=self.config.hbar, omega=self.config.omega, phi=self.config.phi)

        try:
            if len(params) >= 3 and params[0] in ("ops", "op", "operators"):
                out = fn(ops, cfg, 0.0)
            elif len(params) >= 2 and params[0] in ("ops", "op"):
                out = fn(ops, cfg)
            else:
                return False
        except Exception:
            return False

        import numpy as _np
        if isinstance(out, _np.ndarray) and out.ndim == 2 and out.shape[0] == self.config.N and out.shape[1] == self.config.N:
            self.add_non_unitary_operator(out, strength=1.0)
            return True
        return False

    def add_thermal_noise(self, temperature: float = 0.1, friction: float = 0.01) -> None:
        kT = float(temperature)

        def noise_term(psi: np.ndarray, t: float) -> np.ndarray:
            sigma = np.sqrt(2 * friction * kT)
            noise = (np.random.normal(0, sigma, psi.shape) +
                     1j * np.random.normal(0, sigma, psi.shape))
            return -friction * psi + noise

        self.add_non_unitary(noise_term)

    def add_lindblad_damping(self, gamma: float = 0.05, target_state: Optional[np.ndarray] = None) -> None:
        """Simple amplitude-damping-like non-unitary: relax toward `target_state`.

        This is a simplistic, numerically stable helper (not a full Lindblad solver).
        """
        if target_state is None:
            # default to ground (basis |0>)
            target = np.zeros(self.config.N, dtype=complex)
            target[0] = 1.0
        else:
            target = target_state.astype(complex)

        def damping(psi: np.ndarray, t: float) -> np.ndarray:
            return -0.5 * gamma * (psi - target)

        self.add_non_unitary(damping)

    def add_collapse_operator(self, matrix: np.ndarray) -> None:
        """Register a static collapse operator (numpy matrix) for Lindblad solvers.

        The matrix should be shape (N,N). When `EngineConfig.use_qutip=True`, these
        will be forwarded to `qutip.mesolve` as `c_ops`.
        """
        assert matrix.shape == (self.config.N, self.config.N)
        self.collapse_operators.append(matrix.astype(complex))

    def add_relativistic_mass_term(self, eps: float = 1e-3) -> None:
        """Add a small momentum-dependent correction as an operator term."""
        def rel_term(ops, cfg, t):
            p = ops.get("p")
            return -float(eps) * (p @ p)

        self.add_operator_term(rel_term)

    def symbolic_check(self) -> str:
        """Attempt a lightweight symbolic check (requires SymPy)."""
        try:
            import sympy as sp
        except Exception:
            return "sympy not installed"

        # Minimal illustrative Noether-style check: commutator [H, N]
        from .operators import number_op
        Nop = number_op(self.config.N)
        H = self._build_H(0.0)
        comm = H @ Nop - Nop @ H
        # quantify magnitude
        val = float(np.max(np.abs(comm)))
        return f"max |[H,N]| = {val:.6e}"

    def simulate_with_logs(
        self,
        psi0: np.ndarray,
        times: np.ndarray,
        forcing: Optional[Callable] = None,
        log_every: int = 1,
        energy_threshold: Optional[float] = None,
        norm_threshold: Optional[float] = None,
    ) -> SimulationResult:
        N = self.config.N
        c = self.config
        assert psi0.shape == (N,), f"psi0 must have shape ({N},)"
        psi = psi0.astype(complex).copy()
        psi /= np.linalg.norm(psi)

        states = np.zeros((len(times), N), dtype=complex)
        energies = np.zeros(len(times))
        norms = np.zeros(len(times))
        logs: list[str] = []

        logs.append("=" * 64)
        logs.append("  PHYSICS ENGINE  -  SIMULATION START")
        logs.append("=" * 64)
        logs.append(f"  dim N     : {c.N}")
        logs.append(f"  dt        : {c.dt}")
        logs.append(f"  hbar      : {c.hbar}   omega : {c.omega}   phi : {c.phi:.6f}")
        logs.append(f"  lambda    : {c.lam}   kappa : {c.kappa}")
        logs.append(f"  steps     : {len(times)}")
        logs.append("=" * 64)
        logs.append(f"  {'step':>6}  {'t':>10}  {'energy':>14}  {'norm':>10}  {'peak |n>':>8}")
        logs.append("-" * 64)

        for i, t in enumerate(times):
            H = self._build_H(t, forcing)
            psi = expm(-1j * H * c.dt / c.hbar) @ psi
            psi /= np.linalg.norm(psi)
            energy = float(np.real(psi.conj() @ H @ psi))
            norm = float(np.linalg.norm(psi))

            states[i] = psi
            energies[i] = energy
            norms[i] = norm

            threshold_msgs = []
            if energy_threshold is not None and abs(energy) > energy_threshold:
                threshold_msgs.append(f"[THRESHOLD PASSED] step={i} t={t:.4f} energy={energy:.8f} > {energy_threshold}")
            if norm_threshold is not None and abs(norm) > norm_threshold:
                threshold_msgs.append(f"[THRESHOLD PASSED] step={i} t={t:.4f} norm={norm:.8f} > {norm_threshold}")

            if i % log_every == 0:
                peak_n = int(np.argmax(np.abs(psi) ** 2))
                logs.append(
                    f"  {i:>6}  {t:>10.4f}  {energy:>14.8f}  {norm:>10.8f}  {peak_n:>8}"
                )
                logs.extend(threshold_msgs)
            elif threshold_msgs:
                logs.extend(threshold_msgs)

        logs.append("=" * 64)
        logs.append("  SIMULATION COMPLETE")
        logs.append(f"  final energy : {energies[-1]:.8f}")
        logs.append(f"  final norm   : {norms[-1]:.8f}")
        logs.append("=" * 64)

        return SimulationResult(
            times=times, states=states, energies=energies, norms=norms, logs=logs
        )

    @staticmethod
    def expectation(states: np.ndarray, operator: np.ndarray) -> np.ndarray:
        return np.real(np.einsum("bi,ij,bj->b", states.conj(), operator, states))

    # --- Game-friendly helpers ---
    def game_update(self, psi: np.ndarray, delta_time: float, inputs: dict | None = None) -> tuple[np.ndarray, int]:
        """Game-friendly update: accumulate fixed steps at 60Hz (by default).

        - `psi`: current state vector (shape (N,))
        - `delta_time`: wall-clock delta to consume
        - returns: (new_psi, steps_taken)

        This helper is intentionally lightweight and does not mutate engine state.
        """
        if inputs is None:
            inputs = {}
        fixed_dt = getattr(self, "fixed_dt", None) or 1.0 / 60.0
        accumulator = float(inputs.get("_accumulator", 0.0))
        accumulator += float(delta_time)
        steps = 0
        psi = psi.astype(complex).copy()
        # Optional deterministic RNG seed per-step
        use_det = bool(inputs.get("use_deterministic", getattr(self.config, "use_deterministic", False)))
        seed = inputs.get("deterministic_seed", getattr(self.config, "random_seed", None))

        while accumulator >= fixed_dt:
            if use_det and seed is not None:
                import numpy as _np

                _np.random.seed(int(seed))
            psi = self._fixed_step(psi, fixed_dt, inputs=inputs)
            accumulator -= fixed_dt
            steps += 1
            # advance seed deterministically if provided
            if seed is not None:
                try:
                    seed = int(seed) + 1
                except Exception:
                    seed = None

        # return updated psi and steps (caller may store leftover accumulator in inputs)
        return psi, steps

    def set_game_param(self, name: str, value: float) -> None:
        """Set a game-exposed parameter by name. This modifies `self.config` or
        registers simple effects like thermal noise.

        Example keys:
          - 'coupling_kappa' -> maps to `config.kappa`
          - 'temperature' -> calls `add_thermal_noise`
        """
        key = (name or "").strip().lower()
        if key in ("coupling_kappa", "kappa"):
            try:
                self.config.kappa = float(value)
            except Exception:
                pass
        elif key in ("lambda", "lam"):
            try:
                self.config.lam = float(value)
            except Exception:
                pass
        elif key == "temperature":
            try:
                # replace existing thermal noise with new parameters
                self.add_thermal_noise(temperature=float(value))
            except Exception:
                pass
        elif key == "friction":
            try:
                self.add_thermal_noise(temperature=getattr(self.config, "temperature", 0.1), friction=float(value))
            except Exception:
                pass
        else:
            # Generic fallback: try to set attribute on config if present
            if hasattr(self.config, name):
                try:
                    setattr(self.config, name, float(value))
                except Exception:
                    pass

    def _fixed_step(self, psi: np.ndarray, dt: float, inputs: dict | None = None) -> np.ndarray:
        """Perform a single fixed-step evolution on `psi` using timestep `dt`.

        This reuses the same integrator as `simulate` but for a single step.
        """
        if inputs is None:
            inputs = {}
        # Allow caller to pass a forcing callable via inputs
        forcing = inputs.get("forcing", None)
        t = float(inputs.get("time", 0.0))

        H = self._build_H(t, forcing)
        # unitary propagation for this small dt
        new_psi = expm(-1j * H * dt / self.config.hbar) @ psi
        # apply non-unitary terms (first-order) as in simulate
        if self.non_unitary_terms or self.non_unitary_ops:
            delta = np.zeros_like(new_psi, dtype=complex)
            for fn in self.non_unitary_terms:
                try:
                    part = fn(new_psi, t)
                    if part is not None:
                        delta += part
                except Exception:
                    continue

            for (C, strength) in self.non_unitary_ops:
                try:
                    K = C.conj().T @ C
                    delta += -0.5 * float(strength) * (K @ new_psi)
                except Exception:
                    continue

            new_psi = new_psi + (dt * delta)

        # renormalize
        try:
            new_psi = new_psi / np.linalg.norm(new_psi)
        except Exception:
            pass
        return new_psi
 
