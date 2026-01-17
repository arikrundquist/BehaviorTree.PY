import pytest
from btpy.core import LayeredDict


def test_single_layered_dict() -> None:
    uut = LayeredDict[str, str]()
    uut["key 1"] = "value 1"
    uut["key 2"] = "value 2"
    uut["key 3"] = "value 3"

    expected = {
        "key 1": "value 1",
        "key 2": "value 2",
        "key 3": "value 3",
    }

    for key, value in expected.items():
        assert key in uut
        assert uut[key] == value

    assert uut.flatten() == expected


def test_multi_layered_dict() -> None:
    prev: LayeredDict[str, str] | None = None
    for i in range(1, 4):
        uut = LayeredDict[str, str](prev)
        prev = uut
        for j in range(i, 4):
            uut[f"key {j}"] = f"value {j}-{i}"

    expected = {
        "key 1": "value 1-1",
        "key 2": "value 2-2",
        "key 3": "value 3-3",
    }

    for key, value in expected.items():
        assert key in uut
        assert uut[key] == value

    assert uut.flatten() == expected


def test_layered_dict_errors() -> None:
    uut = LayeredDict[str, str]()
    unexpected = "unexpected"

    assert unexpected not in uut
    with pytest.raises(KeyError):
        uut[unexpected]
