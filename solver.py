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
        return M, False
    
    decision_point = decision_points.pop()

    M = M[:decision_point] + [-M[decision_point]]
    update_msg(M, True, "backtrack")
    return M, True

def decide(clauses, M, decision_points):
    changed = False
    for literal in clauses.literals:
        if literal not in M and -literal not in M:
            decision_points.append(len(M)) # basically save the places where the big dots in the slide would be
            M = M + [literal]
            changed = True
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

    while True:

        if check_conflict(clauses, M): # backtrack if there's a conflict
            print("Conflict: ", M, "\n")
            M, can_backtrack = backtrack(M, decision_points)
            if not can_backtrack: # fail if can't backtrack anymore
                print("\nFailed\n")
                solution = SolverResult(UNSAT)
                print("\nSolution is", solution.assignment, "\n")
                return solution
            else:
                continue

        all_assigned = True
        for literal in clauses.literals:
            if literal not in M and -literal not in M:
                all_assigned = False
                break

        if all_assigned: #this would mean it's satisfied
            solution = SolverResult(result, assignment=M)
            print("\nSolution is", solution.assignment, "\n")
            return solution

        M, changed = pure(clauses, M)
        if changed:
            continue
        M, changed = propagate(clauses, M)
        if changed:
            continue
        M, changed = decide(clauses, M, decision_points)        