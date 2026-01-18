from contextlib import contextmanager
from typing import Iterator, override

from btpy import BehaviorTree, BTParser, NodeStatus
from btpy.builtins import Observer


class _Observer1(Observer):
    _calls = list[tuple[str, NodeStatus]]()

    @override
    @contextmanager
    def observe(self, node: BehaviorTree) -> Iterator[None]:
        yield
        _Observer1._calls.append((node.name(), node.status()))


class _Observer2(Observer):
    _calls = list[tuple[str, NodeStatus]]()

    @override
    @contextmanager
    def observe(self, node: BehaviorTree) -> Iterator[None]:
        yield
        _Observer2._calls.append((node.name(), node.status()))


def test_observers_ignore_observers() -> None:
    """test that observer nodes do not observe other observers"""
    xml = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4">
    <BehaviorTree ID="main">
        <Sequence name="top">
          <Sequence name="first" />
          <Fallback name="second" />
        </Sequence>
    </BehaviorTree>
</root>
""".strip()
    BTParser(_Observer1, _Observer2).parse_string(xml).tick()

    expected_calls = [
        ("first", NodeStatus.SUCCESS),
        ("second", NodeStatus.FAILURE),
        ("top", NodeStatus.FAILURE),
    ]
    assert _Observer1._calls == expected_calls
    assert _Observer2._calls == expected_calls
