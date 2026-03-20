"""Convergence benchmark: sweep basis size N and compare numeric HO eigenvalues to analytic energies."""
import csv
import numpy as np
from physics_engine.hamiltonian import build_H
from physics_engine.config import EngineConfig

Ns = [10, 20, 40, 80]
levels = 6
results = []
for N in Ns:
    cfg = EngineConfig(N=N, hbar=1.0, omega=1.0)
    F_pure = np.zeros(cfg.N + 1)
    F_pure[1] = 0.5
    F_pure[2] = 1.0
    H_pure = build_H(N=cfg.N, hbar=cfg.hbar, omega=cfg.omega, phi=1.0, F=F_pure, g=np.zeros(cfg.N), h=np.zeros((cfg.N, cfg.N)))
    evals = np.linalg.eigvalsh(H_pure)
    n = np.arange(levels)
    analytic = cfg.hbar * cfg.omega * (n + 0.5)
    rel_err = np.abs(evals[:levels] - analytic) / (np.abs(analytic) + 1e-12)
    results.append((N, evals[:levels].tolist(), analytic.tolist(), rel_err.tolist()))

print('Convergence benchmark (relative errors for first {} levels)'.format(levels))
for N, evs, ana, err in results:
    print(f'\nN={N}')
    print(' numeric:', np.round(evs, 8).tolist())
    print(' analytic:', np.round(ana, 8).tolist())
    print(' rel_err:', np.round(err, 8).tolist())

# Optionally save CSV
with open('physics engine/examples/benchmark_convergence_results.csv', 'w', newline='') as f:
    w = csv.writer(f)
    header = ['N'] + [f'level_{i}_num' for i in range(levels)] + [f'level_{i}_analytic' for i in range(levels)] + [f'level_{i}_relerr' for i in range(levels)]
    w.writerow(header)
    for N, evs, ana, err in results:
        row = [N] + evs + ana + err
        w.writerow(row)
print('\nSaved results to physics engine/examples/benchmark_convergence_results.csv')