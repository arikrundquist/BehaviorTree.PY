import csv
import time
from pathlib import Path
from typing import Callable, Iterator, override

import pytest
from btpy import BehaviorTree, BTParser, NodeRegistration, NodeStatus
from btpy.builtins import Observer


class _RecordingObserver(Observer):
    record = list[tuple[BehaviorTree, NodeStatus]]()

    @override
    def observe(self, node: BehaviorTree, status: NodeStatus) -> None:
        _RecordingObserver.record.append((node, status))


class _PortMappedAction(BehaviorTree):
    def init(self) -> None:
        super().init()
        self._idx = 0

    @override
    def tick(self) -> NodeStatus:
        self._idx = self._idx + 1
        status = self.get(f"_{self._idx}", str).value
        assert status is not None
        return NodeStatus[status]


class _SleepAction(BehaviorTree):
    @override
    def tick(self) -> NodeStatus:
        delay = self.get("sleep_msec", int).value
        if delay is None:
            return NodeStatus.FAILURE
        time.sleep(delay / 1_000)
        return NodeStatus.SUCCESS


@pytest.fixture(autouse=True)
def register_add_action() -> Iterator[None]:
    with NodeRegistration.context():
        NodeRegistration.register(_PortMappedAction)
        NodeRegistration.register(_SleepAction)
        yield


def _integration_test_cases(
    test_case: Path = Path(__file__).parent / "cases",
) -> Iterator[
    tuple[str, int, list[tuple[str, str]], Callable[[list[tuple[str, str]]], None]]
]:
    if not test_case.is_dir():
        return

    for sub_dir in test_case.iterdir():
        yield from _integration_test_cases(sub_dir)

    try:
        with open(test_case / "tree.xml", "r") as f:
            xml = f.read()

        with open(test_case / "tick_count.txt", "r") as f:
            tick_count = int(f.read().strip())

        with open(test_case / "expected_observations.csv", "r") as f:
            expected_observations = [(name, status) for (name, status) in csv.reader(f)]

    except Exception:
        return

    def write_actual_observations(
        actual_observations: list[tuple[str, str]],
        test_case: Path = test_case,
    ) -> None:
        with open(test_case / "expected_observations.csv", "w") as f:
            writer = csv.writer(f)
            for row in actual_observations:
                writer.writerow(row)
            writer.writerow(["needs", "validation"])

    yield xml, tick_count, expected_observations, write_actual_observations


@pytest.mark.parametrize(
    "xml,tick_count,expected_observations,write_back", _integration_test_cases()
)
def test_integration(
    xml: str,
    tick_count: int,
    expected_observations: list[tuple[str, str]],
    write_back: Callable[[list[tuple[str, str]]], None],
) -> None:
    _RecordingObserver.record = []
    tree = BTParser(_RecordingObserver).parse_string(xml)
    for _ in range(tick_count):
        tree.tick()
    actual_observations = [
        (node.name(), status.name) for (node, status) in _RecordingObserver.record
    ]
    if len(expected_observations) == 0:
        write_back(actual_observations)
    assert actual_observations == expected_observations
