from typing import assert_never, override


from btpy.core import NodeStatus
from btpy.core import BehaviorTree
from btpy.core import NodeRegistration


@NodeRegistration.register
class Fallback(BehaviorTree):
    def init(self) -> None:
        super().init()
        self._index = 0

    @override
    def halt(self) -> None:
        super().halt()
        self._index = 0

    @override
    def tick(self) -> NodeStatus:
        for self._index in range(self._index, len(self.children())):
            match self.children()[self._index].tick():
                case NodeStatus.SUCCESS:
                    self.halt()
                    return NodeStatus.SUCCESS

                case NodeStatus.RUNNING:
                    return NodeStatus.RUNNING

                case NodeStatus.SKIPPED | NodeStatus.FAILURE:
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        self.halt()
        return NodeStatus.FAILURE


@NodeRegistration.register
class ReactiveFallback(BehaviorTree):
    @override
    def tick(self) -> NodeStatus:
        status = NodeStatus.FAILURE

        for child in self.children():
            match child.tick():
                case NodeStatus.SUCCESS:
                    self.halt()
                    return NodeStatus.SUCCESS

                case NodeStatus.RUNNING:
                    status = NodeStatus.RUNNING

                case NodeStatus.SKIPPED | NodeStatus.FAILURE:
                    continue

                case _:  # pragma: no cover
                    assert_never(self)

        if status == NodeStatus.FAILURE:
            self.halt()

        return status
