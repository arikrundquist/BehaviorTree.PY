from typing import override

import pytest

from btpy.builtins.sequences import Sequence
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
    "first,second,final",
    [
        (NodeStatus.FAILURE, NodeStatus.SKIPPED, NodeStatus.FAILURE),
        (NodeStatus.RUNNING, NodeStatus.SKIPPED, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.RUNNING, NodeStatus.RUNNING),
        (NodeStatus.SKIPPED, NodeStatus.SKIPPED, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.SKIPPED, NodeStatus.SUCCESS),
        (NodeStatus.SUCCESS, NodeStatus.SUCCESS, NodeStatus.SUCCESS),
    ],
)
def test_sequence(first: NodeStatus, second: NodeStatus, final: NodeStatus) -> None:
    one, two = _EchoAction([]), _EchoAction([])
    one.status = first
    two.status = second
    assert Sequence([one, two]).tick() == final
