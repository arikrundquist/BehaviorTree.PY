from typing import override

import pytest
from btpy import BehaviorTree, NodeStatus
from btpy.builtins import Fallback, ReactiveFallback


class _EchoAction(BehaviorTree):
    def init(self) -> None:
        super().init()
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
        (NodeStatus.RUNNING, NodeStatus.SKIPPED, False, NodeStatus.RUNNING),
        (NodeStatus.SUCCESS, NodeStatus.SKIPPED, True, NodeStatus.SUCCESS),
        (NodeStatus.SKIPPED, NodeStatus.RUNNING, False, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.SUCCESS, True, NodeStatus.SUCCESS),
        (NodeStatus.FAILURE, NodeStatus.SKIPPED, True, NodeStatus.FAILURE),
        (NodeStatus.FAILURE, NodeStatus.SUCCESS, True, NodeStatus.SUCCESS),
        (NodeStatus.SKIPPED, NodeStatus.SKIPPED, True, NodeStatus.FAILURE),
    ],
)
def test_fallback(
    first: NodeStatus, second: NodeStatus, should_halt: bool, final: NodeStatus
) -> None:
    one, two = _EchoAction(), _EchoAction()
    one.status = first
    two.status = second

    assert Fallback([one, two]).tick() == final
    assert one.halted == should_halt
    assert two.halted == should_halt


@pytest.mark.parametrize(
    "first,second,third,should_halt,final",
    [
        (
            NodeStatus.FAILURE,
            NodeStatus.FAILURE,
            NodeStatus.FAILURE,
            True,
            NodeStatus.FAILURE,
        ),
        (
            NodeStatus.SUCCESS,
            NodeStatus.FAILURE,
            NodeStatus.FAILURE,
            True,
            NodeStatus.SUCCESS,
        ),
        (
            NodeStatus.RUNNING,
            NodeStatus.SUCCESS,
            NodeStatus.FAILURE,
            True,
            NodeStatus.SUCCESS,
        ),
        (
            NodeStatus.FAILURE,
            NodeStatus.RUNNING,
            NodeStatus.SUCCESS,
            True,
            NodeStatus.SUCCESS,
        ),
        (
            NodeStatus.FAILURE,
            NodeStatus.RUNNING,
            NodeStatus.FAILURE,
            False,
            NodeStatus.RUNNING,
        ),
    ],
)
def test_reactive_fallback(
    first: NodeStatus,
    second: NodeStatus,
    third: NodeStatus,
    should_halt: bool,
    final: NodeStatus,
) -> None:
    statuses = (first, second, third)
    echos = [_EchoAction() for _ in statuses]
    for echo, status in zip(echos, statuses, strict=True):
        echo.status = status

    assert ReactiveFallback(list(echos)).tick() == final
    for echo in echos:
        assert echo.halted == should_halt
