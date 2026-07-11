# Primary Agent

## Role

The Primary Agent is the main conversational representative of Beta.
It is the face of the system from the user's perspective.

## Responsibilities

- Represent Beta in all conversations with the user.
- Maintain conversation continuity and coherence across turns.
- Understand the user's goal and intent.
- Discover which specialist agent is best suited for each task.
- Delegate sub-tasks to specialist agents via MAS Runtime.
- Execute handoffs when full ownership transfer is appropriate.
- Synthesize and summarize results from specialist agents.
- Communicate progress, blockers, and outcomes back to the user.

## What the Primary Agent Does NOT Do

- Does not directly execute OS-level actions.
- Does not own the memory engine.
- Does not own the safety engine.
- Does not contain all of Beta's business logic.
- Does not import specialist agent implementations directly.
- Does not bypass safety or execution layers.

## Communication Contract

**Incoming:**

- User messages (via Interaction layer)
- AgentStatus, AgentArtifact, AgentMessage from MAS Runtime

**Outgoing:**

- AgentTask (delegate to specialist agents via MAS Runtime)
- Handoff (transfer ownership to a specialist agent)
- Consult (request opinion without transferring ownership)
- User-facing responses (via Interaction layer)

## Allowed Tools

- Context assembly (read-only)
- Memory retrieval (read-only, via Memory service)
- MemoryProposal creation (write proposals only)
- Interaction output (text, voice, notification)

## Private Context Expectations

- Current conversation context
- Active task summary (not raw task state)
- Active delegation registry (what has been delegated to whom)

The Primary Agent does not hold raw task state. Task state is owned by MAS Runtime.

## Restrictions

- Must not call execution directly.
- Must not call infrastructure adapters directly.
- Must not read or write `var/memory/` directly.
- Must not import `ComputerAgent`, `CodingAgent`, or any specialist agent class.
- Must not reduce the active safety policy.

## Success Criteria

A conversation turn is successful when:

1. The user's intent is correctly understood.
2. The appropriate agent(s) are engaged.
3. The result is synthesized into a coherent, accurate response.
4. Any side effects are verified (via Verifier Agent where appropriate).
5. Any memory-worthy observations are submitted as MemoryProposals.
