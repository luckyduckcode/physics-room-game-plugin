"""One-shot script to overwrite all physics_engine source files."""
import pathlib, textwrap

BASE = pathlib.Path('/Volumes/USB-HDD/coding projects/physics engine/src/physics_engine')
ROOT = pathlib.Path('/Volumes/USB-HDD/coding projects/physics engine')

# ── config.py ────────────────────────────────────────────────────────────────
(BASE / "config.py").write_text(textwrap.dedent("""\
    from __future__ import annotations

    from dataclasses import dataclass, field
    from typing import Callable, Optional

    import numpy as np


    @dataclass
    class EngineConfig:
        N:      int   = 40
        hbar:   float = 1.0
        omega:  float = 1.0
        phi:    float = float(np.e)
        dt:     float = 0.01
        lam:    float = 0.0
        kappa:  float = 0.0
        F:      Optional[np.ndarray] = field(default=None, repr=False)
        g:      Optional[np.ndarray] = field(default=None, repr=False)
        h:      Optional[np.ndarray] = field(default=None, repr=False)
        Vcosmo: Optional[Callable[[np.ndarray], np.ndarray]] = field(default=None, repr=False)

        def __post_init__(self) -> None:
            assert self.N     >  2,  f"N must be > 2, got {self.N}"
            assert self.hbar  >  0,  f"hbar must be > 0, got {self.hbar}"
            assert self.omega >  0,  f"omega must be > 0, got {self.omega}"
            assert self.phi   >  0,  f"phi must be > 0, got {self.phi}"
            assert self.dt    >  0,  f"dt must be > 0, got {self.dt}"
            assert self.lam   >= 0,  f"lam must be >= 0, got {self.lam}"
            assert self.kappa >= 0,  f"kappa must be >= 0, got {self.kappa}"
            if self.F is None:
                self.F = np.ones(self.N + 1)
            if self.g is None:
                self.g = np.zeros(self.N)
            if self.h is None:
                self.h = np.zeros((self.N, self.N))
            assert len(self.F) >= self.N + 1
            assert len(self.g) >= self.N
            assert self.h.shape[0] >= self.N and self.h.shape[1] >= self.N


    @dataclass
    class CouplingConfig:
        F:     Optional[np.ndarray] = None
        g:     Optional[np.ndarray] = None
        h:     Optional[np.ndarray] = None
        lam:   float = 0.0
        kappa: float = 0.0


    @dataclass
    class SimulationResult:
        times:    np.ndarray
        states:   np.ndarray
        energies: np.ndarray
        norms:    np.ndarray
        logs:     list = field(default_factory=list)
"""), encoding="utf-8")
print("config.py written")

# ── operators.py ──────────────────────────────────────────────────────────────
(BASE / "operators.py").write_text(textwrap.dedent("""\
    from __future__ import annotations

    import numpy as np


    def ladder_ops(N: int) -> tuple[np.ndarray, np.ndarray]:
        assert N > 1, f"N must be > 1, got {N}"
        A = np.zeros((N, N), dtype=complex)
        for n in range(1, N):
            A[n - 1, n] = np.sqrt(float(n))
        return A, A.conj().T


    def mat_power(M: np.ndarray, n: int) -> np.ndarray:
        assert n >= 0, "n must be >= 0"
        if n == 0:
            return np.eye(M.shape[0], dtype=complex)
        if n == 1:
            return M.copy()
        out = M.copy()
        for _ in range(n - 1):
            out = out @ M
        return out


    def position_op(N: int) -> np.ndarray:
        A, Ad = ladder_ops(N)
        return (A + Ad) / np.sqrt(2.0)


    def momentum_op(N: int) -> np.ndarray:
        A, Ad = ladder_ops(N)
        return 1j * (Ad - A) / np.sqrt(2.0)


    def number_op(N: int) -> np.ndarray:
        A, Ad = ladder_ops(N)
        return Ad @ A


    def commutator(A: np.ndarray, B: np.ndarray) -> np.ndarray:
        return A @ B - B @ A


    def check_hermitian(M: np.ndarray, tol: float = 1e-10) -> bool:
        return bool(np.max(np.abs(M - M.conj().T)) < tol)
"""), encoding="utf-8")
print("operators.py written")

