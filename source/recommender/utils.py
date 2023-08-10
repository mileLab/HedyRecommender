from types import GenericAlias
from typing import Union, Type, get_origin, get_args


def convert_type_to_input_str(t: Union[Type, GenericAlias]) -> str:
    origin = get_origin(t)
    if origin is None:
        return get_type_name(t)
    else:
        args = get_args(t)
        # origin,arg1,arg2,arg3,...
        return ','.join([get_type_name(origin)] + [get_type_name(t) for t in args])


def get_type_name(t: Type) -> str:
    return t.__name__.lower()
