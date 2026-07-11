# ADR-0005: Controlled Self-Modification

**Status:** Accepted  
**Date:** 2026-07

---

## Context

Beta is designed to learn from experience. This includes updating memory,
recording workflows, synthesizing skills, and potentially proposing improvements
to its own code. Uncontrolled self-modification is a safety and reliability risk.

---

## Decision

Beta uses a **zoned self-modification model** with different rules per zone.

---

## Zone Definitions

### Zone 1: Beta May Write According to Policy

These areas are designed for runtime writes and learning outputs:

- `var/memory/` — via MemoryProposal + policy evaluation
- `var/runtime/` — runtime state managed by MAS Runtime
- `var/workspaces/` — task working areas
- `skills/candidates/` — newly synthesized skill proposals
- `config/user/` — user-confirmed configuration preferences

Writes in this zone follow the defined policy flows but do not require
human approval for every write (only MemoryProposals require policy gate;
runtime state is managed by the system).

### Zone 2: Beta May Only Propose Patches

These areas contain code that agents may need to evolve, but changes
require a structured review process:

- `src/beta/agents/` — agent definitions and logic
- `src/beta/tools/` — tool contracts and registry
- `src/beta/infrastructure/` — infrastructure adapters
- `src/beta/interaction/` — interaction layer

In this zone, Beta may **create a patch proposal** but must not apply it
without testing and approval.

### Zone 3: No Self-Merge Without Human Approval

These areas are critical infrastructure that must not be modified by
automated processes without explicit human review and approval:

- `src/beta/mas/` — core MAS runtime and contracts
- `src/beta/safety/` — safety policies and decisions
- `src/beta/execution/` — execution and validation
- `docs/policies/` — policy documentation

Any proposed change to these zones must go through the full self-modification
flow and be approved by a human.

---

## Self-Modification Flow

For any code change proposed by Beta:

```
1. Detect problem or improvement opportunity
2. Create a patch proposal (documented, scoped)
3. Run in sandbox
4. Execute automated tests
5. Verifier Agent evaluates the change
6. Human reviews and approves or rejects
7. If approved: merge
8. If rejected: log rationale, archive proposal
```

No step may be skipped for Zone 2 or Zone 3 changes.

---

## Memory Auto-Update

Memory is updated automatically according to the memory policy (ADR-0004).
This is not considered "self-modification" of code.
It is the normal operation of the learning system.

---

## Workflow Recording

Workflows observed during task execution are automatically recorded in
`var/memory/workflows/` as candidates. They are not immediately activated.
Promotion follows the skill promotion policy.

---

## Consequences

- Beta can improve over time without requiring human intervention for
  every memory update or workflow recording.
- Core safety and MAS runtime code is protected from automated changes.
- All self-initiated code changes are auditable and reversible.
- Users retain final authority over what gets merged into the core system.
