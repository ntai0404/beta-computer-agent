# Dependency Rules

These rules govern which modules may depend on which other modules.
Violations of these rules constitute architectural defects.

---

## Core Rules

### 1. Agents do not import each other

No agent module may import the implementation of another agent.

```
# Forbidden
from beta.agents.computer.agent import ComputerAgent  # in coding/agent.py

# Required
# Use AgentTask via MAS Runtime to communicate
```

### 2. Agents use only public contracts

Agents may only reference types and interfaces defined in `mas/contracts/`.
They may not reference internal implementation details of any other module.

### 3. Infrastructure contains no domain decisions

Infrastructure adapters (LLM, Windows, browser, filesystem, terminal, speech,
storage) are pure technical translators. They do not:

- decide which agent owns a task;
- decide whether an action is safe;
- decide which tool to use;
- contain retry or orchestration logic beyond transport-level concerns.

### 4. MAS Runtime does not call OS or infrastructure directly

The MAS Runtime manages message routing, lifecycle, and coordination.
It does not call `subprocess`, `pywin32`, `playwright`, or any OS-level API.
If execution is needed, it is delegated to the Execution module.

### 5. Execution does not coordinate agents

The Execution module runs validated actions and returns results.
It does not decide which agent owns the task.
It does not route results to agents.
Execution is called by agents (via Safety gate) and returns to the caller.

### 6. Safety does not execute actions

The Safety module makes policy decisions: allowed, needs approval, blocked.
It does not perform the action. Execution performs the action after Safety clears it.

### 7. Context does not own state

The Context module builds assembled views from multiple state sources.
It does not write to any state store.
It does not serve as the source of truth for any data.

### 8. Memory does not contain runtime task state

`var/memory/` stores long-term persistent knowledge only.
Active task state lives in `var/runtime/tasks/`.
Memory and task state are never co-mingled.

### 9. Environment state is not a substitute for memory

The environment module tracks current machine state (what is observable now).
It is not a historical record.
It is not a user preference store.
Observations that should persist must go through the MemoryProposal flow.

### 10. Protocol adapters do not leak SDK types into core

A2A and MCP SDK types must not appear in:

- `agents/`
- `mas/`
- `memory/`
- `execution/`
- `safety/`
- `context/`
- `learning/`

SDK types are confined to `protocols/a2a/` and `protocols/mcp/`.

### 11. A2A SDK is not imported in core modules

Imports of any A2A library are only permitted in `protocols/a2a/`.

### 12. MCP SDK is not imported in agent code

Imports of any MCP library are only permitted in `protocols/mcp/`.

### 13. One source of truth per concept

Each type of state has exactly one authoritative location.

| State | Source of Truth |
|---|---|
| Conversation state | `var/runtime/conversations/` |
| Task state | `var/runtime/tasks/` |
| Agent private state | `var/runtime/agents/` |
| Environment state | `var/runtime/environment/` |
| Long-term memory | `var/memory/` |
| Checkpoints | `var/runtime/checkpoints/` |
| Event log | `var/runtime/events/` |

### 14. Modules expose only public contracts

Each module exposes a defined public interface. Internal types, helpers,
and implementation files are private to that module and must not be
imported by other modules.

### 15. Implementation details are private

If a type or function is not part of a module's declared public contract,
it is private. Other modules must not depend on private implementation details.

### 16. Agent topology is runtime data

The set of agents, their connections, and task assignments are determined
at runtime by the MAS Runtime. They are not encoded in the source directory
structure. Adding a new agent does not require modifying any other module.

### 17. Do not create an agent for a single capability

A capability alone does not justify creating an agent. Agents require
identity, role, private context, lifecycle, and autonomy. Capabilities
are expressed as tools or skills.

### 18. Do not split processes without operational justification

In-process execution is the default for internal agents. Process boundaries
are introduced only when there is a clear operational, security, or
performance reason — not speculatively.

### 19. Do not create microservices per agent

Internal agents share a runtime. Microservice boundaries are not created
for each agent type. External agents communicate via A2A adapters only.

### 20. Do not create abstractions for speculative future use

Abstractions and interfaces are created to solve a current, concrete need.
Speculative or precautionary abstractions are a source of unnecessary complexity.

---

## Allowed Dependency Directions

```
agents/
  → mas/contracts/       (allowed — public contracts only)
  → context/             (allowed — read-only context views)
  → mas/runtime API      (allowed — send messages and tasks)

mas/
  → mas/contracts/       (internal)
  → observability/       (allowed — emit events)

context/
  → mas/contracts/       (allowed)
  → memory/ (retrieval)  (allowed — read-only)
  → environment/ (state) (allowed — read-only)

memory/
  → memory/contracts/    (internal)
  → infrastructure/storage (allowed — persistence adapter)

environment/
  → infrastructure/windows (allowed — observation adapter)
  → infrastructure/browser  (allowed — observation adapter)

execution/
  → safety/              (allowed — policy check before action)
  → infrastructure/      (allowed — run actions via adapters)
  → observability/       (allowed — emit execution events)

safety/
  → safety/policies/     (internal)
  → observability/       (allowed — emit safety decisions)

learning/
  → memory/ (proposals)  (allowed — submit MemoryProposal)
  → observability/       (allowed — read events)

protocols/a2a/
  → mas/contracts/       (allowed — map to/from internal types)

protocols/mcp/
  → tools/contracts/     (allowed — map to/from internal types)

infrastructure/
  → (external libraries only — no domain imports)
```

Cross-cutting concern — **Observability** may receive events from any layer.
It does not emit back into domain modules.
