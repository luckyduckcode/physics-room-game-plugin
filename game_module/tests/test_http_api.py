from fastapi.testclient import TestClient

from game_module import http_api


class DummyResult:
    def __init__(self):
        import numpy as np
        self.times = np.array([0.0, 0.01, 0.02])
        self.energies = np.array([1.0, 1.0, 1.0])
        self.norms = np.array([1.0, 1.0, 1.0])
        # small 3xN states
        self.states = np.zeros((3, 4), dtype=complex)
        self.states[0, 0] = 1.0 + 0j


class FakeAdapterSuccess:
    def __init__(self, *args, **kwargs):
        pass

    def run_experiment(self, psi0, times, overrides=None, forcing=None, simulate_with_logs=False):
        return DummyResult()


class FakeAdapterError:
    def __init__(self, *args, **kwargs):
        pass

    def run_experiment(self, *args, **kwargs):
        raise RuntimeError("forced failure for test")


client = TestClient(http_api.app)


def test_simulate_success(monkeypatch):
    # Replace the adapter class used by the API with the fake success adapter
    monkeypatch.setattr(http_api, "PhysicsEngineAdapter", FakeAdapterSuccess)
    # ensure API auth is satisfied in test client
    monkeypatch.setenv("GAME_MODULE_API_KEY", "test-key")
    payload = {
        "psi0_real": [1, 0, 0, 0],
        "psi0_imag": [0, 0, 0, 0],
        "times": [0.0, 0.01, 0.02],
        "overrides": {"N": 4},
        "simulate_with_logs": False,
    }
    r = client.post("/simulate", json=payload, headers={"x-api-key": "test-key"})
    assert r.status_code == 200
    data = r.json()
    assert "times" in data and "energies" in data and "states_real" in data


def test_simulate_error(monkeypatch):
    monkeypatch.setattr(http_api, "PhysicsEngineAdapter", FakeAdapterError)
    monkeypatch.setenv("GAME_MODULE_API_KEY", "test-key")
    payload = {
        "psi0_real": [1, 0, 0, 0],
        "psi0_imag": [0, 0, 0, 0],
        "times": [0.0, 0.01, 0.02],
        "overrides": {"N": 4},
        "simulate_with_logs": False,
    }
    r = client.post("/simulate", json=payload, headers={"x-api-key": "test-key"})
    assert r.status_code == 500
    data = r.json()
    assert data.get("detail", "").startswith("Simulation error")
