from pathlib import Path
from typing import Callable, Self
from xml.etree import ElementTree as XML

from btpy.core._impl.behavior_tree import BehaviorTree, RootTree, SubTree
from btpy.core._impl.blackboard import Blackboard
from btpy.core._impl.node_registration import NodeRegistration


class BTParser:
    """loads `BehaviorTree` objects from xml"""

    def __init__(self, *decorators: Callable[[BehaviorTree], BehaviorTree]) -> None:
        """create a `BTParser` that applies `decorators` to each node it constructs"""
        self._main_tree: str | None = None
        self._tree_descriptions = dict[str, XML.Element]()
        self._decorators = decorators

    def parse(self, path: Path, blackboard: Blackboard | None = None) -> RootTree:
        """load a `BehaviorTree` from file"""
        return self._parse(path, first=True).get(
            *self._decorators, global_blackboard=blackboard
        )

    def parse_string(
        self, xml: str, cwd: Path = Path(), blackboard: Blackboard | None = None
    ) -> RootTree:
        """load a `BehaviorTree` from an xml string"""
        return self._parse_string(xml, cwd, first=True).get(
            *self._decorators, global_blackboard=blackboard
        )

    def _parse(self, path: Path, first: bool) -> Self:
        """load the tree description from file"""
        with open(path, "r") as f:
            return self._parse_string(f.read(), path.parent, first=first)

    def _parse_string(self, xml: str, cwd: Path, first: bool) -> Self:
        """load the tree description from an xml string"""
        return self._from_xml(XML.fromstring(xml), cwd, first=first)

    def _from_xml(self, xml: XML.Element, cwd: Path, first: bool) -> Self:
        """load the tree description from an `XML.Element`"""
        assert xml.tag == "root"
        assert xml.attrib["BTCPP_format"] == "4"
        if first:
            self._main_tree = xml.attrib.get("main_tree_to_execute", None)

        for child in xml:
            match child.tag:
                case "BehaviorTree":
                    id = child.attrib["ID"]
                    assert not NodeRegistration.has(id)
                    self._main_tree = self._main_tree or id
                    (self._tree_descriptions[id],) = child

                case "include":
                    assert (
                        "ros_pkg" not in child.attrib
                    ), "ros_pkg is not currently supported"
                    self._parse(cwd / child.attrib["path"], first=False)

                case "TreeNodesModel":
                    pass  # this tag is for tools like Groot

                case _:
                    raise RuntimeError(f"invalid tag: {child.tag}")

        return self

    def get(
        self,
        *decorators: Callable[[BehaviorTree], BehaviorTree],
        global_blackboard: Blackboard | None = None,
    ) -> RootTree:
        """instantiate the loaded tree description"""
        assert self._main_tree is not None
        assert self._main_tree in self._tree_descriptions
        return RootTree(
            self._main_tree,
            self._load(self._tree_descriptions[self._main_tree], *decorators),
        ).attach_blackboard(global_blackboard or Blackboard())

    def _load(
        self, xml: XML.Element, *decorators: Callable[[BehaviorTree], BehaviorTree]
    ) -> BehaviorTree:
        """instantiate the tree from the `xml` description"""
        name = xml.tag
        attrs = xml.attrib.copy()

        if name == "SubTree":
            name = attrs.pop("ID")
            assert len(xml) == 0
            return SubTree(
                name, self._load(self._tree_descriptions[name], *decorators), **attrs
            )

        if name == "Action":
            name = attrs.pop("ID")

        children = [self._load(child, *decorators) for child in xml]
        loaded = NodeRegistration.get(name)(children, **attrs)
        assert loaded.class_name() == name
        for decorator in decorators:
            loaded = decorator(loaded)
        return loaded
