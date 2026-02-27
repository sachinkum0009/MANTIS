"""
Bi Teleop script to control both SO 101 robots
"""

from lerobot.cameras.configs import CameraConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower
from mantis.controller_position import Pose
from mantis.ik_planner import IkPlanner
from pathlib import Path


class BiTeleop:
    def __init__(self):
        """Bi Teleop Initialize Robots"""
        # left robot setup
        left_camera_config: dict[str, CameraConfig] = {
            "front": OpenCVCameraConfig(
                index_or_path=0, width=1920, height=1080, fps=30
            )
        }
        left_robot_config = SO101FollowerConfig(
            port="/dev/ttyUSB0", id="left_robot_arm", cameras=left_camera_config
        )
        self._left_robot = SO101Follower(left_robot_config)

        # right robot setup
        right_camera_config: dict[str, CameraConfig] = {
            "front": OpenCVCameraConfig(
                index_or_path=0, width=1920, height=1080, fps=30
            )
        }
        right_robot_config = SO101FollowerConfig(
            port="/dev/ttyUSB1", id="right_robot_arm", cameras=right_camera_config
        )
        self._right_robot = SO101Follower(right_robot_config)
        urdf_path = Path("/home/asus/backup/zzzzz/isaac/MANTIS/urdf/so_arm101.urdf")
        self._ik_planner = IkPlanner(urdf_path)

    def connect_robots(self):
        """Connect both robots"""
        self._left_robot.connect()
        self._right_robot.connect()

    def teleop_robots(
        self, left_action: dict[str, float], right_action: dict[str, float]
    ):
        """
        @brief Teleop Bi Robots
        @param left_action
        @param right_action
        """
        left_observation = self._left_robot.get_observation()
        right_observation = self._right_robot.get_observation()
        self._left_robot.send_action(left_action)
        self._right_robot.send_action(right_action)
        print(left_observation, right_observation)

    def send_pose(self, left_pose: Pose, right_pose: Pose):
        """Send pose to both robots"""
        left_joint_val = self._ik_planner.compute_ik(left_pose)
        right_joint_val = self._ik_planner.compute_ik(right_pose)
        self.teleop_robots(left_joint_val, right_joint_val)
