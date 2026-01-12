from typing import Final, Sequence, override

from .models.node_status import NodeStatus

from .blackboard import Blackboard


from .models.behavior_tree import BehaviorTreeNode


class BehaviorTree(BehaviorTreeNode):
    def __init__(self, __children: list[BehaviorTreeNode], **ports: str) -> None:
        self.__children: Final = __children
        self.__ports: Final = ports

    @override
    def children(self) -> Sequence["BehaviorTreeNode"]:
        return self.__children

    @override
    def mappings(self) -> dict[str, str]:
        return self.__ports


class SubTree(BehaviorTree):
    def __init__(self, __name: str, __child: BehaviorTreeNode, **ports: str) -> None:
        super().__init__([__child], **ports)
        self.__name: Final = __name
        self.__child = __child

    @override
    def name(self) -> str:
        return self.__name

    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return Blackboard()

    @override
    def tick(self) -> NodeStatus:
        return self.child().tick()

    def child(self) -> BehaviorTreeNode:
        return self.__child


class RootTree(SubTree):
    @override
    def make_blackboard(self, parent: Blackboard) -> Blackboard:
        return BehaviorTree.make_blackboard(self, parent)
