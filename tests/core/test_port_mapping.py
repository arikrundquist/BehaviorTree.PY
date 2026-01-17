from typing import Iterator, override

import pytest
from btpy import BehaviorTree, Blackboard, BTParser, NodeRegistration, NodeStatus


class _AddAction(BehaviorTree):
    @override
    def tick(self) -> NodeStatus:
        x = self.get("x", int)
        y = self.get("y", int)
        z = self.get("z", int)

        if x.value is None or y.value is None:
            return NodeStatus.FAILURE

        z.value = x.value + y.value
        return NodeStatus.SUCCESS


@pytest.fixture(autouse=True)
def register_add_action() -> Iterator[None]:
    with NodeRegistration.context():
        NodeRegistration.register(_AddAction)
        yield


def test_name_mapping() -> None:
    assert _AddAction().attach_blackboard(Blackboard()).name() == "_AddAction"
    assert _AddAction(name="adder").attach_blackboard(Blackboard()).name() == "adder"


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_no_port_mapping(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Action ID="_AddAction" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = blackboard.set("x", x) + blackboard.set("y", y)
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("z").value == expected


@pytest.mark.parametrize("data", range(3))
def test_basic_port_mapping(data: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <SubTree ID="add" x="{data}" y="4" z="{result}" />
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = blackboard.set("data", data) + 4
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("result").value == expected


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_complex_port_mapping(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Sequence>
      <Action ID="_AddAction" y="4" z="{first}" />
      <SubTree ID="double" n="{first}" result="{second}" />
      <SubTree ID="add" x="{second}" y="{y}" z="{result}" />
    </Sequence>
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" />
  </BehaviorTree>

  <BehaviorTree ID="double">
    <Action ID="_AddAction" x="{n}" y="{n}" z="{result}" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = (blackboard.set("x", x) + 4) * 2 + blackboard.set("y", y)
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("result").value == expected


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_auto_remapping(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Sequence>
      <SubTree ID="add" _autoremap="true" />
    </Sequence>
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = blackboard.set("x", x) + blackboard.set("y", y)
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("z").value == expected


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_auto_remapping_private(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Sequence>
      <Action ID="_AddAction" x="{x}" y="{x}" z="{_private}" />
      <SubTree ID="add" _autoremap="true" />
    </Sequence>
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" x="{y}" y="{y}" z="{_private}" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    blackboard.set("y", y)
    expected = 2 * blackboard.set("x", x)
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("_private").value == expected


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_global_blackboard(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Sequence>
      <SubTree ID="add" />
      <Action ID="_AddAction" x="{result}" y="{result}" z="{result}" />
      <Action ID="_AddAction" x="{@result}" y="{@result}" z="{@result}" />
    </Sequence>
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" x="{@x}" y="{@y}" z="{@result}" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = 4 * (blackboard.set("x", x) + blackboard.set("y", y))
    assert tree.tick() == NodeStatus.SUCCESS
    assert blackboard.get("result").value == expected


@pytest.mark.parametrize("x,y", [(x, y) for x in range(3) for y in range(3)])
def test_bad_port_mapping(x: int, y: int) -> None:
    description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Sequence>
      <_AddAction />
      <SubTree ID="add" x="{z}" y="{z}" z="{result}" />
      <SubTree ID="add" x="{bad1}" y="{bad2}" z="{z}" />
    </Sequence>
  </BehaviorTree>

  <BehaviorTree ID="add">
    <Action ID="_AddAction" />
  </BehaviorTree>
</root>
""".strip()

    blackboard = Blackboard()
    tree = BTParser().parse_string(description, blackboard=blackboard)
    expected = 2 * (blackboard.set("x", x) + blackboard.set("y", y))
    assert tree.tick() == NodeStatus.FAILURE
    assert blackboard.get("result").value == expected
