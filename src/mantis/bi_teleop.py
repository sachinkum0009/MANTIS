"""
Bi Teleop script to control both SO 101 robots
"""

from lerobot.cameras.configs import CameraConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.processor import RobotAction
from lerobot.robots.bi_so_follower import BiSOFollowerConfig, BiSOFollower
from lerobot.robots.so_follower import SO101FollowerConfig
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

        # right robot setup
        right_camera_config: dict[str, CameraConfig] = {
            "front": OpenCVCameraConfig(
                index_or_path=0, width=1920, height=1080, fps=30
            )
        }
        right_robot_config = SO101FollowerConfig(
            port="/dev/ttyUSB1", id="right_robot_arm", cameras=right_camera_config
        )
        bi_so_follower_config = BiSOFollowerConfig(
            left_arm_config=left_robot_config, right_arm_config=right_robot_config
        )
        self._bi_so_follower = BiSOFollower(bi_so_follower_config)
        urdf_path = Path("/home/asus/backup/zzzzz/isaac/MANTIS/urdf/so_arm101.urdf")
        self._ik_planner = IkPlanner(urdf_path)

    def connect_robots(self):
        self._bi_so_follower.connect()

    def disconnect_robots(self):
        """Disconnect both robots"""
        self._bi_so_follower.disconnect()

    def get_observations(self) -> tuple[dict[str, float], dict[str, float]]:
        """Get observations from both robots"""
        observations = self._bi_so_follower.get_observation()
        left_observation = observations["left_arm"]
        right_observation = observations["right_arm"]
        return left_observation, right_observation

    def teleop_robots(
        self, left_action: dict[str, float], right_action: dict[str, float]
    ):
        """
        @brief Teleop Bi Robots
        @param left_action
        @param right_action
        """
        robot_actions = RobotAction(
            {
                "left_arm": left_action,
                "right_arm": right_action,
            }
        )
        self._bi_so_follower.send_action(robot_actions)

    def send_pose(self, left_pose: Pose, right_pose: Pose):
        """Send pose to both robots"""
        left_joint_val = self._ik_planner.compute_ik(left_pose)
        right_joint_val = self._ik_planner.compute_ik(right_pose)
        self.teleop_robots(left_joint_val, right_joint_val)
