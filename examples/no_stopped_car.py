import os, sys; sys.path += ["."]
import craft

env = craft.NoStoppedCar()

# Try other policies to reach the right hand side?
# [1, 1] or [1, -1] will veer it off-course

# Render loop
obs = env.reset()
done = False
while not done:
    obs, reward, done, info = env.step([1, -1])
    env.render()