# Specs

One specification per subject.

- Specs owned elsewhere open with a **Scope** line: owner, authoritative source.
- Specs describe the present. Update in the PR that changes the thing.
- Start a new spec by copying `TEMPLATE.md`. Specs are validated in CI by the
  `validate-agent-setup` action of `rouvydev/agent-setup-example`; to run it locally, use
  `python3 <agent-setup-example>/scripts/validate_specs.py --root .`.

| Spec | Description |
|------|-------------|
| [`VENDORED_NODATIME_ASSEMBLY.md`](VENDORED_NODATIME_ASSEMBLY.md) | Which upstream `NodaTime.dll` this repository redistributes, the tzdb it carries, how the Unity `.meta` GUIDs are produced, and the rules for re-packing. Upstream-owned. |
