from contextlib import contextmanager
from typing import Iterator
from .models.behavior_tree import BehaviorTreeNodeClass
from .layered_dict import LayeredDict


class NodeRegistration:
    __registered_nodes = LayeredDict[str, BehaviorTreeNodeClass]()

    @staticmethod
    def get(name: str) -> BehaviorTreeNodeClass:
        return NodeRegistration.__registered_nodes[name]

    @staticmethod
    def has(name: str) -> bool:
        return name in NodeRegistration.__registered_nodes

    @staticmethod
    def register(Class: BehaviorTreeNodeClass) -> BehaviorTreeNodeClass:
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
