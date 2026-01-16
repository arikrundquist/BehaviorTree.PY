from typing import override

import pytest

from btpy.builtins.sequences import ReactiveSequence, Sequence, SequenceWithMemory

from btpy.models.node_status import NodeStatus
from btpy.behavior_tree import BehaviorTree


class _EchoAction(BehaviorTree):
    def __init__(self, __children: list[BehaviorTree] | None = None, **ports: str):
        super().__init__(__children, **ports)
        self.status = NodeStatus.SUCCESS
        self.halted = False

    @override
    def tick(self) -> NodeStatus:
        return self.status

    @override
    def halt(self) -> None:
        super().halt()
        self.halted = True


@pytest.mark.parametrize(
    "first,second,should_halt,final",
    [
        (NodeStatus.FAILURE, NodeStatus.SKIPPED, True, NodeStatus.FAILURE),
        (NodeStatus.RUNNING, NodeStatus.SKIPPED, False, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.RUNNING, False, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.SKIPPED, True, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.SKIPPED, True, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.SUCCESS, True, NodeStatus.SUCCESS),
    ],
)
def test_sequence(
    first: NodeStatus, second: NodeStatus, should_halt: bool, final: NodeStatus
) -> None:
    one, two = _EchoAction([]), _EchoAction([])
    one.status = first
    two.status = second

    assert Sequence([one, two]).tick() == final
    assert one.halted == should_halt
    assert two.halted == should_halt


def test_sequence_memory() -> None:
    one, two = _EchoAction([]), _EchoAction([])
    one.status = NodeStatus.SUCCESS
    two.status = NodeStatus.RUNNING

    uut_memory = SequenceWithMemory([one, two])
    uut_control = Sequence([one, two])

    assert uut_memory.tick() == NodeStatus.RUNNING
    assert uut_control.tick() == NodeStatus.RUNNING

    uut_memory.halt()
    uut_control.halt()
    one.status = NodeStatus.RUNNING
    two.status = NodeStatus.FAILURE

    assert uut_memory.tick() == NodeStatus.FAILURE
    assert uut_control.tick() == NodeStatus.RUNNING


def test_reactive_sequence() -> None:
    one, two = _EchoAction([]), _EchoAction([])
    one.status = NodeStatus.SUCCESS
    two.status = NodeStatus.RUNNING

    uut_reactive = ReactiveSequence([one, two])
    uut_control = Sequence([one, two])

    assert uut_reactive.tick() == NodeStatus.RUNNING
    assert uut_control.tick() == NodeStatus.RUNNING

    one.status = NodeStatus.FAILURE
    two.status = NodeStatus.SUCCESS

    assert uut_reactive.tick() == NodeStatus.FAILURE
    assert uut_control.tick() == NodeStatus.SUCCESS

    one.status = NodeStatus.SUCCESS

    assert uut_reactive.tick() == NodeStatus.SUCCESS
