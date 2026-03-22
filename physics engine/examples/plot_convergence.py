"""Plot convergence results saved by benchmark_convergence.py and save PNG."""
import csv
import numpy as np
import matplotlib.pyplot as plt

csv_path = 'physics engine/examples/benchmark_convergence_results.csv'
Ns = []
levels = None
nums = []
anas = []
errs = []
with open(csv_path, newline='') as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        N = int(row[0])
        Ns.append(N)
        # parse numeric, analytic, relerr
        l = len(row)
        half = (l - 1) // 3
        num = list(map(float, row[1:1+half]))
        ana = list(map(float, row[1+half:1+2*half]))
        err = list(map(float, row[1+2*half:1+3*half]))
        nums.append(num)
        anas.append(ana)
        errs.append(err)

Ns = np.array(Ns)
nums = np.array(nums)
errs = np.array(errs)

# plot relative error for first few levels
plt.figure(figsize=(6,4))
for lvl in range(errs.shape[1]):
    plt.plot(Ns, errs[:, lvl], marker='o', label=f'level {lvl}')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Basis size N')
plt.ylabel('Relative error')
plt.title('Convergence of HO eigenvalues vs analytic')
plt.legend()
plt.grid(True)
plt.tight_layout()
out_png = 'physics engine/examples/benchmark_convergence_plot.png'
plt.savefig(out_png)
print('Saved plot to', out_png)
plt.close()
