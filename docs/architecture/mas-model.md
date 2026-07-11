# MAS Model

This document describes the conceptual model of the Beta Multi-Agent System.

---

## Agent Identity

Every agent has a stable identity:

- `agent_id`: unique, immutable identifier within the system.
- `agent_type`: the class or role of agent (primary, computer, coding, etc.).
- `display_name`: human-readable label.
- `capabilities`: declared capability set (not implementation references).
- `tool_permissions`: explicit list of tools the agent is allowed to invoke.

An **AgentCard** is the published declaration of an agent's identity, capabilities,
and communication contract. AgentCards are registered with the MAS Runtime.

---

## Agent Autonomy

Each agent is autonomous within its declared domain:

- It can make decisions without being instructed step-by-step.
- It can request input, raise objections, or propose alternatives.
- It can declare itself blocked and request assistance.
- It cannot act outside its declared capability set.
- It cannot bypass safety or execution layers.

---

## Agent Registry

The MAS Runtime maintains an agent registry:

- Maps `agent_id` to capability declarations and communication endpoints.
- Tracks agent lifecycle state: `idle`, `active`, `blocked`, `suspended`.
- Allows dynamic registration of new agents at runtime.
- Agent topology is **runtime data** — not hard-coded in source.

---

## Mailbox

Each agent has a mailbox managed by the MAS Runtime:

- Incoming messages and tasks are queued in the mailbox.
- Agents consume from their mailbox at their own pace.
- The Runtime guarantees delivery ordering within a conversation.
- External agents communicate through protocol adapters (A2A) before reaching the mailbox.

---

## Task

A task represents a unit of work with ownership and a lifecycle:

- `task_id`: unique identifier.
- `owner_agent_id`: the agent currently responsible.
- `goal`: the desired outcome.
- `status`: created → planning → waiting_approval → running → verifying → completed / failed / cancelled.
- `artifact`: the result produced by the task.
- `approval_requirement`: whether human or verifier approval is required before execution.

---

## Message

A message is the atomic unit of agent communication:

- `message_id`
- `sender_agent_id`
- `recipient_agent_id` (or broadcast topic)
- `conversation_id`
- `task_id` (if related to a task)
- `intent`: one of the defined interaction types (see below)
- `payload`: structured content (typed, not raw text)
- `timestamp`

---

## Artifact

An artifact is a typed result returned by an agent:

- `artifact_id`
- `produced_by_agent_id`
- `task_id`
- `artifact_type`: report, patch, screenshot, transcript, verification_result, etc.
- `content`: the artifact payload
- `confidence`: estimated reliability
- `timestamp`

---

## Interaction Types

| Type | Description |
|---|---|
| `inform` | One agent notifies another of a fact or status |
| `request` | One agent asks another to perform something |
| `delegate` | A delegates a sub-task to B; A retains ownership |
| `handoff` | A transfers full ownership of a task to B |
| `consult` | A asks B for opinion; B does not take ownership |
| `broadcast` | A sends an event to all interested subscribers |
| `return` | B completes work and returns control to A |
| `cancel` | A cancels a task or outstanding request |
| `challenge` | B disputes the goal, safety, or feasibility of a request |

### Delegate vs. Handoff

**Delegate:** Agent A retains task ownership. Agent B does a bounded sub-task and
returns an artifact or status. Agent A synthesizes the result.

**Handoff:** Agent A transfers full task ownership to Agent B. Agent A is no
longer responsible for the outcome.

### Consult

Agent A asks Agent B for an opinion, review, or recommendation.
Agent B does not acquire ownership. Agent A makes the final decision.

### Broadcast

An agent emits an event or announcement to all agents subscribed to a topic.
No response is expected. Used for status updates and shared environment notifications.

---

## Ownership

Every active task has exactly one owning agent at any point in time.

Ownership changes only through:

- `delegate` (temporary, bounded sub-task; A retains overall ownership)
- `handoff` (permanent transfer of ownership for this task)

The MAS Runtime tracks and enforces ownership at all times.

---

## Agent Lifecycle

```
registered
 └─ idle
     ├─ active (task received)
     │   ├─ blocked (waiting for input, sub-task, or approval)
     │   └─ completing
     │        └─ idle
     └─ suspended (paused by runtime or user)
         └─ idle
```

Lifecycle transitions are managed by the MAS Runtime, not by agents themselves.

---

## Dynamic Topology

The set of active agents, their connections, and active task assignments are
runtime data. They are not fixed by the module structure.

This means:

- New agent types can be added without modifying the core MAS.
- The system can operate with a subset of agents.
- Agent availability is determined at runtime.

---

## Event and Subscription System

The MAS Runtime maintains an event bus:

- Agents may subscribe to topic categories (e.g., `environment.changed`, `task.completed`).
- Events are emitted by agents, the runtime, and infrastructure observers.
- Subscriptions are registered dynamically and managed by the runtime.
- This enables broadcast communication without direct coupling.
