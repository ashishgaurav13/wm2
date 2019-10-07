import os, sys

def get_root_dir():
    return os.path.dirname(sys.modules['__main__'].__file__)

def get_file_from_root(f):
    return os.path.join(get_root_dir(), f)