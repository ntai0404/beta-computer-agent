# ADR-0001: Modular Monolith Architecture

**Status:** Accepted  
**Date:** 2026-07

---

## Context

Beta is a multi-agent system with multiple internal modules (agents, MAS runtime,
context, memory, execution, safety, etc.). We must choose an initial deployment
architecture that enables rapid development and evolution while avoiding
premature complexity.

---

## Decision

Beta is built as a **modular monolith** for its initial form:

- All internal agents run in the **same process**.
- Modules are separated by clear boundaries with defined public contracts.
- In-process communication is used between internal agents (not HTTP).
- The source code is organized by module, but all modules are deployed together.

---

## Rationale

| Concern | Rationale |
|---|---|
| **Debuggability** | A single process is far easier to debug, trace, and inspect than a distributed system |
| **Development speed** | No need to manage inter-service contracts, serialization, or network failures during early development |
| **Audit clarity** | A single event log and single runtime make it easier to reconstruct what happened |
| **Refactoring** | Moving boundaries within a monolith is easier than changing microservice APIs |
| **Operational simplicity** | One process to start, one to monitor, one to restart |

---

## Consequences

- Agent topology is runtime data, not deployment topology.
- Adding a new agent type does not require a new service.
- If an agent needs process isolation (for security or stability), it can be
  extracted and communicated with via the A2A adapter — without changing core agent logic.
- A2A is the **external boundary adapter**, not the internal communication mechanism.

---

## What We Are Explicitly Not Doing (Yet)

- We are not deploying each agent as a separate microservice.
- We are not using a message broker (Redis, RabbitMQ, Kafka) between internal agents.
- We are not requiring HTTP between internal modules.

These decisions may be revisited when there is a concrete operational reason
(e.g., a specific agent needing GPU isolation, or a sandboxed execution environment).
