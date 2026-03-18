import json
import matplotlib.pyplot as plt
import numpy as np

with open("limit_test_results.json") as f:
    rows = json.load(f)

time_limits = set()
memory_limits = set()
clauses = set()
solvers = set()

for r in rows:
    time_limits.add(r["time_limit"])
    memory_limits.add(r["memory_limit"])
    clauses.add(r["num_clauses"])
    solvers.add(r["solver_name"])

time_limits = sorted(time_limits)
memory_limits = sorted(memory_limits)
clauses = sorted(clauses)
solvers = sorted(solvers)

# table: max clauses solved per time and memory

print(f"\n{'Time (sec)':<10} {'Memory (KB)':<10} {'DPLL max':<10} {'WL max'}")

for time_limit in time_limits:
    for memory_limit in memory_limits:
        dpll_max = 0
        wl_max=0
        for r in rows:
            if r["time_limit"] == time_limit and r["memory_limit"] == memory_limit:
                if r["status"] in ("satisfiable", "unsatisfiable"):
                    if r["solver_name"] == "dpll" and r["num_clauses"] > dpll_max:
                        dpll_max = r["num_clauses"]
                    if r["solver_name"] == "wl" and r["num_clauses"] > wl_max:
                        wl_max = r["num_clauses"]
        print(f"{time_limit:<10} {memory_limit // 1024:<10} {dpll_max:<10} {wl_max}")
print("\n")

def get_time(solver, time_limit, memory_limit, num_clauses):
    for r in rows:
        if r["solver_name"] == solver and r["time_limit"] == time_limit and r["memory_limit"] == memory_limit and r["num_clauses"] == num_clauses:
            return r["time_taken"]
    return None
 
def get_status(solver, time_limit, memory_limit, num_clauses):
    for r in rows:
        if r["solver_name"] == solver and r["time_limit"] == time_limit and r["memory_limit"] == memory_limit and r["num_clauses"] == num_clauses:
            return r["status"]
    return "Skipped"

def convert_to_index(status):
    if status in ("satisfiable", "unsatisfiable"):
        return 2
    if status == "time":
        return 1
    return 0

# heatmap code

for time_limit in time_limits:
    solvers = ["dpll", "wl", "wl_stable"]
    solvers_names = {"dpll": "DPLL", "wl": "WL", "wl_stable": "WL + Stable"}
    figure, axes = plt.subplots(1, len(solvers), figsize=(8 * len(solvers), 6))
    for axis, solver in zip(axes, solvers):
        grid = []
        for memory_limit in memory_limits:
            row = []
            for clause in clauses:
                row.append(convert_to_index(get_status(solver, time_limit, memory_limit, clause)))
            grid.append(row)

        grid = np.array(grid)
        axis.imshow(grid, cmap="RdYlGn", origin="lower")
        axis.set_xticks(range(len(clauses)))
        axis.set_xticklabels(clauses)
        axis.set_yticks(range(len(memory_limits)))

        y_tick_labels = []
        for memory_limit in memory_limits:
            y_tick_labels.append(f"{memory_limit // 1024}")
        
        axis.set_yticklabels(y_tick_labels)
        axis.set_xlabel("# Clauses")
        axis.set_ylabel("Memory Limits (KB)")
        axis.set_title(solvers_names[solver])
            
        for i, mem_limit in enumerate(memory_limits):
            for j, clause in enumerate(clauses):
                status = get_status(solver, time_limit, mem_limit, clause)
                label = {"satisfiable": "SAT", "unsatisfiable": "UNSAT", "time": "TIME", "memory": "MEM"}.get(status, "None")
                axis.text(j, i, label, ha="center", va="center")
        
    figure.suptitle(f"Result by Clauses and Memory Limit (time limit = {time_limit} seconds)", fontsize=20)
    plt.savefig(f"heatmap_{time_limit}s.png")
    plt.close()


max_time_limit = max(time_limits)
max_mem_limit = max(memory_limits)

# table: memory used per num clauses and ratio

solvers = ["dpll", "wl", "wl_stable"]

print(f"{'Clauses':<12} {'DPLL Memory':<12} {'WL Memory':<12} {'Ratio'}")

for clause in clauses:
    print(f"\n{clause} clauses")
    for solver in solvers:
        for row in rows:
            if row["time_limit"] == max_time_limit and row["memory_limit"] == max_mem_limit and row["num_clauses"] == clause and row["solver_name"] == solver:
                if row["max_mem"] is not None:
                    print(f" {solver}: {row['max_mem']:} B")

# for clause in clauses:
#     dpll_mem = None
#     wl_mem = None
    
#     for r in rows:
#         if r["time_limit"] == max_time_limit and r["memory_limit"] == max_mem_limit and r["num_clauses"] == clause:
#                 if r["solver_name"] == "dpll":
#                     dpll_mem = r["max_mem"]
#                 if r["solver_name"] == "wl":
#                     wl_mem = r["max_mem"]
    
#     dpll_m = "None"
#     wl_m = "None"

#     if dpll_mem is not None:
#         dpll_m = f"{dpll_mem}B"
#     if wl_mem is not None:
#         wl_m = f"{wl_mem} B"

#     print(f"{clause:<12} {dpll_m:<12} {wl_m:<12} {wl_mem / dpll_mem:.1f}x") 

# print("\n")