---
name: victor-sovereign-skill-genesis
description: Capability specification layer. Determines whether a missing capability should exist, its minimum authority, boundaries, dependencies, permissions, and acceptance tests before compilation.
version: 1.0.0
jurisdiction: capability-specification
capabilities: [gap-analysis, capability-specification, permission-design, acceptance-criteria]
authority: governance
priority: 90
status: active
depends_on: [victor-sovereign-kernel, victor-existence-graph-steward]
conflicts_with: [skillsmith-prime]
---
# Victor Sovereign Skill Genesis

Answer **should this capability exist, and under what authority?**

Output a bounded capability specification containing purpose, jurisdiction, inputs, outputs, permissions, dependencies, prohibited behavior, failure conditions, acceptance tests, and required evidence.

Do not compile the final skill instructions; delegate compilation to `skillsmith-prime` after governance approval.
