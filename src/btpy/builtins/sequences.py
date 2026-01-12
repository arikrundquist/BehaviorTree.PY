from typing import assert_never, override

from ..models.behavior_tree import BehaviorTreeNode

from ..models.node_status import NodeStatus
from ..behavior_tree import BehaviorTree
from ..node_registration import NodeRegistration


@NodeRegistration.register
class Sequence(BehaviorTree):
    def __init__(self, __children: list[BehaviorTreeNode], **ports: str):
        super().__init__(__children, **ports)
        self._index = 0

    @override
    def tick(self) -> NodeStatus:
        if self._index >= len(self.children()):
            return NodeStatus.SUCCESS

        match self.children()[self._index].tick():
            case NodeStatus.FAILURE:
                return NodeStatus.FAILURE

            case NodeStatus.RUNNING:
                return NodeStatus.RUNNING

            case NodeStatus.SKIPPED | NodeStatus.SUCCESS:
                self._index += 1
                return self.tick()

            case _:  # pragma: no cover
                assert_never(self)


# TODO
# @NodeRegistration.register
# class ReactiveSequence(BehaviorTree):
#     pass

# TODO
# @NodeRegistration.register
# class SequenceWithMemory(BehaviorTree):
#     pass
