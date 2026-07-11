# State Ownership

This document defines the authoritative ownership, read/write access,
retention, versioning, and audit requirements for each type of state in Beta.

---

## State Ownership Table

| State Type | Owner | Source of Truth | Writable By | Readable By | Retention | Versioning | Audit Required |
|---|---|---|---|---|---|---|---|
| Conversation State | MAS Runtime | `var/runtime/conversations/` | MAS Runtime | Primary Agent (via Context), Observability | Session + archive policy | Append-only log | Yes |
| Task State | MAS Runtime | `var/runtime/tasks/` | MAS Runtime; owning agent (via MAS API) | Owning agent, Verifier Agent (via Context, scoped) | Task lifetime + archive | Per-transition log | Yes |
| Agent Private State | Individual agent | `var/runtime/agents/` | That agent only | That agent only | Current task; cleared on completion | None (ephemeral) | No |
| Environment State | Environment module | `var/runtime/environment/` | Environment observers (infrastructure) | Any agent (via Context, read-only) | Real-time; no historical guarantee | Snapshot on demand | No |
| Long-Term Memory | Memory module | `var/memory/` | Memory module (via MemoryProposal promotion only) | Any agent (via Memory retrieval, filtered) | Indefinite; subject to expiry policy | Full version history | Yes |
| Skill Artifact | Skills module | `skills/active/` | Skills module (after promotion approval) | Any authorized agent | Active lifecycle | Versioned by promotion | Yes |
| Workspace | Execution / Coding Agent | `var/workspaces/` | Assigned agent (within task scope) | Assigned agent; Verifier Agent | Task lifetime; archived after completion | Checkpoint-based | Recommended |
| Checkpoint | MAS Runtime | `var/runtime/checkpoints/` | MAS Runtime; agents (via checkpoint API) | MAS Runtime; Verifier Agent | Policy-defined (rolling or fixed count) | Each checkpoint is immutable | Yes |
| Event Log | Observability module | `var/runtime/events/` | Any component (append-only) | Observability tools; Verifier Agent; audit processes | Audit retention policy | Append-only (immutable) | Inherent |

---

## State Access Principles

### Conversation State

- Primary Agent reads via Context layer (assembled view, not raw store).
- MAS Runtime is the only writer.
- Other agents may read conversation summaries, not full raw history,
  and only when included in their scoped context view.

### Task State

- The owning agent reads its own task context via the Context layer.
- The owning agent updates task state via the MAS Runtime API (not direct writes).
- The Verifier Agent may read task context during verification (read-only, scoped).
- No agent reads another agent's task context without explicit delegation or handoff.

### Agent Private State

- Strictly private to the individual agent.
- Not shared with any other agent or system component.
- Must not be used as the source of truth for task outcomes.
- Outcomes must be returned as AgentArtifact or AgentStatus via MAS Runtime.

### Environment State

- Updated continuously by infrastructure observers (Windows, browser, etc.).
- Agents read current environment state via the Context layer.
- Historical environment state is captured in Checkpoints, not in Environment State.
- Not a substitute for long-term memory.

### Long-Term Memory

- Never written directly by agents.
- All writes go through MemoryProposal → Memory Policy → promotion.
- Each memory entry carries: `source`, `scope`, `confidence`, `version`, `status`.
- Superseded entries are versioned, not deleted.
- Contradictions are flagged for review, not silently overwritten.

### Skill Artifact

- Skills start in `skills/candidates/` and are promoted through the skill lifecycle.
- `skills/active/` contains only promoted, approved skills.
- Agents invoke skills via the Skills registry; they do not read `skills/` directly.
- All promotions are logged and reversible.

### Workspace

- Created per task for agents that need a working area.
- Scoped to the task and the assigned agent.
- Archived after task completion for post-hoc audit.
- Verifier Agent may read a workspace during verification.

### Checkpoint

- Automatically created by MAS Runtime at defined task lifecycle points.
- Manually requested by agents via MAS API when a risky action is imminent.
- Immutable once written.
- Used for rollback and recovery.

### Event Log

- Append-only. No modification or deletion.
- Contains: task transitions, agent messages, safety decisions, execution outcomes,
  memory promotions and rejections, skill promotions and rejections.
- Retained according to the audit retention policy.
- Primary input for observability, debugging, and compliance audit.
