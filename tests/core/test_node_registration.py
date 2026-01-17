from typing import override

from btpy import BehaviorTree, NodeRegistration, NodeStatus


class _FakeNode(BehaviorTree):
    @override
    def tick(self) -> NodeStatus:
        return NodeStatus.SUCCESS


def test_node_registration() -> None:
    """test that a node can be registered"""
    name = _FakeNode().class_name()
    assert not NodeRegistration.has(name)
    with NodeRegistration.scope():
        NodeRegistration.register(_FakeNode)
        assert NodeRegistration.has(name)
        assert NodeRegistration.get(name) is _FakeNode
    assert not NodeRegistration.has(name)