# ── hamiltonian.py ────────────────────────────────────────────────────────────
(BASE / "hamiltonian.py").write_text(textwrap.dedent("""\
    from __future__ import annotations

    from typing import Callable, Optional

    import numpy as np

    from .operators import ladder_ops, mat_power, position_op, momentum_op


    def build_H(
        N: int = 40,
        hbar: float = 1.0,
        omega: float = 1.0,
        phi: float = float(np.e),
        F: Optional[np.ndarray] = None,
        g: Optional[np.ndarray] = None,
        h: Optional[np.ndarray] = None,
        lam: float = 0.0,
        kappa: float = 0.0,
        Vcosmo: Optional[Callable] = None,
        f_t: float = 0.0,
    ) -> np.ndarray:
        A, Ad = ladder_ops(N)
        x = position_op(N)
        p = momentum_op(N)
        Nc = N - 1

        if F is None:
            F = np.ones(N + 1)
        if g is None:
            g = np.zeros(N)
        if h is None:
            h = np.zeros((N, N))

        H = np.zeros((N, N), dtype=complex)

        # Term 1: sum_n hbar*omega * F_{n+1} * (Ad)^n A^n
        for n in range(Nc + 1):
            H += hbar * omega * F[n + 1] * (mat_power(Ad, n) @ mat_power(A, n))

        # Term 2: 0.5 * (ln phi)^2 * (p^2 + x^2)
        c  = 0.5 * (np.log(phi) ** 2)
        H += c * (p @ p + x @ x)

        # Term 3: cosmological potential V(x)
        if Vcosmo is not None:
            H += Vcosmo(x)

        # Term 4: lambda * sum_n g_n * (Ad)^n A^n * f(t)
        if lam != 0.0:
            for n in range(Nc + 1):
                H += lam * g[n] * (mat_power(Ad, n) @ mat_power(A, n)) * f_t

        # Term 5: kappa * sum_{n,m} h_nm * [(Ad)^n A^m + (Ad)^m A^n] * (-1)^(n-m)
        if kappa != 0.0:
            for n in range(Nc + 1):
                for m in range(Nc + 1):
                    parity = (-1) ** (n - m)
                    term   = (mat_power(Ad, n) @ mat_power(A, m) +
                              mat_power(Ad, m) @ mat_power(A, n))
                    H     += kappa * h[n, m] * parity * term

        return 0.5 * (H + H.conj().T)
"""), encoding="utf-8")
print("hamiltonian.py written")

# ── engine.py ─────────────────────────────────────────────────────────────────
(BASE / "engine.py").write_text(textwrap.dedent("""\
    from __future__ import annotations

    from typing import Callable, Optional

    import numpy as np
    from scipy.linalg import expm

    from .config import EngineConfig, SimulationResult
    from .hamiltonian import build_H


    class PhysicsEngine:
        def __init__(self, config: EngineConfig) -> None:
            self.config = config

        def _build_H(self, t: float, forcing: Optional[Callable] = None) -> np.ndarray:
            f_t = float(forcing(t)) if forcing else 0.0
            c = self.config
            return build_H(
                N=c.N, hbar=c.hbar, omega=c.omega, phi=c.phi,
                F=c.F, g=c.g, h=c.h,
                lam=c.lam, kappa=c.kappa, Vcosmo=c.Vcosmo, f_t=f_t,
            )

        def simulate(
            self,
            psi0: np.ndarray,
            times: np.ndarray,
            forcing: Optional[Callable] = None,
        ) -> SimulationResult:
            N = self.config.N
            assert psi0.shape == (N,), f"psi0 must have shape ({N},)"
            psi = psi0.astype(complex).copy()
            psi /= np.linalg.norm(psi)

            states   = np.zeros((len(times), N), dtype=complex)
            energies = np.zeros(len(times))
            norms    = np.zeros(len(times))

            for i, t in enumerate(times):
                H = self._build_H(t, forcing)
                psi = expm(-1j * H * self.config.dt / self.config.hbar) @ psi
                psi /= np.linalg.norm(psi)
                states[i]   = psi
                energies[i] = float(np.real(psi.conj() @ H @ psi))
                norms[i]    = float(np.linalg.norm(psi))

            return SimulationResult(times=times, states=states, energies=energies, norms=norms)

        def simulate_with_logs(
            self,
            psi0: np.ndarray,
            times: np.ndarray,
            forcing: Optional[Callable] = None,
            log_every: int = 1,
        ) -> SimulationResult:
            N  = self.config.N
            c  = self.config
            assert psi0.shape == (N,), f"psi0 must have shape ({N},)"
            psi = psi0.astype(complex).copy()
            psi /= np.linalg.norm(psi)

            states   = np.zeros((len(times), N), dtype=complex)
            energies = np.zeros(len(times))
            norms    = np.zeros(len(times))
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
                H   = self._build_H(t, forcing)
                psi = expm(-1j * H * c.dt / c.hbar) @ psi
                psi /= np.linalg.norm(psi)
                energy = float(np.real(psi.conj() @ H @ psi))
                norm   = float(np.linalg.norm(psi))

                states[i]   = psi
                energies[i] = energy
                norms[i]    = norm

                if i % log_every == 0:
                    peak_n = int(np.argmax(np.abs(psi) ** 2))
                    logs.append(
                        f"  {i:>6}  {t:>10.4f}  {energy:>14.8f}  {norm:>10.8f}  {peak_n:>8}"
                    )

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
"""), encoding="utf-8")
print("engine.py written")

