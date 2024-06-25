import time

import cv2
import numpy as np
import placo

from mini_bdx.hwi import HWI
from mini_bdx.utils.xbox_controller import XboxController
from mini_bdx.walk_engine import WalkEngine

xbox = XboxController()


hwi = HWI()

max_target_step_size_x = 0.03
max_target_step_size_y = 0.03
max_target_yaw = np.deg2rad(15)
target_step_size_x = 0
target_step_size_y = 0
target_yaw = 0
target_head_pitch = 0
target_head_yaw = 0
target_head_z_offset = 0
time_since_last_left_contact = 0
time_since_last_right_contact = 0
walking = False
start_button_timeout = time.time()

robot = placo.RobotWrapper(
    "../../mini_bdx/robots/bdx/robot.urdf", placo.Flags.ignore_collisions
)

walk_engine = WalkEngine(robot, frequency=1.5, swing_gain=0.0)


def xbox_input():
    global target_step_size_x, target_step_size_y, target_yaw, walking, t, walk_engine, target_head_pitch, target_head_yaw, target_head_z_offset, start_button_timeout, max_target_step_size_x, max_target_step_size_y, max_target_yaw
    inputs = xbox.read()
    # print(inputs)
    target_step_size_x = -inputs["l_y"] * max_target_step_size_x
    target_step_size_y = inputs["l_x"] * max_target_step_size_y
    if inputs["l_trigger"] > 0.2:
        target_head_pitch = inputs["r_y"] / 2 * np.deg2rad(45)
        target_head_yaw = -inputs["r_x"] / 2 * np.deg2rad(120)
        target_head_z_offset = inputs["r_trigger"] * 4 * 0.08
    else:
        target_yaw = -inputs["r_x"] * max_target_yaw

    if inputs["start"] and time.time() - start_button_timeout > 0.5:
        walking = not walking
        start_button_timeout = time.time()


# while True:
#     xbox_input()

im = np.zeros((80, 80, 3), dtype=np.uint8)


# TODO
def get_imu():
    return [0, 0, 0], [0, 0, 0]


# hwi.turn_off()
# exit()
hwi.turn_on()
time.sleep(1)
# hwi.goto_init()

# exit()
gyro = [0, 0.0, 0]
accelerometer = [0, 0, 0]

skip = 10
prev = time.time()
while True:
    dt = time.time() - prev
    t = time.time()
    xbox_input()

    # Get sensor data
    # gyro, accelerometer = get_imu()

    walk_engine.update(
        walking,
        gyro,
        accelerometer,
        False,
        False,
        target_step_size_x,
        target_step_size_y,
        target_yaw,
        target_head_pitch,
        target_head_yaw,
        target_head_z_offset,
        dt,
        ignore_feet_contact=True,
    )
    angles = walk_engine.get_angles()

    if skip > 0:
        skip -= 1
        continue
    hwi.set_position_all(angles)

    # print("-")
    cv2.imshow("image", im)
    key = cv2.waitKey(1)
    if key == ord("p"):
        gyro[1] += 0.001
    if key == ord("o"):
        gyro[1] -= 0.001
    if key == ord("m"):
        walk_engine.default_trunk_x_offset += 0.01
    if key == ord("l"):
        walk_engine.default_trunk_x_offset -= 0.01
    if key == ord("i"):
        walk_engine.default_trunk_z_offset += 0.01
    if key == ord("u"):
        walk_engine.default_trunk_z_offset -= 0.01
    print(gyro)
    print(walk_engine.default_trunk_x_offset)
    print(walk_engine.default_trunk_z_offset)

    prev = t
