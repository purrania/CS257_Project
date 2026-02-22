SAT = True
UNSAT = False

class SolverResult:
    def __init__(self, result, assignment = None):
       self.result = result
       self.assignment = assignment

def update_msg(M, changed, name):
    print(f"try {name}, new M={M}, changed = {changed}")

def check_conflict(clauses, M):
    for clause in clauses.clause_list:
        conflicting = True
        for literal in clause.literals:
            if -literal not in M:
                conflicting = False
                break
        if conflicting:
            return True
    return False

def propagate(clauses, M):
    changed = False
    candidate = None
    for clause in clauses.clause_list:
        neg_literal_in_M_count = 0 
        candidate = None
        for literal in clause.literals:
            if -literal in M:
                neg_literal_in_M_count +=1
            elif literal not in M:
                if candidate is None:
                    candidate = literal
                else:
                    break
            else:
                break
        if candidate is not None and neg_literal_in_M_count == len(clause.literals)-1:
            M =  M + [candidate]
            changed = True
            break
    update_msg(M, changed, "prop")
    return M, changed

def backtrack(M, decision_points):
    if len(decision_points) == 0:
        return M
    
    decision_point = decision_points.pop() # again cant tell if this is off by one error NEED TO TEST

    M = M[:decision_point] + [-M[decision_point]]
    return M

def fail():
    # tbh idek if we need this function but i'll change solve first to see if we need it
    pass

def decide(clauses, M, decision_points):
    changed = False
    for literal in clauses.literals:
        if literal not in M and -literal not in M:
            M =  M + [literal]
            changed = True
            decision_points.append(len(M)) # basically save the places where the big dots in the slide would be - might have off by one error so gotta test logic
            break
    update_msg(M, changed, "decide")
    return M, changed

def pure(clauses, M):
    changed = False
    for literal in clauses.literals:
        if literal not in M and -literal not in M:
            if -literal not in clauses.literals: # suppose we terminate early
                changed = True
                M =  M + [literal]
                break
    update_msg(M, changed, "pure")
    return M, changed

def solve(test_case):
    print(f"\nTest case:{test_case.raw_clauses}")
    clauses = test_case.clauses
    result = True
    M = []
    decision_points = []
    i = 0 
    if test_case.result == SAT:
        # NOTE: I have not added the backtrack or fail cases
        # So we have to break on i, otherwise, we may go in circles. 
        while (len(M) != len(clauses.unique_literals)) and i < 5: 
            M, changed = pure(clauses, M)
            if changed:
                continue
            M, changed = propagate(clauses, M)
            if changed:
                continue
            M, changed = decide(clauses, M, decision_points)
            i += 1
    solution = SolverResult(result, assignment=M)
    print("\nSolution is", solution.assignment, "\n")
    return solution