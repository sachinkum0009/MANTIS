from dataclasses import dataclass
import json
from typing import Any, Dict


class InvalidControllerData(ValueError):
    """Raised when controller data is invalid or missing required fields."""


@dataclass
class Pose:
    """
    Represent a 3D pose with x, y, and z coordinates.

    Attributes:
        x (float): X-coordinate.
        y (float): Y-coordinate.
        z (float): Z-coordinate.

    Examples:
        >>> p = Pose(x=1.0, y=2.0, z=3.0)
        >>> (p.x, p.y, p.z)
        (1.0, 2.0, 3.0)

    Create a Pose instance from a mapping with 'x', 'y', and 'z' keys.

    Args:
        data (Dict[str, float]): Mapping containing the keys 'x', 'y', and 'z'.
            Values may be numeric or convertible to float.

    Returns:
        Pose: A new Pose instance with coordinates parsed from `data`.

    Raises:
        KeyError: If any of the required keys ('x', 'y', 'z') are missing.
        ValueError: If any value cannot be converted to float.

    Examples:
        >>> Pose.from_dict({'x': '1.0', 'y': 2, 'z': 3.0})
        Pose(x=1.0, y=2.0, z=3.0)

    Return the pose coordinates as a list of floats: [x, y, z].

    This convenience method returns the three coordinate values in order.
    When called on an instance it returns that instance's coordinates; when
    called on the class it attempts to read class-level attributes `x`, `y`,
    and `z`.

    Returns:
        list[float]: Coordinates in order [x, y, z].

    Raises:
        AttributeError: If x, y, or z is not defined on the instance or class.

    Examples:
        >>> p = Pose(x=1.0, y=2.0, z=3.0)
        >>> p.get_pose()
        [1.0, 2.0, 3.0]
    """

    x: float
    y: float
    z: float
    ox: float = 0.0
    oy: float = 0.0
    oz: float = 0.0
    ow: float = 1.0

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Pose":
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            z=float(data["z"]),
            ox=float(data.get("ox", 0.0)),
            oy=float(data.get("oy", 0.0)),
            oz=float(data.get("oz", 0.0)),
            ow=float(data.get("ow", 1.0)),
        )

    @classmethod
    def get_pose(cls) -> list[float]:
        return [cls.x, cls.y, cls.z, cls.ox, cls.oy, cls.oz, cls.ow]


@dataclass
class ControllerState:
    """
    Represents the Controller State

    Attributes:
        grip: float
        trigger: float
        valid: bool
        pose: Pose
    """

    grip: float
    trigger: float
    valid: bool
    pose: Pose

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ControllerState":
        try:
            return cls(
                grip=float(data["grip"]),
                trigger=float(data["trigger"]),
                valid=bool(data["valid"]),
                pose=Pose.from_dict(data),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidControllerData(f"Invalid ControllerState data: {exc}")


@dataclass
class ControllerPositions:
    """
    Represents the ControllerPositions

    Attributes:
        left: ControllerState
        right: ControllerState
        type: str = "controller_positions"
    """

    left: ControllerState
    right: ControllerState
    type: str = "controller_positions"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ControllerPositions":
        try:
            left = ControllerState.from_dict(data["left"])
            right = ControllerState.from_dict(data["right"])
            ctype = data.get("type", "controller_positions")
            return cls(left=left, right=right, type=str(ctype))
        except (KeyError, TypeError, ValueError) as exc:
            msg = f"Invalid ControllerPositions data: {exc}"
            raise InvalidControllerData(msg)

    @classmethod
    def from_json(cls, json_str: str) -> "ControllerPositions":
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise InvalidControllerData(f"Invalid JSON: {exc}")
        return cls.from_dict(data)
