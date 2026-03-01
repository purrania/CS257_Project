from test_case_maker import * 
from solver import solve
import time

VERBOSE = False
SAT = True
UNSAT = False


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
    test_case_list = [make_test_case(x[0],x[1],x[2]) for x in RAW_TEST_CASES]
    test_case_list += DIMACS_TEST_CASES
    return test_case_list
if __name__ == "__main__":
    test_cases = load_test_cases()
    test_cases_length = len(test_cases) 

    correct_questions = 0 

    start_time = time.time()
    for i, test_case in enumerate(test_cases):
        #print(test_case)
        solver_result = solve(test_case)
        if solver_result.result == test_case.result:
            if VERBOSE:
                print(f"Test case {i+1}/{test_cases_length} passed, for raw clauses: {test_case.raw_clauses}")
            correct_questions += 1
        else:
            if VERBOSE:
                print(f"Test case {i+1}/{test_cases_length} failed, for clauses: {test_case.raw_clauses}")
    stop_time = time.time()
    time_taken = stop_time - start_time
    metrics = {
        "time_taken": time_taken,   
        "correct questions": correct_questions,
        "total questions": test_cases_length, 
        "correctness": correct_questions/test_cases_length
    }   
    #print(metrics) 

        
            
            