from contextlib import contextmanager
from typing import Iterator, Protocol

from btpy.core._impl.behavior_tree import BehaviorTree
from btpy.core._impl.layered_dict import LayeredDict


class BehaviorTreeFactory(Protocol):
    """a named factory function that instantiates a `BehaviorTree` with children and mapped ports"""

    __name__: str

    def __call__(
        self, __children: list[BehaviorTree] | None = None, **ports: str
    ) -> BehaviorTree:
        """instantiate the tree with the specified `__children` and mapped `ports`"""


class NodeRegistration:
    __registered_nodes = LayeredDict[str, BehaviorTreeFactory]()

    @staticmethod
    def get(name: str) -> BehaviorTreeFactory:
        """get the registered factory by `name`"""
        return NodeRegistration.__registered_nodes[name]

    @staticmethod
    def has(name: str) -> bool:
        """check whether a factory has been registered for the given `name`"""
        return name in NodeRegistration.__registered_nodes

    @staticmethod
    def register(factory: BehaviorTreeFactory) -> BehaviorTreeFactory:
        """register the `factory`"""
        assert factory.__name__ not in NodeRegistration.__registered_nodes
        NodeRegistration.__registered_nodes[factory.__name__] = factory
        return factory

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
