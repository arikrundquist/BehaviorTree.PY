from typing import override

import pytest
from btpy import BehaviorTree, NodeStatus
from btpy.builtins import ReactiveSequence, Sequence, SequenceWithMemory


class _EchoAction(BehaviorTree):
    def init(self) -> None:
        super().init()
        self.next_status = NodeStatus.SUCCESS
        self.halted = False

    @override
    def _do_tick(self) -> NodeStatus:
        return self.next_status

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
    """test the sequence node"""
    one, two = _EchoAction(), _EchoAction()
    one.next_status = first
    two.next_status = second

    assert Sequence([one, two]).tick() == final
    assert one.halted == should_halt
    assert two.halted == should_halt


def test_sequence_with_memory() -> None:
    """test the sequence with memory node"""
    one, two = _EchoAction(), _EchoAction()
    one.next_status = NodeStatus.SUCCESS
    two.next_status = NodeStatus.RUNNING

    uut_memory = SequenceWithMemory([one, two])
    uut_control = Sequence([one, two])

    assert uut_memory.tick() == NodeStatus.RUNNING
    assert uut_control.tick() == NodeStatus.RUNNING

    uut_memory.halt()
    uut_control.halt()
    one.next_status = NodeStatus.RUNNING
    two.next_status = NodeStatus.FAILURE

    assert uut_memory.tick() == NodeStatus.FAILURE
    assert uut_control.tick() == NodeStatus.RUNNING


def test_reactive_sequence() -> None:
    """test the reactive sequence node"""
    one, two = _EchoAction(), _EchoAction()
    one.next_status = NodeStatus.SUCCESS
    two.next_status = NodeStatus.RUNNING

    uut_reactive = ReactiveSequence([one, two])
    uut_control = Sequence([one, two])

    assert uut_reactive.tick() == NodeStatus.RUNNING
    assert uut_control.tick() == NodeStatus.RUNNING

    one.next_status = NodeStatus.FAILURE
    two.next_status = NodeStatus.SUCCESS

    assert uut_reactive.tick() == NodeStatus.FAILURE
    assert uut_control.tick() == NodeStatus.SUCCESS

    one.next_status = NodeStatus.SUCCESS

    assert uut_reactive.tick() == NodeStatus.SUCCESS
