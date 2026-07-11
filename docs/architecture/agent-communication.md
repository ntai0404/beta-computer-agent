# Agent Communication

Beta uses a single unified semantic communication model for all agent interactions.
The underlying transport (in-process or A2A) is an implementation detail that
does not change the semantic contract.

---

## One Semantic Model

All agents use the same message and task vocabulary regardless of where they run.

Core semantic types:

- `AgentIdentity` — who is communicating
- `AgentCard` — published capability declaration
- `AgentMessage` — a single communication unit
- `AgentTask` — a unit of work with lifecycle
- `AgentArtifact` — a typed result
- `AgentStatus` — a lifecycle or progress update
- `AgentEnvelope` — transport wrapper (carries routing metadata)
- `Delegation` — bounded sub-task assignment (owner retained)
- `Handoff` — full ownership transfer

These types are defined in `mas/contracts/`. They are **not** SDK types.
They are not imported from A2A or MCP libraries.

---

## Transport: In-Process vs. A2A

### In-Process Transport

Used for internal agents running in the same process:

- Direct message queue delivery via MAS Runtime.
- No HTTP server required.
- No serialization overhead.
- Agents are registered in the shared agent registry.

### A2A Transport

Used for:

- External agents (different process, different host).
- Agents from other frameworks or vendors.
- Remote agents accessed over a network.

A2A adapters live in `protocols/a2a/`. They map Beta's internal contracts
to and from A2A protocol objects. A2A SDK types do not leak into core modules.

**Rule:** Internal agents never need HTTP to talk to each other.

---

## MCP Transport

MCP is used for agent-to-tool and agent-to-resource communication.

- Agents declare tool requirements via their AgentCard.
- Tools are accessed through MCP server connections managed in `protocols/mcp/`.
- MCP SDK types do not appear in agent code.

---

## Interaction Types

### `request`

Agent A asks Agent B to perform an action. Agent B is expected to respond
with an artifact, status, or challenge.

### `delegate`

Agent A creates a bounded sub-task and assigns it to Agent B.
Agent A retains overall task ownership. Agent B returns an artifact or status.

### `handoff`

Agent A transfers full ownership of a task to Agent B.
Agent A is no longer responsible. Agent B becomes the new owner.

### `consult`

Agent A requests Agent B's opinion or review.
Agent B does not acquire ownership. Agent A makes the final decision.

### `broadcast`

An agent emits an event or announcement to all subscribers of a topic.
No response is required.

### `return`

Agent B has completed its work and is returning control (and an artifact
or status) to Agent A.

### `cancel`

Agent A cancels an outstanding task or request. Agent B stops work and
acknowledges.

### `challenge`

Agent B raises a concern about the safety, feasibility, or goal of a
request. The MAS Runtime routes the challenge to the appropriate handler
(e.g., Primary Agent or Safety).

### `artifact`

A standalone delivery of a typed result, produced by one agent for
the requesting agent or the MAS Runtime.

### `progress`

A lightweight status update from an agent indicating current step,
percentage, or a user-facing description of ongoing work.

---

## Minimum Necessary Context

When sending a task or message, agents must include only the context
that the recipient genuinely needs to do its work.

Rules:

- Do not send full conversation history if only the current goal is needed.
- Do not send full long-term memory if only a preference is needed.
- Do not send screen content if only a file path is needed.
- Do not send personal data if only a task ID is needed.

This rule is especially critical when communicating with external agents
across A2A boundaries, which are **trust boundaries**.

---

## Trust Boundary

External agents (accessed via A2A) are trust boundaries.

Rules at trust boundaries:

- Validate all incoming messages before processing.
- Do not send full memory contents over A2A.
- Do not assume external agents share the same safety policy.
- Do not expose internal system identifiers unnecessarily.
- Apply the same safety evaluation to external-agent-initiated actions as to user-initiated actions.

---

## Message Routing

All messages are routed by the MAS Runtime:

```
Sender Agent
 └─ creates AgentMessage or AgentTask
      └─ MAS Runtime
           ├─ looks up recipient in agent registry
           ├─ resolves transport (in-process or A2A)
           ├─ delivers to recipient mailbox
           └─ tracks delivery and acknowledgement
```

Agents do not address each other by implementation class.
They address each other by `agent_id` or by capability query.
