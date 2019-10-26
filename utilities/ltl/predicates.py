import utilities
from inspect import isfunction

class SeqPredicates:
    """Sequential predicates. Pass in predicates as
    lambda functions dependent on previous evaluations, timestep t.
    Less efficient than SeqAP (no bitwise storage).

    Additionally, you can also pass extra objects and use them through p.

    class Z: pass
    z = Z()
    z.zz = 20
    objs = {
        "z": z,
    }
    seq_predicates = {
        "a": lambda p, t: p['z'].zz * 2 + t,
        "b": lambda p, t: p['a'] * 2,
        "c": lambda p, t: p['b'] * 2,
    }
    p = SeqPredicates(seq_predicates, objs)
    p.t => 0
    p[0,1,2] => 20, 40, 80
    ap.step()
    ap.t => 1
    ap[0,1,2] => 21, 42, 84
    ...
    """

    def __init__(self, predicates = {}, objs = {}):
        assert(type(predicates) == dict)
        assert(type(objs) == dict)
        self._d = {}
        self._p = predicates
        self._n = len(self._p)
        self._k = list(self._p.keys())
        self.objs = objs
        self.t = 0
        self.update_data() # initial values

    def update_data(self):
        evaluated = utilities.combine_dicts({}, self.objs)
        for i, func in enumerate(self._p.values()):
            if not isfunction(func):
                evaluated[self._k[i]] = func
            else:
                evaluated[self._k[i]] = func(evaluated, self.t)
            self._d[i] = evaluated[self._k[i]]          

    def reset(self):
        self.t = 0

    def step(self):
        self.t += 1
        self.update_data() # initial values
    
    def __getitem__(self, index):
        return self._d[index]
    
    def __iter__(self):
        for i in range(self._n):
            yield self._d[i]

    def get_dict(self):
        ret = {}
        for i, k in enumerate(self._k):
            ret[k] = self._d[i]
        return ret