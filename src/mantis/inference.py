import draccus
from dataclasses import dataclass
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
import logging
import torch


@dataclass
class BiManualInferenceConfig:
    ip: str
    port: int


class BiManualInference:
    def __init__(self):
        """BiManualInference Initialize Policy"""
        policy_repo = "sachinkum0009/smolvla"
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._policy_config = SmolVLAConfig(repo_id=policy_repo, device=device)
        self._policy = SmolVLAPolicy(self._policy_config)

    def infer_action(self, observation: dict[str, float]) -> dict[str, float]:
        """Infer action from observation"""
        self._policy.eval()
        self._policy.to(self._policy_config.device)
        action = self._policy(observation)
        return action


@draccus.wrap
def main(cfg: BiManualInferenceConfig):
    """Main function for BiManualInference"""
    logging.info("Starting BiManualInference")
    inference = BiManualInference()
    # Here you would typically set up a server to receive observations and send actions
    # For example, using a simple TCP server or a web server
    # This is just a placeholder for demonstration purposes
    while True:
        observation: dict[str, float] = (
            {}
        )  # Replace with actual observation retrieval logic
        action = inference.infer_action(observation)
        # Send action back to the robot or client
        logging.info(f"Inferred action: {action}")
