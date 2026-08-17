# Victor Skill Kernel

A deterministic, offline-first control plane for auditing, routing, governing, registering, and consolidating Victor/ChatGPT-style `SKILL.md` capabilities.

## Why this exists

A large skill library fails when multiple skills claim the same authority. The kernel replaces name-based prestige with explicit jurisdiction, capability metadata, lifecycle state, evidence, and deterministic routing.

The core loop is:

```text
State -> Need -> Capability Specification -> Skill Compilation
      -> Implementation -> Verification -> Registration -> Reuse
```

**Invariant:** generated does not mean trusted.

## Consolidated architecture

```text
Victor Sovereign Kernel                 constitution
        |
        +-- Existence Graph Steward     continuity / state
        +-- Skill Auditor               independent evaluator
        +-- Sovereign Skill Genesis     capability specification
                |
                +-- Skillsmith Prime    skill compiler
                        |
                        +-- Production Engineering Forge
                              modes: repo | local app | local AI | refactor | integration | package | test | deploy
                        +-- SQL Expert
                        +-- Physics Attention Architect
```

The Production Engineering Forge is the deliberate merge target for the overlapping repository synthesizer, local application builder, and local-AI builder responsibilities identified in the source audit.

## Quick start

Requires Python 3.11+ and no runtime dependencies.

```bash
python -m unittest discover -s tests -v
python -m victor_skill_kernel audit skills --json audit.json --markdown audit.md
python -m victor_skill_kernel route skills "build a production local AI repository"
python -m victor_skill_kernel register skills --db victor-skills.db
python -m victor_skill_kernel graph --db victor-skills.db
```

Or install the CLI:

```bash
python -m pip install -e .
victor-skills audit skills
```

## What the auditor checks

- missing routing metadata;
- missing jurisdiction/capabilities;
- authority inflation;
- duplicate names;
- lexical/capability/jurisdiction overlap;
- merge candidates;
- unsupported completion/implementation language;
- lifecycle-state validity.

## Repository layout

- `victor_skill_kernel/` — parser, auditor, router, SQLite capability graph and receipt store.
- `skills/` — consolidated canonical skill definitions.
- `config/architecture.json` — lifecycle, authority order and merge policy.
- `docs/AUDIT_REPORT.md` — consolidation rationale and limitations.
- `examples/legacy-visible-skills.json` — mapping from the visible skills in the original audit.
- `tests/` — deterministic regression tests.
- `.github/workflows/ci.yml` — CI test + generated audit artifacts.

## Evidence model

The included SQLite registry stores skill nodes, dependency/conflict edges, and evidence receipts. Empty evidence is rejected. This prevents a prompt from converting narrative statements such as "implemented" into canonical state without proof.

## Legacy conductor

The historical `victor-orchestral-conductor/` folder is retained as **legacy/experimental** until its implementation claims are backed by executable tests or receipts. The new kernel does not delete it automatically.

## License

MIT.
