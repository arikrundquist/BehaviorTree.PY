from abc import abstractmethod
from typing import final, override

from btpy.core import BehaviorTree, NodeStatus


class StatefulActionNode(BehaviorTree):
    @override
    def init(self) -> None:
        super().init()
        self.__started = False

    @final
    @override
    def halt(self) -> None:
        super().halt()
        if self.__started:
            self.on_halted()
            self.__started = False

    @final
    @override
    def _do_tick(self) -> NodeStatus:
        if self.__started:
            return self.on_running()

        self.__started = True
        return self.on_start()

    @abstractmethod
    def on_halted(self) -> None:
        """called when the node is halted"""

    @abstractmethod
    def on_start(self) -> NodeStatus:
        """called when the node starts to tick"""

    @abstractmethod
    def on_running(self) -> NodeStatus:
        """called when the node is ticked while running"""
