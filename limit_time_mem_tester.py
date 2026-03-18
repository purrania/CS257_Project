import signal, time, json

from test_case_maker import load_saved_test_cases
from solver import dpll_solve
from new_watch_lit_solver import watched_literals_solve, wl_stable_solve

def timeout(sig, frame):
    raise TimeoutError

signal.signal(signal.SIGALRM, timeout)

DIMACS_TEST_CASES = load_saved_test_cases("dimacs_tests.json")
MEMORY_LIMITS_BYTES = [1024, 4*1024, 16*1024, 64*1024, 128*1024, 512 * 1024, 1024 * 1024]
# # TIME_LIMITS_SECONDS = [90]
TIME_LIMITS_SECONDS = [5, 15, 30, 60, 90, 120, 240]

# MEMORY_LIMITS_BYTES = [512 * 1024, 1024 * 1024]
# TIME_LIMITS_SECONDS = [90, 120]

# MEMORY_LIMITS_BYTES = [262144, 524288]
# TIME_LIMITS_SECONDS = [120, 300]

# MEMORY_LIMITS_BYTES = [1024]
# TIME_LIMITS_SECONDS = [60]
# MEMORY_LIMITS_BYTES  = [1024*1024]

SOLVERS = {"dpll": dpll_solve, "wl": watched_literals_solve, "wl_stable": wl_stable_solve}

results = []

for time_limit in TIME_LIMITS_SECONDS:
    for memory_limit in MEMORY_LIMITS_BYTES:
        print(f"time limit: {time_limit} seconds, memory_limit: {memory_limit / 1024:.0f} KB\n")

        for solver_name, solve in SOLVERS.items():
            print(f"\nfor solver: {solver_name}")

            timed_out = False
            for test_case in DIMACS_TEST_CASES:
                num_clauses = len(test_case.raw_clauses)
                if timed_out:
                    results.append({"time_limit": time_limit, "memory_limit": memory_limit, "solver_name": solver_name, "num_clauses": num_clauses, "status": "time", "time_taken": None, "max_mem": None})
                    continue
                signal.alarm(time_limit)
                try:
                    start_time = time.time()
                    result = solve(test_case, mem_lim=memory_limit)
                    is_sat = "unsatisfiable" 
                    if result.result:
                        is_sat = "satisfiable"
                    total_time = time.time()-start_time
                    print(f"{num_clauses} clauses: {is_sat} {total_time:.3f} seconds")
                    results.append({"time_limit": time_limit, "memory_limit": memory_limit, "solver_name": solver_name, "num_clauses": num_clauses, "status": is_sat, "time_taken": total_time, "max_mem": result.max_mem})
                except MemoryError:
                    print(f"{num_clauses} clauses: ran out of memory")
                    results.append({"time_limit": time_limit, "memory_limit": memory_limit, "solver_name": solver_name, "num_clauses": num_clauses, "status": "memory", "time_taken": None, "max_mem": None})
                except TimeoutError:
                    print(f"{num_clauses} clauses: ran out of time")
                    results.append({"time_limit": time_limit, "memory_limit": memory_limit, "solver_name": solver_name, "num_clauses": num_clauses, "status": "time", "time_taken": None, "max_mem": None})
                    timed_out = True
                signal.alarm(0)

with open("limit_test_results.json", "w") as f:
    json.dump(results, f)
