from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Program:
    main_block: List['Item']

    def __init__(self, main_block: List['Item']):
        self.main_block = main_block

@dataclass
class Literal:
    value: str

@dataclass
class Variable:
    name: str

@dataclass
class CWScriptBlockID:
    id: str

# Argument variants
class Argument:
    pass

@dataclass
class RawString(Argument):
    value: str

@dataclass
class LiteralArg(Argument):
    literal: Literal

@dataclass
class IdentifierArg(Argument):
    variable: Variable

# Call variants
class Call:
    pass

@dataclass
class FunctionCall(Call):
    dependencies: List[Call]
    function_name: Variable
    arguments: List[Argument]
    return_var: Optional[Variable] = None

@dataclass
class CWScriptBlockCall(Call):
    dependencies: List[Call]
    block_id: CWScriptBlockID
    arguments: List[Argument]
    return_var: Optional[Variable] = None

@dataclass
class Expression:
    dependencies: List[Call] = field(default_factory=list)
    content: Optional[Argument] = None

@dataclass
class Statement:
    dependencies: List[Call] = field(default_factory=list)
    content: List[Call] = field(default_factory=list)

# Item variants
class Item:
    pass

@dataclass
class FunctionDeclaration(Item):
    name: str
    parameters: List[Variable]
    body: List[Statement]

@dataclass
class Event(Item):
    name: str
    body: List[Statement]
