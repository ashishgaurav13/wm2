import craft

env = craft.WaitPriorityEnv()

obs = env.reset()
done = False

# Try other policies to reach the right hand side?
# [1, 1] or [1, -1] will veer it off-course
while not done:
    obs, reward, done, info = env.step([0, 0])
    env.render()