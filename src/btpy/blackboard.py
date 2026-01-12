from typing import Any, Final, TypeVar

from .models.pointer import Pointer


from .layered_dict import LayeredDict

_T = TypeVar("_T")


class Blackboard:
    def __init__(self, parent: "Blackboard | None" = None) -> None:
        self._data: Final[LayeredDict[str, Pointer[Any]]] = LayeredDict(
            None if parent is None else parent._data
        )

    @staticmethod
    def remap(
        parent: "Blackboard", child: "Blackboard", mappings: dict[str, str]
    ) -> None:
        for child_port, mapping in mappings.items():
            if mapping.startswith("{"):
                assert mapping.endswith("}")
                parent_port = mapping[1:-1]
                child._data[child_port] = parent.get(parent_port)

            else:
                child._data[child_port] = Pointer(mapping)

    def get(self, key: str) -> Pointer[Any]:
        if key in self._data:
            return self._data[key]

        root = self._data
        while root.has_parent():
            root = root.parent()

        root[key] = Pointer(None)
        return root[key]

    def set(self, key: str, value: _T) -> _T:
        self.get(key).value = value
        return value
