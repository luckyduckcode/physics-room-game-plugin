from __future__ import annotations

from typing import Callable, Optional, Dict

import numpy as np

from .operators import ladder_ops, mat_power, position_op, momentum_op


# Registry for optional Hamiltonian term providers
_TERM_REGISTRY: Dict[str, Callable] = {}


def register_term(name: str, fn: Callable) -> None:
    """Register a callable that returns an NxN Hermitian matrix.

    The callable receives a dictionary of prebuilt operators and the
    engine config and current time: fn(ops, cfg, t) -> np.ndarray
    """
    _TERM_REGISTRY[name] = fn


def get_registered_terms() -> Dict[str, Callable]:
    return dict(_TERM_REGISTRY)


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
    extra_terms: Optional[Dict[str, Callable]] = None,
    t: float = 0.0,
) -> np.ndarray:
    """Construct the Hamiltonian matrix with optional extra terms.

    Extra terms are provided as a mapping name->callable and are evaluated
    and summed into the returned matrix. Registered terms (via
    `register_term`) are not applied automatically unless passed in
    `extra_terms` or the caller explicitly includes them.
    """
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
    c = 0.5 * (np.log(phi) ** 2)
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
                term = (mat_power(Ad, n) @ mat_power(A, m) +
                        mat_power(Ad, m) @ mat_power(A, n))
                H += kappa * h[n, m] * parity * term

    # Add any caller-provided extra terms
    ops = {"A": A, "Ad": Ad, "x": x, "p": p}
    if extra_terms is not None:
        for name, fn in extra_terms.items():
            try:
                add = fn(ops, dict(N=N, hbar=hbar, omega=omega, phi=phi), t)
                if add is not None:
                    H += add
            except Exception:
                # Do not fail construction if an optional term errors; leave
                # the engine to handle runtime diagnostics.
                continue

    return 0.5 * (H + H.conj().T)


# Small example: weak-field relativistic correction (toy model)
def weak_field_relativistic(ops: dict, cfg: dict, t: float = 0.0) -> np.ndarray:
    """Toy weak-field correction: small momentum-dependent term.

    This is intentionally simple — a lead-in for adding GR-inspired
    corrections without depending on heavy external libraries.
    """
    p = ops["p"]
    N = cfg.get("N", p.shape[0])
    eps = 1e-3 * float(cfg.get("hbar", 1.0))
    return -eps * (p @ p)


# Register the toy relativistic correction under an easy name
register_term("weak_rel", weak_field_relativistic)
 
