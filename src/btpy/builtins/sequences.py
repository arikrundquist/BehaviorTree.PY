from typing import assert_never, override


from ..models.node_status import NodeStatus
from ..behavior_tree import BehaviorTree
from ..node_registration import NodeRegistration


@NodeRegistration.register
class SequenceWithMemory(BehaviorTree):
    def init(self) -> None:
        super().init()
        self._index = 0

    @override
    def tick(self) -> NodeStatus:
        for self._index in range(self._index, len(self.children())):
            match self.children()[self._index].tick():
                case NodeStatus.FAILURE:
                    self.halt()
                    return NodeStatus.FAILURE

                case NodeStatus.RUNNING:
                    return NodeStatus.RUNNING

                case NodeStatus.SKIPPED | NodeStatus.SUCCESS:
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        self.halt()
        return NodeStatus.SUCCESS


@NodeRegistration.register
class Sequence(SequenceWithMemory):
    @override
    def halt(self) -> None:
        super().halt()
        self._index = 0


@NodeRegistration.register
class ReactiveSequence(BehaviorTree):
    @override
    def tick(self) -> NodeStatus:
        for child in self.children():
            match child.tick():
                case NodeStatus.FAILURE:
                    self.halt()
                    return NodeStatus.FAILURE

                case NodeStatus.RUNNING:
                    return NodeStatus.RUNNING

                case NodeStatus.SKIPPED | NodeStatus.SUCCESS:
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        self.halt()
        return NodeStatus.SUCCESS
