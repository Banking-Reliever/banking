#!/usr/bin/env python3
"""
concat_files.py — Concatenates all ADR, BCM, templates and externals-templates files into a single document.

Recursively traverses the `adr/`, `bcm/`, `templates/` and `externals-templates/` directories to produce
a single file containing all content, with separators indicating the path of each source file.

Usage:
    python tools/concat_files.py                    # Output to stdout
    python tools/concat_files.py -o output.txt      # Write to a file
    python tools/concat_files.py --adr-only         # ADR only
    python tools/concat_files.py --bcm-only         # BCM only
    python tools/concat_files.py --templates-only   # Internal + external templates
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, TextIO


# File extensions to include
VALID_EXTENSIONS = {".md", ".yaml", ".yml"}


def find_files(directory: Path, extensions: set[str] | None = None) -> List[Path]:
    """
    Recursively finds all files with the specified extensions.

    Args:
        directory: Root directory to traverse
        extensions: Extensions to include (e.g. {".md", ".yaml"})

    Returns:
        List of paths sorted alphabetically
    """
    if extensions is None:
        extensions = VALID_EXTENSIONS

    if not directory.exists():
        return []

    files = []
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in extensions:
            # Exclude __pycache__ files
            if "__pycache__" not in str(path):
                files.append(path)

    return sorted(files)


def format_separator(file_path: Path, repo_root: Path) -> str:
    """
    Generates a visual separator for a file.

    Args:
        file_path: Absolute path of the file
        repo_root: Repository root used to display the relative path

    Returns:
        Formatted separator string
    """
    relative_path = file_path.relative_to(repo_root)
    width = 80
    separator_line = "=" * width
    
    return f"""
{separator_line}
FILE: {relative_path}
{separator_line}
"""


def concat_files(
    files: List[Path],
    repo_root: Path,
    output: TextIO
) -> int:
    """
    Concatenates files with separators and writes them to output.

    Args:
        files: List of files to concatenate
        repo_root: Repository root
        output: Output stream (file or stdout)

    Returns:
        Number of files processed
    """
    count = 0

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            separator = format_separator(file_path, repo_root)
            output.write(separator)
            output.write(content)
            if not content.endswith("\n"):
                output.write("\n")
            count += 1
        except Exception as e:
            print(f"WARNING: Error reading {file_path}: {e}", file=sys.stderr)

    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Concatenates ADR, BCM, templates and externals-templates files into a single document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/concat_files.py                    # All to stdout
  python tools/concat_files.py -o context.txt     # Save to a file
  python tools/concat_files.py --adr-only         # ADR only
  python tools/concat_files.py --bcm-only         # BCM only
  python tools/concat_files.py --templates-only   # Templates + externals-templates only
  python tools/concat_files.py --ext .yaml        # YAML only
"""
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output file (default: stdout)"
    )

    parser.add_argument(
        "--adr-only",
        action="store_true",
        help="Concatenate ADR files only"
    )

    parser.add_argument(
        "--bcm-only",
        action="store_true",
        help="Concatenate BCM files only"
    )

    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Concatenate template files only (templates/ + externals-templates/)"
    )

    parser.add_argument(
        "--ext",
        type=str,
        action="append",
        dest="extensions",
        help="Extensions to include (can be repeated, e.g. --ext .yaml --ext .md)"
    )

    parser.add_argument(
        "--no-separator",
        action="store_true",
        help="Disable separators between files"
    )

    args = parser.parse_args()

    # Determine the repository root
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    adr_dir = repo_root / "adr"
    bcm_dir = repo_root / "bcm"
    templates_dir = repo_root / "templates"
    externals_templates_dir = repo_root / "externals-templates"

    # Extensions to use
    extensions = set(args.extensions) if args.extensions else VALID_EXTENSIONS

    # Collect files according to options
    all_files: List[Path] = []

    selected_only_modes = sum([args.adr_only, args.bcm_only, args.templates_only])
    if selected_only_modes > 1:
        parser.error("--adr-only, --bcm-only and --templates-only are mutually exclusive")

    if args.adr_only:
        adr_files = find_files(adr_dir, extensions)
        all_files.extend(adr_files)
    elif args.bcm_only:
        bcm_files = find_files(bcm_dir, extensions)
        all_files.extend(bcm_files)
    elif args.templates_only:
        templates_files = find_files(templates_dir, extensions)
        externals_templates_files = find_files(externals_templates_dir, extensions)
        all_files.extend(templates_files)
        all_files.extend(externals_templates_files)
    else:
        adr_files = find_files(adr_dir, extensions)
        bcm_files = find_files(bcm_dir, extensions)
        templates_files = find_files(templates_dir, extensions)
        externals_templates_files = find_files(externals_templates_dir, extensions)
        all_files.extend(adr_files)
        all_files.extend(bcm_files)
        all_files.extend(templates_files)
        all_files.extend(externals_templates_files)

    if not all_files:
        print("WARNING: No file found.", file=sys.stderr)
        return 1

    # Output
    if args.output:
        output_path = Path(args.output)
        with output_path.open("w", encoding="utf-8") as f:
            count = concat_files(all_files, repo_root, f)
        print(f"[OK] {count} files concatenated into {output_path}", file=sys.stderr)
    else:
        count = concat_files(all_files, repo_root, sys.stdout)
        print(f"\n# Total: {count} files concatenated", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
