import json
import shutil
import subprocess
import sys
import tempfile
import typer
from pathlib import Path
from typing import List


app = typer.Typer()


def find_aseprite_binary(aseprite_path: str) -> str:
    binary = shutil.which(aseprite_path)

    if binary is None:
        print(f"Error: Aseprite binary not found: {aseprite_path}", file=sys.stderr)
        print("Please specify the correct path with --aseprite", file=sys.stderr)
        raise typer.Exit(code=1)

    return binary


def run_aseprite_command(cmd: List[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: Aseprite command failed", file=sys.stderr)
        print(f"Command: {' '.join(cmd)}", file=sys.stderr)

        if result.stderr:
            print(f"Error output: {result.stderr}", file=sys.stderr)

        raise typer.Exit(code=1)


def export_combined_sheet(
    aseprite_bin: str,
    input_files: List[Path],
    output_img: Path,
    combined_json: Path
) -> None:
    cmd = [
        aseprite_bin,
        "--batch",
        *[str(f) for f in input_files],
        "--sheet", str(output_img),
        "--data", str(combined_json),
        "--format", "json-array"
    ]

    run_aseprite_command(cmd)


def export_individual_metadata(
    aseprite_bin: str,
    input_file: Path,
    output_json: Path
) -> None:
    cmd = [
        aseprite_bin,
        "--batch",
        str(input_file),
        f"--data={output_json}",
        "--list-tags",
        "--list-slices",
        "--format", "json-array"
    ]
    run_aseprite_command(cmd)


def build_frame_lookup(combined_json_path: Path) -> dict:
    try:
        with open(combined_json_path, 'r') as f:
            data = json.load(f)

        frame_lookup = {}

        for frame in data.get('frames', []):
            filename = frame.get('filename')

            if filename:
                frame_lookup[filename] = frame

        return frame_lookup
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Failed to parse combined JSON: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def process_individual_json(
    basename: str,
    individual_json_path: Path,
    frame_lookup: dict,
    output_path: Path
) -> None:
    try:
        with open(individual_json_path, 'r') as f:
            data = json.load(f)

        frames_count = len(data.get('frames', []))

        for frame_idx in range(frames_count):
            lookup_key = f"{basename} {frame_idx}.aseprite"

            if lookup_key not in frame_lookup:
                print(f"Warning: Frame {lookup_key} not found in combined sheet", file=sys.stderr)
                continue

            combined_frame = frame_lookup[lookup_key]
            data['frames'][frame_idx]['frame'] = combined_frame.get('frame', {})

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: Failed to process {individual_json_path}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def main(
    input_files: List[Path] = typer.Argument(
        ...,
        help="One or more .aseprite files to combine",
        exists=True,
    ),
    output_img: Path = typer.Option(
        ...,
        "--output-img", "-i",
        help="Output PNG path for combined spritesheet"
    ),
    output_data_folder: Path = typer.Option(
        ...,
        "--output-data-folder", "-d",
        help="Output directory for individual JSON metadata files"
    ),
    aseprite: str = typer.Option(
        "aseprite",
        "--aseprite",
        help="Path to aseprite binary (default: 'aseprite' from PATH)"
    )
) -> None:
    aseprite_bin = find_aseprite_binary(aseprite)

    output_data_folder.mkdir(parents=True, exist_ok=True)

    tempdir = Path(tempfile.mkdtemp())

    try:
        combined_json = tempdir / "combined.json"
        print(f"Exporting combined spritesheet to {output_img}...")
        export_combined_sheet(aseprite_bin, input_files, output_img, combined_json)

        frame_lookup = build_frame_lookup(combined_json)

        for input_file in input_files:
            basename = input_file.stem
            individual_json = tempdir / f"{basename}.json"
            output_json = output_data_folder / f"{basename}.json"

            print(f"Processing {input_file.name}...")

            export_individual_metadata(aseprite_bin, input_file, individual_json)
            process_individual_json(basename, individual_json, frame_lookup, output_json)

            print(f"    Created {output_json}")

        print("Done!")

    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    app()
