from dataclasses import dataclass, field
from typing import List, Union

@dataclass
class FunctionParameter:
    value: str

@dataclass
class Parameter:
    value: str = ""
    l: str = ""
    t: str = ""

@dataclass
class Tuple:
    value: List[Union[str, 'Parameter', 'Tuple']] = field(default_factory=list)
    t: str = "tuple"

@dataclass
class Action:
    globalid: str = ""
    id: str = ""
    text: List[Union[str, Parameter, Tuple]] = field(default_factory=list)

@dataclass
class FunctionDeclaration:
    globalid: str = ""
    variable_overrides: List[FunctionParameter] = field(default_factory=list)
    id: str = "6"
    text: List[Union[str, Parameter, Tuple]] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)

@dataclass
class Event:
    globalid: str = ""
    id: str = ""
    text: List[Union[str, Parameter, Tuple]] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)

@dataclass
class Script:
    alias: str = ""
    class_: str = "script"
    content: List[Union[FunctionDeclaration, Event]] = field(default_factory=list)

def to_dict(obj):
    if isinstance(obj, list):
        return [to_dict(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dataclass_fields__'):
        res = {}
        for field_name in obj.__dataclass_fields__:
            val = getattr(obj, field_name)
            key = 'class' if field_name == 'class_' else field_name
            res[key] = to_dict(val)
        return res
    else:
        return obj
