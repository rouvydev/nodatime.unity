# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this repository is

`rouvydev/nodatime.unity` re-packages **one upstream binary** — `NodaTime.dll`, the
`netstandard2.0` build of [NodaTime](https://nodatime.org) 2.4.18 — as the Unity UPM package
`rouvy.nodatime.unity`. There is no Rouvy source code here: the only non-documentation,
non-tooling file tracked is the DLL itself. NodaTime is a date, time and time zone library
used instead of `DateTime`.

| | |
|---|---|
| Upstream library | NodaTime 2.4.18, Apache-2.0, by Jon Skeet |
| Vendored asset | `lib/netstandard2.0/NodaTime.dll` from the nuget.org package, unmodified |
| Time zone data | tzdb **2022a**, embedded in the assembly — no side-car file, no network |
| Package | `rouvy.nodatime.unity` **1.0.0**, published 2023-10-20 to `https://npm.pkg.github.com/@rouvydev` |
| Consumers | `rouvydev/rouvyapp` and `rouvydev/rouvyugc`, both pinned to `1.0.0` |
| Default branch | `master`. The repository is **public**. |

All of that is verified and written down, with the commands that produced it, in
[`specs/VENDORED-NODATIME-ASSEMBLY.md`](specs/VENDORED-NODATIME-ASSEMBLY.md). Read it before
making any claim about which build this is.

## The layout, all of it

```
.
├── rouvy.nodatime.unity/            # the UPM package, published as-is
│   ├── package.json                 # name, version, publishConfig
│   └── Runtime/
│       └── NodaTime.2.4.18/         # directory name carries the upstream version
│           └── NodaTime.dll         # vendored, never hand-edited
├── .github/workflows/release.yml    # manual workflow_dispatch publish
├── specs/                           # one spec per subject, indexed by specs/README.md
├── scripts/                         # the two standard doc validators
└── .claude/skills/                  # agent skills (see "Agent tooling")
```

## Rules that actually bite here

- **The DLL is vendored.** Never hand-edit, re-sign, IL-merge or strip it. A version change
  replaces it wholesale — the `repack-nodatime-version` skill is the procedure.
- **`Runtime/NodaTime.<version>/` is the only record of the upstream version** in the tree.
  `package.json`'s description states the convention: *"Every dll has its version defined in
  the directory name."* Keep it exact.
- **`.meta` files are not committed.** `release.yml` generates them at publish time with
  `rouvydev/metagen-gha`, from a fixed `seed`. Do not commit a `.meta`, and do not change
  that seed — asset GUIDs are derived from it plus the asset path.
- **`package.json` `version` is independent of the NodaTime version** (`1.0.0` vs `2.4.18`)
  and must be bumped for a publish to be accepted at all.
- **Consumers pin exact versions**, so a publish reaches nobody until `rouvyapp` and
  `rouvyugc` bump their own `Packages/manifest.json`.
- **Ask before touching `.github/workflows/release.yml`.** It holds the publish path and the
  metagen seed. It has also never actually run in this repository (the Actions API reports
  zero runs), so any change to it is untested by definition.

## Conventions that do not exist here

Do not invent them, and do not copy them from a Rouvy service repository:

- **No tests, no build, no formatter, no linter.** There is nothing to compile: the only
  code here is a third-party binary. `python3 scripts/validate_skills.py` and
  `python3 scripts/validate_specs.py` are the only checks that run.
- **No `.gitignore`, no `LICENSE`, no `CHANGELOG`.** The missing `LICENSE`/`NOTICE` next to a
  publicly redistributed Apache-2.0 binary is recorded in the spec as an open question for a
  human, not something to fix on the way past.

## Agent tooling

Follows [`rouvydev/agent-setup-example`](https://github.com/rouvydev/agent-setup-example).

- **Skills** live in `.claude/skills/`, one canonical copy. There is one:
  `repack-nodatime-version`.
- **Specs** live in `specs/`, indexed by [`specs/README.md`](specs/README.md).
- **Validated in CI** by [`.github/workflows/pull_request.yml`](.github/workflows/pull_request.yml).
  Run locally with `python3 scripts/validate_skills.py && python3 scripts/validate_specs.py`.
- **No hook, and no per-harness adapters, deliberately.** A hook exists to run something
  after every agent edit; this repository has nothing to run. There is no formatter, no
  build and no test target, and the only editable files are Markdown and one `package.json`.
  Under the standard that is a complete setup, not a gap — so `.claude/settings.json`,
  `.codex/hooks.json`, `.cursor/hooks.json` and `.github/hooks/` are all absent on purpose.
  All four adapters or none; three would be drift.
- **Codex** does not read `.claude/skills/`. Link it locally and keep that out of git:

  ```bash
  mkdir -p .agents && ln -sfn ../.claude/skills .agents/skills
  echo ".agents/" >> .git/info/exclude    # local-only, NOT .gitignore
  ```

  A committed second copy would make the skill appear twice in the Cursor and Copilot
  pickers.
