from btpy.builtins.sequences import Sequence
from btpy.node_registration import NodeRegistration


class _FakeNode(Sequence):
    pass


def test_node_registration() -> None:
    name = _FakeNode([]).name()
    assert not NodeRegistration.has(name)
    with NodeRegistration.context():
        NodeRegistration.register(_FakeNode)
        assert NodeRegistration.has(name)
        assert NodeRegistration.get(name) is _FakeNode
    assert not NodeRegistration.has(name)
