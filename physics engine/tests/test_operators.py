import numpy as np
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
