import re
from dataclasses import dataclass
from typing import List

from .ast import (
    Program, Item, Attribute, Inline, ExportAs, AttributeItem,
    FunctionDeclaration, FunctionDeclarationItem, Statement,
    ExpressionStatement, AssignmentStatement, LinkStatement,
    Expression, LiteralExpr, CWScriptBlockIDExpr, IdentifierExpr,
    BinOperationExpr, UnaryOperationExpr, CallExpr,
    Literal, Integer, Float, String, RawString, Bool,
    BinOperator, UnaryOperator
)

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int

# Token patterns
TOKEN_SPECIFICATION = [
    ('RAW_STRING', r'#"[^"]*"'),
    ('STRING', r'"[^"]*"'),
    ('FLOAT', r'\d+\.\d+'),
    ('INT', r'\d+'),
    ('CW_BLOCK_ID', r'#\d+'),
    ('ATTR_START', r'#\['),
    ('STAR_STAR', r'\*\*'),
    ('STAR', r'\*'),
    ('PLUS', r'\+'),
    ('MINUS', r'-'),
    ('SLASH', r'/'),
    ('DOT', r'\.'),
    ('COMMA', r','),
    ('BANG', r'!'),
    ('EQUALS', r'='),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('SEMICOLON', r';'),
    ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('WS', r'[ \t\r\n]+'),
    ('COMMENT', r'//[^\n]*'),
    ('MISMATCH', r'.'),
]

KEYWORDS = {"link", "let", "function", "true", "false"}

def tokenize(code: str) -> List[Token]:
    tokens = []
    line_num = 1
    line_start = 0
    
    # Compile regex
    tok_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPECIFICATION)
    
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group(kind)
        column = mo.start() - line_start + 1
        
        if kind == 'WS':
            newlines = value.count('\n')
            if newlines > 0:
                line_num += newlines
                last_nl = value.rfind('\n')
                line_start = mo.start() + last_nl + 1
            continue
        elif kind == 'COMMENT':
            # Comments also end at newline, but the pattern does not consume it.
            # However, if there are newlines, they will be handled by WS.
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f"Unexpected character {value!r} at line {line_num}, col {column}")
        
        if kind == 'IDENTIFIER':
            if value in KEYWORDS:
                kind = value.upper()
        
        tokens.append(Token(kind, value, line_num, column))
    
    tokens.append(Token('EOF', '', line_num, len(code) - line_start + 1))
    return tokens

# Pratt Precedence Constants
PREC_COMMA = 1
PREC_DOT = 2
PREC_ADD_SUB = 3
PREC_MUL_DIV = 4
PREC_POWER = 5
PREC_UNARY = 6
PREC_CALL = 7

