from dataclasses import dataclass
from typing import List, Union
from enum import Enum, auto

class BinOperator(Enum):
    Addition = auto()
    Subtraction = auto()
    Multiplication = auto()
    Division = auto()
    Power = auto()
    Dot = auto()
    Comma = auto()

class UnaryOperator(Enum):
    NumeralNegation = auto()
    LogicalNegation = auto()
    CallExpression = auto()

# Literals
class Literal:
    pass

@dataclass
class Integer(Literal):
    value: str

@dataclass
class Float(Literal):
    value: str

@dataclass
class String(Literal):
    value: str

@dataclass
class RawString(Literal):
    value: str

@dataclass
class Bool(Literal):
    value: bool

# Expressions
class Expression:
    pass

@dataclass
class LiteralExpr(Expression):
    literal: Literal

@dataclass
class CWScriptBlockIDExpr(Expression):
    id: str

@dataclass
class IdentifierExpr(Expression):
    name: str

@dataclass
class BinOperationExpr(Expression):
    lhs: Expression
    op: BinOperator
    rhs: Expression

@dataclass
class UnaryOperationExpr(Expression):
    op: UnaryOperator
    expr: Expression

@dataclass
class CallExpr(Expression):
    function: Expression
    arguments: List[Expression]

# Statements
class Statement:
    pass

@dataclass
class ExpressionStatement(Statement):
    expr: Expression

@dataclass
class AssignmentStatement(Statement):
    lhs: Expression
    rhs: Expression

@dataclass
class LinkStatement(Statement):
    path: str

# Attributes
class Attribute:
    pass

@dataclass
class Inline(Attribute):
    pass

@dataclass
class ExportAs(Attribute):
    value: str

# Items
class Item:
    pass

@dataclass
class AttributeItem(Item):
    attribute: Attribute

@dataclass
class FunctionDeclaration:
    name: str
    parameters: List[Expression]
    body: List[Statement]

@dataclass
class FunctionDeclarationItem(Item):
    function: FunctionDeclaration

@dataclass
class Program:
    link_statements: List[Statement]
    main_block: List[Item]
