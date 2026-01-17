import time
from typing import Iterator, override

import pytest

from btpy.blackboard import Blackboard
from btpy.builtins.decorators import (
    Delay,
    ForceFailure,
    ForceSuccess,
    Inverter,
    KeepRunningUntilFailure,
    Repeat,
    RetryUntilSuccessful,
    RunOnce,
)

from btpy.models.node_status import NodeStatus
from btpy.behavior_tree import BehaviorTree


class _EchoAction(BehaviorTree):
    def init(self) -> None:
        super().init()
        self.status = NodeStatus.SUCCESS

    @override
    def tick(self) -> NodeStatus:
        return self.status


@pytest.mark.parametrize(
    "status,final",
    [
        (NodeStatus.RUNNING, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.SKIPPED),
        (NodeStatus.FAILURE, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.FAILURE),
    ],
)
def test_inverter(status: NodeStatus, final: NodeStatus) -> None:
    child = _EchoAction()
    child.status = status
    assert Inverter([child]).tick() == final


@pytest.mark.parametrize(
    "status,final",
    [
        (NodeStatus.RUNNING, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.SUCCESS),
        (NodeStatus.FAILURE, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.SUCCESS),
    ],
)
def test_force_success(status: NodeStatus, final: NodeStatus) -> None:
    child = _EchoAction()
    child.status = status
    assert ForceSuccess([child]).tick() == final


@pytest.mark.parametrize(
    "status,final",
    [
        (NodeStatus.RUNNING, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.FAILURE),
        (NodeStatus.FAILURE, NodeStatus.FAILURE),
        (NodeStatus.SUCCESS, NodeStatus.FAILURE),
    ],
)
def test_force_failure(status: NodeStatus, final: NodeStatus) -> None:
    child = _EchoAction()
    child.status = status
    assert ForceFailure([child]).tick() == final


class _StatusSequenceAction(BehaviorTree):
    def init(self) -> None:
        super().init()
        self.status_sequence: list[tuple[int, NodeStatus]] = []
        self.status_iterator = self._iterate_sequence()

    def _iterate_sequence(self) -> Iterator[NodeStatus]:
        for count, status in self.status_sequence:
            for _ in range(count):
                yield status

        raise NotImplementedError

    @override
    def tick(self) -> NodeStatus:
        return next(self.status_iterator)


@pytest.mark.parametrize(
    "num_cycles,status_sequence,expected_status",
    [
        (None, [], NodeStatus.FAILURE),
        (-2, [], NodeStatus.FAILURE),
        (5, [(5, NodeStatus.SUCCESS)], NodeStatus.SUCCESS),
        (5, [(1, NodeStatus.FAILURE)], NodeStatus.FAILURE),
        (-1, [(100, NodeStatus.SUCCESS), (1, NodeStatus.RUNNING)], NodeStatus.RUNNING),
    ],
)
def test_repeat(
    num_cycles: int | None,
    status_sequence: list[tuple[int, NodeStatus]],
    expected_status: NodeStatus,
) -> None:
    blackboard = Blackboard()
    blackboard.set("num_cycles", num_cycles)

    child = _StatusSequenceAction()
    child.status_sequence = status_sequence

    uut = Repeat([child]).attach_blackboard(blackboard)
    assert uut.tick() == expected_status


@pytest.mark.parametrize(
    "num_attempts,status_sequence,expected_status",
    [
        (None, [], NodeStatus.FAILURE),
        (-2, [], NodeStatus.FAILURE),
        (5, [(1, NodeStatus.RUNNING)], NodeStatus.RUNNING),
        (5, [(5, NodeStatus.FAILURE)], NodeStatus.FAILURE),
        (-1, [(100, NodeStatus.FAILURE), (1, NodeStatus.SKIPPED)], NodeStatus.SKIPPED),
    ],
)
def test_retry_until_successful(
    num_attempts: int | None,
    status_sequence: list[tuple[int, NodeStatus]],
    expected_status: NodeStatus,
) -> None:
    blackboard = Blackboard()
    blackboard.set("num_attempts", num_attempts)

    child = _StatusSequenceAction()
    child.status_sequence = status_sequence

    uut = RetryUntilSuccessful([child]).attach_blackboard(blackboard)
    assert uut.tick() == expected_status


@pytest.mark.parametrize(
    "child_status,expected_status",
    [
        (NodeStatus.FAILURE, NodeStatus.FAILURE),
        (NodeStatus.SKIPPED, NodeStatus.SKIPPED),
        (NodeStatus.RUNNING, NodeStatus.RUNNING),
        (NodeStatus.SUCCESS, NodeStatus.RUNNING),
    ],
)
def test_keep_running_until_failure(
    child_status: NodeStatus,
    expected_status: NodeStatus,
) -> None:
    echo = _EchoAction()
    echo.status = child_status

    uut = KeepRunningUntilFailure([echo])
    assert uut.tick() == expected_status


@pytest.mark.parametrize(
    "delay_msec,sleep_time,expected_status",
    [
        (None, 0, NodeStatus.FAILURE),
        (1_000_000, 0, NodeStatus.RUNNING),
        (0, 0.01, NodeStatus.SKIPPED),
    ],
)
def test_delay(
    delay_msec: int | None, sleep_time: float, expected_status: NodeStatus
) -> None:
    blackboard = Blackboard()
    blackboard.set("delay_msec", delay_msec)

    echo = _EchoAction()
    echo.status = NodeStatus.SKIPPED

    uut = Delay([echo]).attach_blackboard(blackboard)
    uut.tick()
    time.sleep(sleep_time)
    assert uut.tick() == expected_status


@pytest.mark.parametrize("delay_msec", [10])
def test_halt_delay(delay_msec: int) -> None:
    blackboard = Blackboard()
    blackboard.set("delay_msec", delay_msec)

    echo = _EchoAction()
    echo.status = NodeStatus.SUCCESS

    uut = Delay([echo]).attach_blackboard(blackboard)
    assert uut.tick() == NodeStatus.RUNNING

    time.sleep(delay_msec / 1_000)
    assert uut.tick() == NodeStatus.SUCCESS

    uut.halt()
    assert uut.tick() == NodeStatus.RUNNING


@pytest.mark.parametrize(
    "then_skip,status_sequence,expected_status",
    [
        (False, [NodeStatus.FAILURE, NodeStatus.SUCCESS], NodeStatus.FAILURE),
        ("false", [NodeStatus.SUCCESS, NodeStatus.FAILURE], NodeStatus.SUCCESS),
        ("false", [NodeStatus.RUNNING, NodeStatus.RUNNING], NodeStatus.RUNNING),
        (True, [NodeStatus.FAILURE, NodeStatus.SUCCESS], NodeStatus.SKIPPED),
        ("true", [NodeStatus.SUCCESS, NodeStatus.FAILURE], NodeStatus.SKIPPED),
    ],
)
def test_run_once(
    then_skip: bool | str,
    status_sequence: list[NodeStatus],
    expected_status: NodeStatus,
) -> None:
    blackboard = Blackboard()
    blackboard.set("then_skip", then_skip)

    child = _StatusSequenceAction()
    child.status_sequence = [
        (i + 1, status) for (i, status) in enumerate(status_sequence)
    ]

    uut = RunOnce([child]).attach_blackboard(blackboard)
    uut.tick()

    assert uut.tick() == expected_status
    uut.halt()
    assert uut.tick() == expected_status
