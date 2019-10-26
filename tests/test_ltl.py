from utilities.ltl import Bits, AP, SeqAP, LTLProperty, \
    Parser, Scanner, LTLProperties

# TODO: rename propositions in this file => predicates

# T1 <= t <= T2
def construct_trace(propositions, T1, T2):
    assert(type(T1) == int)
    assert(type(T2) == int)
    assert(type(propositions) == dict)
    assert(T1 <= T2)
    ap = AP(propositions)
    ap.t = T1
    ap.update_data()
    trace = []
    trace_list = []
    for t in range(T1, T2+1):
        trace += [int(ap)]
        trace_list += [list(ap)]
        ap.step()
    return trace, trace_list

def construct_parser_and_bits(propositions, scan_str):
    assert(type(propositions) == list)
    p = Parser()
    p.APdict = {key: i for i, key in enumerate(propositions)}
    p.SetProperty(Scanner(scan_str))
    return p, Bits()

def check_ltl_property(propositions, property_str, maxT, 
    expected_statuses, reward = -1, debug = False, mode = 'violation'):

    assert(mode in ['violation', 'satisfaction'])

    if debug:
        print("property to check: %s (%s)" % (property_str, mode))

    trace, trace_list = construct_trace(propositions, 0, maxT)
    ltlp = LTLProperty(property_str, reward, propositions, mode = mode)
    ltlp.reset()
    
    for T in range(maxT+1):
        status, info = ltlp(trace[T])
        if debug:
            print("T%d: %s, %s, ap: %s (expected %s)" % (T, status, info, 
                trace_list[T], expected_statuses[T]))
        else:
            assert(status == expected_statuses[T])
    
    if debug: print('')

def check_ltl_properties(propositions, properties_rewards_modes, maxT,
    expected_rewards, expected_num_violations, expected_num_satisfactions,
    debug = False, sequential = False, objs = {}):

    if debug:
        for item in properties_rewards_modes:
            p, reward, mode = item
            print("property to check: %s (%s)" % (p, mode))

    ltl = LTLProperties(propositions, properties_rewards_modes,
        sequential, objs)
    
    total_reward, info, t = ltl.reset()

    if debug:
        print("T%d: %.2f, %s, ap: %s" % (t, total_reward, info, list(ltl.ap)))
    else:
        assert(total_reward == expected_rewards[t])
        if 'violations' in info:
            assert(len(info['violations']) == expected_num_violations[t])
        else:
            assert(0 == expected_num_violations[t])
        if 'satisfactions' in info:
            assert(len(info['satisfactions']) == expected_num_satisfactions[t])
        else:
            assert(0 == expected_num_satisfactions[t])

    for T in range(1, maxT+1):
        total_reward, info, t = ltl.step()
        if debug:
            print("T%d: %.2f, %s, ap: %s" % (t, total_reward, info, list(ltl.ap))) 
        else:
            assert(total_reward == expected_rewards[t])
        if 'violations' in info:
            assert(len(info['violations']) == expected_num_violations[t])
        else:
            assert(0 == expected_num_violations[t])
        if 'satisfactions' in info:
            assert(len(info['satisfactions']) == expected_num_satisfactions[t])
        else:
            assert(0 == expected_num_satisfactions[t])
    
    if debug: print('')

def test_bits():
    bits = Bits()
    assert(bits[0] == False)
    assert(bits[3] == False)
    bits[3] = True
    assert(bits[3] == True)

def test_ap():
    propositions = {
        "A": lambda t: t % 2 == 0,
        "B": lambda t: t == 3,
    }
    ap = AP(propositions)
    expected_values = {
        0: [True, False],
        1: [False, False],
        2: [True, False],
        3: [False, True],
    }
    for t, v in expected_values.items():
        assert(ap.t == t)
        assert(ap[0] == v[0])
        assert(ap[1] == v[1])
        assert(list(ap) == v)
        ap.step()

def test_seq_ap():
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
    expected_values = {
        0: [True, False, True],
        1: [False, True, True],
        2: [True, False, True],
        3: [False, True, True],
    }
    for t, v in expected_values.items():
        assert(ap.t == t)
        assert(ap[0] == v[0])
        assert(ap[1] == v[1])
        assert(ap[2] == v[2])
        assert(list(ap) == v)
        ap.step()

def test_construct_trace():
    propositions = {
        "A": lambda t: t == 1,
        "B": lambda t: t == 2,
    }
    trace, trace_list = construct_trace(propositions, 0, 2)
    assert(trace == [
        0b00, 0b01, 0b10
    ])
    assert(trace_list == [
        [0, 0], [1, 0], [0, 1]
    ])

def test_parser_single_factor():
    p, ap = construct_parser_and_bits(["A"], "A")
    ap[0] = 1
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    p.ResetProperty()
    ap[0] = 0
    assert(p.CheckIncremental(int(ap)) == Parser.FALSE)

def test_parser_conjunction():
    p, ap = construct_parser_and_bits(["A", "B"], "A and B")
    p.ResetProperty()
    ap[0], ap[1] = 0, 0
    assert(p.CheckIncremental(int(ap)) == Parser.FALSE)
    p.ResetProperty()
    ap[0], ap[1] = 0, 1
    assert(p.CheckIncremental(int(ap)) == Parser.FALSE)
    p.ResetProperty()
    ap[0], ap[1] = 1, 0
    assert(p.CheckIncremental(int(ap)) == Parser.FALSE)
    p.ResetProperty()
    ap[0], ap[1] = 1, 1
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)    

