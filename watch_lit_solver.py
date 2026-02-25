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

#New Watched Literals Starts Here

def _lit_is_false(lit, M_set):
    """Returns List of false literals"""
    return -lit in M_set

def _enqueue(lit, M, M_set):
    """New way to do Unit Propagation! 
    """
    if lit in M_set:
        return True
    if -lit in M_set:
        return False
    M.append(lit)
    M_set.add(lit)
    return True

def _init_watches(clauses):
    """
    watchlist[lit]: Tells us for an input literal lit what clauses are "watching it"
    watched[clause]: #Tells us for an input clause, what literals it is "watching" (each clause watches 2, so watched[clause] is a tuple of length 2)
    """
    watchlist = {}
    watched = {}

    for clause in clauses.clause_list:
        lits = clause.literals
        if len(lits) == 0:
            watched[clause] = (None, None) #if the clause is empty -> UNSAT 
            continue

        w1 = lits[0]
        w2 = lits[0] if len(lits) == 1 else lits[1]
        watched[clause] = (w1, w2) #Otherwise we assign it two literals to "watch" (unless it is unit of course)

        watchlist.setdefault(w1, []).append(clause) #adds w1 to the dictionary if it isn't there already, then appends the clause watching it
        if w2 != w1:
            watchlist.setdefault(w2, []).append(clause)

    return watchlist, watched

def _bcp_watched(M, M_set, qhead, watchlist, watched):
    while qhead < len(M):
        lit_true = M[qhead]
        qhead += 1
        lit_false = -lit_true
        wl = watchlist.get(lit_false, []) #gets the list of clauses watching lit_false (they might be conflicting now)

        i = 0
        while i < len(wl):
            clause = wl[i]
            w1, w2 = watched[clause]

            if w2 == lit_false: #reorders if needed so that w1 is the false literal
                w1, w2 = w2, w1
                watched[clause] = (w1, w2)


            # Try to find a new literal to watch (anything works except stuff in _lit_is_false, the list of false literals)
            moved = False
            for l in clause.literals:
                if l == w2:
                    continue
                if not _lit_is_false(l, M_set):
                    watched[clause] = (l, w2) #replace w1 with l

                    # Bookkeeping (remove clause from list, update watchlist)
                    wl[i] = wl[-1]
                    wl.pop()

                    watchlist.setdefault(l, []).append(clause) 
                    moved = True
                    break

            if moved:
                continue  

            #deals with the other cases. clause is either SAT, UNIT, or CONFLICT: 
            #if we got here, then every other literal in the clause except possibly w2 is false:
            if w2 in M_set: #SAT
                i += 1
                continue

            if _lit_is_false(w2, M_set): #conflict
                return False, qhead

            if not _enqueue(w2, M, M_set): #unit
                return False, qhead
            i += 1

    return True, qhead

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
    M_set = set() 
    decision_points = []

    watchlist, watched = _init_watches(clauses) #sets up our watched literals variables
    qhead = 0

    # Starts by checking for UNSAT
    for clause in clauses.clause_list:
        if len(clause.literals) == 0:
            print("\nFailed\n")
            solution = SolverResult(UNSAT)
            print("\nSolution is", solution.assignment, "\n")
            return solution
    
    #Starts by checking for Unit clauses
    for clause in clauses.clause_list:
        if len(clause.literals) == 1:
            if not _enqueue(clause.literals[0], M, M_set): #failed immediately
                print("\nFailed\n")
                solution = SolverResult(UNSAT)
                print("\nSolution is", solution.assignment, "\n")
                return solution

    while True:
        ok, qhead = _bcp_watched(M, M_set, qhead, watchlist, watched)
        if not ok: # backtrack if there's a conflict
            print("Conflict: ", M, "\n")
            M, can_backtrack = backtrack(M, decision_points)
            if not can_backtrack: # fail if can't backtrack anymore
                print("\nFailed\n")
                solution = SolverResult(UNSAT)
                print("\nSolution is", solution.assignment, "\n")
                return solution
            else:
                # Rebuild fast structures after backtrack.
                M_set = set(M)
                qhead = len(M) - 1  # propagate the flipped decision
                continue

        all_assigned = True
        for literal in clauses.literals:
            if literal not in M_set and -literal not in M_set:
                all_assigned = False
                break

        if all_assigned: #this would mean it's satisfied
            solution = SolverResult(result, assignment=M)
            print("\nSolution is", solution.assignment, "\n")
            return solution

        M, changed = pure(clauses, M)
        if changed:
            M_set = set(M)
            continue
        M, changed = decide(clauses, M, decision_points)
        if changed:
            M_set = set(M)