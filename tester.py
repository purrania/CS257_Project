from test_case_maker import * 
from solver import dpll_solve
from watch_lit_solver import watched_literals_solve
from pathlib import Path
import time, json, argparse, csv, datetime
DEFAULT_SOLVER = "both"
SANITY_TEST_INCLUDE = False
DIMACS_TEST_INCLUDE = True
VERBOSE = False
SAT = True
UNSAT = False


SOLVERS = {
    "dpll": dpll_solve,
    "wl": watched_literals_solve
}

def load_test_cases():
    '''
    test_case_list = [
        make_test_case(
            name = "Simple test case",
            raw_clauses = [
                [1]
            ],
            result = SAT
        ),
        make_test_case(
            name = "pure/prop test case",
            raw_clauses = [
                [1], 
                [-1,2],
            ],
            result = SAT
        ),
        make_test_case(
            name = "pure/prop longer",
            raw_clauses=[
                [1,2,3,4,5],
                [-1,-2,-3,4,5],
                [-1,2,3,-4,5],
                [-1,-2,-3,-4,5],
            ],
            result = SAT
        )
    ]
    return test_case_list
    '''
    test_case_list = []
    if SANITY_TEST_INCLUDE:
        test_case_list = [make_test_case(x[0],x[1],x[2]) for x in RAW_TEST_CASES]
    if DIMACS_TEST_INCLUDE:
        test_case_list += DIMACS_TEST_CASES
    return test_case_list
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # we can set either "both", to run both, for our full test
    # or "dpll", "wl" to run DPLL or watched literals solver
    parser.add_argument("--solver_name", type=str, default=DEFAULT_SOLVER)
    args = parser.parse_args()
    if args.solver_name == "both":
        solvers_to_run = SOLVERS
    else:
        solvers_to_run = {args.solver_name: SOLVERS[args.solver_name]}    
   
    test_cases = load_test_cases()
    test_cases_length = len(test_cases)

    Path("results").mkdir(exist_ok=True)
    rows = []

    for solver_name, solve in solvers_to_run.items():
        for i, test_case in enumerate(test_cases):
            print(f"{solver_name} {1+i}/{len(test_cases)}")
            start_time = time.time()
            solver_result = solve(test_case)
            time_taken = time.time() - start_time
            correct = solver_result.result == test_case.result
            size = len(test_case.raw_clauses)
            rows.append({
                "solver": solver_name,
                "size": size,
                "time": time_taken,
                "correct": correct
            })
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file_path = f"results/benchmark_{timestamp}.csv"
    with open(output_file_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["solver", "size", "time", "correct"]
        )
        writer.writeheader()
        writer.writerows(rows) 
    
