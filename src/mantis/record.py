from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.cameras.configs import CameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower

camera_config: dict[str, CameraConfig] = {
    "front": OpenCVCameraConfig(index_or_path=0, width=1920, height=1080, fps=30)
}

robot_config = SO101FollowerConfig(
    port="/dev/ttyUSB0", id="my_robot_arm", cameras=camera_config
)

teleop_config = SO101LeaderConfig(
    port="/dev/ttyUSB1",
    id="my_leader_arm",
)

robot = SO101Follower(robot_config)
teleop_device = SO101Leader(teleop_config)

robot.connect()
teleop_device.connect()

while True:
    observation = robot.get_observation()
    action = teleop_device.get_action()
    robot.send_action(action)
