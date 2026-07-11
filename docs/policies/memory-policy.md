# Memory Policy

This document defines the rules governing long-term memory in Beta.

---

## Memory Types

| Type | Description |
|---|---|
| User Preference | Expressed or inferred preferences about how the user wants Beta to behave |
| Project Fact | Persistent facts about a specific project (structure, conventions, decisions) |
| Workflow | A learned multi-step procedure for accomplishing a recurring goal |
| Experience | An agent's record of what worked and what did not in past tasks |
| Learned Rule | A user-stated or inferred rule that should govern future behavior |

---

## Memory Entry Fields

Every long-term memory entry must carry:

| Field | Description |
|---|---|
| `memory_id` | Unique identifier |
| `type` | One of the memory types above |
| `content` | The memory content (structured, not raw text) |
| `source` | Which agent or system generated the proposal |
| `scope` | `conversation`, `project`, `user`, or `global` |
| `confidence` | Estimated reliability: `high`, `medium`, `low` |
| `version` | Monotonically increasing version number |
| `status` | `active`, `superseded`, `expired`, `under_review` |
| `created_at` | Timestamp of first promotion |
| `updated_at` | Timestamp of last update |
| `expires_at` | Optional expiry timestamp |
| `source_task_id` | The task from which this memory was derived |

---

## MemoryProposal

Agents do not write directly to `var/memory/`.

To propose a new memory entry, an agent or the Learning module creates
a `MemoryProposal`:

- `proposed_by` — agent or module
- `proposed_content` — the candidate memory entry
- `rationale` — why this should be remembered
- `confidence` — estimated reliability
- `scope` — proposed scope

The Memory Policy evaluates each proposal before promotion.

---

## Auto-Save Rule

**Not every user utterance is saved as long-term memory.**

A memory entry is promoted only when:

1. The content is genuinely worth retaining across sessions.
2. The confidence level meets the threshold for the given scope.
3. There is no contradicting active memory entry that takes precedence.
4. The proposal passes the memory policy evaluation.

Transient task state, short conversation context, and ephemeral observations
are **not** candidates for long-term memory.

---

## Contradiction Handling

When a MemoryProposal contradicts an existing active memory entry:

1. The contradiction is flagged and both entries are placed `under_review`.
2. If confidence in the new proposal is significantly higher, it may supersede
   the old entry (which becomes `superseded`).
3. If the contradiction cannot be resolved automatically, it is queued for
   user review.
4. Contradictions are never silently overwritten.

---

## Versioning

- Each update to a memory entry increments its `version`.
- Previous versions are retained (not deleted).
- The most recent `active` version is the current authoritative entry.
- Superseded versions are retained for audit.

---

## Expiry

- Memory entries may carry an `expires_at` timestamp.
- Expired entries transition to `expired` status and are no longer returned
  by retrieval queries by default.
- Expired entries may be reviewed and re-promoted or archived.

---

## Review and Promotion Flow

```
MemoryProposal created (by Learning module or agent)
 └─ Memory Policy evaluates:
      ├─ confidence threshold met?
      ├─ scope appropriate?
      ├─ contradiction exists?
      │    ├─ Yes → flag for review or supersede
      │    └─ No → continue
      └─ Approved → promote to var/memory/ with status: active
           or
           Rejected → logged, not stored
```

---

## Scope Rules

| Scope | Meaning | Readable by |
|---|---|---|
| `conversation` | Relevant only to the current conversation | Primary Agent, within session |
| `project` | Relevant to a specific project | Agents with project access |
| `user` | Personal preferences and facts | All agents (with filtering) |
| `global` | Universal rules or system-wide knowledge | All agents |

Agents request memory retrieval filtered by scope. They do not read raw memory stores.
