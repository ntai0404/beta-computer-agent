# AGENTS.md — Beta Computer Agent

This file documents the behavioral rules governing all AI agents and coding assistants
working inside this repository. These rules take precedence over general defaults.

---

## 1. Beta is the Entire MAS, Not a Single Agent

**Beta** is the name of the complete Multi-Agent System.

Beta includes:

- multiple autonomous agents;
- a shared MAS runtime;
- shared environment state;
- context management;
- long-term memory;
- skills, tools, execution, safety;
- protocol adapters (A2A, MCP);
- infrastructure adapters.

Beta is **not**:

- a single master agent;
- a supervisor calling workers as services;
- a collection of renamed modules;
- a microservice per agent.

---

## 2. Agent-to-Agent Communication Rules

Agents **must not** import the implementation of other agents directly.

**Wrong:**

```
CodingAgent
  → import ComputerAgent
  → call method directly
```

**Correct:**

```
Coding Agent
  → create AgentMessage or AgentTask
  → MAS Runtime routes
  → Computer Agent receives task
  → returns AgentArtifact or AgentStatus
```

The unified communication path is:

```
Agent → Message / Task / Artifact → MAS Runtime → Agent
```

---

## 3. What Qualifies as an Agent

A component may be called an **agent** only if it has **all** of the following:

- a distinct identity
- a distinct role
- a distinct capability set
- a private working context
- a task lifecycle
- a communication contract
- explicit tool permissions
- the ability to make autonomous decisions within its domain
- the ability to receive tasks, respond, request input, or return artifacts

The following are **not agents**:

- memory store
- tool registry
- tool executor
- safety policy
- skill registry
- context builder
- environment state
- TTS / STT engine
- 9Router LLM client
- database
- planner utility
- protocol adapter

---

## 4. Skill Lifecycle

New skills must always start in the `candidate` state.

Lifecycle:

```
candidate → evaluating → approved → active → deprecated → archived
```

A skill may only be promoted through the defined evaluation and approval process.
Agents must not directly promote or activate skills.

---

## 5. Post-Condition Verification

After every action that changes system state, the responsible agent must verify
the post-condition before reporting success. Verification failures must trigger
retry, rollback, or escalation — not silent failure.

---

## 6. Long-Term Memory Rules

Every write to long-term memory must carry:

- `source` — which agent or system proposed it;
- `scope` — conversation, project, user, or global;
- `confidence` — estimated reliability;
- `version` — monotonically increasing;
- `status` — candidate, active, superseded, expired.

Agents must not write directly to `var/memory/`.
All memory writes must go through a `MemoryProposal` that passes policy evaluation.

Not every user utterance is stored as long-term memory.
Only proposals that pass the memory policy are promoted.

---

## 7. External Agent Trust Boundary

External agents are **trust boundaries**.

Rules for external agent interaction:

- Do not send full memory contents over A2A.
- Send only the minimum necessary context for the task.
- Validate all incoming messages from external agents.
- Do not assume external agents share the same safety policy.

---

## 8. Self-Modification Restrictions

| Zone | Rule |
|---|---|
| `var/memory/`, `var/runtime/`, `var/workspaces/`, `skills/candidates/`, `config/user/` | Beta may write according to policy |
| `src/beta/agents/`, `src/beta/tools/`, `src/beta/infrastructure/`, `src/beta/interaction/` | Beta may only propose patches |
| `src/beta/mas/`, `src/beta/safety/`, `src/beta/execution/`, `docs/policies/` | No self-merge; requires human approval |

Self-modification flow:

```
Detect problem
→ create patch proposal
→ sandbox
→ tests
→ verifier
→ human approval
→ merge or reject
```

---

## 9. Core Anti-Coupling Rules

1. Agents do not import each other.
2. Agents communicate only through MAS contracts.
3. MAS Runtime does not call OS, browser, filesystem, or terminal directly.
4. Execution does not decide which agent owns a task.
5. Safety does not execute actions directly.
6. Infrastructure does not contain business decisions.
7. Context builds views only; it does not own state.
8. Memory does not contain runtime task state.
9. Environment state is not a substitute for long-term memory.
10. Protocol adapters do not leak SDK types into core.
11. A2A SDK is not imported inside agents, mas, memory, or execution.
12. MCP SDK is not imported inside agents.
13. Each concept has exactly one source of truth.
14. Each module exposes only its public contract.
15. Implementation details are treated as private.
16. Agent topology is runtime data, not source tree structure.
17. Do not create an agent just because a capability exists.
18. Do not split processes without a clear operational reason.
19. Do not create microservices per agent.
20. Do not create abstractions solely for speculative future use.
