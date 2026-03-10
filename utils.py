VERBOSE = False
def update_msg(M, changed, name):
    if VERBOSE: 
        # ideally, we set this condition on calls to update_msg, but 
        # this is hard to enforce/guarantee a call is accidentally added
        # without the verbose condition 
        print(f"try {name}, new M={M}, changed = {changed}")
def trunc_print(name, some_list, trunc=50):
    if VERBOSE:
        if len(some_list) < 100:
            print(f"\n{name} is: ", some_list, "\n")
        else:
            print(f"\n{name} is: [",", ".join([str(x) for x in some_list[:trunc]]),"...]\n")

