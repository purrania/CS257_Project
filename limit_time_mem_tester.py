import signal, time

from test_case_maker import load_saved_test_cases
from solver import dpll_solve
from watch_lit_solver import watched_literals_solve

def timeout(sig, frame):
    raise TimeoutError

signal.signal(signal.SIGALRM, timeout)

DIMACS_TEST_CASES = load_saved_test_cases("dimacs_tests.json")
# MEMORY_LIMITS_BYTES = [1024, 4096, 16384, 65536, 262144, 512 * 1024, 1024 * 1024]
# TIME_LIMITS_SECONDS = [5, 15, 30, 60, 90, 120, 300]

# MEMORY_LIMITS_BYTES = [512 * 1024, 1024 * 1024]
# TIME_LIMITS_SECONDS = [90, 120]

# MEMORY_LIMITS_BYTES = [262144, 524288]
# TIME_LIMITS_SECONDS = [120, 300]

MEMORY_LIMITS_BYTES = [1024]
TIME_LIMITS_SECONDS = [5]
SOLVERS = {"dpll": dpll_solve, "wl": watched_literals_solve}

for time_limit in TIME_LIMITS_SECONDS:
    for memory_limit in MEMORY_LIMITS_BYTES:
        print(f"time limit: {time_limit} seconds, memory_limit: {memory_limit / 1024:.0f} KB\n")

        for solver_name, solve in SOLVERS.items():
            print(f"\nfor solver: {solver_name}")
            for test_case in DIMACS_TEST_CASES:
                num_clauses = len(test_case.raw_clauses)
                signal.alarm(time_limit)
                try:
                    start_time = time.time()
                    result = solve(test_case, mem_lim=memory_limit)
                    is_sat = "unsatisfiable" 
                    if result.result:
                        is_sat = "satisfiable"
                    print(f"{num_clauses} clauses: {is_sat} {time.time()-start_time:.3f} seconds")
                except MemoryError:
                    print(f"{num_clauses} clauses: ran out of memory")
                except TimeoutError:
                    print(f"{num_clauses} clauses: ran out of time")
                    break
                signal.alarm(0)