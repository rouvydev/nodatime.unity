# Specs

One specification per subject.

- Specs owned elsewhere open with a **Scope** line: owner, authoritative source.
- Specs describe the present. Update in the PR that changes the thing.
- Start a new spec by copying `TEMPLATE.md`. Validate locally with
  `python3 scripts/validate_specs.py`.

| Spec | Description |
|------|-------------|
| [VENDORED-NODATIME-ASSEMBLY.md](VENDORED-NODATIME-ASSEMBLY.md) | Which upstream `NodaTime.dll` this repository redistributes, the tzdb it carries, how the Unity `.meta` GUIDs are produced, and the rules for re-packing. Upstream-owned. |
