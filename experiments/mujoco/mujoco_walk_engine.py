import argparse
import time

import mujoco
import mujoco.viewer
import numpy as np
import placo
from scipy.spatial.transform import Rotation as R

from mini_bdx.utils.mujoco_utils import check_contact
from mini_bdx.utils.xbox_controller import XboxController
from mini_bdx.walk_engine import WalkEngine

parser = argparse.ArgumentParser()
parser.add_argument("-x", "--xbox_controller", action="store_true")
args = parser.parse_args()

if args.xbox_controller:
    xbox = XboxController()

model = mujoco.MjModel.from_xml_path("../../mini_bdx/robots/bdx/scene.xml")
data = mujoco.MjData(model)


max_target_step_size_x = 0.03
max_target_step_size_y = 0.03
max_target_yaw = np.deg2rad(15)
target_step_size_x = 0
target_step_size_y = 0
target_yaw = 0
target_head_pitch = 0
target_head_yaw = 0
target_head_z_offset = 0
walking = False
time_since_last_left_contact = 0
time_since_last_right_contact = 0
walking = False

start_timeout = time.time()


def xbox_input():
    global target_step_size_x, target_step_size_y, target_yaw, walking, t, walk_engine, target_head_pitch, target_head_yaw, target_head_z_offset, start_timeout, max_target_step_size_x, max_target_step_size_y, max_target_yaw
    inputs = xbox.read()
    target_step_size_x = -inputs["l_y"] * max_target_step_size_x
    target_step_size_y = inputs["l_x"] * max_target_step_size_y
    if inputs["l_trigger"] > 0.5:
        target_head_pitch = inputs["r_y"] * np.deg2rad(45)
        target_head_yaw = -inputs["r_x"] * np.deg2rad(120)
        target_head_z_offset = inputs["r_trigger"] * 0.08
    else:
        target_yaw = -inputs["r_x"] * max_target_yaw

    if inputs["start"] and time.time() - start_timeout > 0.5:
        walking = not walking
        start_timeout = time.time()


def key_callback(keycode):
    global target_step_size_x, target_step_size_y, target_yaw, walking, t, walk_engine, max_target_step_size_x, max_target_step_size_y, max_target_yaw
    if keycode == 265:  # up
        max_target_step_size_x += 0.005
    if keycode == 264:  # down
        max_target_step_size_x -= 0.005
    if keycode == 263:  # left
        max_target_step_size_y -= 0.005
    if keycode == 262:  # right
        max_target_step_size_y += 0.005
    if keycode == 81:  # a
        max_target_yaw += np.deg2rad(1)
    if keycode == 69:  # e
        max_target_yaw -= np.deg2rad(1)
    if keycode == 257:  # enter
        walking = not walking
    if keycode == 79:  # o
        walk_engine.swing_gain -= 0.005
    if keycode == 80:  # p
        walk_engine.swing_gain += 0.005
    if keycode == 76:  # l
        walk_engine.tune_trunk_x_offset += 0.001
    if keycode == 59:  # m
        walk_engine.tune_trunk_x_offset -= 0.001
    if keycode == 266:  # page up
        walk_engine.frequency += 0.1
    if keycode == 267:  # page down
        walk_engine.frequency -= 0.1
    if keycode == 32:  # space
        target_step_size_x = 0
        target_step_size_y = 0
        target_yaw = 0
    if keycode == 261:  # delete
        walking = False
        target_step_size_x = 0
        target_step_size_y = 0
        target_yaw = 0
        walk_engine.reset()
        data.qpos[:7] = 0
        data.qpos[2] = 0.19
        data.ctrl[:] = 0
        t = 0

    print("----------------")
    print("walking" if walking else "not walking")
    print("MAX_TARGET_STEP_SIZE_X (up, down)", max_target_step_size_x)
    print("MAX_TARGET_STEP_SIZE_Y (left, right)", max_target_step_size_y)
    print("MAX_TARGET_YAW (a, e)", np.rad2deg(max_target_yaw))
    print("swing gain (o, p)", walk_engine.swing_gain)
    print("trunk x offset (l, m)", walk_engine.trunk_x_offset)
    print("frequency (pageup, pagedown)", walk_engine.frequency)
    print("----------------")


viewer = mujoco.viewer.launch_passive(model, data, key_callback=key_callback)

robot = placo.RobotWrapper(
    "../../mini_bdx/robots/bdx/robot.urdf", placo.Flags.ignore_collisions
)
solver = placo.KinematicsSolver(robot)


walk_engine = WalkEngine(
    robot,
    solver,
    rise_gain=0.02,
    frequency=2.0,
    trunk_x_offset=0.007,
)


def get_imu(data):

    rot_mat = np.array(data.body("base").xmat).reshape(3, 3)
    gyro = R.from_matrix(rot_mat).as_euler("xyz")

    accelerometer = np.array(data.body("base").cvel)[3:]

    return gyro, accelerometer


prev = data.time
t = 0
throttled = False
try:
    while True:
        dt = data.time - prev

        if args.xbox_controller:
            xbox_input()

        if not check_contact(data, model, "foot_module", "floor"):  # right
            time_since_last_right_contact += dt
        else:
            time_since_last_right_contact = 0
        if not check_contact(data, model, "foot_module_2", "floor"):  # left
            time_since_last_left_contact += dt
        else:
            time_since_last_left_contact = 0

        if (
            not time_since_last_left_contact > walk_engine.rise_duration
            and not time_since_last_right_contact > walk_engine.rise_duration
        ):
            t += dt

        if t > walk_engine.step_duration:
            t = 0
            walk_engine.new_step()

        gyro, accelerometer = get_imu(data)
        walk_engine.update(
            walking,
            gyro,
            target_step_size_x,
            target_step_size_y,
            target_yaw,
            target_head_pitch,
            target_head_yaw,
            target_head_z_offset,
            t,
        )
        angles = walk_engine.compute_angles()
        robot.update_kinematics()
        solver.solve(True)

        data.ctrl[:] = list(angles.values())

        prev = data.time
        mujoco.mj_step(model, data)
        viewer.sync()
        time.sleep(model.opt.timestep / 2.5)
except KeyboardInterrupt:
    viewer.close()