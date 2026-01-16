from abc import ABC, abstractmethod
from typing import Callable, Final, Iterator, Sequence, final, overload, override

from .models.pointer import Pointer

from .models.node_status import NodeStatus

from .blackboard import Blackboard, BlackboardChildType


from typing import (
    Any,
    Self,
    TypeVar,
)


_T = TypeVar("_T")


class BehaviorTree(ABC):
    def __init__(
        self, __children: list["BehaviorTree"] | None = None, **ports: str
    ) -> None:
        self.__children: Final = __children or []
        self.__ports: Final = ports

        self.init()

    def init(self) -> None:
        self.__blackboard: Blackboard | None = None

    @final
    def children(self) -> Sequence["BehaviorTree"]:
        return self.__children

    @final
    def mappings(self) -> dict[str, str]:
        return self.__ports

    @abstractmethod
    def tick(self) -> NodeStatus:
        pass

    def halt(self) -> None:
        for child in self.children():
            child.halt()

    def name(self) -> str:
        return self.__class__.__name__

    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return parent.create_child(BlackboardChildType.CHILD)

    @final
    def attach_blackboard(self, blackboard: Blackboard) -> Self:
        assert self.__blackboard is None
        self.__blackboard = self.make_blackboard(blackboard)
        Blackboard.remap(blackboard, self.__blackboard, self.mappings())

        for child in self.children():
            child.attach_blackboard(self.__blackboard)

        return self

    @final
    def __iter__(self) -> Iterator["BehaviorTree"]:
        yield self
        for child in self.children():
            yield from child

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

    def get_bool(self, key: str) -> Pointer[bool | None]:
        ptr = self.get(key)
        match ptr.value:
            case "true":
                ptr.value = True

            case "false":
                ptr.value = False

        assert ptr.value is None or isinstance(ptr.value, bool)
        return ptr


class SubTree(BehaviorTree):
    def __init__(self, __name: str, __child: BehaviorTree, **ports: str) -> None:
        super().__init__([__child], **ports)
        self.__name: Final = __name
        self.__child = __child

        autoremap = self.mappings().get("_autoremap", "false")
        assert autoremap in {"true", "false"}
        self.__autoremap = autoremap == "true"

    @override
    def name(self) -> str:
        return self.__name

    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return parent.create_child(
            BlackboardChildType.REMAPPED
            if self.__autoremap
            else BlackboardChildType.CLEAN
        )

    @override
    def tick(self) -> NodeStatus:
        return self.child().tick()

    def child(self) -> BehaviorTree:
        return self.__child


class RootTree(SubTree):
    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return BehaviorTree.make_blackboard(self, parent)
