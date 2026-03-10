from clauses import Clause, Clauses
import glob, random, json
SAT = True
UNSAT = False
NUM_TESTS = 9
class TestCase:
    def __init__(self, name, raw_clauses, clauses, result, assignment =  None):
        self.name = name
        self.raw_clauses = raw_clauses # for now, we keep this just for debugging
        self.clauses = clauses
        self.result = result
        self.assignment = assignment

def make_dimacs_case(name, clauses, result, num_clauses=100):
    # ensure we don't sample more clauses than exist
    num_clauses = min(num_clauses, len(clauses))
    sampled_clauses = random.sample(clauses, num_clauses)
    return make_test_case(name, sampled_clauses, result)

def load_dimacs(path):
    clauses = []
    with open(path) as f:
        for line in f:
            if line.startswith(("c", "p")):
                continue
            clauses.append([int(x) for x in line.split() if x != "0"])
    return clauses

def make_dimacs_cases(path):
    dimacs_clauses = load_dimacs(path)
    sizes = [10 * 2 ** n for n in range(NUM_TESTS)]
    test_cases = []
    for size in sizes:
        print(f"making test case of size {size}, max {10 * 2 ** (NUM_TESTS-1)}")
        test_case = make_dimacs_case(f"dimacs_{size}", dimacs_clauses, SAT, size)
        test_cases.append(test_case)
    return test_cases 
def make_test_case(name, raw_clauses, result):
    clause_list = [Clause(x) for x in raw_clauses]
    clauses = Clauses(clause_list)
    result = result
    test_case = TestCase(name, raw_clauses, clauses, result)
    return test_case 

def save_test_cases(test_cases, path):
    data = []

    for tc in test_cases:
        data.append({
            "name": tc.name,
            "raw_clauses": tc.raw_clauses,
            "result": tc.result
        })

    with open(path, "w") as f:
        json.dump(data, f)

def load_saved_test_cases(path):
    with open(path) as f:
        data = json.load(f)

    test_cases = []

    for entry in data:
        tc = make_test_case(
            entry["name"],
            entry["raw_clauses"],
            entry["result"]
        )
        test_cases.append(tc)

    return test_cases

RAW_TEST_CASES = [
    ("EASY - One literal", [[1]], SAT),
    
    ("EASY - pure/prop", [[1], [1,2]], SAT),

    ("EASY - pure/prop longer", [
        [-1, 2, 3],
        [-1,-2, 3],
        [1,-2, -3]
    ], SAT),
    
    ("EASY - longer pure/prop/decide", [
        [1,2,3,-4,5],
        [-1,2,3,-4,5],
        [-1,-2,-3,-4,-5],
        [1,2,3,-4,5]
    ], SAT),

    ("EASY - only one solution, longer", [
        [x * int(x==y) - x * int(x != y) for x in range(1,6)] for y in range(6)
    ], SAT 
    ),

    ("DEBUG - example from lec 4 slides", [
        [1, -2], [-1, -2], [2, 3], [-3, 2], [1, 4]
    ], UNSAT),

    ("DEBUG - example from hw2", [
        [1, 2, 3], [-1, -2, -3], [-1, 2, 3], [-2, 3], [2, -3]
    ], SAT), # NOTE: this test case had to be fixed, as it is SAT, based on HW2 solutions
]

DIMACS_TEST_CASES = load_saved_test_cases("dimacs_tests.json")
if __name__ == "__main__":
    cnf_file = [x for x in glob.glob("*.cnf")][0] # for now, we are only testing on one file
    dimacs_test_cases = make_dimacs_cases(cnf_file)
    save_test_cases(dimacs_test_cases, "dimacs_tests.json") 
