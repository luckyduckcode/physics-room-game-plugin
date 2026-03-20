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
    assert any("SIMULATION START"    in line for line in result.logs)
    assert any("SIMULATION COMPLETE" in line for line in result.logs)

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
