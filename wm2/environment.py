import graphics
from utilities.ltl import Bits
import numpy as np
import time, datetime
import gym

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
            'show_elapsed': None,
        }
        self.debug = {k: False for k in self.debug_fns.keys()}
        self.debug_variables = {}

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

    def state(self):
        assert(hasattr(self, 'f'))
        if self.debug['state_inspect']:
            for agent in self.agents:
                print('%s => %s' % (agent.name, agent.f))
        return np.array([agent.f.numpy() for agent in self.agents])

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
        self.init_time = time.time()
        for agent in self.agents:
            agent.reset()
        return self.state()
    
    def step(self, action):
        agents_in_bounds = 0
        reward = 0
        done = False
        info = {}

        # ACTION for EGO
        # CONTROL VARIABLES
        
        # update non-egos
        for aid, agent in enumerate(self.agents):
            if not agent.ego and self.agents_drawn[aid]:
                control_inputs = self.policies[aid](agent)
                agent.step(control_inputs)
            agents_in_bounds += self.is_agent_in_bounds(agent)

        # terminate if nothing is within bounds
        if agents_in_bounds == 0: done = True

        # debugging
        if self.debug['intersection_enter']:
            self.debug_fns['intersection_enter']()
        if self.debug['show_elapsed'] and done:
            assert(self.init_time)
            diff = int(time.time() - self.init_time)
            print('Execution: %s' % str(datetime.timedelta(seconds = diff)))

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