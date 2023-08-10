from dataclasses import dataclass
from typing import Literal, Union


class ParameterTypeRegistry:
    registry: dict[Literal['Demand', 'Supplier'], dict[str, dataclass]] = {'Demand': {}, 'Supplier': {}}

    @classmethod
    def register(cls, method: str, type: Literal['Demand', 'Supplier'], input_class: dataclass):
        cls.registry[type][method] = input_class

    @classmethod
    def get_input_type(cls, type: Literal['Demand', 'Supplier']):
        return Union[tuple(cls.registry[type].values())]
