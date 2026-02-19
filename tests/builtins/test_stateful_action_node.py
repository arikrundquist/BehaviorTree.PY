from typing import override

from btpy import NodeStatus, StatefulActionNode


class _StatefulActionNode(StatefulActionNode):
    @override
    def init(self) -> None:
        super().init()
        self.halted = False

    @override
    def on_halted(self) -> None:
        self.halted = True

    @override
    def on_running(self) -> NodeStatus:
        return NodeStatus.SUCCESS

    @override
    def on_start(self) -> NodeStatus:
        return NodeStatus.RUNNING


def test_stateful_action_node() -> None:
    """test the stateful action node"""
    uut = _StatefulActionNode()

    uut.halt()
    assert not uut.halted

    assert uut.tick() == NodeStatus.RUNNING
    assert uut.tick() == NodeStatus.SUCCESS

    assert not uut.halted
    uut.halt()
    assert uut.halted

    assert uut.tick() == NodeStatus.RUNNING
