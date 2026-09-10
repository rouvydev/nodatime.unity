# Subject Title

**Scope:** _(only if this subject is owned elsewhere) the owner, and the authoritative source — docs, repo, or vendor page._
**Last verified:** _(pairs with Scope) date, and what it was verified against._

## Intent

_Mandatory — the subject, and why it is worth specifying._

## Specification

_Mandatory — written as rules, a contract, or a table that reviewers and tests can point at. Delete the prompts below and write the subject's actual rules or shape; update them in the same PR if the subject changes._

- What is covered, what is deliberately not (can also live in Non-goals).
- Where the data or authority comes from, and precedence when two sources disagree.
- Edge cases and how they are handled (a lookup miss, an empty or partial response, a value that cannot be mapped).
- Anything a reader would otherwise have to guess.

`[NEEDS CLARIFICATION: question]` marks an open question next to the rule it blocks. Do not implement that rule until it is answered, and remove the marker before the spec lands.

## User story

_Recommended — keep it only when a persona framing adds something the Intent does not; skip it for a spec that describes a contract rather than user-facing behaviour._

> As a `<role>`, I want …, so that ….

## Definition of done

_Recommended — verifiable outcomes before calling the work done._

- [ ] **Tests cover every rule.** Each rule in `## Specification` (including edge cases) has a corresponding test, or is explicitly noted as untestable and why.
- [ ] **Self-review of the diff against this spec.**
- [ ] **Spec is true.** `## Specification` matches the delivered behaviour, updated in the same PR if it drifted.

## Non-goals

_Recommended — decisions deliberately out of scope, so review does not re-litigate them._

- Something adjacent that this spec deliberately does not cover, and why.

## Technical notes

_Recommended — kept light; point at the authoritative source instead of restating it._

## References

_Recommended — upstream contracts, related specs, vendor docs._

- Related spec: [`OTHER-SPEC.md`](OTHER-SPEC.md).
