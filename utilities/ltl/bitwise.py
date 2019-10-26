import utilities

class Bits:
    """A bit-control class that allows us bit-wise manipulation as shown in the
    example::

    bits = Bits()
    bits[0] = False
    bits[2] = bits[0]
    """

    def __init__(self, value=0):
        self._d = value

    def __getitem__(self, index):
        return (self._d >> index) & 1

    def __setitem__(self, index, value):
        value = (value & 1) << index
        mask = 1 << index
        self._d = (self._d & ~mask) | value

    def __getslice__(self, start, end):
        mask = 2**(end - start) - 1
        return (self._d >> start) & mask

    def __setslice__(self, start, end, value):
        mask = 2**(end - start) - 1
        value = (value & mask) << start
        mask = mask << start
        self._d = (self._d & ~mask) | value
        return (self._d >> start) & mask

    def __int__(self):
        return self._d


class AP:
    """Atomic Propositions. Pass in propositions as
    lambda functions dependent on the timestep t.
    Ensure these lambdas return boolean.

    propositions = {
        "A": lambda t: t % 2 == 0,
        "B": lambda t: t == 3,
    }
    ap = AP(propositions)
    ap.t => 0
    ap[0,1] => True, False
    ap.step()
    ap.t => 1
    ap[0,1] => False, False
    ...
    """

    def __init__(self, propositions = {}):
        assert(type(propositions) == dict)
        self._d = Bits()
        self._p = propositions
        self._n = len(self._p)
        self.t = 0
        self.update_data() # initial values

    def update_data(self):
        for i, func in enumerate(self._p.values()):
            self._d[i] = func(self.t)

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
    
    def __int__(self):
        return int(self._d)

class SeqAP:
    """Sequential Atomic Propositions. Pass in propositions as
    lambda functions dependent on previous evaluations, timestep t.
    Ensure these lambdas return boolean.

    Additionally, you can also pass extra objects and use them through p.

    class Z: pass
    z = Z()
    z.zz = 20
    objs = {
        "z": z,
    }
    seq_propositions = {
        "A": lambda p, t: t % 2 == 0,
        "B": lambda p, t: not p['A'],
        "C": lambda p, t: p['z'].zz == 20
    }
    ap = SeqAP(seq_propositions, objs)
    ap.t => 0
    ap[0,1,2] => True, False, True
    ap.step()
    ap.t => 1
    ap[0,1,2] => False, True, True
    ap.step()
    ap.t => 2
    ap[0,1,2] => True, False, True
    ...
    """

    def __init__(self, propositions = {}, objs = {}):
        assert(type(propositions) == dict)
        assert(type(objs) == dict)
        self._d = Bits()
        self._p = propositions
        self._n = len(self._p)
        self._k = list(self._p.keys())
        self.objs = objs
        self.t = 0
        self.update_data() # initial values

    def update_data(self):
        evaluated = utilities.combine_dicts({}, self.objs)
        for i, func in enumerate(self._p.values()):
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
    
    def __int__(self):
        return int(self._d)