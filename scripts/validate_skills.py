#!/usr/bin/env python3
"""Validate .claude/skills/*/SKILL.md and .github/skills/*/SKILL.md frontmatter.

Each skill must start with YAML frontmatter containing non-empty `name` and
`description` fields. The block is parsed as a YAML mapping subset (plain
scalars, quoted scalars, and `|` / `>` blocks) so malformed metadata cannot
pass and valid block scalars are accepted. Exit 0 when valid, 1 when any
skill fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOTS = (REPO_ROOT / ".claude" / "skills", REPO_ROOT / ".github" / "skills")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
BLOCK_INDICATORS = frozenset({"|", "|-", "|+", ">", ">-", ">+"})
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024


def decode_quoted_scalar(raw: str) -> str | None:
    if len(raw) < 2:
        return None
    quote = raw[0]
    if quote not in {'"', "'"} or not raw.endswith(quote):
        return None
    inner = raw[1:-1]
    if quote == '"':
        if inner.endswith("\\") and (len(inner) - len(inner.rstrip("\\"))) % 2 == 1:
            return None
        return inner
    return inner.replace("''", "'")


def leading_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def read_block_lines(lines: list[str], start: int, path: Path) -> tuple[list[str], int, str | None]:
    collected: list[str] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            collected.append("")
            index += 1
            continue
        indent = leading_indent(line)
        if "\t" in indent:
            return (
                collected,
                index,
                f"{path}: YAML block scalars must be indented with spaces, not tabs",
            )
        if not indent:
            break
        collected.append(line.strip())
        index += 1
    while collected and collected[-1] == "":
        collected.pop()
    return collected, index, None


def parse_frontmatter_mapping(frontmatter: str, path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    data: dict[str, str] = {}
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if line.startswith(" ") or line.startswith("\t"):
            errors.append(f"{path}: unexpected indented line in YAML frontmatter")
            index += 1
            continue
        if ":" not in line:
            errors.append(f"{path}: invalid YAML frontmatter line `{stripped}`")
            index += 1
            continue

        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        index += 1
        if not key:
            errors.append(f"{path}: empty YAML mapping key")
            continue

        if rest in BLOCK_INDICATORS:
            block_lines, index, block_error = read_block_lines(lines, index, path)
            if block_error:
                errors.append(block_error)
                index += 1
                continue
            if rest.startswith(">"):
                data[key] = " ".join(part for part in block_lines if part)
            else:
                data[key] = "\n".join(block_lines)
            continue

        if rest.startswith('"') or rest.startswith("'"):
            decoded = decode_quoted_scalar(rest)
            if decoded is None:
                errors.append(f"{path}: unclosed quoted YAML scalar for `{key}`")
                continue
            data[key] = decoded
            continue

        data[key] = rest

    return data, errors


def validate_skill(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return [f"{path}: missing YAML frontmatter (expected --- name/description --- block)"]

    data, errors = parse_frontmatter_mapping(match.group(1), path)
    if errors:
        return errors

    name = data.get("name", "").strip()
    expected_name = path.parent.name
    if not name:
        errors.append(f"{path}: missing required frontmatter field `name`")
    elif name != expected_name:
        errors.append(f"{path}: frontmatter `name` must match directory `{expected_name}`")
    elif len(name) > MAX_NAME_LENGTH or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is None:
        errors.append(
            f"{path}: `name` must be at most {MAX_NAME_LENGTH} lowercase letters, digits, or hyphens"
        )

    description = data.get("description", "").strip()
    if not description:
        errors.append(f"{path}: missing required frontmatter field `description`")
    elif "Use when" not in description:
        errors.append(
            f"{path}: description should state what the skill does and include a "
            "`Use when ...` trigger clause"
        )
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"{path}: `description` must be at most {MAX_DESCRIPTION_LENGTH} characters")

    return errors


def main() -> int:
    skill_files = sorted(p for root in SKILLS_ROOTS for p in root.glob("*/SKILL.md"))
    if not skill_files:
        roots = " or ".join(str(root) for root in SKILLS_ROOTS)
        print(f"ERROR: no skills found under {roots}", file=sys.stderr)
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
