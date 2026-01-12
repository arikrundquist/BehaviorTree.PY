from typing import override

from ..models.behavior_tree import BehaviorTreeNode

from ..models.node_status import NodeStatus
from ..behavior_tree import BehaviorTree
from ..node_registration import NodeRegistration


class _Decorator(BehaviorTree):
    def __init__(self, __children: list[BehaviorTreeNode], **ports: str):
        (self.__child,) = __children

    def child(self) -> BehaviorTreeNode:
        return self.__child


@NodeRegistration.register
class Inverter(_Decorator):
    @override
    def tick(self) -> NodeStatus:
        match status := self.child().tick():
            case NodeStatus.SUCCESS:
                return NodeStatus.FAILURE

            case NodeStatus.FAILURE:
                return NodeStatus.SUCCESS

            case _:
                return status


# TODO
# @NodeRegistration.register
# class ForceSuccess(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class ForceFailure(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class Repeat(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class RetryUntilSuccessful(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class KeepRunningUntilFailure(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class Delay(_Decorator):
#     pass


# TODO
# @NodeRegistration.register
# class RunOnce(_Decorator):
#     pass
