def combine_dicts(*args):
    ret = {}
    for d in args:
        for key, value in d.items():
            assert(key not in ret.keys())
            ret[key] = value
    return ret