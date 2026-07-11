# Architecture Overview

## System Flow

```
User
 │
 ▼
Interaction Layer
(text input, voice input, notification display)
 │
 ▼
Primary Agent
(conversation continuity, goal understanding, delegation)
 │
 ▼
MAS Runtime
(message routing, task management, lifecycle, coordination)
 │
 ├─► Computer Agent   (desktop control, window management)
 ├─► Coding Agent     (code analysis, modification, review)
 ├─► Research Agent   (information gathering, synthesis)
 └─► Verifier Agent   (independent evaluation, post-condition check)
        │
        ▼
   Context View Assembly
   (conversation + task + environment + memory fragments)
        │
        ▼
   Skills / Tools
   (skill registry, tool registry, capability catalog)
        │
        ▼
   Safety
   (risk classification, permissions, approval gate)
        │
        ▼
   Execution
   (validate, execute, retry, rollback, capture result)
        │
        ▼
   Infrastructure
   (LLM, Windows automation, browser, filesystem, terminal, speech, storage)
        │
        ▼
   Result / Artifact
   (returned to agent → MAS Runtime → requesting agent → Primary Agent → User)
        │
        ▼
   Memory Proposal
   (learning module proposes; memory policy evaluates; promote or reject)
```

---

## Layer Responsibilities

### Interaction Layer

Handles all user-facing I/O:

- Text input and output.
- Voice input (STT) and output (TTS).
- Avatar state management.
- Approval dialogs and notifications.

The Interaction layer does not contain agent logic.

### Primary Agent

- The single point of contact between the user and the MAS.
- Maintains conversation continuity.
- Understands user intent and delegates tasks.
- Synthesizes results from specialist agents.

### MAS Runtime

The shared runtime that enables all agent cooperation:

- Agent registry and lifecycle management.
- Mailbox-based message delivery.
- Task creation, routing, ownership tracking.
- Delegation and handoff coordination.
- Event publication and subscription.

### Specialist Agents

Each specialist agent is autonomous within its domain:

- **Computer Agent** — desktop and OS control.
- **Coding Agent** — software development tasks.
- **Research Agent** — information gathering and synthesis.
- **Verifier Agent** — independent evaluation and verification.

### Context View Assembly

Assembles a relevant, filtered, scoped view of context for each agent:

- Pulls from Conversation Context, Task Context, Environment State, and Memory.
- Does not own any state — read-only assembly.

### Skills and Tools

- **Skills**: multi-step reusable capabilities that agents can invoke.
- **Tools**: atomic, typed, sandboxed actions with defined input/output schemas.

### Safety

Policy-gated decision point for all actions:

- Classifies risk level.
- Enforces permissions and approval requirements.
- Protects secrets and blocks destructive operations.

### Execution

Responsible for the controlled execution of actions:

- Validates action inputs.
- Applies timeout and retry logic.
- Captures results and errors.
- Triggers rollback when required.

### Infrastructure

Technical adapters that bridge the domain model to external systems:

- LLM (via 9Router, OpenAI-compatible).
- Windows automation.
- Browser control.
- Filesystem.
- Terminal.
- Speech (TTS, STT).
- Database and storage.

Infrastructure adapters contain no business decisions.

### Memory Proposal

After a task, the Learning module observes outcomes and generates `MemoryProposal` entries.
The Memory Policy evaluates each proposal before any promotion to long-term memory.

---

## Design Invariants

- Agent topology is determined at runtime, not encoded in source structure.
- All inter-agent communication flows through MAS Runtime.
- Safety is never bypassed.
- Execution is the only layer that runs actions against the OS or infrastructure.
- Context is assembled on demand; it is never persisted as a canonical state.
