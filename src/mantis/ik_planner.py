"""
IK Planner for controlling robot arm
"""

import ikpy
from ikpy.chain import Chain
from ikpy.link import OriginLink, URDFLink
from pathlib import Path

from mantis.controller_position import Pose


class IkPlanner:
    """
    IkPlanner class
    helps to find `Inverse Kinematics` for desired pose
    """
    def __init__(self, urdf_path: Path):
        self.urdf_chain = Chain.from_urdf_file(urdf_path.absolute())

    def compute_ik(self, pose: Pose) -> list[float]:
        joint_positions = self.urdf_chain.inverse_kinematics(pose.get_pose())
        return joint_positions
