import numpy as np
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
