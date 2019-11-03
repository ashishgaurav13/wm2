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

    canvas = ...
    default_policy = lambda c: c.aggressive_driving()
    env = Environment(canvas, default_policy)

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

    def __init__(self, canvas, default_policy = None):
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
            'record_reward_trajectory': None
        }
        self.debug = {k: False for k in self.debug_fns.keys()}
        self.debug_variables = {}

        # Call make_ready to set ready to true
        self.ready = False

    # Create obs space and action space after everything is set
    def make_ready(self):
        assert(not self.ready)
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
    def reward_structure(self, d, p, r, t, s, round_to = 3, clip_to = None):
        assert(not self.reward_specified)
        assert(self.ego_id != None)
        objs = {
            'ego': self.agents[self.ego_id],
        }
        self.reward_structure = RewardStructure(d, p, r, t, s, objs)
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

        return self.state(), reward, done, info
        
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