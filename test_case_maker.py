from clauses import Clause, Clauses
import glob
SAT = True
UNSAT = False

class TestCase:
    def __init__(self, raw_clauses, clauses, result, assignment =  None):
        self.raw_clauses = raw_clauses # for now, we keep this just for debugging
        self.clauses = clauses
        self.result = result
        self.assignment = assignment

# NOTE: I have introduced a num_clauses restriction because the problems 
# from the SAT comp are far too huge for our current implementation to handle.
# Because we only want to use SAT examples to test, we can just use an 
# arbitrary subset of the clauses in each problem. Later, we can do this 
# selection of the subset at random, but for now we can just 
# use clauses 1 ... {num_clauses}
def make_dimacs_case(name, path, result, num_clauses = 5):
    raw_clauses = []
    with open(path, "r") as f:
        lines = f.readlines()[1:num_clauses]
        raw_clauses = [[int(x) for x in line.split()] for line in lines]
    return make_test_case(name, raw_clauses, result)

def make_test_case(name, raw_clauses, result):
    clause_list = [Clause(x) for x in raw_clauses]
    clauses = Clauses(clause_list)
    result = result
    test_case = TestCase(raw_clauses, clauses, result)
    return test_case 

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
    ], UNSAT),
]

# NOTE: download the problems from the leaderboard site, then extract the .cnf into the repo, 
# my .gitignore makes sure we won't clutter the repo with the test cases.  
DIMACS_TEST_CASES = [
    make_dimacs_case(name = "dimacs {f}", path = f, result = SAT) for f in glob.glob("*.cnf")
] 