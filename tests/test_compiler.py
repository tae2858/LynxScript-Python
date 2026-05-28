import os
import pytest
from lynxscript.parser import Parser
from lynxscript.compiler import Compiler, SymbolTable, SymbolType
from lynxscript.codegen import structures as c_ast

# Map Python AST classes to their corresponding Rust names and formatting types
CLASS_MAP = {
    c_ast.Program: ("Program", "struct"),
    c_ast.FunctionDeclaration: ("FunctionDeclaration", "struct"),
    c_ast.Event: ("Event", "struct"),
    c_ast.Statement: ("Statement", "struct"),
    c_ast.Literal: ("Literal", "struct"),
    c_ast.Variable: ("Variable", "struct"),
    c_ast.CWScriptBlockID: ("CWScriptBlockID", "struct"),
    c_ast.CWScriptBlockCall: ("CWScriptBlockCall", "struct"),
    c_ast.FunctionCall: ("FunctionCall", "struct"),
    c_ast.RawString: ("RawString", "tuple_enum"),
    c_ast.LiteralArg: ("Literal", "tuple_enum"),
    c_ast.IdentifierArg: ("Identifier", "tuple_enum"),
}

def rust_debug_format(obj, indent: int = 0) -> str:
    spaces = " " * indent
    next_spaces = " " * (indent + 4)
    
    if isinstance(obj, list):
        if not obj:
            return "[]"
        res = "[\n"
        for item in obj:
            res += f"{next_spaces}{rust_debug_format(item, indent + 4)},\n"
        res += f"{spaces}]"
        return res
        
    if isinstance(obj, str):
        return f'"{obj}"'
        
    if isinstance(obj, bool):
        return "true" if obj else "false"
        
    obj_class = obj.__class__
    if obj_class in CLASS_MAP:
        rust_name, rep_type = CLASS_MAP[obj_class]
        if rep_type == "unit_enum":
            return rust_name
        elif rep_type == "tuple_enum":
            fields = list(obj.__dataclass_fields__.keys())
            val = getattr(obj, fields[0])
            val_str = rust_debug_format(val, indent + 4)
            return f"{rust_name}(\n{next_spaces}{val_str},\n{spaces})"
        elif rep_type == "struct":
            fields = list(obj.__dataclass_fields__.keys())
            if not fields:
                return f"{rust_name} {{}}"
            res = f"{rust_name} {{\n"
            for field in fields:
                val = getattr(obj, field)
                val_str = rust_debug_format(val, indent + 4)
                res += f"{next_spaces}{field}: {val_str},\n"
            res += f"{spaces}}}"
            return res
            
    return str(obj)

def load_rust_snapshot(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---")
    return parts[-1].strip()

def test_simple_function_compiling():
    input_code = """
    #[export_as("c")]
    function add(a, b) {
      #0(#"", "Hello, World!");
    }"""
    
    parser = Parser()
    syntax_tree = parser.parse_program_from_str(input_code)
    
    compiler = Compiler(syntax_tree)
    structure_res = compiler.compile()
    
    actual_formatted = rust_debug_format(structure_res)
    
    # Path to original Rust snapshot
    test_dir = os.path.dirname(os.path.abspath(__file__))
    snap_path = os.path.abspath(os.path.join(
        test_dir, "..", "..", "LynxScript", "src", "compiler", "snapshots",
        "lync__compiler__test__compiler_tests__simple_function_compiling.snap"
    ))
    
    expected_formatted = load_rust_snapshot(snap_path)
    
    assert actual_formatted == expected_formatted

def test_symbol_table_shadowing_mangles():
    table = SymbolTable()
    root_scope = table.root_scope()
    outer = table.add_symbol(root_scope, "x", SymbolType.Variable)
    
    child_scope = table.enter_scope(root_scope)
    inner = table.add_symbol(child_scope, "x", SymbolType.Variable)
    
    assert outer.original_name == "x"
    assert outer.unique_name == "x"
    assert inner.unique_name != "x"
    
    resolved = table.resolve(child_scope, "x")
    assert resolved is not None
    assert resolved.unique_name == inner.unique_name

def test_symbol_table_duplicate_in_scope_errors():
    table = SymbolTable()
    root_scope = table.root_scope()
    table.add_symbol(root_scope, "x", SymbolType.Variable)
    
    with pytest.raises(ValueError):
        table.add_symbol(root_scope, "x", SymbolType.Variable)