# ── log_api.py ────────────────────────────────────────────────────────────────
(BASE / "log_api.py").write_text(textwrap.dedent("""\
    from __future__ import annotations

    import datetime
    import math
    import os
    from typing import Any

    import numpy as np
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import PlainTextResponse, StreamingResponse
    from pydantic import BaseModel, Field

    from .config import EngineConfig
    from .engine import PhysicsEngine


    class SimulateRequest(BaseModel):
        N:         int   = Field(40,  gt=2)
        hbar:      float = Field(1.0, gt=0)
        omega:     float = Field(1.0, gt=0)
        phi:       float = Field(2.718281828, gt=0)
        dt:        float = Field(0.01, gt=0)
        lam:       float = Field(0.0, ge=0)
        kappa:     float = Field(0.0, ge=0)
        t_start:   float = 0.0
        t_end:     float = 10.0
        n_steps:   int   = Field(100, gt=0)
        log_every: int   = Field(10,  gt=0)
        run_name:  str   = "run"
        logs_dir:  str   = "logs"
        psi0_mode: str   = "ground"


    def _make_psi0(mode: str, N: int) -> np.ndarray:
        psi = np.zeros(N, dtype=complex)
        if mode == "coherent":
            alpha = 1.0
            for n in range(N):
                psi[n] = (alpha ** n) / math.sqrt(math.factorial(n))
            psi *= math.exp(-0.5 * abs(alpha) ** 2)
        elif mode == "thermal":
            beta    = 1.0
            weights = np.array([math.exp(-beta * n) for n in range(N)])
            psi     = np.sqrt(weights / weights.sum()).astype(complex)
        else:
            psi[0] = 1.0
        return psi / np.linalg.norm(psi)


    def _build_engine(req: SimulateRequest) -> tuple[PhysicsEngine, np.ndarray, np.ndarray]:
        cfg    = EngineConfig(N=req.N, hbar=req.hbar, omega=req.omega,
                              phi=req.phi, dt=req.dt, lam=req.lam, kappa=req.kappa)
        engine = PhysicsEngine(cfg)
        psi0   = _make_psi0(req.psi0_mode, req.N)
        times  = np.linspace(req.t_start, req.t_end, req.n_steps)
        return engine, psi0, times


    def _save_log(lines: list[str], logs_dir: str, run_name: str) -> str:
        os.makedirs(logs_dir, exist_ok=True)
        ts   = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        safe = run_name.strip().replace(" ", "_")
        path = os.path.join(logs_dir, f"{ts}_{safe}.log")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\\n".join(lines) + "\\n")
        return path


    def create_log_app() -> FastAPI:
        app = FastAPI(
            title="Physics Engine - Log API",
            description="Localhost data-log server. Terminal-style simulation output.",
            version="1.0.0",
        )

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok", "service": "physics-engine-log-api"}

        @app.get("/logs")
        def list_logs(logs_dir: str = "logs") -> dict[str, Any]:
            if not os.path.isdir(logs_dir):
                return {"files": [], "count": 0}
            files = sorted(f for f in os.listdir(logs_dir) if f.endswith(".log"))
            return {"files": files, "count": len(files)}

        @app.get("/logs/{filename}", response_class=PlainTextResponse)
        def read_log(filename: str, logs_dir: str = "logs") -> str:
            path = os.path.join(logs_dir, filename)
            if not os.path.isfile(path):
                raise HTTPException(status_code=404, detail="Log file not found")
            return open(path, encoding="utf-8").read()

        @app.post("/simulate/log")
        def simulate_log(req: SimulateRequest) -> dict[str, Any]:
            try:
                engine, psi0, times = _build_engine(req)
                result = engine.simulate_with_logs(psi0, times, log_every=req.log_every)
                return {
                    "logs":         result.logs,
                    "final_energy": float(result.energies[-1]),
                    "final_norm":   float(result.norms[-1]),
                    "n_steps":      len(times),
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/simulate/log/text", response_class=PlainTextResponse)
        def simulate_log_text(req: SimulateRequest) -> str:
            try:
                engine, psi0, times = _build_engine(req)
                result = engine.simulate_with_logs(psi0, times, log_every=req.log_every)
                return "\\n".join(result.logs)
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/simulate/log/stream")
        def simulate_log_stream(req: SimulateRequest) -> StreamingResponse:
            try:
                engine, psi0, times = _build_engine(req)
                result = engine.simulate_with_logs(psi0, times, log_every=req.log_every)
                def _gen():
                    for line in result.logs:
                        yield line + "\\n"
                return StreamingResponse(_gen(), media_type="text/plain")
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/simulate/log/save")
        def simulate_log_save(req: SimulateRequest) -> dict[str, Any]:
            try:
                engine, psi0, times = _build_engine(req)
                result = engine.simulate_with_logs(psi0, times, log_every=req.log_every)
                path   = _save_log(result.logs, req.logs_dir, req.run_name)
                return {
                    "saved_to":     path,
                    "final_energy": float(result.energies[-1]),
                    "final_norm":   float(result.norms[-1]),
                    "n_steps":      len(times),
                    "log_lines":    len(result.logs),
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return app
"""), encoding="utf-8")
print("log_api.py written")

