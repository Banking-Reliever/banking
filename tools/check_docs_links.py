#!/usr/bin/env python3
"""
check_docs_links.py — Markdown link consistency checker.

Checks:
  1) Internal links to files (existing targets)
  2) Markdown anchor links (file.md#anchor or local #anchor)

Usage:
  python tools/check_docs_links.py
  python tools/check_docs_links.py --root .

Return codes:
  0 -> no issue
  1 -> at least one inconsistency detected
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def slugify(title: str) -> str:
    value = title.strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[`*~\[\](){}:;,.!?\"'\\/|+=<>@#$%^&]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def extract_anchors(md_path: Path) -> set[str]:
    text = md_path.read_text(encoding="utf-8")
    anchors: list[str] = []
    counts: dict[str, int] = {}

    for _, heading in HEADING_RE.findall(text):
        base = slugify(heading)
        if not base:
            continue
        suffix_idx = counts.get(base, 0)
        counts[base] = suffix_idx + 1
        anchors.append(base if suffix_idx == 0 else f"{base}-{suffix_idx}")

    return set(anchors)


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "file://", "vscode://"))


def iter_md_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.md"))


def iter_links_with_locations(text: str) -> list[tuple[int, str]]:
    links: list[tuple[int, str]] = []
    in_fenced_code = False
    fence_marker = ""

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.lstrip()

        if not in_fenced_code and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fenced_code = True
            fence_marker = stripped[:3]
            continue

        if in_fenced_code:
            if stripped.startswith(fence_marker):
                in_fenced_code = False
                fence_marker = ""
            continue

        line = INLINE_CODE_RE.sub("", raw_line)
        for match in LINK_RE.finditer(line):
            links.append((line_number, match.group(1)))

    return links


def check_links(root: Path) -> tuple[list[str], list[str]]:
    missing_files: list[str] = []
    broken_anchors: list[str] = []
    anchors_cache: dict[Path, set[str]] = {}

    for src in iter_md_files(root):
        text = src.read_text(encoding="utf-8")
        for line_number, raw_target in iter_links_with_locations(text):
            if is_external(raw_target):
                continue

            target, anchor = raw_target, None
            if "#" in raw_target:
                target, anchor = raw_target.split("#", 1)

            if target == "":
                target_path = src
            else:
                target_path = (src.parent / target).resolve()

            if target and not target_path.exists():
                rel_src = src.relative_to(root)
                missing_files.append(f"{rel_src}:{line_number} -> {target}")
                continue

            if anchor is None:
                continue

            if target_path.suffix.lower() != ".md":
                continue

            if target_path not in anchors_cache:
                anchors_cache[target_path] = extract_anchors(target_path)

            anchor_slug = slugify(anchor)
            if anchor_slug not in anchors_cache[target_path]:
                rel_src = src.relative_to(root)
                rel_target = target_path.relative_to(root)
                broken_anchors.append(
                    f"{rel_src}:{line_number} -> {raw_target} (resolved to {rel_target})"
                )

    return missing_files, broken_anchors


def main() -> int:
    parser = argparse.ArgumentParser(description="Checks the consistency of internal Markdown links.")
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root to analyse (default: .)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[FATAL] Directory not found: {root}")
        return 1

    missing_files, broken_anchors = check_links(root)

    if missing_files:
        print(f"[FAIL] {len(missing_files)} link(s) to missing file(s):")
        for issue in missing_files:
            print(f"  x {issue}")

    if broken_anchors:
        print(f"[FAIL] {len(broken_anchors)} missing anchor(s):")
        for issue in broken_anchors:
            print(f"  x {issue}")

    total = len(missing_files) + len(broken_anchors)
    if total:
        print(f"\n[FAIL] {total} inconsistency(ies) detected")
        return 1

    print("[OK] No broken Markdown link (files + anchors).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
