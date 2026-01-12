from typing import override

import pytest

from btpy.builtins.decorators import Inverter
from btpy.models.behavior_tree import BehaviorTreeNode

from btpy.models.node_status import NodeStatus
from btpy.behavior_tree import BehaviorTree


class _EchoAction(BehaviorTree):
    def __init__(self, __children: list[BehaviorTreeNode], **ports: str):
        super().__init__(__children, **ports)
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
def test_sequence(status: NodeStatus, final: NodeStatus) -> None:
    child = _EchoAction([])
    child.status = status
    assert Inverter([child]).tick() == final
