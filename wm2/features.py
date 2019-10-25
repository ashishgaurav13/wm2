from functools import total_ordering


@total_ordering
class Feature:
    # holds a certain feature

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.dtype = type(value)
        assert(type(value) in [float, int, bool])
   
    def __repr__(self):
        return "%s:%g" % (self.name, self.value)
    
    def __eq__(self, v):
        if type(v) in [float, int, bool]:
            return self.value == v
        elif type(v) == Feature:
            return self.value == v.value
        elif type(v) == str:
            return str(self) == v
        else:
            return NotImplementedError()
    
    def __lt__(self, v):
        if type(v) in [float, int, bool]:
            return self.value < v
        elif type(v) == Feature:
            return self.value < v.value
        else:
            return NotImplementedError()

class Features:
    # holds a bunch of features, almost like utilities.ltl.Bits
    # but the features can be any value

    def __init__(self, f):
        assert(type(f) == dict)
        self.o = {key: Feature(key, value) for key, value in f.items()}
    
    def __getitem__(self, index):
        return self.o[index].value
    
    def __setitem__(self, index, value):
        if index not in self.o:
            self.o[index] = Feature(index, value)
        else:
            self.o[index].value = value

    def __repr__(self):
        return ", ".join([str(item) for item in self.o.values()])