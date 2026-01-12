from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Iterator,
    Protocol,
    Self,
    Sequence,
    TypeVar,
    overload,
)

from .pointer import Pointer

from .node_status import NodeStatus

from ..blackboard import Blackboard

_T = TypeVar("_T")


class BehaviorTreeNodeClass(Protocol):
    __name__: str

    def __call__(
        self, __children: list["BehaviorTreeNode"], **ports: str
    ) -> "BehaviorTreeNode":
        pass


class BehaviorTreeNode(ABC):
    __blackboard: Blackboard | None = None

    @abstractmethod
    def children(self) -> Sequence["BehaviorTreeNode"]:
        pass

    @abstractmethod
    def mappings(self) -> dict[str, str]:
        pass

    @abstractmethod
    def tick(self) -> NodeStatus:
        pass

    def halt(self) -> None:
        pass

    def name(self) -> str:
        return self.__class__.__name__

    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return Blackboard(parent)

    def attach_blackboard(self, blackboard: Blackboard) -> Self:
        assert self.__blackboard is None
        self.__blackboard = self.make_blackboard(blackboard)
        Blackboard.remap(blackboard, self.__blackboard, self.mappings())

        for child in self.children():
            child.attach_blackboard(self.__blackboard)

        return self

    @overload
    def get(self, key: str) -> Pointer[Any | None]:
        pass

    @overload
    def get(self, key: str, converter: Callable[[Any], _T]) -> Pointer[_T | None]:
        pass

    def get(
        self, key: str, converter: Callable[[Any], _T] | None = None
    ) -> Pointer[Any | None]:
        assert self.__blackboard is not None
        ptr = self.__blackboard.get(key)
        if ptr.value is not None and converter is not None:
            ptr.value = converter(ptr.value)
        return ptr

    def __iter__(self) -> Iterator["BehaviorTreeNode"]:
        yield self
        for child in self.children():
            yield from child
