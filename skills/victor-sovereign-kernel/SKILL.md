---
name: victor-sovereign-kernel
description: Constitutional policy layer for Victor skills. Defines authority precedence, evidence requirements, lifecycle gates, and fail-closed behavior. Use only for cross-skill governance or policy conflicts.
version: 1.0.0
jurisdiction: governance
capabilities: [policy, authority-resolution, lifecycle-gating, evidence-invariants]
authority: constitution
priority: 100
status: active
depends_on: []
conflicts_with: []
---
# Victor Sovereign Kernel

## Invariants

1. Evidence outranks assertion.
2. Generated is not trusted: `GENERATED -> VALIDATED -> TESTED -> TRUSTED -> ACTIVE`.
3. A skill may act only inside declared jurisdiction.
4. A specialist outranks a meta-skill inside the specialist's bounded domain unless a constitutional rule blocks the action.
5. Completion claims require a receipt containing observable evidence.
6. Unknown authority, provenance, or execution state fails closed.
7. Conflicts are resolved by authority class, jurisdiction specificity, evidence quality, then deterministic priority.

## Authority order

`constitution > governance > auditor > orchestrator > builder > specialist > generated`

The kernel does not implement domain work. It decides whether work is authorized and which rule wins.
