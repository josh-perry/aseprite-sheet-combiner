# aseprite-sheet-combiner
A utility for combining multiple Aseprite files into a single spritesheet with corrected animation frame positions.

This lets you have loose `.aseprite` files for your assets but still combine them into one spritesheet (for runtime draw performance via batching).

## Usage
To combine multiple files:

```bash
aseprite-sheet-combiner first.aseprite second.aseprite --output-img final.png --output-data-folder ./output --aseprite /bin/aseprite
```

This will give you a combined png (`final.png`) and a json file for each input file (`./output/first.json` and `./output/second.json`). Each output JSON preserves the full structure from Aseprite's export (frames, meta, frameTags, slices, etc.) with frame coordinates updated to reference the combined spritesheet.

### Arguments
- `input_files` - One or more `.aseprite` files to combine (positional arguments)
- `--output-img`, `-i` - Output .png path for the combined spritesheet (required)
- `--output-data-folder`, `-d` - Output directory for individual JSON metadata files (required)
- `--aseprite` - Path to Aseprite binary (optional - defaults to `aseprite` from PATH)

## Development
```bash
uv sync
uv run aseprite-sheet-combiner test1.aseprite test2.aseprite \
  --output-img output.png \
  --output-data-folder ./data
```

## Requirements
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager
- [Aseprite](https://www.aseprite.org/) (installed and accessible via PATH or specified with `--aseprite`)

## Why does this exist?
Aseprite sort of has CLI options for handling multiple files:
```
aseprite --batch first.aseprite second.aseprite --data=data.json --list-tags --list-slices
```

but it merges the data into an unusable mess:
```json
"frameTags": [
  { "name": "Idle", "from": 0, "to": 1, "direction": "forward", "color": "#000000ff" },
  { "name": "Walk", "from": 2, "to": 3, "direction": "forward", "color": "#000000ff" },
  { "name": "Idle", "from": 0, "to": 1, "direction": "forward", "color": "#000000ff" },
  { "name": "Walk", "from": 2, "to": 3, "direction": "forward", "color": "#000000ff" }
],
"slices": [
  { "name": "head", "color": "#0000ffff", "data": "walk frame 1", "keys": [{ "frame": 0, "bounds": {"x": 13, "y": 18, "w": 25, "h": 22 } }] }
]
```

There's no way to know which tag or slice belonged to which input aseprite file.

This utility merges the **images** into a spritesheet but keeps the frame/tag/slice JSON separate and corrects the coordinates to point at the final spritesheet locations.