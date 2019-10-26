import craft

env = craft.IntersectionOnlyEgoEnv()

# Debugging properties
# env.debug['state_inspect'] = True => try out env.state()
# env.debug['intersection_enter'] = True
env.debug['show_elapsed'] = True

obs = env.reset()
done = False

while not done:
    obs, reward, done, info = env.step([1, 0])
    env.render()