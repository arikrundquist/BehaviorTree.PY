# BehaviorTree.PY

A Python implementation of the industry standard [BehaviorTree.CPP](https://www.behaviortree.dev/), published under the same permissive [MIT license](./LICENSE).

---

## Table of Contents

- **[Quick Start](#quick-start)**
  - **[Install](#install-the-package)**
  - **[Run a tree](#run-a-tree)**
- **[Alternatives](#alternatives)**
- **[Features](#features)**
- **[Examples](#examples)**
  - **[Loading a tree](#loading-a-tree-from-an-xml-file-or-string)**
  - **[Serializing a tree](#serializing-a-tree-to-string)**
  - **[Defining custom nodes](#defining-a-custom-node-type)**
  - **[Registering custom nodes](#registering-a-custom-node-type-for-deserialization)**
  - **[Interacting with the blackboard](#interacting-with-the-blackboard)**
  - **[Decorating nodes](#decorating-nodes)**

---

## Quick Start

#### Install the package

```bash
git clone https://github.com/arikrundquist/BehaviorTree.PY
cd BehaviorTree.PY
pip install -e .
```

#### Run a tree

```py
import time
from btpy import BTParser, NodeStatus

description = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Delay delay_msec="500">
      <Sequence name="sequence" />
    </Delay>
  </BehaviorTree>
</root>
""".strip()
tree = BTParser().parse_string(description)

# typically, the tree would be ticked once per frame / cycle
while tree.tick() == NodeStatus.RUNNING:
    print("ticked!")
    time.sleep(0.1)
print("completed with status", tree.status())

# Output:
# ticked!
# ticked!
# ticked!
# ticked!
# ticked!
# completed with status NodeStatus.SUCCESS
```

## Alternatives

- [py_trees](https://py-trees.readthedocs.io/en/devel/): a feature-rich behavior tree framework that is more than sufficient for many use cases. The principal drawback of this library is its apparent lack of support for loading trees from file.
- [pybts](https://pypi.org/project/pybts/): layered on top of `py_trees`, this package adds additional vizualization tools.
- [`BehaviorTree.CPP`](https://www.behaviortree.dev/): of course, if you are willing to write C++, it's hard to beat the original.

While there are other Python behavior tree libraries out there, all seem to lack either 1) static type annotations, 2) support for dynamically loading trees from file, or both. This library stemmed from a need of the the author to find a behavior tree package that met both of these criteria.

## Features

- **Batteries included**: with many built-in nodes (e.g. `Sequence`, `Fallback`, `Delay`, etc) included by default, this package provides a standard implementation for many of the most common behavior tree idioms.
- **Data-driven tree construction**: tree serialization/deserialization to/from XML is a first-class feature of this package, not an ad-hoc add-on. In fact, constructing a tree from XML is the preferred method of tree instantiation, rather than instantiating nodes directly (though that is certainly still an option).
- **User-defined nodes**: custom node types can be easily registered with the core system, allowing user-defined nodes to be loaded during XML deserialization.
- **`BehaviorTree.CPP` compatibility**: due to the de facto dominance of `BehaviorTree.CPP`, this package strives to maintain compatibility with that library. The same XML schema is used, and the built-ins were chosen and implemented to match the core C++ built-ins listed in the [`BehaviorTree.CPP` docs](https://www.behaviortree.dev/docs/category/nodes-library). This means that porting a project over from `BehaviorTree.CPP` to `BehaviorTree.PY` is as simple as porting over your user-defined nodes -- all of your XML tree descriptions remain the same.
- **Powerful and expressive `core`**: this package is organized into two subpackages, `btpy.core` and `btpy.builtins`. The `builtins` package depends only on the public interface of `core`, ensuring the built-in nodes do not have privileged access to any of the internal details of the library. All of this technical speak is just to say that there is nothing special about any of the provided built-ins -- user-created nodes have all of the same features available to them.

## Examples

#### Loading a tree from an XML file or string

```py
from btpy import BTParser

tree = BTParser().parse("/path/to/tree.xml")
tree = BTParser().parse_string("""
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
      <Action ID="MyFirstAction" />
  </BehaviorTree>
</root>
""".strip())
```

#### Serializing a tree to string

```py
from btpy import BTParser
from btpy.core import BTWriter

tree = BTParser().parse("/path/to/tree.xml")
serialized = BTWriter().to_xml(tree)
```

#### Defining a custom node type

A custom node must extend `btpy.BehaviorTree`.

It is **strongly** recommended that custom nodes do not define their own constructor. This is a general rule, and there are good reasons to break it, but be aware that doing so may limit your ability to deserialize that node. Since, however, it is common for nodes to require initialization, the `BehaviorTree` constructor finishes by calling `self.init()`. This is the preferred method in which to place initialization logic.

> ⚠️ **Important!**
>
> In order for a node to be fully initialized, `BehaviorTree.__init__` and `BehaviorTree.init` must both be called. If you choose to override either, you **must** call the corresponding `super` method.

The only method you are required to implement is `_do_tick()`. This should perform the node's logic, potentially calling `tick()` on some of the node's `children()`, and return a `NodeStatus`. You may also need to implement the `halt()` method to cancel any ongoing actions that have not completed.

> 💡 **Note**
>
> `halt()` may be called on a node even if it is not currently running.

```py
from typing import override
from btpy import BehaviorTree, NodeStatus


class UserDefinedNode(BehaviorTree):
    @override
    def init(self) -> None:
        self._times_halted = 0

    @override
    def halt(self) -> None:
        super().halt()
        self._times_halted = self._times_halted + 1

    @override
    def _do_tick(self) -> NodeStatus:
        for child in self.children():
            child.tick()
        return NodeStatus.SUCCESS
```

#### Registering a custom node type for deserialization

In order for a custom node to be deserialized from file, it must first be registered. A custom node type can be registered in one of two ways:

1. Unconditional registration via a decorator

```py
from typing import override
from btpy import BehaviorTree, NodeRegistration, NodeStatus


@NodeRegistration.register
class UserDefinedNode(BehaviorTree):
    @override
    def _do_tick(self) -> NodeStatus:
        return NodeStatus.SUCCESS


@NodeRegistration.register("RenamedNode")
class AnotherUserDefinedNode(BehaviorTree):
    @override
    def _do_tick(self) -> NodeStatus:
        return NodeStatus.SUCCESS


assert NodeRegistration.get("UserDefinedNode") is UserDefinedNode
assert NodeRegistration.get("RenamedNode") is AnotherUserDefinedNode
```

2. Conditional registration via direct function call

```py
nodes_should_be_registered = True
if nodes_should_be_registered:
    NodeRegistration.register(UserDefinedNode)
    NodeRegistration.register("RenamedNode", AnotherUserDefinedNode)

    assert NodeRegistration.get("UserDefinedNode") is UserDefinedNode
    assert NodeRegistration.get("RenamedNode") is AnotherUserDefinedNode
```

Nodes can also be temporarily registered by registering them within a registration scope context (this is intended primarily to allow tests to register nodes without polluting the global registry for other tests):

```py
with NodeRegistration.scope():
    NodeRegistration.register(UserDefinedNode)
    assert NodeRegistration.has("UserDefinedNode")

assert not NodeRegistration.has("UserDefinedNode")
```

#### Interacting with the blackboard

See the `BehaviorTree.CPP` docs for information about the [blackboard](https://www.behaviortree.dev/docs/tutorial-basics/tutorial_02_basic_ports). `BehaviorTree.PY` also supports the [global blackboard idiom](https://www.behaviortree.dev/docs/tutorial-advanced/tutorial_16_global_blackboard).

Nodes access values on the blackboard using the `get(key)` method. This returns a reference to a value, allowing the node to both read and write to that blackboard location. Obviously, there is no way to know statically what value may or may not be present there on the blackboard, so it has type `Any`. When a particular type is expected, the `get` method also accepts a conversion function `(Any) -> T`. This function will be called on the blackboard entry (mutating the blackboard), coercing the blackboard entry to a value of type `T | None` (since there might not have been a value available to convert).

The coercion function should have the following characteristics:

- it should be idempotent, so calling it multiple times on a value should return the value unchanged,
- it should handle conversion from strings (since values on the blackboard may have been loaded as a string from XML).

> 💡 **Note**
>
> The built-in Python types `str`, `int`, and `float` work well here. `bool`, however, does not, since it treats all non-empty strings as truthy. For this reason, there is a special case when `bool` is provided as the conversion function: rather than using the built-in Python `bool` function, the library instead maps `{"true", True} -> True` and `{"false", False} -> False`, erroring on anything else.

```py
from typing import override
from btpy import BehaviorTree, NodeStatus


class UserDefinedNode(BehaviorTree):
    @override
    def _do_tick(self) -> NodeStatus:
        input = self.get("input_port", int).value
        assert input is not None
        self.get("output_port").value = input + 1
        return NodeStatus.SUCCESS
```

#### Decorating nodes

The `BTParser` can accept a sequence of decorators to apply to each node as it parses an XML tree description. Any function `(BehaviorTree) -> BehaviorTree` may be used. Of particular interest may be the `btpy.builtins.Observer`, which can be used as a decorator to gain pre- and post-`tick` hooks for each node in the tree.

```py
from contextlib import contextmanager
from typing import Iterator, override

from btpy import BehaviorTree, BTParser, Blackboard
from btpy.builtins import Observer, Sequence, Fallback


def replace_sequences_with_fallbacks(node: BehaviorTree) -> BehaviorTree:
    if not isinstance(node, Sequence):
        return node

    return Fallback([*node.children()], **node.mappings())


class UserDefinedObserver(Observer):
    @contextmanager
    def observe(self, node: BehaviorTree) -> Iterator[None]:
        print(f"Entering node: {node.name()} (type {node.class_name()})")
        yield
        print(f"Node {node.name()} exited with status:", node.status())


xml = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
      <Sequence name="sequence">
        <Fallback name="fallback" />
      </Sequence>
  </BehaviorTree>
</root>
""".strip()


global_blackboard = Blackboard()
BTParser(replace_sequences_with_fallbacks, UserDefinedObserver).parse_string(
    xml, blackboard=global_blackboard
).tick()

# Output:
# Entering node: sequence (type Fallback)
# Entering node: fallback (type Fallback)
# Node fallback exited with status: NodeStatus.FAILURE
# Node sequence exited with status: NodeStatus.FAILURE
```