class Parser:
    def __init__(self):
        self.tokens: List[Token] = []
        self.pos = 0

    def parse_program_from_str(self, input_str: str) -> Program:
        self.tokens = tokenize(input_str)
        self.pos = 0
        return self.parse_program()

    def peek(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.type != 'EOF':
            self.pos += 1
        return tok

    def consume(self, expected_type: str) -> Token:
        tok = self.peek()
        if tok.type == expected_type:
            return self.advance()
        raise SyntaxError(f"Expected token {expected_type}, got {tok.type} ({tok.value!r}) at line {tok.line}, col {tok.column}")

    def parse_program(self) -> Program:
        # LinkStatementList
        while self.peek().type == 'LINK':
            self.advance()
            self.consume('STRING')
            self.consume('SEMICOLON')
        
        # TopLevelMainBlock (Item*)
        main_block = []
        while self.peek().type != 'EOF':
            main_block.append(self.parse_item())
        
        self.consume('EOF')
        return Program(link_statements=[], main_block=main_block)

    def parse_item(self) -> Item:
        tok = self.peek()
        if tok.type == 'ATTR_START':
            return AttributeItem(attribute=self.parse_attribute())
        elif tok.type == 'FUNCTION':
            return FunctionDeclarationItem(function=self.parse_function_declaration())
        else:
            raise SyntaxError(f"Expected item (attribute or function), got {tok.type} ({tok.value!r}) at line {tok.line}, col {tok.column}")

    def parse_attribute(self) -> Attribute:
        self.consume('ATTR_START')
        name_tok = self.consume('IDENTIFIER')
        name = name_tok.value
        
        content = None
        if self.peek().type == 'LPAREN':
            self.consume('LPAREN')
            str_tok = self.consume('STRING')
            content = str_tok.value[1:-1]  # strip quotes
            self.consume('RPAREN')
        self.consume('RBRACKET')
        
        if name == 'inline':
            return Inline()
        elif name == 'export_as':
            return ExportAs(value=content if content is not None else name)
        else:
            raise SyntaxError(f"Unknown attribute: {name}")

    def parse_function_declaration(self) -> FunctionDeclaration:
        self.consume('FUNCTION')
        name_tok = self.consume('IDENTIFIER')
        name = name_tok.value
        
        self.consume('LPAREN')
        parameters = []
        if self.peek().type != 'RPAREN':
            param_expr = self.parse_expression()
            parameters = self.expand_comma_expression(param_expr)
        self.consume('RPAREN')
        
        body = self.parse_block()
        return FunctionDeclaration(name=name, parameters=parameters, body=body)

    def parse_block(self) -> List[Statement]:
        self.consume('LBRACE')
        body = []
        while self.peek().type != 'RBRACE':
            body.append(self.parse_statement())
        self.consume('RBRACE')
        return body

    def parse_statement(self) -> Statement:
        tok = self.peek()
        if tok.type == 'LET':
            self.advance()
            lhs_tok = self.consume('IDENTIFIER')
            lhs = IdentifierExpr(name=lhs_tok.value)
            self.consume('EQUALS')
            rhs = self.parse_expression()
            self.consume('SEMICOLON')
            return AssignmentStatement(lhs=lhs, rhs=rhs)
        else:
            expr = self.parse_expression()
            if self.peek().type == 'EQUALS':
                self.consume('EQUALS')
                rhs = self.parse_expression()
                self.consume('SEMICOLON')
                return AssignmentStatement(lhs=expr, rhs=rhs)
            else:
                self.consume('SEMICOLON')
                return ExpressionStatement(expr=expr)

    def parse_expression(self, precedence: int = 0) -> Expression:
        tok = self.peek()
        lhs = self.nud(tok)
        
        while True:
            next_tok = self.peek()
            next_prec = self.get_precedence(next_tok)
            if next_prec <= precedence:
                break
            self.advance()  # consume operator
            lhs = self.led(next_tok, lhs)
        return lhs

    def get_precedence(self, tok: Token) -> int:
        if tok.type == 'COMMA':
            return PREC_COMMA
        elif tok.type == 'DOT':
            return PREC_DOT
        elif tok.type in ('PLUS', 'MINUS'):
            return PREC_ADD_SUB
        elif tok.type in ('STAR', 'SLASH'):
            return PREC_MUL_DIV
        elif tok.type == 'STAR_STAR':
            return PREC_POWER
        elif tok.type == 'LPAREN':
            return PREC_CALL
        return 0

    def nud(self, tok: Token) -> Expression:
        self.advance()
        
        if tok.type == 'INT':
            return LiteralExpr(literal=Integer(value=tok.value))
        elif tok.type == 'FLOAT':
            return LiteralExpr(literal=Float(value=tok.value))
        elif tok.type == 'STRING':
            return LiteralExpr(literal=String(value=tok.value[1:-1]))
        elif tok.type == 'RAW_STRING':
            # strip #" from start and " from end
            return LiteralExpr(literal=RawString(value=tok.value[2:-1]))
        elif tok.type == 'TRUE':
            return LiteralExpr(literal=Bool(value=True))
        elif tok.type == 'FALSE':
            return LiteralExpr(literal=Bool(value=False))
        elif tok.type == 'CW_BLOCK_ID':
            return CWScriptBlockIDExpr(id=tok.value[1:])
        elif tok.type == 'IDENTIFIER':
            return IdentifierExpr(name=tok.value)
        elif tok.type == 'MINUS':
            expr = self.parse_expression(PREC_UNARY)
            return UnaryOperationExpr(op=UnaryOperator.NumeralNegation, expr=expr)
        elif tok.type == 'BANG':
            expr = self.parse_expression(PREC_UNARY)
            return UnaryOperationExpr(op=UnaryOperator.LogicalNegation, expr=expr)
        elif tok.type == 'LPAREN':
            expr = self.parse_expression()
            self.consume('RPAREN')
            return expr
        
        raise SyntaxError(f"Expected expression, got {tok.type} ({tok.value!r}) at line {tok.line}, col {tok.column}")

    def led(self, tok: Token, lhs: Expression) -> Expression:
        if tok.type == 'COMMA':
            rhs = self.parse_expression(PREC_COMMA)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Comma, rhs=rhs)
        elif tok.type == 'DOT':
            rhs = self.parse_expression(PREC_DOT)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Dot, rhs=rhs)
        elif tok.type == 'PLUS':
            rhs = self.parse_expression(PREC_ADD_SUB)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Addition, rhs=rhs)
        elif tok.type == 'MINUS':
            rhs = self.parse_expression(PREC_ADD_SUB)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Subtraction, rhs=rhs)
        elif tok.type == 'STAR':
            rhs = self.parse_expression(PREC_MUL_DIV)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Multiplication, rhs=rhs)
        elif tok.type == 'SLASH':
            rhs = self.parse_expression(PREC_MUL_DIV)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Division, rhs=rhs)
        elif tok.type == 'STAR_STAR':
            rhs = self.parse_expression(PREC_POWER)
            return BinOperationExpr(lhs=lhs, op=BinOperator.Power, rhs=rhs)
        elif tok.type == 'LPAREN':
            arguments = []
            if self.peek().type != 'RPAREN':
                arg_expr = self.parse_expression()
                arguments = self.expand_comma_expression(arg_expr)
            self.consume('RPAREN')
            return CallExpr(function=lhs, arguments=arguments)
        
        raise SyntaxError(f"Unexpected operator {tok.value!r} at line {tok.line}")

    def expand_comma_expression(self, expr: Expression) -> List[Expression]:
        if isinstance(expr, BinOperationExpr) and expr.op == BinOperator.Comma:
            return self.expand_comma_expression(expr.lhs) + [expr.rhs]
        return [expr]
