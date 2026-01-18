from abc import abstractmethod
from contextlib import contextmanager
from typing import Final, Iterator, TypeVar, final, override

from btpy.core import BehaviorTree, NodeStatus

_T = TypeVar("_T")


class Observer(BehaviorTree):
    """a node decorator that observes the status of the non-observer node beneath it"""

    def __init__(self, node: BehaviorTree) -> None:
        super().__init__([node])
        self.__node: Final = node
        self.__observed: Final = self._find_observed()

    def _find_observed(self) -> BehaviorTree:
        """find the first non-observer descendent"""
        return (
            self.__node.__observed if isinstance(self.__node, Observer) else self.__node
        )

    @abstractmethod
    @contextmanager
    def observe(self, node: BehaviorTree) -> Iterator[None]:
        """context for observing the node upon entry and exit"""

    @final
    @override
    def _do_tick(self) -> NodeStatus:
        with self.observe(self.__observed):
            return self.__node.tick()
