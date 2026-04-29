#!/usr/bin/env python3
"""Verify that the natural language used under sources/ matches the BCM.

The BCM (bcm/) is the source of truth for the project's ubiquitous language.
Any code produced under sources/ (or src/) must be written in the same natural
language as the BCM — no mixing English / French / Spanish across the model
boundary.

Detection is stop-word based: we tokenise text, count occurrences of well-known
short stop-words for each candidate language, and pick the dominant one. This
is intentionally tiny so the validator stays in the "PyYAML only" envelope of
tools/requirements.txt and needs no extra deps in CI.

Exit codes:
  0 — BCM and code agree (or there is no code yet).
  1 — BCM and code disagree.
  2 — BCM language could not be determined.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BCM_DIR = ROOT / "bcm"
SOURCE_DIRS = [ROOT / "sources", ROOT / "src"]
BCM_EXTS = {".yaml", ".yml", ".md"}
SOURCE_EXTS = {
    ".cs", ".fs", ".vb",
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".java", ".kt", ".go", ".rs",
    ".rb", ".php", ".swift",
    ".html", ".htm", ".vue", ".svelte",
    ".css", ".scss",
    ".md", ".txt",
}

STOPWORDS: dict[str, set[str]] = {
    "en": {
        "the", "of", "and", "to", "in", "is", "that", "for", "with", "on",
        "as", "by", "this", "be", "are", "from", "or", "an", "at", "have",
        "has", "it", "not", "but", "they", "we", "you", "their", "our",
        "your", "which", "when", "what", "where", "how", "can", "must",
        "should", "will", "may", "any", "all", "into", "between",
    },
    "fr": {
        "le", "la", "les", "de", "du", "des", "et", "à", "en", "un", "une",
        "dans", "sur", "pour", "avec", "que", "qui", "est", "sont", "par",
        "se", "ne", "pas", "ce", "cette", "ces", "il", "elle", "ils",
        "elles", "nous", "vous", "leur", "leurs", "au", "aux", "ou", "mais",
        "comme", "plus", "si", "sa", "son", "ses", "mon", "ma", "mes",
        "ton", "ta", "tes", "notre", "votre", "être", "avoir",
    },
    "es": {
        "el", "la", "los", "las", "de", "y", "a", "en", "un", "una", "que",
        "es", "son", "por", "con", "para", "del", "al", "se", "no", "su",
        "sus", "como", "pero", "más", "ser", "estar", "este", "esta",
        "estos", "estas", "lo", "le", "les", "yo", "tu", "él", "ella",
    },
}

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+")


def collect_text(roots: list[Path], exts: set[str]) -> str:
    chunks: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in exts:
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    return "\n".join(chunks)


def detect_language(text: str) -> tuple[str | None, dict[str, int]]:
    counts = {lang: 0 for lang in STOPWORDS}
    if not text:
        return None, counts
    for raw in WORD_RE.findall(text):
        token = raw.lower()
        for lang, words in STOPWORDS.items():
            if token in words:
                counts[lang] += 1
    if all(c == 0 for c in counts.values()):
        return None, counts
    return max(counts, key=counts.get), counts


def main() -> int:
    bcm_text = collect_text([BCM_DIR], BCM_EXTS)
    code_text = collect_text(SOURCE_DIRS, SOURCE_EXTS)

    bcm_lang, bcm_counts = detect_language(bcm_text)
    code_lang, code_counts = detect_language(code_text)

    print(f"BCM stop-word counts: {bcm_counts}")
    print(f"Code stop-word counts: {code_counts}")
    print(f"BCM language : {bcm_lang}")
    print(f"Code language: {code_lang}")

    if bcm_lang is None:
        print("ERROR: unable to determine BCM language — bcm/ has no detectable text.", file=sys.stderr)
        return 2

    if code_lang is None:
        print("No source language detected (no code under sources/ or src/). Skipping.")
        return 0

    if bcm_lang != code_lang:
        print(
            f"ERROR: source code is written in '{code_lang}' but the BCM is written in '{bcm_lang}'.\n"
            f"       The code must use the same natural language as the BCM (the ubiquitous-language source of truth).",
            file=sys.stderr,
        )
        return 1

    print(f"OK: code and BCM agree on language ({bcm_lang}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
