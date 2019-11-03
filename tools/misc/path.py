import os, sys

def get_root_dir():
    # Keep going up until we find a requirements.txt
    ret = os.path.dirname(os.path.realpath(sys.modules['__main__'].__file__))
    FILENAME = 'requirements.txt'
    get_files = lambda x: [f for f in os.listdir(x) if os.path.isfile(os.path.join(x, f))]
    tries, total_tries = 0, 3
    # Not more than 3 levels deep
    while True:
        if FILENAME in get_files(ret):
            return ret
        elif tries <= total_tries:
            ret = os.path.realpath(os.path.join(ret, '..'))
            tries += 1
        else:
            print("Something went wrong in utilities.get_root_dir")
            exit(0)

def get_file_from_root(f):
    return os.path.join(get_root_dir(), f)