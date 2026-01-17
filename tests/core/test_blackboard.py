from btpy import Blackboard
from btpy.core import BlackboardChildType


def test_top_level_blackboard() -> None:
    """test basic blackboard functionality"""
    uut = Blackboard()
    uut.set("key 1", "value 1")
    uut.set("key 2", "value 2")
    uut.set("key 3", "value 3")

    expected = {
        "key 1": "value 1",
        "key 2": "value 2",
        "key 3": "value 3",
        "key 4": None,
    }

    for key, value in expected.items():
        assert uut.get(key).value == value


def test_multi_level_blackboard() -> None:
    """test blackboards can get values from up their hierarchy"""
    uut = Blackboard()
    for i in range(1, 4):
        uut = uut.create_child(BlackboardChildType.CHILD)
        for j in range(i, 4):
            uut.set(f"key {j}", f"value {i}-{j}")

    expected = {
        "key 1": "value 1-1",
        "key 2": "value 2-2",
        "key 3": "value 3-3",
        "key 4": None,
    }

    for key, value in expected.items():
        assert uut.get(key).value == value


def test_top_level_world_blackboard() -> None:
    """test that a top level blackboard is its own world blackboard"""
    uut = Blackboard()
    uut.set("key 1", "value 1")
    uut.set("key 2", "value 2")
    uut.set("key 3", "value 3")
    uut.set("@key 4", "value 4")
    uut.set("@key 5", "value 5")
    uut.set("@key 6", "value 6")

    expected = {
        "key 1": "value 1",
        "key 2": "value 2",
        "key 3": "value 3",
        "key 4": "value 4",
        "key 5": "value 5",
        "key 6": "value 6",
        "key 7": None,
    }

    for key, value in expected.items():
        assert uut.get(key).value == value
        assert uut.get(f"@{key}").value == value


def test_different_world_and_parent() -> None:
    """test that blackboards delegate correctly to either their parent or their world"""
    parent = Blackboard()
    world = Blackboard()

    uut = Blackboard(parent, world=world)
    uut.set("key", "value")
    uut.set("@key", "global value")

    assert parent.get("key").value == "value"
    assert world.get("key").value == "global value"

    assert parent.get("@key").value == "value"
    assert world.get("@key").value == "global value"


def test_clean_child() -> None:
    """test that a clean child can affect its parent except through the world"""
    parent = Blackboard()
    uut = parent.create_child(BlackboardChildType.CLEAN)
    uut.set("key", "value")
    uut.set("@global key", "global value")

    assert parent.get("key").value is None
    assert uut.get("key").value == "value"
    assert uut.get("@key").value is None

    assert parent.get("global key").value == "global value"
    assert uut.get("global key").value is None
    assert uut.get("@global key").value == "global value"


def test_remapped_child() -> None:
    """test that a remapped child can affect its parent except for private ports"""
    parent = Blackboard()
    uut = parent.create_child(BlackboardChildType.REMAPPED)
    uut.set("key", "value")
    uut.set("_private key", "private value")
    uut.set("@global key", "global value")
    uut.set("@_global private key", "global private value")

    assert parent.get("key").value == "value"
    assert uut.get("key").value == "value"
    assert uut.get("@key").value == "value"

    assert parent.get("_private key").value is None
    assert uut.get("_private key").value == "private value"
    assert uut.get("@_private key").value is None

    assert parent.get("global key").value == "global value"
    assert uut.get("global key").value == "global value"
    assert uut.get("@global key").value == "global value"

    assert parent.get("_global private key").value == "global private value"
    assert uut.get("_global private key").value is None
    assert uut.get("@_global private key").value == "global private value"


def test_port_remapping() -> None:
    """test that remapped ports reference the same data"""
    uut1 = Blackboard()
    uut2 = Blackboard()

    uut1.set("uut1", "uut1")
    uut2.set("uut2", "uut2")

    mappings = {
        "uut1": "not uut1",
        "actually uut1": "{uut1}",
        "also actually uut1": "{@uut1}",
    }

    Blackboard.remap(uut1, uut2, mappings)

    assert uut1.get("uut1").value == "uut1"
    assert uut2.get("uut1").value == "not uut1"

    assert uut1.get("uut2").value is None
    assert uut2.get("uut2").value == "uut2"

    assert uut1.get("actually uut1").value is None
    assert uut2.get("actually uut1").value == "uut1"

    assert uut1.get("also actually uut1").value is None
    assert uut2.get("also actually uut1").value == "uut1"


def test_get_transformation() -> None:
    """test that the requested transform is applied"""
    uut = Blackboard()
    uut.set("int", 12)
    uut.set("str", "24")
    uut.set("none", None)

    assert uut.get("int").value == 12
    assert uut.get("int", int).value == 12
    assert uut.get("int", str).value == "12"
    assert uut.get("int").value == "12"

    assert uut.get("str").value == "24"
    assert uut.get("str", str).value == "24"
    assert uut.get("str", int).value == 24
    assert uut.get("str").value == 24

    assert uut.get("none").value is None
    assert uut.get("none", int).value is None
    assert uut.get("none", str).value is None
