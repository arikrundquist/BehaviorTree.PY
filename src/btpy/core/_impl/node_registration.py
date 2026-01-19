from contextlib import contextmanager
from typing import Callable, Iterator, Protocol, TypeVar, overload

from btpy.core._impl.behavior_tree import BehaviorTree
from btpy.core._impl.layered_dict import LayeredDict


class BehaviorTreeFactoryFunction(Protocol):
    """a factory function that instantiates a `BehaviorTree` with children and mapped ports"""

    def __call__(
        self, __children: list[BehaviorTree] | None = None, **ports: str
    ) -> BehaviorTree:
        """instantiate the tree with the specified `__children` and mapped `ports`"""


class BehaviorTreeFactory(BehaviorTreeFactoryFunction, Protocol):
    """a named factory function that instantiates a `BehaviorTree` with children and mapped ports"""

    __name__: str


_BTFF = TypeVar("_BTFF", bound=BehaviorTreeFactoryFunction)
_BTF = TypeVar("_BTF", bound=BehaviorTreeFactory)


class NodeRegistration:
    __registered_nodes = LayeredDict[str, BehaviorTreeFactoryFunction]()

    @staticmethod
    def get(name: str) -> BehaviorTreeFactoryFunction:
        """get the registered factory by `name`"""
        return NodeRegistration.__registered_nodes[name]

    @staticmethod
    def has(name: str) -> bool:
        """check whether a factory has been registered for the given `name`"""
        return name in NodeRegistration.__registered_nodes

    @overload
    @staticmethod
    def register(name: str, factory: _BTFF, /) -> _BTFF:
        """register the `factory` under the given `name`"""

    @overload
    @staticmethod
    def register(name: str, /) -> Callable[[_BTFF], _BTFF]:
        """return a function to register a factory under the given `name`"""

    @overload
    @staticmethod
    def register(factory: _BTF, /) -> _BTF:
        """register the `factory` under its own name"""

    @staticmethod
    def register(
        arg1: str | _BTF, arg2: _BTFF | None = None, /
    ) -> _BTFF | _BTF | Callable[[_BTF], _BTF]:
        if not isinstance(arg1, str):
            return NodeRegistration.register(arg1.__name__, arg1)

        if arg2 is None:
            return lambda arg2: NodeRegistration.register(arg1, arg2)

        assert arg1 not in NodeRegistration.__registered_nodes
        NodeRegistration.__registered_nodes[arg1] = arg2
        return arg2

    @contextmanager
    @staticmethod
    def scope() -> Iterator[None]:
        """
        create a new registration scope context

        useful to temporarily register a factory
        (e.g. for a test) without polluting the global registry
        """
        NodeRegistration.__registered_nodes = LayeredDict(
            NodeRegistration.__registered_nodes
        )

        try:
            yield

        finally:
            NodeRegistration.__registered_nodes = (
                NodeRegistration.__registered_nodes.parent()
            )
