import mujoco_BDX_env
import pickle
import os
import gymnasium as gym

env = gym.make("BDX-standup-v0")
configs: list = []
filename: str = env.get_initial_config_filename()

if os.path.exists(filename):
    configs = pickle.load(open(filename, "rb"))

try:
    while True:
        env.reset(use_cache=False)
        configs.append([env.sim.data.qpos.copy(), env.sim.data.ctrl.copy()])

        if len(configs) % 100 == 0:
            print(f"Generated {len(configs)} initial in the file {filename}")
            pickle.dump(configs, open(filename, "wb"))
except KeyboardInterrupt:
    print("Saving...")
    pickle.dump(configs, open(filename, "wb"))
