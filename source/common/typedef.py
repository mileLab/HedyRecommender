import math
from typing import TypeVar, Generic, Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

T = TypeVar('T')


# bug in fastapi doc: https://github.com/tiangolo/fastapi/pull/4126
@dataclass
class Range(Generic[T]):
    min: Optional[T] = Field(default=None, description="Lower bound of a range, if left out corresponds to -infinity")
    max: Optional[T] = Field(default=None, description="Upper bound of a range, if left out corresponds to infinity")

    @staticmethod
    def from_list(inp: list[Optional[T]]):
        return Range(min=inp[0], max=inp[1])

    def __post_init_post_parse__(self):
        if self.min is None:
            self.min = -math.inf
        if self.max is None:
            self.max = math.inf


# due to a bug in fastapi, it cannot handle generics properly
@dataclass
class BaseRange:
    pass


@dataclass
class RangeInt(BaseRange):
    min: Optional[int] = Field(default=None, description="Lower bound of a range, if left out corresponds to -infinity")
    max: Optional[int] = Field(default=None, description="Upper bound of a range, if left out corresponds to infinity")


@dataclass
class RangeFloat(BaseRange):
    min: Optional[float] = Field(default=None,
                                 description="Lower bound of a range, if left out corresponds to -infinity")
    max: Optional[float] = Field(default=None,
                                 description="Upper bound of a range, if left out corresponds to infinity")
