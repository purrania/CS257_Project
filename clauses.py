class Clause:
    def __init__(self, literals):
        self.literals = literals 

class Clauses:
    def __init__(self, clause_list):
        self.clause_list = clause_list
        self.literals = set([literal for clause in self.clause_list for literal in clause.literals])
        self.unique_literals = set([abs(x) for x in self.literals])