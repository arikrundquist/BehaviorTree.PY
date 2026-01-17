from dataclasses import dataclass
from typing import Generic, TypeVar

_T = TypeVar("_T", covariant=True)


@dataclass
class Pointer(Generic[_T]):
    """a reference to a value"""

    value: _T
