from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional

class SymbolType(Enum):
    Variable = auto()
    Function = auto()
    Event = auto()
    UIObject = auto()

@dataclass(frozen=True)
class ScopeId:
    value: int

@dataclass
class SymbolRecord:
    original_name: str
    unique_name: str
    symbol_type: SymbolType
    scope_id: ScopeId

@dataclass
class Scope:
    parent: Optional[ScopeId]
    symbols: List[SymbolRecord] = field(default_factory=list)

class SymbolTable:
    def __init__(self):
        root_scope = Scope(parent=None)
        self.scopes: List[Scope] = [root_scope]

    def root_scope(self) -> ScopeId:
        return ScopeId(0)

    def enter_scope(self, parent: ScopeId) -> ScopeId:
        scope_id = ScopeId(len(self.scopes))
        new_scope = Scope(parent=parent)
        self.scopes.append(new_scope)
        return scope_id

    def exit_scope(self, scope_id: ScopeId) -> ScopeId:
        if scope_id.value >= len(self.scopes):
            raise ValueError(f"Invalid scope id: {scope_id.value}")
        scope = self.scopes[scope_id.value]
        if scope.parent is None:
            raise ValueError("Cannot exit root scope")
        return scope.parent

    def add_symbol(self, scope_id: ScopeId, name: str, symbol_type: SymbolType) -> SymbolRecord:
        is_shadowing = self.is_shadowing_name(scope_id, name)
        unique_name = f"{name}__s{scope_id.value}" if is_shadowing else name

        if self.find_in_scope(scope_id, name) is not None:
            raise ValueError(f"Duplicate symbol in scope {scope_id.value}: {name}")

        if scope_id.value >= len(self.scopes):
            raise ValueError(f"Invalid scope id: {scope_id.value}")
        
        scope = self.scopes[scope_id.value]
        record = SymbolRecord(
            original_name=name,
            unique_name=unique_name,
            symbol_type=symbol_type,
            scope_id=scope_id
        )
        scope.symbols.append(record)
        return record

    def find_in_scope(self, scope_id: ScopeId, name: str) -> Optional[SymbolRecord]:
        if scope_id.value >= len(self.scopes):
            return None
        scope = self.scopes[scope_id.value]
        for symbol in scope.symbols:
            if symbol.original_name == name:
                return symbol
        return None

    def resolve(self, scope_id: ScopeId, name: str) -> Optional[SymbolRecord]:
        curr: Optional[ScopeId] = scope_id
        while curr is not None:
            symbol = self.find_in_scope(curr, name)
            if symbol is not None:
                return symbol
            if curr.value >= len(self.scopes):
                break
            curr = self.scopes[curr.value].parent
        return None

    def is_shadowing_name(self, scope_id: ScopeId, name: str) -> bool:
        if scope_id.value >= len(self.scopes):
            return False
        curr: Optional[ScopeId] = self.scopes[scope_id.value].parent
        while curr is not None:
            if self.find_in_scope(curr, name) is not None:
                return True
            if curr.value >= len(self.scopes):
                break
            curr = self.scopes[curr.value].parent
        return False
