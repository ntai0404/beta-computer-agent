# ADR-0006: Anti-Coupling Rules

**Status:** Accepted  
**Date:** 2026-07

---

## Context

In complex systems, coupling between modules accumulates gradually. Each
individual shortcut seems harmless, but collectively they make the system
impossible to reason about, test, or safely modify.

This ADR records the complete set of structural coupling rules that Beta
must adhere to at all times.

---

## The 20 Anti-Coupling Rules

### 1. Agents do not import each other.

No agent module may import or instantiate another agent.
All inter-agent coordination goes through MAS Runtime.

### 2. Agents communicate only through MAS contracts.

The only types agents use for inter-agent communication are those defined
in `mas/contracts/`. No raw function calls, no shared objects across agents.

### 3. MAS Runtime does not call OS, browser, filesystem, or terminal directly.

The MAS Runtime handles routing and lifecycle. Any action requiring OS or
infrastructure interaction is delegated to Execution, which uses Infrastructure adapters.

### 4. Execution does not decide which agent owns a task.

Execution validates and runs actions. Ownership and task routing are the
responsibility of MAS Runtime and the owning agent.

### 5. Safety does not execute actions directly.

Safety makes policy decisions: allowed, needs approval, blocked.
Execution runs actions after Safety clears them.

### 6. Infrastructure does not contain business decisions.

Infrastructure adapters translate between domain models and external systems.
They contain no logic about which agent should handle what, or whether a
given action is safe.

### 7. Context builds views only; it does not own state.

The Context module assembles read-only views from multiple state sources.
It does not write to any store. It is not the source of truth for anything.

### 8. Memory does not contain runtime task state.

`var/memory/` stores long-term, persistent knowledge.
Active task state lives in `var/runtime/tasks/`.
These are never co-located.

### 9. Environment state is not a substitute for long-term memory.

Environment state is a real-time snapshot. Observations that should persist
must go through the MemoryProposal flow.

### 10. Protocol adapters do not leak SDK types into core.

A2A and MCP SDK types are confined to `protocols/a2a/` and `protocols/mcp/`
respectively. They do not appear in agents, mas, memory, execution, safety,
context, or learning.

### 11. A2A SDK is not imported in core modules.

A2A library imports are only permitted in `protocols/a2a/`.

### 12. MCP SDK is not imported in agent code.

MCP library imports are only permitted in `protocols/mcp/`.

### 13. Each concept has exactly one source of truth.

There is no duplication of authoritative state. Every type of state has
one defined location (see state-ownership.md).

### 14. Each module exposes only its public contract.

Internal types, helpers, and implementation details are private.
Other modules depend only on declared public contracts.

### 15. Implementation details are private.

Importing a module's internal types or functions from outside that module
is a coupling violation. Only use what a module explicitly exports.

### 16. Agent topology is runtime data.

The set of active agents, their connections, and task assignments are
managed by MAS Runtime at runtime. They are not encoded in the source tree.

### 17. Do not create an agent for a single capability.

Having a capability does not make a component an agent. See ADR-0002 for
the full criteria for what qualifies as an agent.

### 18. Do not split processes without operational justification.

In-process execution is the default. Process boundaries are introduced only
for concrete operational reasons (security isolation, GPU requirements, etc.).

### 19. Do not create microservices per agent.

Internal agents share a runtime. Each agent is not a microservice.
External agents use A2A adapters.

### 20. Do not create abstractions for speculative future use.

Every abstraction must solve a current, concrete problem.
Speculative abstractions add complexity without benefit.

---

## Enforcement

These rules are documented here as the authoritative reference.

Violations should be flagged during code review.

When Beta proposes a code change (patch), the Verifier Agent must check the
proposed change against these rules before recommending approval.

Any exception to these rules requires a new ADR documenting the rationale.