# ── __init__.py ───────────────────────────────────────────────────────────────
(BASE / "__init__.py").write_text(textwrap.dedent("""\
    from .config    import EngineConfig, CouplingConfig, SimulationResult
    from .engine    import PhysicsEngine
    from .log_api   import create_log_app
    from .operators import (
        ladder_ops,
        mat_power,
        position_op,
        momentum_op,
        number_op,
        commutator,
        check_hermitian,
    )

    __all__ = [
        "EngineConfig",
        "CouplingConfig",
        "SimulationResult",
        "PhysicsEngine",
        "create_log_app",
        "ladder_ops",
        "mat_power",
        "position_op",
        "momentum_op",
        "number_op",
        "commutator",
        "check_hermitian",
    ]
"""), encoding="utf-8")
print("__init__.py written")

# ── pyproject.toml ────────────────────────────────────────────────────────────
(ROOT / "pyproject.toml").write_text(textwrap.dedent("""\
    [build-system]
    requires      = ["setuptools>=68", "wheel"]
    build-backend = "setuptools.backends.legacy:build"

    [project]
    name        = "physics-engine"
    version     = "0.1.0"
    description = "Reusable quantum physics engine - callable as a local API"
    requires-python = ">=3.11"

    dependencies = [
        "numpy>=1.26",
        "scipy>=1.12",
        "fastapi>=0.110",
        "uvicorn[standard]>=0.29",
        "pydantic>=2.6",
    ]

    [project.optional-dependencies]
    dev = [
        "pytest>=8.1",
        "httpx>=0.27",
    ]

    [tool.setuptools.packages.find]
    where = ["src"]
"""), encoding="utf-8")
print("pyproject.toml written")

# ── run_server.py ─────────────────────────────────────────────────────────────
(ROOT / "run_server.py").write_text(textwrap.dedent("""\
    \"\"\"
    Start the Physics Engine Log API server.
    Usage:
        python run_server.py
    Env vars:
        PHYSICS_HOST  (default: 127.0.0.1)
        PHYSICS_PORT  (default: 8010)
    \"\"\"
    import os, sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent / 'src'))

    import uvicorn
    from physics_engine.log_api import create_log_app

    HOST = os.getenv("PHYSICS_HOST", "127.0.0.1")
    PORT = int(os.getenv("PHYSICS_PORT", "8010"))

    if __name__ == "__main__":
        print(f"  Physics Engine Log API")
        print(f"  Listening : http://{HOST}:{PORT}")
        print(f"  Docs      : http://{HOST}:{PORT}/docs")
        print(f"  Log files : http://{HOST}:{PORT}/logs")
        print()
        uvicorn.run(create_log_app(), host=HOST, port=PORT, log_level="info")
"""), encoding="utf-8")
print("run_server.py written")

# ── tests/ ────────────────────────────────────────────────────────────────────
TEST_DIR = ROOT / "tests"
TEST_DIR.mkdir(exist_ok=True)
(TEST_DIR / "__init__.py").write_text("", encoding="utf-8")

