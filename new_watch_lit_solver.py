import sys

from utils import update_msg, trunc_print
SAT = True
UNSAT = False


class SolverResult:
    def __init__(self, result, assignment=None):
        self.result = result
        self.assignment = assignment


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


# New Watched Literals Starts Here

def _lit_is_false(lit, M_set):
    """Returns List of false literals"""
    return -lit in M_set



def _lit_value(lit, M_set):
    """For the stable watches optimization we assign each literal a number 
    depending on its value: false -> 0, unassigned -> 1, true -> 2."""
    if lit in M_set:
        return 2
    if -lit in M_set:
        return 0
    return 1



def _current_stability(lit, M_set, stability, decision_count):
    """Returns how long a literal has been in its current state (here time is measured in decisions)"""
    if stability is None:
        return 0
    value = stability.get(lit, 0)
    if lit in M_set:
        return decision_count - value
    return value



def _stable_score(lit, M_set, stability, decision_count):
    return _lit_value(lit, M_set) * _current_stability(lit, M_set, stability, decision_count)



def _limp(lit, stability, decision_count):
    """The stability dictionary tracks for each literal how long it has been in its
    current state. This function updates the stability value for a given literal when that literal 
    becomes relevant (e.g. when it is assigned or unassigned. It's nice because we don't need to update
    every literal at every iteration."""
    if stability is None:
        return
    stability[lit] = decision_count - stability.get(lit, 0)



def _enqueue(lit, M, M_set, stability=None, decision_count=0):
    """New way to do Unit Propagation!
    """
    if lit in M_set:
        return True
    if -lit in M_set:
        return False
    M.append(lit)
    M_set.add(lit)
    _limp(lit, stability, decision_count)
    return True


