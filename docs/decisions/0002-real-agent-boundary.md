# ADR-0002: Real Agent Boundary

**Status:** Accepted  
**Date:** 2026-07

---

## Context

In AI system design, there is a pattern of calling any module that does something
useful an "agent." This leads to bloated architectures where memory stores,
tool registries, planners, and protocol adapters are all labeled as agents.

---

## Decision

A component is only created as an **agent** if it meets **all** of the following criteria:

1. It has a distinct **identity** (agent_id, display name).
2. It has a distinct **role** (a domain it is responsible for).
3. It has a distinct **capability set** (declared in its AgentCard).
4. It has a **private working context** for the duration of a task.
5. It has a **task lifecycle** (it receives, works on, and completes tasks).
6. It has a **communication contract** (defined message and task types it accepts).
7. It has **explicit tool permissions** (declared, not implicit).
8. It can **make autonomous decisions** within its domain.
9. It can **receive tasks, respond, request input, or return artifacts**.

If a component does not meet all nine criteria, it is a service, module, or
utility — not an agent.

---

## Components That Are NOT Agents

The following components exist in Beta as modules and services, not as agents:

| Component | What it is |
|---|---|
| Memory store | A persistence service |
| Tool registry | A catalog and lookup service |
| Tool executor | A controlled execution layer |
| Safety policy | A policy decision module |
| Skill registry | A catalog and lifecycle service |
| Context builder | A read-only assembly service |
| Environment state | An observation and state model |
| TTS / STT engine | Infrastructure adapters |
| 9Router LLM client | An infrastructure adapter |
| Database | A storage backend |
| Planner utility | A planning algorithm or helper |
| Protocol adapter | A transport translation layer |

---

## When Planner Becomes an Agent

A planner may be promoted to an agent **only when it has**:

- a distinct identity;
- private state across a task lifecycle;
- the ability to make autonomous decisions about plan revision;
- a defined communication contract.

A planner that is simply a function called by another agent is **not** an agent.

---

## Consequences

- The initial agent set is small and well-defined:
  Primary, Computer, Coding, Research, Verifier.
- New agents are only added when a clear identity, role, and lifecycle are established.
- All other components are organized as domain modules, not agents.
- This keeps the MAS topology comprehensible and auditable.
