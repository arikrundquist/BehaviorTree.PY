from contextlib import contextmanager
from typing import Iterator, Protocol

from btpy.core._impl.behavior_tree import BehaviorTree
from btpy.core._impl.layered_dict import LayeredDict


class BehaviorTreeFactory(Protocol):
    __name__: str

    def __call__(
        self, __children: list[BehaviorTree] | None = None, **ports: str
    ) -> BehaviorTree:
        pass


class NodeRegistration:
    __registered_nodes = LayeredDict[str, BehaviorTreeFactory]()

    @staticmethod
    def get(name: str) -> BehaviorTreeFactory:
        return NodeRegistration.__registered_nodes[name]

    @staticmethod
    def has(name: str) -> bool:
        return name in NodeRegistration.__registered_nodes

    @staticmethod
    def register(factory: BehaviorTreeFactory) -> BehaviorTreeFactory:
        assert factory.__name__ not in NodeRegistration.__registered_nodes
        NodeRegistration.__registered_nodes[factory.__name__] = factory
        return factory

    @contextmanager
    @staticmethod
    def context() -> Iterator[None]:
        NodeRegistration.__registered_nodes = LayeredDict(
            NodeRegistration.__registered_nodes
        )

        try:
            yield

        finally:
            NodeRegistration.__registered_nodes = (
                NodeRegistration.__registered_nodes.parent()
            )
