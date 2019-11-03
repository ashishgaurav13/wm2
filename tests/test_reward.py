from tools.design import RewardChecker, RewardStructure
from tools.misc.ltl import SeqAP, SeqPredicates

def test_definitions_propositions_together():
    class Z: pass
    z = Z()
    z.zz = 20
    objs = {'z': z}
    definitions = {
        "a": lambda p, t: p['z'].zz,
        "b": lambda p, t: p['a']+t,
    }
    d = SeqPredicates(definitions, objs)
    propositions = {
        "c": lambda p, t: p['z'].zz == 20,
        "d": lambda p, t: p['b'] == 21
    }
    p = SeqAP(propositions, objs, d)
    assert(d.t == p.t == 0)
    assert(d.get_dict() == {"a": 20, "b": 20})
    assert(p.get_dict() == {"c": True, "d": False})
    d.step()
    p.step()
    assert(d.t == p.t == 1)
    assert(d.get_dict() == {"a": 20, "b": 21})
    assert(p.get_dict() == {"c": True, "d": True})

def test_reward_checker_simple():
    class Z: pass
    z = Z()
    z.zz = 20
    objs = {'z': z}
    definitions = {
        "a": lambda p, t: p['z'].zz,
        "b": lambda p, t: p['a']+t,
    }
    d = SeqPredicates(definitions, objs)
    propositions = {
        "c": lambda p, t: p['z'].zz == 20,
        "d": lambda p, t: p['b'] == 21
    }
    p = SeqAP(propositions, objs, d)
    properties = [
        ["c and d", lambda p, t: p['z'].zz+t, "satisfaction"],
    ]
    rc = RewardChecker(d, p, properties, objs)
    assert(rc.reset() == (0, {}, 0))
    assert(rc.step() == (21, {'satisfactions': ['c and d']}, 1))

# Definitions:
#   a : 20
#
# Propositions:
#   b : (p['a'] == 20) and 0 <= t <= 3
#   c : t >= 4
#
# Reward:
#   true, 2**p['b'] (S)
#
# Termination:
#   c, -1 (S)
#
# Success:
#   false, 1 (S)
#
def test_reward_structure_simple():
    objs = {}
    d = {
        "a": 20,
    }
    p = {
        "b": lambda p, t: (p['a'] == 20) and 0 <= t <= 3,
        "c": lambda p, t: t >= 4,
    }
    r = [
        ["true", lambda p, t: 2**p['b'], 'satisfaction'],
    ]
    t = [
        ["c", -1, 'satisfaction'],
    ]
    s = [
        ["false", 1, 'satisfaction'],
    ]
    rs = RewardStructure(d, p, r, t, s, objs)
    assert(rs.reset() == (2, {'satisfactions': ['true'], 'mode': 'reward'}, 0))
    assert(rs.step() == (2, {'satisfactions': ['true'], 'mode': 'reward'}, 1))
    assert(rs.step() == (2, {'satisfactions': ['true'], 'mode': 'reward'}, 2))
    assert(rs.step() == (2, {'satisfactions': ['true'], 'mode': 'reward'}, 3))
    assert(rs.step() == (-1, {'satisfactions': ['c'], 'mode': 'termination'}, 4))
    assert(rs.step() == (-1, {'satisfactions': ['c'], 'mode': 'termination'}, 5))