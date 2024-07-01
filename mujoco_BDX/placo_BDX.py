import placo
import os
from placo_utils.visualization import robot_viz


def load_sigmaban() -> placo.RobotWrapper:
    filename = os.path.join(os.path.dirname(__file__), "../mini_bdx/robots/bdx/robot.urdf")
    print(filename)
    return placo.RobotWrapper(filename, placo.Flags.collision_as_visual)


viz = None


def sigmaban_viz(robot: placo.RobotWrapper) -> None:
    global viz

    if viz is None:
        viz = robot_viz(robot, "sigmaban")

    viz.display(robot.state.q)
