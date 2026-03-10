import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

benchmark_files = glob.glob("results/*.csv")
latest_file = max(benchmark_files, key=os.path.getmtime)
print("Using benchmark:", latest_file)
df = pd.read_csv(latest_file)


#linear
plt.figure()

for solver, group in df.groupby("solver"):
    group = group.sort_values("size")
    plt.plot(group["size"], group["time"], marker="o", label=solver)

plt.xlabel("Number of clauses")
plt.ylabel("Solve time (seconds)")
plt.title("SAT Solver Benchmark (Linear)")
plt.legend()
plt.grid(True)

plt.show()

#logarithmic
plt.figure()

for solver, group in df.groupby("solver"):
    group = group.sort_values("size")
    plt.plot(group["size"], group["time"], marker="o", label=solver)

plt.xlabel("Number of clauses")
plt.ylabel("Solve time (seconds)")
plt.title("SAT Solver Benchmark (Log-Log)")
plt.legend()
plt.grid(True)

plt.xscale("log")
plt.yscale("log")

plt.show()
