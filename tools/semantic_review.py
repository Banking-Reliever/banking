#!/usr/bin/env python3
"""
semantic_review.py — Semantic consistency agent for Pull Requests.

Goals:
  1) Verify ADR consistency (ADR phase)
  2) Verify ADR + BCM consistency (ADR+BCM phase)
  3) Produce a Markdown report for the PR description
  4) Return a non-zero exit code in case of major defects

Major defects:
  - any ADR validation error
  - any failure of validate_repo.py
  - any failure of validate_events.py

Usage:
  python tools/semantic_review.py \
    --base-ref <base_sha> \
    --head-ref <head_sha> \
        --scope pr|full \
    --report-file semantic-review.md \
    --json-file semantic-review.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

import yaml


ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "adr"
ADR_INDEX = ADR_DIR / "0000-adr-index.md"

CAPABILITY_ID_RE = re.compile(r"\bCAP\.[A-Z0-9_.-]+\b")
EVENT_ID_RE = re.compile(r"\bEVT\.[A-Z0-9_.-]+\b")
ARCH_ID_RE = re.compile(r"\b(?:CAP|EVT|OBJ|RES|PROC)\.[A-Z0-9_.-]+\b")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class PhaseResult:
    name: str
    status: str  # ok | failed
    major_defects: list[str]
    details: list[str]
    llm: dict | None = None


@dataclass
class LLMReviewResult:
    status: str  # ok | failed
    score: int | None
    summary: str
    major_defects: list[str]
    minor_defects: list[str]
    details: list[str]
    findings: list[dict]
    action_plan: list[dict]


def run_command(name: str, command: list[str]) -> CommandResult:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )


def get_changed_files(base_ref: str | None, head_ref: str | None) -> list[str]:
    if not base_ref or not head_ref:
        return []

    proc = subprocess.run(
        ["git", "-c", "core.quotepath=off", "diff", "--name-only", "-z", f"{base_ref}...{head_ref}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return []

    raw = proc.stdout or b""
    if not raw:
        return []

    return [
        part.decode("utf-8", errors="replace").strip()
        for part in raw.split(b"\0")
        if part.strip()
    ]


def extract_fail_lines(output: str) -> list[str]:
    lines: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("✗") or "[FATAL]" in line or line.startswith("[FAIL]"):
            lines.append(line)
    return lines


def collect_adr_files() -> list[Path]:
    if not ADR_DIR.exists():
        return []
    return sorted(
        p for p in ADR_DIR.glob("ADR-*.md") if p.is_file()
    )


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```") and s.endswith("```"):
        lines = s.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return s


def _parse_llm_json(content: str) -> dict:
    cleaned = _strip_code_fence(content)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Attempt to recover a JSON object embedded in plain text
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def _build_adr_corpus() -> tuple[str, int]:
    adr_files = collect_adr_files()

    max_chars_per_adr_raw = os.getenv("SEMANTIC_LLM_MAX_ADR_CHARS", "3500").strip() or "3500"
    max_total_chars_raw = os.getenv("SEMANTIC_LLM_MAX_TOTAL_CHARS", "50000").strip() or "50000"
    try:
        max_chars_per_adr = max(800, int(max_chars_per_adr_raw))
    except ValueError:
        max_chars_per_adr = 3500
    try:
        max_total_chars = max(5000, int(max_total_chars_raw))
    except ValueError:
        max_total_chars = 50000

    blocks: list[str] = []
    total_chars = 0
    for adr_file in adr_files:
        content = adr_file.read_text(encoding="utf-8")

        if len(content) > max_chars_per_adr:
            content = content[:max_chars_per_adr] + "\n\n[...TRUNCATED FOR LLM TOKEN BUDGET...]\n"

        block = f"\n===== FILE: {adr_file.name} =====\n{content}\n"
        if total_chars + len(block) > max_total_chars:
            remaining = max_total_chars - total_chars
            if remaining > 200:
                block = block[:remaining] + "\n\n[...GLOBAL LLM TOKEN BUDGET REACHED...]\n"
                blocks.append(block)
            break

        blocks.append(block)
        total_chars += len(block)

    return "\n".join(blocks), len(adr_files)


def _normalize_llm_result(parsed: dict) -> tuple[str, int | None, list[str], list[str], list[dict], list[dict]]:
    summary = str(parsed.get("summary", "")).strip() or "Summary unavailable"

    score_raw = parsed.get("score")
    try:
        score = int(score_raw) if score_raw is not None else None
    except (TypeError, ValueError):
        score = None

    findings_raw = parsed.get("findings") or []
    action_plan_raw = parsed.get("action_plan") or []

    findings: list[dict] = []
    if isinstance(findings_raw, list):
        for idx, item in enumerate(findings_raw):
            if not isinstance(item, dict):
                continue
            fid = str(item.get("id", f"F-{idx + 1:03d}")).strip() or f"F-{idx + 1:03d}"
            severity = str(item.get("severity", "minor")).strip().lower()
            if severity not in {"major", "minor"}:
                severity = "minor"

            finding = {
                "id": fid,
                "title": str(item.get("title", "Untitled issue")).strip() or "Untitled issue",
                "severity": severity,
                "category": str(item.get("category", "governance")).strip() or "governance",
                "adr_refs": [str(x).strip() for x in (item.get("adr_refs") or []) if str(x).strip()],
                "evidence": str(item.get("evidence", "")).strip(),
                "rationale": str(item.get("rationale", "")).strip(),
                "impact": str(item.get("impact", "")).strip(),
                "proposed_fix": str(item.get("proposed_fix", "")).strip(),
                "owner_hint": str(item.get("owner_hint", "")).strip(),
                "priority": str(item.get("priority", "P2")).strip() or "P2",
                "effort": str(item.get("effort", "M")).strip() or "M",
            }
            findings.append(finding)

    action_plan: list[dict] = []
    if isinstance(action_plan_raw, list):
        for idx, item in enumerate(action_plan_raw):
            if not isinstance(item, dict):
                continue
            action_plan.append(
                {
                    "id": str(item.get("id", f"A-{idx + 1:03d}")).strip() or f"A-{idx + 1:03d}",
                    "action": str(item.get("action", "")).strip(),
                    "targets": [str(x).strip() for x in (item.get("targets") or []) if str(x).strip()],
                    "severity": str(item.get("severity", "minor")).strip().lower() or "minor",
                    "priority": str(item.get("priority", "P2")).strip() or "P2",
                    "owner_hint": str(item.get("owner_hint", "")).strip(),
                    "due_hint": str(item.get("due_hint", "")).strip(),
                }
            )

    # Backward compatibility: if the model does not return structured findings.
    if not findings:
        major_defects = [str(x).strip() for x in (parsed.get("major_defects") or []) if str(x).strip()]
        minor_defects = [str(x).strip() for x in (parsed.get("minor_defects") or []) if str(x).strip()]
    else:
        major_defects = [f"[{f['id']}] {f['title']}" for f in findings if f.get("severity") == "major"]
        minor_defects = [f"[{f['id']}] {f['title']}" for f in findings if f.get("severity") != "major"]

    return summary, score, major_defects, minor_defects, findings, action_plan


def run_llm_urbanist_review(llm_mode: str) -> LLMReviewResult:
    details: list[str] = []

    if llm_mode == "off":
        return LLMReviewResult(
            status="ok",
            score=None,
            summary="LLM review disabled (off mode).",
            major_defects=[],
            minor_defects=[],
            details=["LLM review: mode off"],
            findings=[],
            action_plan=[],
        )

    api_key = os.getenv("SEMANTIC_LLM_API_KEY", "").strip()
    api_url = os.getenv("SEMANTIC_LLM_API_URL", "").strip() or "https://api.openai.com/v1/chat/completions"
    model = os.getenv("SEMANTIC_LLM_MODEL", "").strip() or "gpt-4.1"
    timeout_raw = os.getenv("SEMANTIC_LLM_TIMEOUT_SECONDS", "120").strip() or "120"
    try:
        timeout_s = int(timeout_raw)
    except ValueError:
        timeout_s = 120

    max_retries_raw = os.getenv("SEMANTIC_LLM_MAX_RETRIES", "3").strip() or "3"
    retry_delay_raw = os.getenv("SEMANTIC_LLM_RETRY_DELAY_SECONDS", "2").strip() or "2"
    try:
        max_retries = max(0, int(max_retries_raw))
    except ValueError:
        max_retries = 3
    try:
        retry_delay_s = max(1.0, float(retry_delay_raw))
    except ValueError:
        retry_delay_s = 2.0

    if not api_key:
        message = (
            "SEMANTIC_LLM_API_KEY missing: cannot launch the SI urbanist LLM agent."
        )
        if llm_mode == "required":
            return LLMReviewResult(
                status="failed",
                score=None,
                summary=message,
                major_defects=[message],
                minor_defects=[],
                details=[],
                findings=[],
                action_plan=[],
            )
        return LLMReviewResult(
            status="ok",
            score=None,
            summary=message,
            major_defects=[],
            minor_defects=[message],
            details=["LLM review: skipped (missing API key, optional mode)"],
            findings=[],
            action_plan=[],
        )

    adr_corpus, adr_count = _build_adr_corpus()
    details.append(f"LLM review: {adr_count} ADRs sent to the model")

    system_prompt = (
        "You are a senior SI urbanist specialised in BCM/ADR governance. "
        "You must evaluate ONLY the semantic consistency between ADRs. "
        "You classify defects as 'major' (blocking contradictions, pivot incompatibilities, structural inconsistencies) "
        "or 'minor' (ambiguities, weak formulations, imprecisions, redundancies). "
        "You must produce actionable outputs for an action plan. "
        "Respond STRICTLY in valid JSON, without markdown, without any text outside JSON."
    )

    user_prompt = (
        "Analyse all the ADRs below and return a JSON with the exact schema:\n"
        "{\n"
        '  "score": <integer 0..100>,\n'
        '  "summary": "<short summary>",\n'
        '  "findings": [\n'
        "    {\n"
        '      "id": "F-001",\n'
        '      "title": "<short title>",\n'
        '      "severity": "major|minor",\n'
        '      "category": "doctrine|governance|traceability|levels|naming|other",\n'
        '      "adr_refs": ["ADR-..."],\n'
        '      "evidence": "<precise quote or extract>",\n'
        '      "rationale": "<why it is inconsistent>",\n'
        '      "impact": "<SI/business/governance impact>",\n'
        '      "proposed_fix": "<concrete corrective action>",\n'
        '      "owner_hint": "<owner profile>",\n'
        '      "priority": "P1|P2|P3",\n'
        '      "effort": "S|M|L"\n'
        "    }\n"
        "  ],\n"
        '  "action_plan": [\n'
        "    {\n"
        '      "id": "A-001",\n'
        '      "action": "<action to execute>",\n'
        '      "targets": ["ADR-..."],\n'
        '      "severity": "major|minor",\n'
        '      "priority": "P1|P2|P3",\n'
        '      "owner_hint": "<owner profile>",\n'
        '      "due_hint": "<time horizon>"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- low score if major contradictions,\n"
        "- each finding must be actionable, specific and linked to ADRs,\n"
        "- propose concrete corrections (no generalities),\n"
        "- limit to 12 findings max, sorted by severity then priority,\n"
        "- if no defect: findings=[] and action_plan=[]\n"
        "ADR corpus:\n"
        f"{adr_corpus}"
    )

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 1600,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    parsed: dict | None = None
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            req = urlrequest.Request(
                api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                method="POST",
            )
            with urlrequest.urlopen(req, timeout=timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            response_payload = json.loads(body)
            message = (response_payload.get("choices") or [{}])[0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, list):
                text_chunks: list[str] = []
                for chunk in content:
                    if isinstance(chunk, dict) and chunk.get("type") == "text":
                        text_chunks.append(str(chunk.get("text", "")))
                content = "\n".join(text_chunks)
            parsed = _parse_llm_json(content)
            break
        except urlerror.HTTPError as exc:
            # 429 = quota/rate limit; retry with exponential backoff.
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""

            last_error = RuntimeError(
                f"HTTP {exc.code} {exc.reason}" + (f" | body={body[:400]}" if body else "")
            )

            if exc.code == 429 and attempt < max_retries:
                sleep_s = retry_delay_s * (2 ** attempt)
                details.append(
                    f"LLM review: rate-limit (429), retrying {attempt + 1}/{max_retries} in {sleep_s:.1f}s"
                )
                time.sleep(sleep_s)
                continue
            break
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt < max_retries:
                sleep_s = retry_delay_s * (2 ** attempt)
                details.append(
                    f"LLM review: invalid JSON received, retrying {attempt + 1}/{max_retries} in {sleep_s:.1f}s"
                )
                time.sleep(sleep_s)
                continue
            break
        except (urlerror.URLError, KeyError, IndexError, ValueError) as exc:
            last_error = exc
            break

    if parsed is None:
        exc = last_error or RuntimeError("unknown failure during LLM call")
        message = f"Error during SI urbanist LLM evaluation: {exc}"
        if llm_mode == "required":
            return LLMReviewResult(
                status="failed",
                score=None,
                summary=message,
                major_defects=[message],
                minor_defects=[],
                details=details,
                findings=[],
                action_plan=[],
            )
        return LLMReviewResult(
            status="ok",
            score=None,
            summary=message,
            major_defects=[],
            minor_defects=[message],
            details=details,
            findings=[],
            action_plan=[],
        )

    summary, score, major_defects, minor_defects, findings, action_plan = _normalize_llm_result(parsed)

    return LLMReviewResult(
        status="failed" if major_defects else "ok",
        score=score,
        summary=summary,
        major_defects=major_defects,
        minor_defects=minor_defects,
        details=details,
        findings=findings,
        action_plan=action_plan,
    )


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def build_changed_candidates(path: str) -> set[str]:
    normalized = normalize_path(path)
    candidates = {normalized}

    p = Path(normalized)
    if p.name:
        candidates.add(p.name)

    for prefix in ("bcm/", "adr/", "externals/"):
        if normalized.startswith(prefix):
            candidates.add(normalized[len(prefix):])

    return {c for c in candidates if c}


def issue_matches_changed_files(issue: str, changed_files: list[str]) -> bool:
    if not changed_files:
        return True

    match = re.search(r"\[([^\]]+)\]", issue)
    if not match:
        return False

    source = normalize_path(match.group(1))
    if not source or source.startswith("cross-"):
        return False

    changed_candidates: set[str] = set()
    for path in changed_files:
        changed_candidates.update(build_changed_candidates(path))

    if source in changed_candidates:
        return True

    for candidate in changed_candidates:
        if source.endswith(candidate) or candidate.endswith(source):
            return True

    return False


def check_adr_structure(changed_files: list[str], full_scope: bool) -> tuple[list[str], list[str]]:
    """Returns (major_defects, details)."""
    major: list[str] = []
    details: list[str] = []

    adr_files = collect_adr_files()
    if not adr_files:
        major.append("No ADR-*.md file found in adr/.")
        return major, details

    changed_adr_rel = [
        path
        for path in changed_files
        if path.startswith("adr/") and path.endswith(".md") and Path(path).name.startswith("ADR-")
    ]
    changed_adr_names = {Path(path).name for path in changed_adr_rel}

    if full_scope:
        changed_adr_rel = [f"adr/{p.name}" for p in adr_files]
        changed_adr_names = {p.name for p in adr_files}

    if not changed_adr_rel and not full_scope:
        details.append("No ADR file modified in this PR (ADR phase in informational mode).")
        details.append("Blocking ADR checks are limited to ADRs modified by the PR.")

    if changed_adr_rel:
        if not ADR_INDEX.exists():
            major.append("ADR index file missing: adr/0000-adr-index.md")
        else:
            idx = ADR_INDEX.read_text(encoding="utf-8")
            missing_in_index: list[str] = []
            for adr_file in adr_files:
                if changed_adr_names and adr_file.name not in changed_adr_names:
                    continue
                if adr_file.name not in idx:
                    missing_in_index.append(adr_file.name)
            if missing_in_index:
                major.append(
                    "ADRs not referenced in the index: " + ", ".join(missing_in_index)
                )

    for adr_file in adr_files:
        if changed_adr_names and adr_file.name not in changed_adr_names:
            continue
        if not changed_adr_names:
            break

        text = adr_file.read_text(encoding="utf-8")
        has_h1 = any(line.startswith("# ") for line in text.splitlines())
        if not has_h1:
            major.append(f"{adr_file.as_posix()}: H1 title (# ...) missing")

        has_status = bool(re.search(r"(?im)^#{2,6}\s+statut\b|^status\s*:\s*", text))
        if not has_status:
            details.append(f"{adr_file.as_posix()}: explicit status section not detected")

    analyzed_count = len(changed_adr_rel) if changed_adr_rel else 0
    details.append(f"ADRs analyzed (blocking scope): {analyzed_count}")
    return major, details


def run_phase_adr(changed_files: list[str], full_scope: bool) -> PhaseResult:
    major, details = check_adr_structure(changed_files, full_scope=full_scope)

    llm_mode = os.getenv("SEMANTIC_LLM_MODE", "required").strip().lower() or "required"
    if llm_mode not in {"required", "optional", "off"}:
        llm_mode = "required"

    llm_review = run_llm_urbanist_review(llm_mode)
    details.extend(llm_review.details)
    details.append(f"LLM SI urbanist: {llm_review.summary}")
    if llm_review.score is not None:
        details.append(f"LLM consistency score: {llm_review.score}/100")
    if llm_review.findings:
        details.append(f"LLM structured findings: {len(llm_review.findings)}")
    if llm_review.action_plan:
        details.append(f"LLM proposed actions: {len(llm_review.action_plan)}")

    for action in llm_review.action_plan[:10]:
        aid = action.get("id", "A-???")
        severity = action.get("severity", "minor")
        priority = action.get("priority", "P2")
        action_text = action.get("action", "")
        targets = ", ".join(action.get("targets", [])[:3]) if isinstance(action.get("targets"), list) else ""
        details.append(f"[LLM-action:{severity}/{priority}] {aid} {action_text} ({targets})".strip())

    for defect in llm_review.major_defects[:50]:
        major.append(f"[LLM-major] {defect}")

    if llm_review.minor_defects:
        details.append(f"LLM minor defects: {len(llm_review.minor_defects)}")
        for defect in llm_review.minor_defects[:20]:
            details.append(f"[LLM-minor] {defect}")

    links = run_command("check_docs_links", [sys.executable, "tools/check_docs_links.py", "--root", "."])
    fail_lines = extract_fail_lines(links.stdout + "\n" + links.stderr)

    changed_adr_rel = [
        path
        for path in changed_files
        if path.startswith("adr/") and path.endswith(".md") and Path(path).name.startswith("ADR-")
    ]
    if full_scope:
        changed_adr_rel = [f"adr/{p.name}" for p in collect_adr_files()]

    adr_fail_lines = [
        line for line in fail_lines
        if "adr/" in line or "ADR" in line or "0000-adr-index" in line
    ]

    if changed_adr_rel:
        adr_fail_lines = [
            line
            for line in adr_fail_lines
            if any(changed_rel in line for changed_rel in changed_adr_rel)
        ]
    else:
        adr_fail_lines = []

    if links.returncode != 0 and adr_fail_lines:
        major.extend([f"Inconsistent ADR links: {line}" for line in adr_fail_lines[:50]])

    if links.returncode != 0 and not adr_fail_lines:
        details.append(
            "Markdown link inconsistencies exist outside ADR (already covered by the links job)."
        )

    status = "failed" if major else "ok"
    return PhaseResult(
        name="ADR",
        status=status,
        major_defects=major,
        details=details,
        llm={
            "mode": llm_mode,
            "score": llm_review.score,
            "summary": llm_review.summary,
            "findings": llm_review.findings,
            "action_plan": llm_review.action_plan,
        },
    )


def run_phase_adr_bcm(changed_files: list[str], full_scope: bool) -> PhaseResult:
    major: list[str] = []
    details: list[str] = []

    repo_check = run_command("validate_repo", [sys.executable, "tools/validate_repo.py"])
    events_check = run_command("validate_events", [sys.executable, "tools/validate_events.py"])

    if repo_check.returncode != 0:
        lines = extract_fail_lines(repo_check.stdout + "\n" + repo_check.stderr)
        if not lines:
            lines = ["validate_repo.py failed with no exploitable detail."]
        if full_scope:
            major.extend([f"validate_repo: {line}" for line in lines[:80]])
        else:
            scoped = [line for line in lines if issue_matches_changed_files(line, changed_files)]
            major.extend([f"validate_repo: {line}" for line in scoped[:80]])
            ignored = len(lines) - len(scoped)
            if ignored > 0:
                details.append(
                    f"validate_repo.py: {ignored} defect(s) outside PR-impacted files ignored"
                )
    else:
        details.append("validate_repo.py: OK")

    if events_check.returncode != 0:
        lines = extract_fail_lines(events_check.stdout + "\n" + events_check.stderr)
        if not lines:
            lines = ["validate_events.py failed with no exploitable detail."]
        if full_scope:
            major.extend([f"validate_events: {line}" for line in lines[:80]])
        else:
            scoped = [line for line in lines if issue_matches_changed_files(line, changed_files)]
            major.extend([f"validate_events: {line}" for line in scoped[:80]])
            ignored = len(lines) - len(scoped)
            if ignored > 0:
                details.append(
                    f"validate_events.py: {ignored} defect(s) outside PR-impacted files ignored"
                )
    else:
        details.append("validate_events.py: OK")

    status = "failed" if major else "ok"
    return PhaseResult(name="ADR + BCM", status=status, major_defects=major, details=details, llm=None)


def collect_changed_adr_files(changed_files: list[str]) -> list[Path]:
    results: list[Path] = []
    for rel_path in changed_files:
        if rel_path.startswith("adr/") and rel_path.endswith(".md") and Path(rel_path).name.startswith("ADR-"):
            p = ROOT / rel_path
            if p.is_file():
                results.append(p)
    return sorted(results)


def collect_changed_yaml_files(changed_files: list[str]) -> list[Path]:
    results: list[Path] = []
    for rel_path in changed_files:
        if not rel_path.endswith(".yaml"):
            continue
        if not (rel_path.startswith("bcm/") or rel_path.startswith("externals/")):
            continue
        p = ROOT / rel_path
        if p.is_file():
            results.append(p)
    return sorted(results)


def parse_adr_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    closing_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break

    if closing_idx is None:
        return {}

    raw = "\n".join(lines[1:closing_idx])
    parsed = yaml.safe_load(raw) or {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def extract_adr_impacted_ids(adr_files: list[Path]) -> tuple[set[str], set[str], list[str]]:
    impacted_capabilities: set[str] = set()
    impacted_events: set[str] = set()
    details: list[str] = []

    for adr_file in adr_files:
        try:
            front_matter = parse_adr_front_matter(adr_file)
        except Exception as exc:
            details.append(f"{adr_file.relative_to(ROOT).as_posix()}: front matter illisible ({exc})")
            continue

        caps = front_matter.get("impacted_capabilities", [])
        evts = front_matter.get("impacted_events", [])

        if isinstance(caps, list):
            for value in caps:
                if isinstance(value, str) and value.strip():
                    impacted_capabilities.add(value.strip())
        if isinstance(evts, list):
            for value in evts:
                if isinstance(value, str) and value.strip():
                    impacted_events.add(value.strip())

    return impacted_capabilities, impacted_events, details


def extract_ids_from_yaml_value(value: object) -> tuple[set[str], set[str]]:
    caps: set[str] = set()
    evts: set[str] = set()

    if isinstance(value, dict):
        for nested in value.values():
            nested_caps, nested_evts = extract_ids_from_yaml_value(nested)
            caps.update(nested_caps)
            evts.update(nested_evts)
    elif isinstance(value, list):
        for nested in value:
            nested_caps, nested_evts = extract_ids_from_yaml_value(nested)
            caps.update(nested_caps)
            evts.update(nested_evts)
    elif isinstance(value, str):
        caps.update(CAPABILITY_ID_RE.findall(value))
        evts.update(EVENT_ID_RE.findall(value))

    return caps, evts


def extract_arch_ids_from_yaml_value(value: object) -> set[str]:
    ids: set[str] = set()

    if isinstance(value, dict):
        for nested in value.values():
            ids.update(extract_arch_ids_from_yaml_value(nested))
    elif isinstance(value, list):
        for nested in value:
            ids.update(extract_arch_ids_from_yaml_value(nested))
    elif isinstance(value, str):
        ids.update(ARCH_ID_RE.findall(value))

    return ids


def extract_yaml_ids(yaml_file: Path) -> tuple[set[str], set[str], str | None]:
    try:
        parsed = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return set(), set(), f"{yaml_file.relative_to(ROOT).as_posix()}: YAML invalide ({exc})"

    if parsed is None:
        return set(), set(), None

    caps, evts = extract_ids_from_yaml_value(parsed)
    return caps, evts, None


def extract_yaml_arch_ids(yaml_file: Path) -> tuple[set[str], str | None]:
    try:
        parsed = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return set(), f"{yaml_file.relative_to(ROOT).as_posix()}: YAML invalide ({exc})"

    if parsed is None:
        return set(), None

    return extract_arch_ids_from_yaml_value(parsed), None


def collect_all_repo_yaml_files() -> list[Path]:
    yaml_files: list[Path] = []
    for base in (ROOT / "bcm", ROOT / "externals"):
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.yaml")):
            if path.name.startswith("template-"):
                continue
            yaml_files.append(path)
    return yaml_files


def is_concept_metier_yaml(yaml_file: Path) -> bool:
    rel = yaml_file.relative_to(ROOT).as_posix()
    return rel.startswith("bcm/concept-metier/")


def is_processus_ressource_yaml(yaml_file: Path) -> bool:
    rel = yaml_file.relative_to(ROOT).as_posix()
    return rel.startswith("externals/processus-ressource/")


def strip_front_matter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text

    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :])

    return text


def extract_new_decision_ids_from_adr(adr_file: Path) -> set[str]:
    text = strip_front_matter(adr_file.read_text(encoding="utf-8"))
    lines = text.splitlines()

    ids: set[str] = set()
    in_new_section = False

    for raw_line in lines:
        line = raw_line.strip()
        lower = line.lower()

        if line.startswith("##"):
            in_new_section = any(keyword in lower for keyword in ("new", "introduce"))

        if not line:
            continue

        contextual = in_new_section or any(
            keyword in lower
            for keyword in (
                "recommended to introduce",
                "recommends introducing",
                "to introduce",
                "introduce",
                "new",
            )
        )

        if contextual:
            ids.update(ARCH_ID_RE.findall(line))

    return ids


def run_phase_adr_yaml(changed_files: list[str], full_scope: bool) -> PhaseResult:
    major: list[str] = []
    details: list[str] = []

    adr_files_to_check = collect_adr_files() if full_scope else collect_changed_adr_files(changed_files)
    yaml_files_to_check = collect_all_repo_yaml_files() if full_scope else collect_changed_yaml_files(changed_files)

    if not full_scope and not adr_files_to_check and not yaml_files_to_check:
        details.append("No ADR or YAML (bcm/externals) modified in the PR for the ADR↔YAML check.")
        return PhaseResult(name="ADR ↔ YAML", status="ok", major_defects=major, details=details, llm=None)

    if not full_scope and yaml_files_to_check and not adr_files_to_check:
        major.append(
            "YAML files under bcm/ or externals/ are modified without any ADR modified in the PR. "
            "Add/adjust an ADR to trace the decision."
        )

    adr_caps, adr_evts, parse_details = extract_adr_impacted_ids(adr_files_to_check)
    details.extend(parse_details)

    if full_scope:
        details.append(f"ADRs analyzed (full scope): {len(adr_files_to_check)}")
        details.append(f"bcm/externals YAML analyzed (full scope): {len(yaml_files_to_check)}")
    else:
        details.append(f"Modified ADRs analyzed: {len(adr_files_to_check)}")
        details.append(f"Modified bcm/externals YAML analyzed: {len(yaml_files_to_check)}")
    details.append(f"Capability IDs declared by ADR: {len(adr_caps)}")
    details.append(f"Event IDs declared by ADR: {len(adr_evts)}")

    if not full_scope and yaml_files_to_check and adr_files_to_check and not adr_caps and not adr_evts:
        major.append(
            "Modified ADRs expose no impacted_capabilities/impacted_events while bcm/externals YAML files are modified."
        )

    linked_yaml_files = 0
    yaml_files_requiring_overlap = 0

    for yaml_file in yaml_files_to_check:
        yaml_caps, yaml_evts, err = extract_yaml_ids(yaml_file)
        rel = yaml_file.relative_to(ROOT).as_posix()

        if err:
            major.append(err)
            continue

        if is_concept_metier_yaml(yaml_file):
            if not full_scope:
                details.append(
                    f"{rel}: CAP/EVT check skipped (canonical business concept, CAP/EVT references not required)."
                )
            continue

        if is_processus_ressource_yaml(yaml_file):
            if not full_scope:
                details.append(
                    f"{rel}: CAP/EVT check skipped (resource process outside ADR traceability scope)."
                )
            continue

        yaml_files_requiring_overlap += 1

        overlap_caps = sorted(yaml_caps.intersection(adr_caps))
        overlap_evts = sorted(yaml_evts.intersection(adr_evts))
        has_overlap = bool(overlap_caps or overlap_evts)

        if has_overlap:
            linked_yaml_files += 1
            if not full_scope:
                details.append(
                    f"{rel}: consistent with ADR (CAP match={len(overlap_caps)}, EVT match={len(overlap_evts)})"
                )
        elif adr_files_to_check and not full_scope:
            major.append(
                f"{rel}: no CAP/EVT reference overlaps the impacted_* of the modified ADRs."
            )
        elif not full_scope:
            # Case already covered by the "YAML without ADR" rule.
            details.append(f"{rel}: no modified ADR to verify semantic consistency.")

    if (
        not full_scope
        and yaml_files_requiring_overlap > 0
        and adr_files_to_check
        and linked_yaml_files == 0
    ):
        major.append("No modified YAML (bcm/externals) is linked to the impacted_* of the modified ADRs.")

    # Non-blocking supplementary check: "to be introduced" decisions not yet implemented.
    # Surface at minimum as warnings in details, without breaking the build.
    global_yaml_ids: set[str] = set()
    yaml_parse_errors = 0
    for yaml_file in collect_all_repo_yaml_files():
        yaml_ids, err = extract_yaml_arch_ids(yaml_file)
        if err:
            yaml_parse_errors += 1
            continue
        global_yaml_ids.update(yaml_ids)

    adr_for_decision_check = adr_files_to_check if adr_files_to_check else collect_adr_files()
    warning_count = 0
    for adr_file in adr_for_decision_check:
        decision_ids = extract_new_decision_ids_from_adr(adr_file)
        if not decision_ids:
            continue

        missing = sorted(decision_ids - global_yaml_ids)
        if missing:
            warning_count += 1
            rel_adr = adr_file.relative_to(ROOT).as_posix()
            details.append(
                f"[WARN] {rel_adr}: decisions/elements potentially not implemented in bcm|externals YAML: "
                + ", ".join(missing[:12])
                + (" …" if len(missing) > 12 else "")
            )

    if warning_count:
        details.append(f"[WARN] ADR↔YAML: {warning_count} ADR(s) with decision elements not found in YAML files.")
    if yaml_parse_errors:
        details.append(
            f"[WARN] ADR↔YAML: {yaml_parse_errors} YAML file(s) skipped during supplementary check (invalid parse)."
        )

    status = "failed" if major else "ok"
    return PhaseResult(name="ADR ↔ YAML", status=status, major_defects=major, details=details, llm=None)


def build_markdown_report(
    phase_adr: PhaseResult,
    extra_phases: list[PhaseResult],
    changed_files: list[str],
    max_issues: int,
) -> tuple[str, int, str]:
    all_major = list(phase_adr.major_defects)
    for phase in extra_phases:
        all_major.extend(phase.major_defects)
    major_count = len(all_major)

    global_status = "✅ Semantic consistency globally positive" if major_count == 0 else "❌ Major defects detected"

    lines: list[str] = []
    lines.append("## 🧠 Agent report — Semantic consistency")
    lines.append("")
    lines.append(f"- **Global status**: {global_status}")
    lines.append(f"- **Date (UTC)**: `{now_utc_iso()}`")
    lines.append(f"- **Major defects**: `{major_count}`")
    lines.append("")

    if changed_files:
        lines.append("### Files impacted by the PR")
        for path in changed_files[:100]:
            lines.append(f"- `{path}`")
        if len(changed_files) > 100:
            lines.append(f"- … {len(changed_files) - 100} more file(s)")
        lines.append("")

    def append_phase(phase: PhaseResult) -> None:
        icon = "✅" if phase.status == "ok" else "❌"
        lines.append(f"### {icon} Phase {phase.name}")

        if phase.details:
            lines.append("- Details:")
            for detail in phase.details[:20]:
                lines.append(f"  - {detail}")

        if phase.major_defects:
            lines.append(f"- Major defects ({len(phase.major_defects)}):")
            for issue in phase.major_defects[:max_issues]:
                lines.append(f"  - {issue}")
            if len(phase.major_defects) > max_issues:
                lines.append(f"  - … {len(phase.major_defects) - max_issues} more")
        else:
            lines.append("- No major defect detected.")

        lines.append("")

    append_phase(phase_adr)
    for phase in extra_phases:
        append_phase(phase)

    if major_count == 0:
        lines.append("✅ Conclusion: the PR is semantically consistent with ADR and BCM rules.")
    else:
        lines.append(
            "⛔ Conclusion: major defects remain. The build must stay failed until they are fixed."
        )

    report = "\n".join(lines).strip() + "\n"
    status = "ok" if major_count == 0 else "major_defects"
    return report, major_count, status


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PR semantic consistency agent (ADR then ADR+BCM)."
    )
    parser.add_argument("--base-ref", help="PR base SHA", default=None)
    parser.add_argument("--head-ref", help="PR head SHA", default=None)
    parser.add_argument(
        "--scope",
        choices=["pr", "full"],
        default="pr",
        help="pr: only surfaces defects from PR-impacted files; full: analyzes the whole repository",
    )
    parser.add_argument(
        "--llm-mode",
        choices=["required", "optional", "off"],
        default=None,
        help="required: LLM mandatory, optional: LLM best-effort, off: disabled",
    )
    parser.add_argument(
        "--review-mode",
        choices=["all", "inter-adr-only", "adr-yaml-only"],
        default=os.getenv("SEMANTIC_REVIEW_MODE", "all"),
        help=(
            "all: ADR + ADR+BCM + ADR↔YAML check; "
            "inter-adr-only: inter-ADR review only; "
            "adr-yaml-only: ADR↔YAML consistency only"
        ),
    )
    parser.add_argument("--report-file", default="semantic-review.md", help="Markdown report file")
    parser.add_argument("--json-file", default="semantic-review.json", help="JSON output file")
    parser.add_argument("--max-issues", type=int, default=30, help="Max number of issues listed per phase")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.llm_mode:
        os.environ["SEMANTIC_LLM_MODE"] = args.llm_mode

    full_scope = args.scope == "full"
    changed_files = get_changed_files(args.base_ref, args.head_ref)

    if full_scope:
        changed_files = []

    phase_adr = run_phase_adr(changed_files, full_scope=full_scope)
    extra_phases: list[PhaseResult] = []

    if args.review_mode == "all":
        extra_phases.append(run_phase_adr_bcm(changed_files, full_scope=full_scope))
        extra_phases.append(run_phase_adr_yaml(changed_files, full_scope=full_scope))
    elif args.review_mode == "inter-adr-only":
        pass
    elif args.review_mode == "adr-yaml-only":
        phase_adr = PhaseResult(
            name="ADR",
            status="ok",
            major_defects=[],
            details=["ADR phase skipped (--review-mode adr-yaml-only)."],
            llm=None,
        )
        extra_phases.append(run_phase_adr_yaml(changed_files, full_scope=full_scope))

    report_md, major_count, status = build_markdown_report(
        phase_adr,
        extra_phases,
        changed_files,
        max_issues=max(1, args.max_issues),
    )

    report_path = Path(args.report_file)
    report_path.write_text(report_md, encoding="utf-8")

    payload = {
        "status": status,
        "scope": args.scope,
        "review_mode": args.review_mode,
        "major_defect_count": major_count,
        "timestamp_utc": now_utc_iso(),
        "llm": {
            "mode": os.getenv("SEMANTIC_LLM_MODE", "required"),
            "score": None,
            "summary": "",
            "findings": [],
            "action_plan": [],
        },
        "phase_results": [
            {
                "name": phase_adr.name,
                "status": phase_adr.status,
                "major_defect_count": len(phase_adr.major_defects),
                "details": phase_adr.details,
            },
            *[
                {
                    "name": phase.name,
                    "status": phase.status,
                    "major_defect_count": len(phase.major_defects),
                    "details": phase.details,
                }
                for phase in extra_phases
            ],
        ],
        "changed_files": changed_files,
    }

    if isinstance(phase_adr.llm, dict):
        payload["llm"] = phase_adr.llm

    json_path = Path(args.json_file)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report_md)
    print(f"[INFO] Report written to: {report_path}")
    print(f"[INFO] JSON summary written to: {json_path}")

    return 0 if major_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
