from enum import Enum
from typing import Any, Callable, Final, TypeVar, assert_never, overload, override

from btpy.core._impl.pointer import Pointer

_T = TypeVar("_T")


class BlackboardChildType(Enum):
    CHILD = 1
    CLEAN = 2
    REMAPPED = 3


class Blackboard:
    def __init__(
        self,
        parent: "Blackboard | None" = None,
        /,
        *,
        world: "Blackboard | None" = None,
    ) -> None:
        self._stack: Final = parent
        self._world: Final = self._choose_world(parent=parent, world=world)
        self._data: Final = dict[str, Pointer[Any]]()

    def _choose_world(
        self, *, parent: "Blackboard | None", world: "Blackboard | None"
    ) -> "Blackboard":
        if world:
            return world

        if parent:
            return parent._world

        return self

    def create_child(self, type: BlackboardChildType) -> "Blackboard":
        match type:
            case BlackboardChildType.CHILD:
                return Blackboard(self)

            case BlackboardChildType.CLEAN:
                return Blackboard(world=self._world)

            case BlackboardChildType.REMAPPED:
                return _AutoRemapped(self)

            case _:  # pragma: no cover
                assert_never(self)

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

    @overload
    def get(self, key: str) -> Pointer[Any]:
        pass

    @overload
    def get(self, key: str, transform: None) -> Pointer[Any]:
        pass

    @overload
    def get(self, key: str, transform: Callable[[Any], _T]) -> Pointer[_T]:
        pass

    def get(
        self, key: str, transform: Callable[[Any], _T | None] | None = None
    ) -> Pointer[Any]:
        if transform:
            ptr = self.get(key)
            if ptr.value is not None:
                ptr.value = transform(ptr.value)
            return ptr

        if key.startswith("@"):
            return self._world.get(key[1:])

        if key in self._data:
            return self._data[key]

        if self._stack:
            return self._stack.get(key)

        self._data[key] = Pointer(None)
        return self._data[key]

    def set(self, key: str, value: _T) -> _T:
        self.get(key).value = value
        return value


class _AutoRemapped(Blackboard):
    @override
    def get(
        self, key: str, transform: Callable[[Any], _T | None] | None = None
    ) -> Pointer[Any]:
        if key.startswith("_") and key not in self._data:
            self._data[key] = Pointer(None)

        return super().get(key, transform=transform)
