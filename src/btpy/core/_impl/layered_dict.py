from typing import Final, Generic, TypeVar, final

_K = TypeVar("_K")
_V = TypeVar("_V")


@final
class LayeredDict(Generic[_K, _V]):
    """
    a dict-like object consisting of multiple layers (scopes),
    where each scope extends the scopes before it
    """

    def __init__(self, parent: "LayeredDict[_K, _V] | None" = None) -> None:
        self.__parent: Final = parent
        self.__items: Final = dict[_K, _V]()

    def has_parent(self) -> bool:
        """whether there is a preceding layer"""
        return self.__parent is not None

    def parent(self) -> "LayeredDict[_K, _V]":
        """get the preceding layer"""
        assert self.__parent is not None
        return self.__parent

    def __getitem__(self, key: _K) -> _V:
        if key in self.__items:
            return self.__items[key]

        if self.has_parent():
            return self.parent()[key]

        raise KeyError(f"'{key}' not found in {self.flatten()}")

    def __setitem__(self, key: _K, value: _V) -> None:
        self.__items[key] = value

    def __contains__(self, key: _K) -> bool:
        return key in self.__items or (self.has_parent() and key in self.parent())

    def flatten(self) -> dict[_K, _V]:
        """flatten to dict"""
        flat = self.parent().flatten() if self.has_parent() else dict[_K, _V]()
        for k, v in self.__items.items():
            flat[k] = v
        return flat
