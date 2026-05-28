import argparse
import sys
from .parser import Parser
from .compiler import Compiler
from .codegen import CWBlockScriptGenerator

def main():
    parser = argparse.ArgumentParser(description="LynxScript Compiler")
    parser.add_argument("-c", "--compile", required=True, help="Input file path")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    
    args = parser.parse_args()
    
    try:
        with open(args.compile, "r", encoding="utf-8") as f:
            input_content = f.read()
    except Exception as e:
        print(f"File read error: {e}", file=sys.stderr)
        sys.exit(1)
        
    lxs_parser = Parser()
    try:
        syntax_tree = lxs_parser.parse_program_from_str(input_content)
    except Exception as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)
        
    compiler = Compiler(syntax_tree)
    try:
        program = compiler.compile()
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        sys.exit(1)
        
    generator = CWBlockScriptGenerator()
    try:
        script = generator.generate(program)
    except Exception as e:
        print(f"Codegen error: {e}", file=sys.stderr)
        sys.exit(1)
        
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(script)
        except Exception as e:
            print(f"Failed to write output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(script)

if __name__ == "__main__":
    main()
