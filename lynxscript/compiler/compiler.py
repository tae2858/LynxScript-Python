from typing import List, Optional

# import parser and codegen structures
from ..parser import ast as parser_ast
from ..codegen import structures as codegen_struct
from .symbol_table import SymbolTable, SymbolType, ScopeId

class Attribute:
    pass

class InlineAttribute(Attribute):
    pass

class ExportAsAttribute(Attribute):
    def __init__(self, name: str):
        self.name = name

class CompilerState:
    def __init__(self):
        self.attributes: List[Attribute] = []

    def add_attribute(self, attribute: parser_ast.Attribute):
        if isinstance(attribute, parser_ast.Inline):
            self.attributes.append(InlineAttribute())
        elif isinstance(attribute, parser_ast.ExportAs):
            self.attributes.append(ExportAsAttribute(attribute.value))
        else:
            raise ValueError(f"Unknown attribute type: {attribute}")

    def pop_all_attributes(self) -> List[Attribute]:
        attrs = self.attributes
        self.attributes = []
        return attrs

class Compiler:
    def __init__(self, syntax_tree: parser_ast.Program):
        self.syntax_tree = syntax_tree
        self.state = CompilerState()
        self.symbol_table = SymbolTable()
        self.scope_stack: List[ScopeId] = []
        
        root_scope = self.symbol_table.root_scope()
        self.scope_stack.append(root_scope)

    def current_scope(self) -> ScopeId:
        return self.scope_stack[-1]

    def compile(self) -> codegen_struct.Program:
        # Temporarily take out main_block
        main_block = self.syntax_tree.main_block
        self.syntax_tree.main_block = []

        self.register_function_symbols(main_block)

        compiled_items: List[codegen_struct.Item] = []
        for item in main_block:
            compiled_item = self.compile_item(item)
            if compiled_item is not None:
                compiled_items.append(compiled_item)

        # Restore main_block
        self.syntax_tree.main_block = main_block

        return codegen_struct.Program(compiled_items)

    def register_function_symbols(self, items: List[parser_ast.Item]):
        prepass_state = CompilerState()
        root_scope = self.current_scope()
        for item in items:
            if isinstance(item, parser_ast.AttributeItem):
                prepass_state.add_attribute(item.attribute)
            elif isinstance(item, parser_ast.FunctionDeclarationItem):
                func = item.function
                attributes = prepass_state.pop_all_attributes()
                
                export_as = None
                for attr in attributes:
                    if isinstance(attr, ExportAsAttribute):
                        export_as = attr.name
                        break
                
                function_name = export_as if export_as is not None else func.name
                self.symbol_table.add_symbol(root_scope, function_name, SymbolType.Function)

    def compile_item(self, item: parser_ast.Item) -> Optional[codegen_struct.Item]:
        if isinstance(item, parser_ast.AttributeItem):
            self.state.add_attribute(item.attribute)
            return None
        elif isinstance(item, parser_ast.FunctionDeclarationItem):
            func = item.function
            attributes = self.state.pop_all_attributes()

            is_inline = any(isinstance(attr, InlineAttribute) for attr in attributes)
            
            export_as = None
            for attr in attributes:
                if isinstance(attr, ExportAsAttribute):
                    export_as = attr.name
                    break

            function_name = export_as if export_as is not None else func.name
            current_scope = self.current_scope()
            
            symbol = self.symbol_table.find_in_scope(current_scope, function_name)
            if symbol is None:
                raise ValueError("Function should be registered before compilation")
            function_unique_name = symbol.unique_name

            function_scope = self.symbol_table.enter_scope(current_scope)
            self.scope_stack.append(function_scope)

            parameters = []
            for param in func.parameters:
                if isinstance(param, parser_ast.IdentifierExpr):
                    symbol = self.symbol_table.add_symbol(
                        self.current_scope(), param.name, SymbolType.Variable
                    )
                    parameters.append(codegen_struct.Variable(name=symbol.unique_name))
                else:
                    raise NotImplementedError(f"Unsupported parameter type in function declaration: {param}")

            body = []
            for stmt in func.body:
                body.append(self.compile_statement(stmt))

            self.scope_stack.pop()
            self.symbol_table.exit_scope(function_scope)

            return codegen_struct.FunctionDeclaration(
                name=function_unique_name,
                parameters=parameters,
                body=body
            )
        else:
            raise ValueError(f"Unknown item type: {item}")

    def compile_statement(self, stmt: parser_ast.Statement) -> codegen_struct.Statement:
        if isinstance(stmt, parser_ast.ExpressionStatement):
            compiled_expr = self.compile_expression(stmt.expr)
            return codegen_struct.Statement(
                dependencies=compiled_expr.dependencies,
                content=[]
            )
        elif isinstance(stmt, parser_ast.AssignmentStatement):
            raise NotImplementedError(f"Assignment statement compilation to be implemented: {stmt.lhs} = {stmt.rhs}")
        elif isinstance(stmt, parser_ast.LinkStatement):
            raise NotImplementedError(f"Linking CatWeb JSON to object identifiers to be implemented: {stmt.path}")
        else:
            raise ValueError(f"Unknown statement type: {stmt}")

    def compile_expression(self, expr: parser_ast.Expression) -> codegen_struct.Expression:
        if isinstance(expr, parser_ast.LiteralExpr):
            lit = expr.literal
            if isinstance(lit, parser_ast.Bool):
                content = codegen_struct.LiteralArg(
                    literal=codegen_struct.Literal(value=str(lit.value).lower())
                )
            elif isinstance(lit, (parser_ast.Float, parser_ast.Integer, parser_ast.String)):
                content = codegen_struct.LiteralArg(
                    literal=codegen_struct.Literal(value=lit.value)
                )
            elif isinstance(lit, parser_ast.RawString):
                content = codegen_struct.RawString(value=lit.value)
            else:
                raise ValueError(f"Unknown literal type: {lit}")
            
            return codegen_struct.Expression(dependencies=[], content=content)
            
        elif isinstance(expr, parser_ast.IdentifierExpr):
            symbol = self.symbol_table.resolve(self.current_scope(), expr.name)
            if symbol is None:
                raise ValueError(f"Undefined identifier: {expr.name}")
            return codegen_struct.Expression(
                dependencies=[],
                content=codegen_struct.IdentifierArg(
                    variable=codegen_struct.Variable(name=symbol.unique_name)
                )
            )
            
        elif isinstance(expr, parser_ast.CWScriptBlockIDExpr):
            raise NotImplementedError("CWScriptBlockID cannot be read as expressions or values.")
            
        elif isinstance(expr, parser_ast.CallExpr):
            return self.compile_call(expr.function, expr.arguments)
            
        elif isinstance(expr, parser_ast.BinOperationExpr):
            lhs_compiled = self.compile_expression(expr.lhs)
            rhs_compiled = self.compile_expression(expr.rhs)

            if lhs_compiled.content is None:
                raise ValueError("Binary operation expected LHS argument")
            if rhs_compiled.content is None:
                raise ValueError("Binary operation expected RHS argument")

            call = codegen_struct.FunctionCall(
                dependencies=lhs_compiled.dependencies + rhs_compiled.dependencies,
                function_name=codegen_struct.Variable(name=self.map_bin_op(expr.op)),
                arguments=[lhs_compiled.content, rhs_compiled.content],
                return_var=None
            )
            return codegen_struct.Expression(dependencies=[call], content=None)
            
        elif isinstance(expr, parser_ast.UnaryOperationExpr):
            raise NotImplementedError("Unary operations compilation unimplemented")
            
        else:
            raise ValueError(f"Unknown expression type: {expr}")

    def compile_call(self, function: parser_ast.Expression, arguments: List[parser_ast.Expression]) -> codegen_struct.Expression:
        # Compile arguments first
        arg_dependencies = []
        compiled_arguments = []
        
        for arg in arguments:
            dep_expr = self.compile_expression(arg)
            if dep_expr.content is None:
                raise ValueError("Expected argument value")
            arg_dependencies.extend(dep_expr.dependencies)
            compiled_arguments.append(dep_expr.content)

        if isinstance(function, parser_ast.IdentifierExpr):
            symbol = self.symbol_table.resolve(self.current_scope(), function.name)
            if symbol is None:
                raise ValueError(f"Undefined function identifier: {function.name}")
            
            call = codegen_struct.FunctionCall(
                dependencies=arg_dependencies,
                function_name=codegen_struct.Variable(name=symbol.unique_name),
                arguments=compiled_arguments,
                return_var=None
            )
            return codegen_struct.Expression(dependencies=[call], content=None)
            
        elif isinstance(function, parser_ast.CWScriptBlockIDExpr):
            call = codegen_struct.CWScriptBlockCall(
                dependencies=arg_dependencies,
                block_id=codegen_struct.CWScriptBlockID(id=function.id),
                arguments=compiled_arguments,
                return_var=None
            )
            return codegen_struct.Expression(dependencies=[call], content=None)
            
        elif isinstance(function, parser_ast.CallExpr):
            raise NotImplementedError("Function as return value and chained calls are not supported yet.")
        else:
            raise NotImplementedError(f"Unsupported call target in call: {function}")

    @staticmethod
    def map_bin_op(op: parser_ast.BinOperator) -> str:
        if op == parser_ast.BinOperator.Addition:
            return "add"
        elif op == parser_ast.BinOperator.Subtraction:
            return "sub"
        elif op == parser_ast.BinOperator.Multiplication:
            return "mul"
        elif op == parser_ast.BinOperator.Division:
            return "div"
        elif op == parser_ast.BinOperator.Power:
            return "pow"
        else:
            raise ValueError(f"Binary operator {op} cannot be mapped to call signature")
