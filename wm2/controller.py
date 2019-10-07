import utilities

# Every controller has a precondition_fn and a rule_fn to produce control inputs
class Controller:

    def __init__(self, precondition_fn, rule_fn, name):
        assert(precondition_fn)
        assert(rule_fn)
        self.precondition_fn = precondition_fn
        self.rule_fn = rule_fn
        self.name = name

    # Checks if precondition is met
    # v is a dict of predicates
    def active(self, p):
        return self.precondition_fn(p)
    
    # v is a dict of predicates
    # m is a dict of multipliers
    def control(self, p, m):
        assert(self.active(p))
        return self.rule_fn(p, m)

# Always active
class DefaultController:

    def __init__(self, rule_fn, name):
        assert(rule_fn)
        self.rule_fn = rule_fn
        self.name = name

    def control(self, p, m):
        return self.rule_fn(p, m)


# Combination of controllers
class ComplexController:

    def __init__(self, predicates, multipliers, controllers):
        self.predicates = predicates
        self.multipliers = multipliers
        assert(type(controllers) == list)
        assert(type(controllers[-1]) == DefaultController)
        names_of_controllers = []
        self.default_controller = controllers[-1]
        names_of_controllers += [self.default_controller.name]
        self.controllers = controllers[:-1]
        for controller in self.controllers:
            assert(controller.name not in names_of_controllers)
            names_of_controllers += [controller.name]

    # Sequentially evaluate the dict x.
    # x has key, value pairs such that the key is the name
    # of the attribute and value is either of:
    # (i) a lambda function that takes in previously evaluated predicates,
    # (ii) a list of 2 lambda functions, first being condition and second
    # being the function to set key's value to, if condition is true
    def sequential_evaluate(self, x, ex = {}):
        ret = {}
        total = utilities.combine_dicts(ex, ret)
        for key, fn in x.items():
            assert(key not in total.keys())
            if type(fn) == list:
                assert(len(fn) == 2)
                if fn[0](total):
                    new_value = fn[1](total)
                    ret[key] = new_value
                    total[key] = new_value
            else:
                new_value = fn(total)
                ret[key] = new_value
                total[key] = new_value
        return ret

    def control(self, debug = False):
        ep = self.sequential_evaluate(self.predicates)
        em = self.sequential_evaluate(self.multipliers, ep)
        for controller in self.controllers:
            if controller.active(ep):
                if debug: print(controller.name)
                return controller.control(ep, em)
        if debug: print(self.default_controller.name)
        return self.default_controller.control(ep, em)