#!/usr/bin/env python3
"""Validate .claude/skills/*/SKILL.md frontmatter.

Each skill must start with a `---` frontmatter block containing non-empty
`name` and `description` fields. The block is not validated as YAML: the
script only reads the top-level `key: value` lines (and `|` / `>` blocks) to
get at those two fields. Exit 0 when valid, 1 when any skill fails. Spec
structure is `scripts/validate_specs.py`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / ".claude" / "skills"
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
BLOCK_INDICATORS = frozenset({"|", "|-", "|+", ">", ">-", ">+"})
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def read_fields(frontmatter: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line[0] in " \t#" or ":" not in line:
            continue

        key, rest = line.split(":", 1)
        rest = rest.strip()
        if rest not in BLOCK_INDICATORS:
            fields.setdefault(key.strip(), strip_quotes(rest))
            continue

        block: list[str] = []
        while index < len(lines) and (not lines[index].strip() or lines[index][0] in " \t"):
            block.append(lines[index].strip())
            index += 1
        separator = " " if rest.startswith(">") else "\n"
        fields.setdefault(key.strip(), separator.join(part for part in block if part))

    return fields


def validate_skill(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [f"{path}: missing frontmatter (expected --- name/description --- block)"]

    fields = read_fields(match.group(1))
    errors: list[str] = []

    name = fields.get("name", "").strip()
    expected_name = path.parent.name
    if not name:
        errors.append(f"{path}: missing required frontmatter field `name`")
    elif name != expected_name:
        errors.append(f"{path}: frontmatter `name` must match directory `{expected_name}`")
    elif len(name) > MAX_NAME_LENGTH or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None:
        errors.append(
            f"{path}: `name` must be at most {MAX_NAME_LENGTH} lowercase letters, digits, or hyphens"
        )

    description = fields.get("description", "").strip()
    if not description:
        errors.append(f"{path}: missing required frontmatter field `description`")
    elif "Use when" not in description:
        errors.append(
            f"{path}: description should state what the skill does and include a "
            "`Use when ...` trigger clause"
        )
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"{path}: `description` must be at most {MAX_DESCRIPTION_LENGTH} characters"
        )

    return errors


def main() -> int:
    skill_files = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    if not skill_files:
        print(f"ERROR: no skills found under {SKILLS_ROOT}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in skill_files:
        errors.extend(validate_skill(path))

    if errors:
        print("Skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Skill validation passed ({len(skill_files)} skills).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
