from gymnasium.envs.registration import register

register(
    id="BDX-standup-v0",
    entry_point="mujoco_BDX_env.standup_env:StandupEnv"
)
