
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
