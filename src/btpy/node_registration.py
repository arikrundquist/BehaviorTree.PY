from contextlib import contextmanager
from typing import Iterator, Protocol

from .behavior_tree import BehaviorTree
from .layered_dict import LayeredDict


class _BehaviorTreeClass(Protocol):
    __name__: str

    def __call__(
        self, __children: list[BehaviorTree] | None = None, **ports: str
    ) -> BehaviorTree:
        pass


class NodeRegistration:
    __registered_nodes = LayeredDict[str, _BehaviorTreeClass]()

    @staticmethod
    def get(name: str) -> _BehaviorTreeClass:
        return NodeRegistration.__registered_nodes[name]

    @staticmethod
    def has(name: str) -> bool:
        return name in NodeRegistration.__registered_nodes

    @staticmethod
    def register(Class: _BehaviorTreeClass) -> _BehaviorTreeClass:
        assert Class.__name__ not in NodeRegistration.__registered_nodes
        NodeRegistration.__registered_nodes[Class.__name__] = Class
        return Class

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
