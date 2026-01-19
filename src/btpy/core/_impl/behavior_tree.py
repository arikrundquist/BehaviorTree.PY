from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Final,
    Iterator,
    Self,
    Sequence,
    TypeVar,
    final,
    overload,
    override,
)

from btpy.core._impl.blackboard import Blackboard, BlackboardChildType
from btpy.core._impl.node_status import NodeStatus
from btpy.core._impl.pointer import Pointer

_T = TypeVar("_T")


class BehaviorTree(ABC):
    """a node in a behavior tree"""

    def __init__(
        self, __children: list["BehaviorTree"] | None = None, **ports: str
    ) -> None:
        self.__children: Final = __children or []
        self.__ports: Final = ports

        self.init()

    def init(self) -> None:
        """initialize the node"""
        self.__status: NodeStatus = NodeStatus.SKIPPED
        self.__blackboard: Blackboard | None = None
        self.__halted: bool = False

    @final
    def children(self) -> Sequence["BehaviorTree"]:
        """get the node's children"""
        return self.__children

    @final
    def mappings(self) -> dict[str, str]:
        """get the node's remapped ports"""
        return self.__ports

    @final
    def status(self) -> NodeStatus:
        return self.__status

    @abstractmethod
    def _do_tick(self) -> NodeStatus:
        """tick the node"""
        pass

    @final
    def tick(self) -> NodeStatus:
        """tick the node"""
        self.__halted = False
        self.__status = NodeStatus.RUNNING
        self.__status = self._do_tick()
        return self.__status

    def halt(self) -> None:
        """halt the node"""
        if self.__halted:
            return
        for child in self.children():
            child.halt()
        self.__halted = True

    def class_name(self) -> str:
        """get the name of the node's type"""
        return self.__class__.__name__

    def name(self) -> str:
        """get the name of the node"""
        return self.get("name", str).value or self.class_name()

    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        """create a blackboard suitable for the node to use"""
        return parent.create_child(BlackboardChildType.CHILD)

    @final
    def attach_blackboard(self, blackboard: Blackboard) -> Self:
        """attach the `blackboard` to the node"""
        assert self.__blackboard is None
        self.__blackboard = self.make_blackboard(blackboard)
        Blackboard.remap(blackboard, self.__blackboard, self.mappings())

        for child in self.children():
            child.attach_blackboard(self.__blackboard)

        return self

    @final
    def __iter__(self) -> Iterator["BehaviorTree"]:
        """iterate over all of the nodes in the tree"""
        yield self
        for child in self.children():
            yield from child

    @overload
    def get(self, key: str) -> Pointer[Any | None]:
        """get the value at the specified port"""
        pass

    @overload
    def get(self, key: str, converter: Callable[[Any], _T]) -> Pointer[_T | None]:
        """get the value at the specified port and attempt to convert its type"""
        pass

    def get(
        self, key: str, converter: Callable[[Any], _T] | None = None
    ) -> Pointer[Any | None]:
        if converter is bool:
            return self._get_bool(key)

        assert self.__blackboard is not None
        ptr = self.__blackboard.get(key)
        if ptr.value is not None and converter is not None:
            ptr.value = converter(ptr.value)
        return ptr

    def _get_bool(self, key: str) -> Pointer[bool | None]:
        """get the bool at the specified port"""
        ptr = self.get(key)
        match ptr.value:
            case "true":
                ptr.value = True

            case "false":
                ptr.value = False

        assert ptr.value is None or isinstance(ptr.value, bool)
        return ptr


class SubTree(BehaviorTree):
    """a subtree"""

    def __init__(self, __name: str, __child: BehaviorTree, **ports: str) -> None:
        super().__init__([__child], **ports)
        self.__name: Final = __name
        self.__child = __child

        autoremap = self.mappings().get("_autoremap", "false")
        assert autoremap in {"true", "false"}
        self.__autoremap = autoremap == "true"

    @override
    def class_name(self) -> str:
        """get the name of the subtree"""
        return self.__name

    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        """create a clean blackboard for the subtree"""
        return parent.create_child(
            BlackboardChildType.REMAPPED
            if self.__autoremap
            else BlackboardChildType.CLEAN
        )

    @override
    def _do_tick(self) -> NodeStatus:
        """tick the subtree"""
        return self.child().tick()

    def child(self) -> BehaviorTree:
        """get the root of the subtree"""
        return self.__child


class RootTree(SubTree):
    """a top level subtree"""

    @override
    def _do_tick(self) -> NodeStatus:
        """tick the tree"""
        return super()._do_tick()

    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        """special case: the root tree should not create a clean blackboard"""
        return BehaviorTree.make_blackboard(self, parent)
