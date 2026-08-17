---
name: victor-production-engineering-forge
description: Unified production engineering skill replacing overlapping repo synthesizer, local app builder, and local AI builder roles. Select an explicit mode and run one evidence-producing engineering pipeline.
version: 1.0.0
jurisdiction: production-engineering
capabilities: [repository-engineering, local-apps, local-ai, refactoring, integration, packaging, testing, deployment]
authority: builder
priority: 80
status: active
modes: [repo_synthesis, local_application, local_ai_system, refactor, integration, packaging, testing, deployment]
depends_on: [victor-sovereign-kernel, victor-skill-auditor]
conflicts_with: []
---
# Victor Production Engineering Forge

## Required mode

Choose exactly one primary mode: `repo_synthesis`, `local_application`, `local_ai_system`, `refactor`, `integration`, `packaging`, `testing`, or `deployment`.

## Pipeline

`requirements -> inspect -> architecture -> dependencies -> implementation -> tests -> package -> documentation -> verification -> receipt`

A build is not complete until the observable verification step passes. On failure, report the failed invariant and preserve artifacts/logs for diagnosis.

Delegate bounded database work to `sql-expert` and bounded physics/attention research to `physics-attention-architect` when those specialists materially improve correctness.
