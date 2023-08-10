from dataclasses import dataclass
from typing import Union


class PreferenceTypeRegistry:
    registry: dict[str, dataclass] = {}

    @classmethod
    def register(cls, method: str, input_class: dataclass):
        cls.registry[method] = input_class

    @classmethod
    def get_input_type(cls):
        return Union[tuple(cls.registry.values())]
