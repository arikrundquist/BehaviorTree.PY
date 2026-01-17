from abc import abstractmethod
from typing import Final, TypeVar, final, override

from btpy.core import NodeStatus
from btpy.core import BehaviorTree


_T = TypeVar("_T")


class Observer(BehaviorTree):
    __observed: BehaviorTree | None = None

    def __init__(self, node: BehaviorTree) -> None:
        super().__init__([node])
        self.__node: Final = node

    @abstractmethod
    def observe(self, node: BehaviorTree, status: NodeStatus) -> None:
        pass

    @final
    @override
    def tick(self) -> NodeStatus:
        status = self.__node.tick()
        if not isinstance(self.__node, Observer):
            Observer.__observed = self.__node
        assert Observer.__observed is not None
        self.observe(Observer.__observed, status)
        return status
