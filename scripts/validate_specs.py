#!/usr/bin/env python3
"""Validate specs/*.md structure and specs/README.md coverage.

`README.md` (the index) and `TEMPLATE.md` (the skeleton to copy) are not
specs and are skipped.

Required for every spec:
- `# Title` as the first heading, and not the template's `# Subject Title`
- `## Intent` with non-empty body
- `## Specification` with non-empty body (rules, fallbacks, contracts,
  operational constraints — not limited to client-facing behaviour)
- no open `[NEEDS CLARIFICATION: …]` marker: it blocks the rule it sits on, so
  answer the question or drop that rule before the spec lands
- a `**Scope:**` line, if present, is non-empty and paired with a non-empty
  `**Last verified:**` line (whether a spec *needs* a Scope line at all is a
  human call this script can't make — only its shape, once present)

Recommended (warn when missing):
- `## User story`
- `## Definition of done`
- `## Technical notes`
- `## Non-goals`
- `## References`

Exit 0 when required sections pass; warnings go to stderr but do not fail.
Exit 1 on required-section failures or when specs/README.md is stale in
either direction (missing file or leftover index row).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = REPO_ROOT / "specs"
NON_SPEC_FILES = frozenset({"README.md", "TEMPLATE.md"})
README = SPECS_DIR / "README.md"
HEADING_RE = re.compile(r"^## (.+)$", re.MULTILINE)
TITLE_RE = re.compile(r"^# .+\s*$", re.MULTILINE)
# This repo's specs are SCREAMING-KEBAB-CASE.md, not SCREAMING_SNAKE_CASE.md, and the
# index link text may or may not be backtick-wrapped.
INDEX_ENTRY_RE = re.compile(r"\[`?([A-Z0-9-]+\.md)`?\]\(\1\)")
CLARIFICATION_RE = re.compile(r"\[NEEDS CLARIFICATION:([^\]\n]*)")
SCOPE_RE = re.compile(r"^\*\*Scope:\*\*\s*(.*)$", re.MULTILINE)
LAST_VERIFIED_RE = re.compile(r"^\*\*Last verified:\*\*\s*(.*)$", re.MULTILINE)
RECOMMENDED = ("User story", "Definition of done", "Technical notes", "Non-goals", "References")
PLACEHOLDER_TITLE = "# Subject Title"


def section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$"
        r"(.*?)"
        r"(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def first_heading(text: str) -> str | None:
    match = re.search(r"^#+ .+", text, re.MULTILINE)
    return match.group(0).strip() if match else None


def validate_scope(text: str, path: Path) -> list[str]:
    scope_match = SCOPE_RE.search(text)
    if scope_match is None:
        return []

    errors: list[str] = []
    if not scope_match.group(1).strip():
        errors.append(
            f"{path}: `**Scope:**` line is present but empty — name the owner and "
            "authoritative source"
        )

    last_verified_match = LAST_VERIFIED_RE.search(text)
    if last_verified_match is None or not last_verified_match.group(1).strip():
        errors.append(
            f"{path}: `**Scope:**` line needs a paired `**Last verified:**` line "
            "(when, and against what)"
        )

    return errors


def validate_spec(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    headings = HEADING_RE.findall(text)

    heading = first_heading(text)
    if heading is None:
        errors.append(f"{path}: missing `# Title`")
    elif not TITLE_RE.fullmatch(heading):
        errors.append(f"{path}: first heading must be `# Title`, found `{heading}`")
    elif heading == PLACEHOLDER_TITLE:
        errors.append(f"{path}: title is still the template placeholder `{PLACEHOLDER_TITLE}`")

    intent = section_body(text, "Intent")
    if not intent:
        errors.append(f"{path}: missing or empty `## Intent`")

    specification = section_body(text, "Specification")
    if not specification:
        errors.append(f"{path}: missing or empty `## Specification`")

    for heading_name in RECOMMENDED:
        if heading_name not in headings:
            warnings.append(f"{path}: recommended section `## {heading_name}` is missing")
        elif not section_body(text, heading_name):
            warnings.append(f"{path}: recommended section `## {heading_name}` is empty")

    for question in CLARIFICATION_RE.findall(text):
        errors.append(
            f"{path}: open `[NEEDS CLARIFICATION:{question}]` — answer it, or drop the "
            "rule it blocks, before this lands"
        )

    errors.extend(validate_scope(text, path))

    return errors, warnings


def indexed_spec_names(readme: str) -> list[str]:
    specs_section = section_body(readme, "Specs")
    source = specs_section or readme
    return INDEX_ENTRY_RE.findall(source)


def validate_readme(spec_files: list[Path]) -> list[str]:
    errors: list[str] = []
    if not README.is_file():
        return [f"{README}: missing specs index"]

    readme = README.read_text(encoding="utf-8")
    on_disk = {path.name for path in spec_files}
    indexed = indexed_spec_names(readme)
    indexed_set = set(indexed)

    for name in sorted(on_disk - indexed_set):
        errors.append(f"{README}: does not mention `{name}`")
    for name in sorted(indexed_set - on_disk):
        errors.append(f"{README}: stale index entry `{name}` (file is missing)")

    seen: set[str] = set()
    for name in indexed:
        if name in seen:
            errors.append(f"{README}: duplicate index entry `{name}`")
        seen.add(name)

    return errors


def main() -> int:
    spec_files = sorted(p for p in SPECS_DIR.glob("*.md") if p.name not in NON_SPEC_FILES)
    if not spec_files:
        print(f"ERROR: no specs found under {SPECS_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for path in spec_files:
        spec_errors, spec_warnings = validate_spec(path)
        errors.extend(spec_errors)
        warnings.extend(spec_warnings)

    errors.extend(validate_readme(spec_files))

    if warnings:
        print("Spec validation warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"  - {warning}", file=sys.stderr)

    if errors:
        print("Spec validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"Spec validation passed ({len(spec_files)} specs"
        + (f", {len(warnings)} warning(s)" if warnings else "")
        + ")."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
