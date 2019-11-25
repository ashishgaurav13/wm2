from tools.misc.ltl import SeqAP, SeqPredicates, LTLProperty, LTLProperties
from tools.misc import combine_dicts, combine_infos
from inspect import isfunction
import numpy as np

class RewardChecker(LTLProperties):
    """
    Slightly faster version of LTLProperties, suitable for reward
    specification.
    
    (1) definitions d are sequential predicates
    (2) propositions p are sequential propositions, can use d
    (3) properties are defined in terms of propositions, cannot use d;
        properties are passed int(p) as state, nothing from d
    (4) if status == True, 
    """

    def __init__(self, d, p, properties, objs = {}, combine_rewards = lambda a, b: a + b):

        assert(type(d) == SeqPredicates)
        assert(type(p) == SeqAP)
        assert(isfunction(combine_rewards))
        # Create AP
        self._d = d
        self._p = p
        self._r = {}
        self.objs = objs
        self.combine_rewards = combine_rewards
        # Create properties
        self.properties = []
        for p in properties:
            property_str, reward, mode = p
            if not isfunction(reward):
                self._r[property_str] = lambda p, t, r=reward: r # constant
            else:
                self._r[property_str] = reward # lambda function
            self.properties += [
                LTLProperty(property_str, 1, self._p._p, mode)
            ] # if 1, then evaluate the reward function
            self.properties[-1].reset()

    def check(self):
        assert(self._d.t == self._p.t)
        t = self._d.t
        total_reward = -np.inf
        violations = []
        satisfactions = []
        for p in self.properties:
            status, info = p(int(self._p)) # list(self._p) to see the APs
            if status:
                evaluated = combine_dicts(self.objs, self._d.get_dict())
                evaluated = combine_dicts(evaluated, self._p.get_dict())
                new_reward = self._r[p.x](evaluated, t)
                if total_reward == -np.inf:
                    total_reward = new_reward
                else:
                    total_reward = self.combine_rewards(total_reward, new_reward)
                if "violation" in info: violations += [info["violation"]]
                if "satisfaction" in info: satisfactions += [info["satisfaction"]]
        info = {}
        if len(violations) > 0: info["violations"] = violations
        if len(satisfactions) > 0: info["satisfactions"] = satisfactions
        if total_reward == -np.inf:
            total_reward = 0
        return total_reward, info, t

    def reset(self):
        for p in self.properties:
            p.reset()
        return self.check()
    
    def step(self):
        self._d.step()
        self._p.step()
        return self.check()


class RewardStructure:

    # definitions, properties, rewards, terminations, successes
    # See craft.IntersectionOnlyEgoEnv for an example
    def __init__(self, d, p, r, t, s, objs = {}, combine_rewards = lambda a, b: a + b):
        self._d = SeqPredicates(d, objs = objs)
        self._p = SeqAP(p, objs = objs, pre = self._d)
        self.r = RewardChecker(self._d, self._p, r, objs = objs,
            combine_rewards = combine_rewards)
        self.t = RewardChecker(self._d, self._p, t, objs = objs,
            combine_rewards = combine_rewards)
        self.s = RewardChecker(self._d, self._p, s, objs = objs,
            combine_rewards = combine_rewards)
    
    # Combine r, t, s values into a single thing
    def combine_rts(self, r, t, s):
        # check success
        if len(s[1]) != 0:
            s[1]['mode'] = 'success'
            return s
        # check failure
        if len(t[1]) != 0:
            t[1]['mode'] = 'termination'
            return t
        # normal reward
        r[1]['mode'] = 'reward'
        return r

    def reset(self):
        self._d.reset()
        self._p.reset()
        rr = self.r.reset()
        tt = self.t.reset()
        ss = self.s.reset()
        return self.combine_rts(rr, tt, ss)

    def step(self):
        self._d.step()
        self._p.step()
        rr = self.r.check()
        tt = self.t.check()
        ss = self.s.check()
        return self.combine_rts(rr, tt, ss)
