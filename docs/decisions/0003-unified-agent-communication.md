# ADR-0003: Unified Agent Communication Model

**Status:** Accepted  
**Date:** 2026-07

---

## Context

In a multi-agent system, there are many ways agents can communicate:
direct function calls, HTTP REST, message queues, A2A protocol, MCP protocol.

If each communication path uses different types and conventions, the system
becomes difficult to reason about, test, and extend.

There is also a risk that external protocol SDKs (A2A, MCP) contaminate
core agent and MAS logic with transport-specific types.

---

## Decision

Beta uses **one unified semantic communication model** for all agent interactions.

The semantic model is defined in `mas/contracts/` and consists of:

- `AgentIdentity`
- `AgentCard`
- `AgentMessage`
- `AgentTask`
- `AgentArtifact`
- `AgentStatus`
- `AgentEnvelope`
- `Delegation`
- `Handoff`

These types are Beta's own domain types. They are not imported from A2A or MCP libraries.

---

## Two Transports, One Model

### In-Process Transport

- Used for internal agents in the same process.
- No HTTP server required.
- No serialization overhead.
- Messages are delivered via in-process queues managed by MAS Runtime.

### A2A Transport

- Used for external agents, remote agents, or agents from other frameworks.
- A2A adapters in `protocols/a2a/` translate between Beta's internal contracts
  and A2A protocol objects.
- A2A SDK types do not appear outside `protocols/a2a/`.

---

## MCP Transport

- Used for agent-to-tool and agent-to-resource communication.
- MCP adapters in `protocols/mcp/` manage the connection to MCP servers.
- MCP SDK types do not appear in agent code.

---

## Rules

1. Internal agents **never** need to start an HTTP server to communicate with each other.
2. A2A SDK types are confined to `protocols/a2a/`.
3. MCP SDK types are confined to `protocols/mcp/`.
4. Agent code references only `mas/contracts/` types for communication.
5. Adding a new transport does not require changing agent code.

---

## Consequences

- Agents are transport-agnostic. An agent does not know or care whether
  the message it receives came from in-process delivery or A2A.
- The A2A protocol is a capability at the system boundary, not a requirement
  for internal communication.
- Testing agents in isolation is possible without any network infrastructure.
- Future transport changes (e.g., switching A2A implementations) do not affect agent code.
