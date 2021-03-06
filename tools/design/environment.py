import tools.pyglet as graphics
from tools.misc.ltl import Bits, SeqAP
import tools.misc as utilities
from .reward import RewardStructure
import numpy as np
import time, datetime
import gym
from inspect import isfunction
import json

class Environment(gym.Env):
    """
    Gym based environment that needs a canvas.
    Canvas cannot have more than 32 agents (32-bit int).
    zero_pad zero_pads by a certain number of features.

    Eg.

    canvas = ...
    default_policy = lambda c: c.aggressive_driving()
    env = Environment(canvas, default_policy, zero_pad = 3)

    Freeze/unfreeze agents which you want to be updated. If
    frozen, these agents won't move, i.e. their policies
    will not be called. If agent.ego is True, then 
    default_policy doesn't apply to it.

    env.agents_unfrozen() => all by default
    env.agent_freeze(...)
    env.agent_unfreeze(...)
    env.agent_freeze_all()
    env.agent_unfreeze_all()

    Debugging functionalities can be set to True. By default,
    there is no debugging. (TODO: list of debug functionalities)

    env.debug['intersection_enter'] = True

    ...
    env.reset() => return env.state()
    env.state() => get numpy representation of state (mostly trimmed)
    env.f[a]['b'] => get agent (id:a)'s feature 'b'
    ...
    next_obs, reward, done, info = env.step()
    ...
    env.close()
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, canvas, default_policy = None, zero_pad = 0,
        discrete = False):

        assert(type(canvas) == graphics.Canvas)
        self.canvas = canvas
        self.rendering = False
        assert(hasattr(self.canvas, 'agents'))
        assert(type(self.canvas.agents) == list)
        self.agents = self.canvas.agents        
        num_egos = sum([agent.ego for agent in self.agents])
        self.ego_id = None
        for aid, agent in enumerate(self.agents):
            if agent.ego:
                self.ego_id = aid
        assert(num_egos <= 1)
        self.num_agents = len(self.agents)
        self.reward_specified = False
        self.state_specified = False
        self.init_time = time.time()

        # Which agents to actually draw (or update)
        self.agents_drawn = Bits()
        for ai in range(self.num_agents):
            self.agents_drawn[ai] = True

        # Feature-sets for all agents
        self.f = [agent.f for agent in self.agents]

        # Policies for non ego
        self.policies = [default_policy for agent in self.agents]
        if self.ego_id != None: self.policies[self.ego_id] = None

        # Debugging
        self.debug_fns = {
            'intersection_enter': self.debug_intersection_enter,
            'state_inspect': None,
            'kill_after_state_inspect': None,
            'show_elapsed': None,
            'show_steps': None,
            'show_reasons': None,
            'record_reward_trajectory': None,
            'action_buckets': None,
        }
        self.debug = {k: False for k in self.debug_fns.keys()}
        self.debug_variables = {}
        self.debug_variables['buckets'] = set([])

        # Call make_ready to set ready to true
        self.ready = False

        # Zero pad features
        self.zero_pad = zero_pad

        # Discrete actions
        self.discrete = discrete

    # Create obs space and action space after everything is set
    def make_ready(self):
        self.ready = True

        # Observation space (TODO: can be better defined)
        s = self.state()
        self.observation_space = gym.spaces.Box(
            low = -np.inf,
            high = np.inf,
            shape = s.shape,
        )

        # Action space
        self.action_space = None
        if self.ego_id != None:
            ego = self.agents[self.ego_id]
            amax = ego.MAX_ACCELERATION
            psidotmax = ego.MAX_STEERING_ANGLE_RATE
            if self.discrete:
                self.action_space = gym.spaces.Discrete(13)
                # self.action_mapping = {
                #     0: [-amax, 0], # full brake
                #     1: [0, 0], # continue
                #     2: [amax, 0], # full accelerate
                #     3: [amax, psidotmax],
                #     4: [amax, -psidotmax],
                #     5: [amax/2., 0],
                #     6: [amax/2, psidotmax],
                #     7: [amax/2, -psidotmax],
                # }
                self.action_mapping = {
                    0: [amax, psidotmax],
                    1: [amax, 0.75 * psidotmax],
                    2: [amax, 0.5 * psidotmax],
                    3: [amax, 0.25 * psidotmax],
                    4: [amax, 0],
                    5: [amax, -0.25 * psidotmax],
                    6: [amax, -0.5 * psidotmax],
                    7: [amax, -0.75 * psidotmax],
                    8: [amax, -psidotmax],
                    9: [amax/2, 0],
                    10: [0, 0],
                    11: [-amax/2, 0],
                    12: [-amax, 0]
                }
            else:
                self.action_space = gym.spaces.Box(
                    low = np.array([-amax, -psidotmax]),
                    high = np.array([amax, psidotmax]),
                )

    def agents_unfrozen(self):
        return [ai for ai in range(self.num_agents) \
            if self.agents_drawn[ai] == True]

    def agent_unfreeze(self, i):
        self.agents_drawn[i] = True

    def agent_unfreeze_all(self):
        for ai in range(self.num_agents):
            self.agents_drawn[ai] = True

    def agent_freeze(self, i):
        self.agents_drawn[i] = False

    def agent_freeze_all(self):
        for ai in range(self.num_agents):
            self.agents_drawn[ai] = False

    def specify_state(self, ego_fn, other_fn):
        assert(not self.state_specified)
        assert(isfunction(ego_fn))
        assert(isfunction(other_fn))
        self.state_specified = True
        self.ego_fn = ego_fn
        self.other_fn = other_fn
        # self.debug['state_inspect'] = True
        # self.debug['kill_after_state_inspect'] = True

    def state(self):
        assert(hasattr(self, 'f'))

        ret = None
        if self.state_specified:
            ret = {}
            for aid, agent in enumerate(self.agents):
                if aid == self.ego_id:
                    ret[aid] = self.ego_fn(agent, self.reward_structure)
                else:
                    ret[aid] = self.other_fn(agent, self.reward_structure)
            
            if self.zero_pad > 0:
                ret["null"] = {("null_feature_%d" % ki): 0.0 for ki in range(self.zero_pad)}

            if self.debug['state_inspect']: 
                print('Dict:')
                print(json.dumps(ret, indent = 2))
                print('Flattened Numpy:')
                print(utilities.dict_to_numpy(ret))
                print('')
                if self.debug['kill_after_state_inspect']:
                    print('Killing ...')
                    exit(0)
            ret = utilities.dict_to_numpy(ret)

        return ret

    def new_debug_variable(self, key, value):
        if key not in self.debug_variables:
            self.debug_variables[key] = value

    def debug_intersection_enter(self):
        self.new_debug_variable('order', [])
        ii = self.canvas.intersections[0]
        inside = []
        for aid, agent in enumerate(self.agents):
            if ii.x1 <= agent.f['x'] <= ii.x2 and \
                ii.y1 <= agent.f['y'] <= ii.y2:
                if aid not in self.debug_variables['order']:
                    inside += [aid]
                    self.debug_variables['order'] += [aid]
        if len(inside) > 0:
            print("Inside the intersection: %s" % inside)
    
    def is_agent_in_bounds(self, agent):
        return self.canvas.is_agent_in_bounds(agent)

    def reset(self):
        assert(self.ready)
        self.init_time = time.time()
        for agent in self.agents:
            agent.reset()

        if self.reward_specified:
            self.total_reward = 0.0
            self.reward_structure.reset()

        if self.debug['record_reward_trajectory']:
            self.trajectory = []

        return self.state()
    
    # properties, rewards, terminations, successes
    # See craft.IntersectionOnlyEgoEnv for an example
    # round reward to some decimal places
    # combine rewards through a provided 2-parameter function
    def reward_structure(self, d, p, r, t, s, round_to = 3, clip_to = None,
        combine_rewards = lambda a, b: a + b):

        assert(not self.reward_specified)
        assert(self.ego_id != None)
        objs = {
            'ego': self.agents[self.ego_id],
            'v': self.agents,
        }
        self.reward_structure = RewardStructure(d, p, r, t, s, objs,
            combine_rewards = combine_rewards)
        self.reward_specified = True
        self.round_to = round_to
        self.clip_to = [-np.inf, np.inf]
        if clip_to != None:
            assert(len(clip_to) == 2)
            assert(clip_to[0] <= clip_to[1])
            self.clip_to = clip_to

    def step(self, action):
        assert(self.ready)
        agents_in_bounds = 0
        reward = 0
        done = False
        info = {}

        if self.discrete:
            action = self.action_mapping[action[0]]

        # update ego
        if self.ego_id != None:
            if self.agents_drawn[self.ego_id]:
                self.agents[self.ego_id].step(action)
            agents_in_bounds += \
                self.is_agent_in_bounds(self.agents[self.ego_id])

        # update non-egos
        for aid, agent in enumerate(self.agents):
            if not agent.ego and self.agents_drawn[aid]:
                control_inputs = self.policies[aid](agent)
                agent.step(control_inputs)
            agents_in_bounds += self.is_agent_in_bounds(agent)

        # ask the reward structure: what is the reward?
        if self.reward_specified:
            reward, info, _ = self.reward_structure.step()
            if self.total_reward + reward > self.clip_to[1]:
                if self.clip_to[1] != np.inf:
                    reward = self.clip_to[1]-self.total_reward
                else:
                    reward = 0
            if self.total_reward + reward < self.clip_to[0]:
                if self.clip_to[0] != -np.inf:
                    reward = self.clip_to[0]-self.total_reward
                else:
                    reward = 0
            reward = float(reward)
            reward = round(reward, self.round_to)
            self.total_reward += reward

        # if terminated or succeeded
        if info != {}:
            if info['mode'] == 'success': done = True
            if info['mode'] == 'termination': done = True

        # terminate if nothing is within bounds
        if agents_in_bounds == 0: done = True

        # debugging
        if self.debug['intersection_enter']:
            self.debug_fns['intersection_enter']()
        if self.debug['show_steps']:
            T = self.reward_structure._p.t
            print(T, reward, info, done)
        if self.debug['show_elapsed'] and done:
            assert(self.init_time)
            diff = int(time.time() - self.init_time)
            print('Execution: %s' % str(datetime.timedelta(seconds = diff)))
        if self.debug['record_reward_trajectory']:
            self.trajectory += [reward]
            if done: info['traj'] = self.trajectory[:]
        if self.debug['show_reasons'] and done:
            print(info)
        if self.debug['action_buckets']: # bucketize actions
            self.debug_variables['buckets'].add(tuple(action))

        return self.state(), reward, done, info

    def get_action_buckets(self, intervals = 10):
        assert(self.debug['action_buckets'] == True)
        ego = self.agents[self.ego_id]
        amax = ego.MAX_ACCELERATION
        psidotmax = ego.MAX_STEERING_ANGLE_RATE
        grid = np.zeros((intervals, intervals))
        resolve = lambda x, a, b, n: int((x-a) * n * 1.0 / (b-a))
        def resolve2(x, a, b, n):
            x = np.clip(x, a, b)
            if x == b: return n-1
            else: return resolve(x, a, b, n)
        for action in self.debug_variables['buckets']:
            i = resolve2(action[0], -amax, amax, intervals)
            j = resolve2(action[1], -psidotmax, psidotmax, intervals)
            grid[i][j] += 1
        return grid

    def render(self, mode = 'human'):
        if not self.rendering:
            self.rendering = True
            self.canvas.set_visible(True)

        self.canvas.clear()
        self.canvas.switch_to()
        self.canvas.dispatch_events()
        drew_agents = self.canvas.on_draw()
        self.canvas.flip()

        # turn off rendering if nothing is drawn
        if drew_agents == 0:
            self.rendering = False
            self.canvas.set_visible(False)