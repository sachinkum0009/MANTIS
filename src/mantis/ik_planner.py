"""
IK Planner for controlling robot arm
"""

from ikpy.chain import Chain
from pathlib import Path

from mantis.controller_position import Pose


class IkPlanner:
    """
    IkPlanner class
    helps to find `Inverse Kinematics` for desired pose
    """

    def __init__(self, urdf_path: Path):
        self.urdf_chain = Chain.from_urdf_file(urdf_path.absolute())

    def compute_ik(self, pose: Pose) -> dict[str, float]:
        joint_positions = self.urdf_chain.inverse_kinematics(pose.get_pose())
        return {f"joint{i+1}": float(v) for i, v in enumerate(joint_positions)}
