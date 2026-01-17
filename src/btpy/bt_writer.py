from .behavior_tree import BehaviorTree, SubTree


class BTWriter:
    @staticmethod
    def to_xml(tree: SubTree, indent: str | int = "\t") -> str:
        if isinstance(indent, int):
            return BTWriter.to_xml(tree, " " * indent)

        writer = BTWriter()
        subtrees = (node for node in tree if isinstance(node, SubTree))
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="{tree.class_name()}">
{"".join(writer._get_subtree_xml(subtree, indent=indent, level=1) for subtree in subtrees)}</root>
"""

    def __init__(self) -> None:
        self._seen_subtrees = set[str]()

    def _get_port_attrs(self, node: BehaviorTree) -> str:
        return "".join(
            f' {name}="{value}"' for (name, value) in node.mappings().items()
        )

    def _get_subtree_xml(self, tree: SubTree, indent: str, level: int) -> str:
        name = tree.class_name()
        if name in self._seen_subtrees:
            return ""

        self._seen_subtrees.add(name)
        return f"""{indent * level}<BehaviorTree ID="{name}">
{self._to_xml(tree.child(), indent=indent, level=level + 1)}
{indent * level}</BehaviorTree>
"""

    def _to_xml(self, node: BehaviorTree, indent: str, level: int) -> str:
        name = node.class_name()
        attrs = self._get_port_attrs(node)
        children = node.children()

        if isinstance(node, SubTree):
            children = []
            attrs = f' ID="{name}"{attrs}'
            name = "SubTree"

        if len(children) == 0:
            return f"""{indent * level}<{name}{attrs} />"""

        return f"""{indent * level}<{name}{attrs}>
{"\n".join(self._to_xml(child, indent=indent, level=level + 1) for child in children)}
{indent * level}</{name}>"""
