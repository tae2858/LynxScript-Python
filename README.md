# 🐱 LynxScript (Python Port)

LynxScript is a programming language designed for CatWeb, a Roblox game where users can build website-esque creations.
The LynxScript compiler compiles source code files into a JSON format that can be imported directly into CatWeb.

This project is a complete, architecturally faithful port of the original Rust implementation into Python 3.10+.

## Usage

### Syntax
LynxScript features a syntax familiar to web developers:

```js
// Familiar syntax to web-devs
console.log("Hello, world!");

// In-language standard library definition
#[export_as("console.log")]
function log(arg) {
  // Raw CatWeb block ID calls
  #0(#"", arg);
}
```

### Command Line Interface

You can compile a LynxScript source file to JSON using the following CLI arguments:

```bash
# Compile a LynxScript source file to JSON and output it to output.json
lync --compile ./src/main.lxs --output ./out/output.json

# Or just output the JSON onto the console
lync -c ./src/main.lxs
# (-c is shorthand for --compile, and -o for --output)
```

If you are running directly from the source directory, you can invoke the module via Python:

```bash
python -m lynxscript.main -c <path_to_script>.lxs -o <output_path>.json
```

## Features & Roadmap
- [x] Function declarations
- [x] Event handlers
- [x] Raw CatWeb block ID calls
- [x] In-language standard library implementation
- [ ] Link statement (Importing site JSON files and referencing UI objects)
- [ ] Arbitrary expression compilation (binary, boolean)
- [ ] Return statements
- [ ] If statements
- [ ] Loops
- [ ] Optimizations
  - [ ] Function inlining
  - [ ] Constant folding
  - [ ] Dead code elimination

## Installation

1. Clone the repository.
2. Go to the project directory and install the package in editable mode:
   ```bash
   pip install -e .
   ```
3. You can now use the `lync` command directly in your terminal to compile LynxScript files!

## Development & Testing

### Prerequisites
- Python 3.10 or newer.
- `pytest` for running tests (installed automatically via `requirements.txt` or as dev dependency).

### Running Tests
To run tests (which verify the parser and compiler AST output matches character-for-character with original Rust snapshots):
```bash
pytest
```

---

## License
This project is licensed under the [MIT License](LICENSE).

## Acknowledgments
- Similar project: [catlua](https://github.com/quitism/catlua) also shaped the ecosystem of CatWeb text-based programming languages ✨
- Original Rust implementation by [pickaxe828](https://github.com/pickaxe828).

**Rewritten in Python by Ziad.**