def _init_watches(clauses, use_blocking=False):
    """
    watchlist[lit]: Tells us for an input literal lit what clauses are "watching it"
    watched[clause]: #Tells us for an input clause, what literals it is "watching" (each clause watches 2, so watched[clause] is a tuple of length 2)
    The change for blocking literals is that the entries of watchlist[lit] are [clause, blocker] rather than just [clause] 
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

        blocker = w2 if use_blocking else None
        watchlist.setdefault(w1, []).append([clause, blocker]) #adds w1 to the dictionary if it isn't there already, then appends the clause watching it
        if w2 != w1:
            watchlist.setdefault(w2, []).append([clause, blocker])

    return watchlist, watched



def _move_watch(wl, i, new_watch, other_watch, clause, watchlist, watched, use_blocking=False):
    """Move the false watch to new_watch and update watchlist bookkeeping."""
    watched[clause] = (new_watch, other_watch)
    blocker = other_watch if use_blocking else None

    wl[i] = wl[-1]
    wl.pop()
    watchlist.setdefault(new_watch, []).append([clause, blocker])



def _best_non_false_literal(clause, other_watch, M_set, use_stable, stability, decision_count):
    """Picks a new literal to watch among literals that are not false."""
    if not use_stable:
        for lit in clause.literals:
            if lit == other_watch:
                continue
            if not _lit_is_false(lit, M_set):
                return lit
        return None

    best_lit = None
    best_score = -1
    for lit in clause.literals:
        if lit == other_watch:
            continue
        if _lit_is_false(lit, M_set):
            continue
        score = _stable_score(lit, M_set, stability, decision_count)
        if score > best_score:
            best_lit = lit
            best_score = score
    return best_lit



def _best_true_literal(clause, other_watch, M_set, use_stable, stability, decision_count):
    """Finds the SAT literal to use as a blocking literal"""
    if not use_stable:
        for lit in clause.literals:
            if lit == other_watch:
                continue
            if lit in M_set:
                return lit
        return None

    best_lit = None
    best_score = -1
    for lit in clause.literals:
        if lit == other_watch:
            continue
        if lit not in M_set:
            continue
        score = _stable_score(lit, M_set, stability, decision_count)
        if score > best_score:
            best_lit = lit
            best_score = score
    return best_lit



def _bcp_watched(
    M,
    M_set,
    qhead,
    watchlist,
    watched,
    use_blocking=False,
    use_stable=False,
    stability=None,
    decision_count=0,
):
    while qhead < len(M):
        lit_true = M[qhead]
        qhead += 1
        lit_false = -lit_true
        wl = watchlist.get(lit_false, []) #gets the list of clauses watching lit_false (they might be conflicting now)

        i = 0
        while i < len(wl):
            entry = wl[i]
            clause = entry[0]
            blocker = entry[1]

            # This is the main blocking literal optimization. If the blocker is true, we can just skip the entire clause because it's already SAT
            if use_blocking and blocker is not None and blocker in M_set:
                i += 1
                continue

            w1, w2 = watched[clause]

            if w2 == lit_false: #reorders if needed so that w1 is the false literal
                w1, w2 = w2, w1
                watched[clause] = (w1, w2)

            # Sanity Check 
            if w1 != lit_false:
                i += 1
                continue

            if w2 in M_set: #SAT
                if use_blocking:
                    entry[1] = w2
                i += 1
                continue

            if use_blocking:
                true_lit = _best_true_literal(
                    clause,
                    w2,
                    M_set,
                    use_stable,
                    stability,
                    decision_count,
                )
                if true_lit is not None:
                    entry[1] = true_lit
                    i += 1
                    continue

                candidate = _best_non_false_literal(
                    clause,
                    w2,
                    M_set,
                    use_stable,
                    stability,
                    decision_count,
                )
                if candidate is not None:
                    _move_watch(wl, i, candidate, w2, clause, watchlist, watched, use_blocking=True)
                    continue
            else:
                candidate = _best_non_false_literal(
                    clause,
                    w2,
                    M_set,
                    use_stable,
                    stability,
                    decision_count,
                )
                if candidate is not None:
                    _move_watch(wl, i, candidate, w2, clause, watchlist, watched, use_blocking=False)
                    continue

            #deals with the other cases. clause is either SAT, UNIT, or CONFLICT:
            #if we got here, then every other literal in the clause except possibly w2 is false:
            if _lit_is_false(w2, M_set): #conflict
                return False, qhead

            if not _enqueue(w2, M, M_set, stability=stability, decision_count=decision_count): #unit
                return False, qhead

            if use_blocking:
                entry[1] = w2
            i += 1

    return True, qhead



def backtrack(M, decision_points, M_set=None, stability=None, decision_count=0):
    if len(decision_points) == 0:
        return M, False

    decision_point = decision_points.pop()

    if stability is not None:
        for lit in M[decision_point:]:
            _limp(lit, stability, decision_count)

    M = M[:decision_point] + [-M[decision_point]]

    if M_set is not None:
        M_set.clear()
        M_set.update(M)

    if stability is not None:
        _limp(M[-1], stability, decision_count)

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
                M = M + [literal]
                break
    update_msg(M, changed, "pure")
    return M, changed



def _watched_solver_core(test_case, mem_lim=None, use_blocking=False, use_stable=False):
    raw_clauses = test_case.raw_clauses
    trunc_print("Test Case", raw_clauses)
    clauses = test_case.clauses
    result = True
    M = []
    M_set = set()
    decision_points = []
    decision_count = 0
    stability = {} if use_stable else None

    watchlist, watched = _init_watches(clauses, use_blocking=use_blocking) #sets up our watched literals variables
    qhead = 0

    # Starts by checking for UNSAT
    for clause in clauses.clause_list:
        if len(clause.literals) == 0:
            print("\nFailed\n")
            solution = SolverResult(UNSAT)
            return solution

    #Starts by checking for Unit clauses
    for clause in clauses.clause_list:
        if len(clause.literals) == 1:
            if not _enqueue(
                clause.literals[0],
                M,
                M_set,
                stability=stability,
                decision_count=decision_count,
            ):
                print("\nFailed\n")
                solution = SolverResult(UNSAT)
                return solution

    while True:
        if mem_lim is not None:
            used_mem = (
                sys.getsizeof(M)
                + sys.getsizeof(decision_points)
                + sys.getsizeof(M_set)
                + sys.getsizeof(watchlist)
                + sys.getsizeof(watched)
                + sys.getsizeof(stability)
            )
            if used_mem > mem_lim:
                raise MemoryError(f"solver used too much memory: {used_mem} > {mem_lim}")

        ok, qhead = _bcp_watched(
            M,
            M_set,
            qhead,
            watchlist,
            watched,
            use_blocking=use_blocking,
            use_stable=use_stable,
            stability=stability,
            decision_count=decision_count,
        )
        if not ok: # backtrack if there's a conflict
            print("Conflict: ", M, "\n")
            M, can_backtrack = backtrack(
                M,
                decision_points,
                M_set=M_set if use_stable else None,
                stability=stability,
                decision_count=decision_count,
            )
            if not can_backtrack: # fail if can't backtrack anymore
                print("\nFailed\n")
                solution = SolverResult(UNSAT)
                return solution
            else:
                if not use_stable:
                    M_set = set(M)
                qhead = len(M) - 1
                continue

        all_assigned = True
        for literal in clauses.literals:
            if literal not in M_set and -literal not in M_set:
                all_assigned = False
                break

        if all_assigned: #this would mean it's satisfied
            solution = SolverResult(result, assignment=M)
            trunc_print("Solution", solution.assignment)
            return solution

        M, changed = pure(clauses, M)
        if changed:
            M_set = set(M)
            if use_stable:
                _limp(M[-1], stability, decision_count)
            continue

        M, changed = decide(clauses, M, decision_points)
        if changed:
            decision_count += 1
            M_set = set(M)
            if use_stable:
                _limp(M[-1], stability, decision_count)
            continue



def watched_literals_solve(test_case, mem_lim=None):
    return _watched_solver_core(test_case, mem_lim=mem_lim, use_blocking=False, use_stable=False)



def wl_blocking_solve(test_case, mem_lim=None):
    return _watched_solver_core(test_case, mem_lim=mem_lim, use_blocking=True, use_stable=False)



def wl_stable_solve(test_case, mem_lim=None):
    return _watched_solver_core(test_case, mem_lim=mem_lim, use_blocking=False, use_stable=True)



def wl_blocking_stable_solve(test_case, mem_lim=None):
    return _watched_solver_core(test_case, mem_lim=mem_lim, use_blocking=True, use_stable=True)
