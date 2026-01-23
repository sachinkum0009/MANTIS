import pytest

from mantis.controller_position import ControllerPositions, InvalidControllerData


def test_from_json_valid():
    json_str = (
        '{"left":{"grip":0.0,"trigger":0.0,"valid":true,"x":0.1,"y":0.2,"z":-0.1},'
        '"right":{"grip":0.0,"trigger":0.0,"valid":true,"x":0.2,"y":0.3,"z":-0.01},'
        '"type":"controller_positions"}'
    )

    cp = ControllerPositions.from_json(json_str)

    assert cp.type == "controller_positions"
    assert cp.left.pose.x == pytest.approx(0.1)
    assert cp.right.pose.y == pytest.approx(0.3)


def test_from_json_invalid_missing_fields():
    # Missing fields should raise InvalidControllerData
    bad_json = '{"left":{}, "right":{}}'
    with pytest.raises(InvalidControllerData):
        ControllerPositions.from_json(bad_json)
