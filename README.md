# scratch-mcp

MCP server for creating Scratch 3 `.sb3` projects programmatically.

## Run

```bash
python server.py
```

## Tools

- `create_project()` creates an in-memory Scratch project and returns its project ID.
- `add_sprite(project_id, name, svg, ...)` adds a sprite with an SVG costume.
- `add_backdrop(project_id, svg)` adds a stage backdrop.
- `add_variable(project_id, target_id, name, default)` adds a variable.
- `add_block(project_id, target_id, opcode, fields, inputs, ...)` adds a Scratch block.
- `link_next(project_id, target_id, block_id, next_block_id)` links two stack blocks.
- `set_input_block(project_id, target_id, block_id, input_name, provider_block_id)` connects an output block to an input.
- `export_sb3(project_id, output_dir, filename)` writes a `.sb3` file and returns its path.

## Input Values

`add_block` accepts these input value forms:

- numbers, such as `10` or `1.5`, are Scratch numeric literals.
- numeric strings, such as `"10"` or `"-1.5"`, are also numeric literals.
- `lit:<value>` creates an explicit text literal.
- `var:<name>` creates a variable reporter input.
- `block:<id>` references another block explicitly.
- other strings are kept as block IDs for compatibility with older project scripts.
