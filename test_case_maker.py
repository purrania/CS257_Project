from clauses import Clause, Clauses

SAT = True
UNSAT = False

class TestCase:
    def __init__(self, raw_clauses, clauses, result, assignment =  None):
        self.raw_clauses = raw_clauses # for now, we keep this just for debugging
        self.clauses = clauses
        self.result = result
        self.assignment = assignment

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
    )

]