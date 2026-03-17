import sys, io, time, signal, argparse, datetime, statistics
from pathlib import Path
import matplotlib.pyplot as plt

from test_case_maker import load_saved_test_cases, RAW_TEST_CASES, make_test_case
from solver import dpll_solve
from new_watch_lit_solver import (
    watched_literals_solve,
    wl_blocking_solve,
    wl_stable_solve,
    wl_blocking_stable_solve,
)

SAT = True
UNSAT = False
TIME_LIMIT = 60  # seconds per test case if we want to impose a time limit

SOLVERS = {
    "dpll": dpll_solve,
    "wl_base": watched_literals_solve,
    "wl_blocking": wl_blocking_solve,
    "wl_stable": wl_stable_solve,
    "wl_block+stable": wl_blocking_stable_solve,
}


def timeout_handler(sig, frame):
    raise TimeoutError


signal.signal(signal.SIGALRM, timeout_handler)


def run_solver_silent(solve, test_case, time_limit=0):
    """Run a solver with stdout suppressed and an optional time limit."""
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        signal.alarm(time_limit)
        start = time.time()
        result = solve(test_case)
        elapsed = time.time() - start
        signal.alarm(0)
        return result, elapsed
    except TimeoutError:
        return None, time_limit
    finally:
        sys.stdout = old_stdout


def main():
    parser = argparse.ArgumentParser() #Some optional variations on experiments to run
    parser.add_argument(
        "--max-clauses", type=int, default=None,
        help="Only run test cases with at most this many clauses (e.g. 320)",
    )
    parser.add_argument(
        "--timeout", type=int, default=0,
        help="Timeout in seconds per test case (default: 0 = no timeout)",
    )
    parser.add_argument(
        "--include-dpll", action="store_true", default=False,
        help="Include the base DPLL solver (no watched literals)",
    )
    args = parser.parse_args()

    solvers = dict(SOLVERS)
    if not args.include_dpll:
        solvers.pop("dpll", None)

    # Build test cases: sanity checks + DIMACS benchmarks
    sanity_tests = [make_test_case(x[0], x[1], x[2]) for x in RAW_TEST_CASES]
    dimacs_tests = load_saved_test_cases("dimacs_tests.json")
    all_tests = sanity_tests + dimacs_tests

    if args.max_clauses is not None:
        all_tests = [tc for tc in all_tests if len(tc.raw_clauses) <= args.max_clauses]

    
    plot_data = {name: ([], []) for name in solvers}
    timing = {name: {} for name in solvers}

    all_pass = True

    for solver_name, solve in solvers.items():
        print(f"=== {solver_name} ===")
        for i, tc in enumerate(all_tests):
            size = len(tc.raw_clauses)
            result, elapsed = run_solver_silent(solve, tc, time_limit=args.timeout)

            if result is None:
                status = "TIMEOUT"
                correct = False
            else:
                correct = result.result == tc.result
                status = "PASS" if correct else "FAIL"

            if not correct:
                all_pass = False

            got = result.result if result else "TIMEOUT"
            print(
                f"  [{status}] {tc.name:40s} "
                f"clauses={size:5d}  expected={tc.result}  got={got}  "
                f"({elapsed:.4f}s)"
            )

            # Only include in plot if it completed (for timing graph)
            if result is not None:
                plot_data[solver_name][0].append(size)
                plot_data[solver_name][1].append(elapsed)
                timing[solver_name][i] = elapsed

        print()

    # Print final verdict
    print("=" * 50)
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 50)

    # Print median speedup over baseline
    baseline = "dpll" if "dpll" in solvers else "wl_base"
    print(f"\nMedian speedup over {baseline} (higher = faster):")
    baseline_times = timing[baseline]
    for solver_name in solvers:
        if solver_name == baseline:
            continue
        ratios = []
        for i, base_t in baseline_times.items():
            if i in timing[solver_name] and base_t > 0:
                ratios.append(base_t / timing[solver_name][i])
        if ratios:
            median = statistics.median(ratios)
            print(f"  {solver_name:20s} {median:.2f}x")
        else:
            print(f"  {solver_name:20s} (no comparable test cases)")

    # Plot: time vs number of clauses (log-log)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    colors = {
        "dpll": "tab:purple",
        "wl_base": "tab:blue",
        "wl_blocking": "tab:orange",
        "wl_stable": "tab:green",
        "wl_block+stable": "tab:red",
    }

    for solver_name, (sizes, times) in plot_data.items():
        ax1.plot(
            sizes, times,
            marker="o", label=solver_name, color=colors[solver_name],
        )
        ax2.plot(
            sizes, times,
            marker="o", label=solver_name, color=colors[solver_name],
        )

    ax1.set_xlabel("Number of Clauses")
    ax1.set_ylabel("Solve Time (seconds)")
    ax1.set_title("Solver Benchmark (Linear Scale)")
    ax1.legend()
    ax1.grid(True)

    ax2.set_xlabel("Number of Clauses")
    ax2.set_ylabel("Solve Time (seconds)")
    ax2.set_title("Solver Benchmark (Log-Log Scale)")
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.legend()
    ax2.grid(True, which="both", linestyle="--", alpha=0.5)

    plt.tight_layout()
    Path("results").mkdir(exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%b%d_%I%M%p")
    filename = f"results/bench_{timestamp}.png"
    plt.savefig(filename, dpi=150)
    print(f"\nGraph saved to {filename}")


if __name__ == "__main__":
    main()
