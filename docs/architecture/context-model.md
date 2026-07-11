# Context Model

Beta distinguishes eight distinct types of context and state.
Each has a defined owner, source of truth, and lifecycle.

---

## 1. Conversation Context

**What it is:** The running dialogue between the user and the Primary Agent.

Includes:
- message history for the current conversation;
- user utterances and agent responses;
- active topic and detected intent;
- turn metadata (timestamps, message IDs).

**Source of truth:** `var/runtime/conversations/`

**Owned by:** MAS Runtime (conversation state); read by Primary Agent via Context layer.

**Lifetime:** The duration of the conversation session. May be archived.

---

## 2. Task Context

**What it is:** The full state of an active task.

Includes:
- task goal and decomposed plan;
- current step and status;
- owning agent ID;
- produced artifacts;
- approval requirements and approval state;
- retry and rollback state;
- final result.

**Source of truth:** `var/runtime/tasks/`

**Owned by:** MAS Runtime.

**Writable by:** MAS Runtime (lifecycle transitions); owning agent (progress updates via MAS API).

**Readable by:** Any agent with task access (via Context layer, scoped view).

**Lifetime:** From task creation until archival or expiry.

---

## 3. Agent Private Context

**What it is:** The temporary working state of an individual agent for a current task.

Includes:
- local scratchpad for reasoning;
- intermediate values generated during task execution;
- short-term observations relevant only to this agent's current step.

**Source of truth:** `var/runtime/agents/`

**Owned by:** The individual agent.

**Readable by:** Only that agent.

**Lifetime:** Bounded to the current task. Cleared on task completion or handoff.

**Important:** Agent private context is **not** the source of truth for task state.
The agent must not persist important outcomes here — they must be returned as
artifacts or status via MAS Runtime.

---

## 4. Shared Environment Context

**What it is:** A model of the current observable state of the machine.

Includes:
- active application and window;
- running processes;
- open projects and editors;
- focused input element;
- open browser tabs;
- known application login state.

**Source of truth:** `var/runtime/environment/`

**Owned by:** Environment module (observers populate; agents read).

**Writable by:** Environment observers (infrastructure layer).

**Readable by:** Any agent via Context layer (scoped, filtered view).

**Lifetime:** Real-time. Updated continuously. Not a substitute for long-term memory.

**Important:** Environment state describes **what is**, not **what was**.
It is not a memory store. Historical environment states may be captured as snapshots in checkpoints.

---

## 5. Long-Term Memory

**What it is:** Persistent knowledge that survives across sessions.

Includes:
- user preferences and habits;
- project facts and context;
- known workflows;
- learned rules and corrections;
- agent experience.

**Source of truth:** `var/memory/`

**Owned by:** Memory module.

**Writable by:** Memory module only — via promoted `MemoryProposal`.

**Readable by:** Agents via Memory retrieval service (filtered, ranked view).

**Lifetime:** Indefinite, subject to expiry and versioning policy.

**Important:** Agents do not write directly to `var/memory/`. All writes go
through a MemoryProposal that must be evaluated by the memory policy before promotion.

---

## 6. Checkpoint

**What it is:** A point-in-time snapshot of a task's state and environment,
used for recovery and rollback.

**Source of truth:** `var/runtime/checkpoints/`

**Owned by:** MAS Runtime.

**Writable by:** MAS Runtime (automatic) and agents (via checkpoint request).

**Lifetime:** Retained for the duration defined by the checkpoint policy.

---

## 7. Event Log

**What it is:** An append-only log of significant system events.

Includes:
- task lifecycle transitions;
- agent messages sent and received;
- safety decisions;
- execution outcomes;
- memory promotions and rejections.

**Source of truth:** `var/runtime/events/`

**Owned by:** Observability module.

**Writable by:** Any system component (append-only).

**Readable by:** Observability tools, audit processes, and Verifier Agent (read-only).

**Lifetime:** Defined by audit retention policy.

---

## 8. Memory Proposal

**What it is:** A candidate memory entry proposed by the Learning module.

Carries:
- `source` — which agent or process generated it;
- `scope` — conversation, project, user, or global;
- `content` — the proposed memory fact;
- `confidence` — estimated reliability;
- `status` — candidate, evaluating, approved, rejected.

A MemoryProposal must be evaluated against the memory policy before promotion.
Promotion writes an entry into `var/memory/`.

**Source of truth:** Managed by Memory module during evaluation.

---

## Summary Table

| Context Type | Source of Truth | Owner | Writable By | Lifetime |
|---|---|---|---|---|
| Conversation Context | `var/runtime/conversations/` | MAS Runtime | MAS Runtime | Session |
| Task Context | `var/runtime/tasks/` | MAS Runtime | MAS Runtime + owning agent (via API) | Task lifetime |
| Agent Private Context | `var/runtime/agents/` | Individual agent | That agent only | Current task |
| Shared Environment Context | `var/runtime/environment/` | Environment module | Environment observers | Real-time |
| Long-Term Memory | `var/memory/` | Memory module | Memory module (via proposals) | Indefinite |
| Checkpoint | `var/runtime/checkpoints/` | MAS Runtime | MAS Runtime + agents (via API) | Policy-defined |
| Event Log | `var/runtime/events/` | Observability module | Any component (append-only) | Audit retention |
| Memory Proposal | Memory module (in-flight) | Memory module | Learning module | Until promoted/rejected |

---

## Principles

- Short-term context is **not** long-term memory.
- Environment state is **not** memory.
- Agent private context is **not** the source of truth for task outcomes.
- Context builders assemble views from multiple sources; they do not own any state.
- Not every user utterance becomes a long-term memory entry.
- Only MemoryProposals that pass memory policy evaluation are promoted.
