import numpy as np

def combine_dicts(*args):
    ret = {}
    for d in args:
        for key, value in d.items():
            assert(key not in ret.keys())
            ret[key] = value
    return ret

def combine_infos(*args):
    ret = {}
    for d in args:
        for key, value in d.items():
            if key not in ret.keys():
                ret[key] = value
            else:
                ret[key] += value
    return ret

def dict_to_numpy(x):
    if type(x) != dict: return x
    if x == {}: return np.array([])
    return np.hstack([dict_to_numpy(val) for val in x.values()]).flatten()