(TEST_DIR / "test_operators.py").write_text(textwrap.dedent("""\
    import numpy as np
    import pytest
    from physics_engine.operators import (
        ladder_ops, mat_power, position_op,
        momentum_op, number_op, commutator, check_hermitian,
    )

    N = 12

    def test_ladder_shapes():
        A, Ad = ladder_ops(N)
        assert A.shape  == (N, N)
        assert Ad.shape == (N, N)

    def test_ladder_adjoint():
        A, Ad = ladder_ops(N)
        assert np.allclose(A, Ad.conj().T)

    def test_canonical_commutation():
        A, Ad = ladder_ops(N)
        comm = commutator(A, Ad)
        assert np.allclose(comm[:N-1, :N-1], np.eye(N-1), atol=1e-10)

    def test_mat_power_identity():
        A, _ = ladder_ops(N)
        assert np.allclose(mat_power(A, 0), np.eye(N))

    def test_mat_power_one():
        A, _ = ladder_ops(N)
        assert np.allclose(mat_power(A, 1), A)

    def test_mat_power_two():
        A, _ = ladder_ops(N)
        assert np.allclose(mat_power(A, 2), A @ A)

    def test_position_hermitian():
        assert check_hermitian(position_op(N))

    def test_momentum_hermitian():
        assert check_hermitian(momentum_op(N))

    def test_number_op_diagonal():
        diag = np.diag(number_op(N)).real
        assert np.allclose(diag, np.arange(N, dtype=float), atol=1e-10)
"""), encoding="utf-8")

(TEST_DIR / "test_hamiltonian.py").write_text(textwrap.dedent("""\
    import numpy as np
    import pytest
    from physics_engine.hamiltonian import build_H
    from physics_engine.operators   import check_hermitian

    N = 10

    def test_shape():
        assert build_H(N=N).shape == (N, N)

    def test_hermitian():
        assert check_hermitian(build_H(N=N), tol=1e-8)

    def test_real_eigenvalues():
        evals = np.linalg.eigvalsh(build_H(N=N))
        assert np.all(np.isreal(evals))

    def test_with_lambda():
        H = build_H(N=N, lam=1.0, g=np.ones(N), f_t=1.0)
        assert check_hermitian(H, tol=1e-8)

    def test_with_kappa():
        assert check_hermitian(build_H(N=N, kappa=0.1, h=np.eye(N)), tol=1e-8)

    def test_with_vcosmo():
        assert check_hermitian(build_H(N=N, Vcosmo=lambda x: 0.5 * x @ x), tol=1e-8)

    def test_ground_state_non_negative():
        evals = np.linalg.eigvalsh(build_H(N=N))
        assert evals[0] >= -1e-8
"""), encoding="utf-8")

(TEST_DIR / "test_engine.py").write_text(textwrap.dedent("""\
    import numpy as np
    import pytest
    from physics_engine.engine import PhysicsEngine
    from physics_engine.config import EngineConfig


    def make_engine(N=10):
        return PhysicsEngine(EngineConfig(N=N, dt=0.01))

    def make_psi0(N=10):
        psi    = np.zeros(N, dtype=complex)
        psi[0] = 1.0
        return psi


    def test_simulate_shapes():
        result = make_engine().simulate(make_psi0(), np.linspace(0, 1, 20))
        assert result.states.shape   == (20, 10)
        assert result.energies.shape == (20,)
        assert result.norms.shape    == (20,)

    def test_norm_preserved():
        result = make_engine().simulate(make_psi0(), np.linspace(0, 2, 50))
        assert np.allclose(result.norms, 1.0, atol=1e-6)

    def test_logs_present():
        result = make_engine().simulate_with_logs(make_psi0(), np.linspace(0, 1, 20), log_every=5)
        assert len(result.logs) > 0
        assert any("SIMULATION START"    in l for l in result.logs)
        assert any("SIMULATION COMPLETE" in l for l in result.logs)

    def test_energy_finite():
        result = make_engine().simulate_with_logs(make_psi0(), np.linspace(0, 1, 20))
        assert np.all(np.isfinite(result.energies))

    def test_config_bad_N():
        with pytest.raises(AssertionError):
            EngineConfig(N=1)

    def test_config_bad_dt():
        with pytest.raises(AssertionError):
            EngineConfig(dt=-0.1)

    def test_config_bad_hbar():
        with pytest.raises(AssertionError):
            EngineConfig(hbar=0)
"""), encoding="utf-8")

print("tests/ written")
print()
print("ALL FILES WRITTEN.")
