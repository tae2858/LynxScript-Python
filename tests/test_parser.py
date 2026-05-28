import os
import pytest
from lynxscript.parser import Parser, ast as p_ast

# Map Python AST classes to their corresponding Rust names and formatting types
CLASS_MAP = {
    p_ast.Program: ("Program", "struct"),
    p_ast.AttributeItem: ("Attribute", "tuple_enum"),
    p_ast.FunctionDeclarationItem: ("FunctionDeclaration", "tuple_enum"),
    p_ast.Inline: ("Inline", "unit_enum"),
    p_ast.ExportAs: ("ExportAs", "tuple_enum"),
    p_ast.FunctionDeclaration: ("FunctionDeclaration", "struct"),
    p_ast.ExpressionStatement: ("Expression", "struct"),
    p_ast.AssignmentStatement: ("Assignment", "struct"),
    p_ast.LinkStatement: ("Link", "struct"),
    p_ast.LiteralExpr: ("Literal", "tuple_enum"),
    p_ast.CWScriptBlockIDExpr: ("CWScriptBlockID", "tuple_enum"),
    p_ast.IdentifierExpr: ("Identifier", "tuple_enum"),
    p_ast.BinOperationExpr: ("BinOperation", "struct"),
    p_ast.UnaryOperationExpr: ("UnaryOperation", "struct"),
    p_ast.CallExpr: ("Call", "struct"),
    p_ast.Integer: ("Integer", "tuple_enum"),
    p_ast.Float: ("Float", "tuple_enum"),
    p_ast.String: ("String", "tuple_enum"),
    p_ast.RawString: ("RawString", "tuple_enum"),
    p_ast.Bool: ("Bool", "tuple_enum"),
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
        
    if isinstance(obj, (p_ast.BinOperator, p_ast.UnaryOperator)):
        return obj.name
        
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

def test_simple_function_parsing():
    input_code = """
    #[export_as("c")]
    function add(a, b) {
      #0(#"", "Hello, World!");
    }"""
    
    parser = Parser()
    syntax_tree = parser.parse_program_from_str(input_code)
    actual_formatted = rust_debug_format(syntax_tree)
    
    # Path to original Rust snapshot
    test_dir = os.path.dirname(os.path.abspath(__file__))
    snap_path = os.path.abspath(os.path.join(
        test_dir, "..", "..", "LynxScript", "src", "parser", "snapshots",
        "lync__parser__test__parser_tests__simple_function_parsing.snap"
    ))
    
    expected_formatted = load_rust_snapshot(snap_path)
    
    assert actual_formatted == expected_formatted
