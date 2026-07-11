# Beta Computer Agent

**Status: Architecture Design Only — No implementation exists yet.**

---

## What Is Beta

Beta is a personal AI assistant designed to communicate with the user through
text and voice, and to operate applications, files, browsers, and terminal
tools on a Windows computer.

Beta is not a single AI agent. **Beta is the entire Multi-Agent System (MAS).**

---

## Goal

Build a shared-environment Multi-Agent System with a primary companion persona,
capable of:

- natural conversation with the user;
- autonomous task decomposition and delegation;
- desktop and computer control;
- software development assistance;
- research and information gathering;
- verified, safe, and auditable task execution;
- continuous learning from user preferences and workflows.

---

## MAS Architecture

```
User
 └─ Interaction Layer (text, voice, avatar, notifications)
      └─ Primary Agent
           └─ MAS Runtime
                ├─ Computer Agent
                ├─ Coding Agent
                ├─ Research Agent
                └─ Verifier Agent
                     └─ (Skills, Tools, Safety, Execution, Infrastructure)
```

All agent-to-agent communication flows through the MAS Runtime.
Agents do not call each other directly.

The agent topology is **runtime data** — it is not encoded in the source tree.

---

## Module Boundaries

| Module | Responsibility |
|---|---|
| `agents/` | Autonomous agents with identity, role, context, and lifecycle |
| `mas/` | Contracts, runtime, messaging, coordination, persistence |
| `context/` | Build and assemble context views for agents (read-only) |
| `memory/` | Long-term memory: storage, retrieval, consolidation, proposals |
| `environment/` | Shared model of current machine state; observers and snapshots |
| `skills/` | Skill contracts, registry, lifecycle, evaluation |
| `tools/` | Tool contracts, registry, capability catalog |
| `execution/` | Validate and execute actions; retry, rollback, result capture |
| `safety/` | Risk classification, permissions, approval, policy decisions |
| `learning/` | Preference extraction, workflow learning, skill synthesis, proposals |
| `interaction/` | Text, voice, avatar, notification output |
| `protocols/` | A2A and MCP protocol adapters (boundary only) |
| `infrastructure/` | Technical adapters: LLM, Windows, browser, filesystem, terminal, speech, storage |
| `observability/` | Logs, traces, metrics, events, audit |

---

## Context Model

Beta distinguishes five types of context:

1. **Conversation Context** — the current dialogue between user and Primary Agent.
2. **Task Context** — goal, plan, steps, owner, artifacts, approval, and result.
3. **Agent Private Context** — each agent's temporary working state.
4. **Shared Environment Context** — observed state of the current machine.
5. **Long-Term Memory** — persistent knowledge across sessions.

Context builders assemble views from these sources. They do not own state.

---

## Memory Model

Long-term memory is never written directly by agents.

All memory writes go through a `MemoryProposal` that must pass policy evaluation
before being promoted to `active` memory.

Every memory entry carries: `source`, `scope`, `confidence`, `version`, `status`.

Memory types: user preferences, project facts, workflows, experience, learned rules.

---

## A2A and MCP Boundary

- **A2A** is used for agent-to-agent communication across process, host, or trust boundaries.
- **MCP** is used for agent-to-tool and agent-to-resource communication.
- Internal agents in the same process use in-process transport (not HTTP).
- A2A and MCP SDKs are isolated in `protocols/` adapters. Their types do not leak into core modules.

---

## Current Status

This repository contains:

- The intended directory structure.
- Architecture documentation in `docs/architecture/`.
- Policy documentation in `docs/policies/`.
- Architecture decision records in `docs/decisions/`.
- Agent definitions (`AGENT.md`) for each planned agent.

**No implementation code exists yet.**
**No dependencies are installed.**
**No virtual environment is created.**