def test_parser_disjunction():
    p, ap = construct_parser_and_bits(["A", "B"], "A or B")
    p.ResetProperty()
    ap[0], ap[1] = 0, 0
    assert(p.CheckIncremental(int(ap)) == Parser.FALSE)
    p.ResetProperty()
    ap[0], ap[1] = 0, 1
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    p.ResetProperty()
    ap[0], ap[1] = 1, 0
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    p.ResetProperty()
    ap[0], ap[1] = 1, 1
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)    

def test_parser_until():
    p, ap = construct_parser_and_bits(["A", "B"], "A U B")
    p.ResetProperty()
    ap[0], ap[1] = 1, 0
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)
    ap[0], ap[1] = 0, 1
    assert(p.CheckIncremental(int(ap)) == Parser.TRUE)

# TODO: add numbering for tests, eg. test_ltlp_implication{1,2,3...}
#
# Property: a => b (violation)
# 0 <= t <= 7
#
# a: t >= 3, b: t >= 5
# Expected: [0,0,0,1,1,0,0,0]
def test_ltlp_violation_implication():
    propositions = {
        "a": lambda t: t >= 3,
        "b": lambda t: t >= 5,
    }
    property_str = "a => b"
    maxT = 7
    expected_statuses = [0,0,0,1,1,0,0,0]
    check_ltl_property(propositions, property_str, maxT,
        expected_statuses, debug = False)

# Property: a => (b U c) (violation)
# 0 <= t <= 7
#
# a: t >= 3, b: 0 <= t <= 6, c: t >= 7
# Expected: [0,0,0,0,0,0,0,0]
# b must always hold from t=0 to some t, followed by c
# although this is only checked at t >= 3 (a)
#
# a: t >= 3, b: 1 <= t <= 7, c: t >= 0
# Expected: [0,0,0,1,1,1,1,1]
# b holds after c holds, but this is only checked
# after t >= 3 (a)
def test_ltlp_violation_until():
    property_str = "a => (b U c)"
    maxT = 7

    propositions = {
        "a": lambda t: t >= 3,
        "b": lambda t: 0 <= t <= 6,
        "c": lambda t: t >= 7
    }
    expected_statuses = [0,0,0,0,0,0,0,0]
    check_ltl_property(propositions, property_str, maxT,
        expected_statuses, debug = False)

    propositions = {
        "a": lambda t: t >= 3,
        "b": lambda t: 1 <= t <= 7,
        "c": lambda t: t >= 0
    }
    expected_statuses = [0,0,0,1,1,1,1,1]
    check_ltl_property(propositions, property_str, maxT,
        expected_statuses, debug = False)

# Property: a => (b U c) (satisfaction)
# 0 <= t <= 7
#
# a: t >= 3, b: 1 <= t <= 6, c: t >= 7
# Expected: [0,0,0,1,1,1,1,1]
# b must be true throughout before c, although
# this is checked only after t >= 3 (a)
# t < 3, everything is satisfied
def test_ltlp_satisfaction_until():
    property_str = "a => (b U c)"
    maxT = 7

    propositions = {
        "a": lambda t: t >= 3,
        "b": lambda t: 0 <= t <= 6,
        "c": lambda t: t >= 7,
    }
    expected_statuses = [1,1,1,1,1,1,1,1]
    check_ltl_property(propositions, property_str, maxT,
        expected_statuses, debug = False, mode = 'satisfaction')

# Property1: a => b, -1 (V)
# Property2: b or c, -1 (V)
# Property3: a U b, 1 (S)
# Property4: d U b, 1 (S)
# 0 <= t <= 5
#
# a: t >= 2, b: t >= 4, c: t == 3
# Expected total rewards: [-1,-1,-1,0,1,1]
def test_ltl_simple():
    properties = [
        ["a => b", -1, "violation"],
        ["b or c", -1, "violation"],
        ["a U b", 1, "satisfaction"],
        ["d U b", 1, "satisfaction"],
    ]
    maxT = 5
    propositions = {
        "a": lambda t: t >= 2,
        "b": lambda t: t >= 4,
        "c": lambda t: t == 3,
        "d": lambda t: 0 <= t <= 3,
    }
    expected_rewards = [0-1+0+1,0-1+0+1,-1-1+0+1,-1+0+0+1,0+0+0+1,0+0+0+1]
    expected_num_violations = [1,1,2,1,0,0]
    expected_num_satisfactions = [1,1,1,1,1,1]

    check_ltl_properties(propositions, properties, maxT,
        expected_rewards, expected_num_violations, expected_num_satisfactions,
        debug = False)

# Property1: a U b, 1 (S)
# Property2: b => c, -1 (V)
# 0 <= t <= 5
#
# class Z: pass
# z = Z()
# z.zz = 3
# objs = {'z': z}
# a: t <= p['z'].zz, b: not p['a'], c: t == 5
# Expected total rewards: [1,]
def test_ltl_sequential_simple():
    class Z: pass
    z = Z()
    z.zz = 3
    objs = {
        'z': z,
    }
    properties = [
        ["a U b", 1, "satisfaction"],
        ["b => c", -1, "violation"],
    ]
    maxT = 5
    propositions = {
        "a": lambda p, t: t <= p['z'].zz,
        "b": lambda p, t: not p['a'],
        "c": lambda p, t: t == 5,
    }
    expected_rewards = [1+0,1+0,1+0,1+0,1-1,1+0]
    expected_num_violations = [0,0,0,0,1,0]
    expected_num_satisfactions = [1,1,1,1,1,1]

    check_ltl_properties(propositions, properties, maxT,
        expected_rewards, expected_num_violations, expected_num_satisfactions,
        debug = False, sequential = True, objs = objs)