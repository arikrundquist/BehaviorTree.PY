from typing import Iterator, override

import pytest
from btpy import BehaviorTree, NodeRegistration, NodeStatus


@pytest.fixture(autouse=True)
def registration_scope() -> Iterator[None]:
    with NodeRegistration.scope():
        yield


class _FakeNode(BehaviorTree):
    @override
    def _do_tick(self) -> NodeStatus:
        return NodeStatus.SUCCESS


def test_decorator_node_registration() -> None:
    """test that a node can be registered via a decorator"""
    name = _FakeNode().class_name()
    assert not NodeRegistration.has(name)

    registered = NodeRegistration.register(_FakeNode)
    assert registered is _FakeNode
    assert NodeRegistration.has(name)
    assert NodeRegistration.get(name) is _FakeNode


def test_renamed_decorator_node_registration() -> None:
    """test that a node can be registered under a different name via a decorator"""
    name = _FakeNode().class_name()
    updated_name = f"updated {name}"
    assert not NodeRegistration.has(name)
    assert not NodeRegistration.has(updated_name)

    registered = NodeRegistration.register(updated_name)(_FakeNode)
    assert registered is _FakeNode
    assert not NodeRegistration.has(name)
    assert NodeRegistration.has(updated_name)
    assert NodeRegistration.get(updated_name) is _FakeNode


def test_renamed_node_registration() -> None:
    """test that a node can be registered under a different name without decorator currying"""
    name = _FakeNode().class_name()
    updated_name = f"updated {name}"
    assert not NodeRegistration.has(name)
    assert not NodeRegistration.has(updated_name)

    registered = NodeRegistration.register(updated_name, _FakeNode)
    assert registered is _FakeNode
    assert not NodeRegistration.has(name)
    assert NodeRegistration.has(updated_name)
    assert NodeRegistration.get(updated_name) is _FakeNode
