# ADR-0004: Context and Memory Separation

**Status:** Accepted  
**Date:** 2026-07

---

## Context

In many AI assistant systems, "context" and "memory" are treated as the same thing.
This conflation causes several problems:

- Long-term memory grows unbounded with session data.
- Agents treat transient task state as persistent fact.
- Environment observations are stored as user preferences.
- Context builders become stateful and authoritative.

---

## Decision

Beta strictly separates context (short-term, assembled, ephemeral) from
memory (long-term, curated, persistent).

---

## Four Distinct Separations

### 1. Short-Term Context vs. Long-Term Memory

Short-term context includes:

- current conversation messages;
- active task steps and status;
- agent private scratchpad;
- current environment state.

Long-term memory includes:

- user preferences;
- project facts;
- learned workflows;
- agent experience.

These are stored in different locations and managed by different modules.
They are never co-located or conflated.

### 2. Environment State vs. Memory

Environment state is a **current** snapshot of what is observable on the machine.
It is not a historical record. It is not a preference store. It is not memory.

If an environment observation is worth remembering across sessions, it must be
submitted as a `MemoryProposal` and evaluated by the memory policy before promotion.

### 3. Agent Private Context vs. Source of Truth

An agent's private working context is ephemeral and private to that agent.
It is not the source of truth for task outcomes.

Task outcomes, artifacts, and status must be returned via MAS Runtime.
They are recorded in the authoritative task state at `var/runtime/tasks/`.

### 4. Context Builders as Read-Only Assembly

Context builders assemble views from multiple state sources (conversation,
task, environment, memory) to provide agents with a relevant snapshot.

Context builders:

- do not own any state;
- do not write to any state store;
- do not serve as the source of truth;
- produce assembled views on demand.

---

## Consequences

- The memory store does not grow with every conversation turn.
- Environment state remains a real-time, lightweight observation model.
- Agent code does not need to reason about what to persist — it focuses on the task.
- The Learning module is responsible for identifying what is worth proposing as memory.
- Long-term memory stays curated and reliable over time.
