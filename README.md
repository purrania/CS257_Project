A guide to running results:
- For generating the data files, which are created from the SAT Competition dataset, either add in the dimacs_tests.json file at our link, or by running the creation of a new selection of random clauses from a CNF (first make sure a .CNF file of your choosing is present in the same directory as test_case_maker.py) and then run test_case_maker.py. This will create a dimacs_tests.json file in the same directory, which contains the randomly selcted set of test clauses. 
- For testing the DPLL solver,  python3 test_optimizations.py --include-dpll. This will generate the table and graph showing median runtimes for the synthetic dataset. 
- For testing the watched literals solvers, python3 guaranteed_wl_speedup_benchmark.py --sizes 5,10,20,40 --repeats 3. This will generate the table and graph showing median runtimes for the synthetic dataset. 
- For examining the clauses, run inspect_dimacs.py. This will generate the clause length histogram, the average clause length, and the max clause length for our subset of the SAT competition dataset.

The link to our data files, if you want to replicate our results exactly, or if don't want to have to generate test cases of your own, is at: https://drive.google.com/drive/u/0/folders/1Pc-V4d-sVpMeZtfMkgjUTzhV5OtKN6Q-
