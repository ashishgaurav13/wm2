import craft

env = craft.IntersectionOnlyEgoEnv()

# Debugging properties
# env.debug['state_inspect'] = True => try out env.state()
# env.debug['intersection_enter'] = True
env.debug['show_elapsed'] = True
env.debug['show_steps'] = True
# env.agent_freeze_all()

obs = env.reset()
done = False

while not done:
    obs, reward, done, info = env.step([1, 0])
    env.render()