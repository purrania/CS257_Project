A guide to running results:
- For generating the data files, which are created from the SAT Competition dataset, either add in the dimacs_tests.json file at our link, or by running the creation of a new selection of random clauses from a CNF (first make sure a .CNF file of your choosing is present in the same directory as test_case_maker.py) and then run test_case_maker.py. This will create a dimacs_tests.json file in the same directory, which contains the randomly selcted set of test clauses. 
- For testing the DPLL solver,  python3 test_optimizations.py --include-dpll
- For testing the watched literals solvers, run python3 guaranteed_wl_speedup_benchmark.py
- For examining the clauses, run inspect_dimacs.py

The link to our data files, if you want to replicate our results exactly, or if don't want to have to generate test cases of your own, is at: https://drive.google.com/drive/u/0/folders/1Pc-V4d-sVpMeZtfMkgjUTzhV5OtKN6Q-
