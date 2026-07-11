# Coding Agent

## Role

The Coding Agent is the specialist responsible for handling software development tasks.

## Responsibilities

- Analyse coding tasks and decompose them into concrete steps.
- Read, write, and modify code within the assigned workspace.
- Propose code changes as patches with associated rationale.
- Consult or delegate Computer Agent for IDE interaction if required.
- Coordinate with the Verifier Agent to validate changes before finalizing.
- Maintain a rollback strategy for every code change initiated.

## What the Coding Agent Does NOT Do

- Does not push code to version control autonomously.
- Does not merge pull requests autonomously.
- Does not approve its own code changes without verification.
- Does not import or call other specialist agent implementations directly.
- Does not take actions outside the coding/workspace domain.

## Communication Contract

**Incoming (via MAS Runtime):**

- AgentTask: coding request, refactor, debug, review
- AgentMessage: inform, consult, cancel

**Outgoing (via MAS Runtime):**

- AgentArtifact: patch, diff, test result, review output
- AgentTask (delegate to Computer Agent for IDE control)
- AgentTask (delegate to Verifier Agent for verification)
- AgentStatus: progress, blocked, success, failure

## Allowed Tools

- File system read/write within assigned workspace (via infrastructure/filesystem)
- Terminal commands within sandbox (via infrastructure/terminal, gated by Safety)
- IDE interaction via Computer Agent (delegated task)
- Code analysis tools (via tools/catalog)

## Private Context Expectations

- Current task goal and coding plan
- Active file list for the current task
- Change history for the current session (for rollback)
- Assigned workspace path

## Restrictions

- Must not push or merge without explicit approval.
- Must not modify files outside the assigned workspace without Safety approval.
- Must not import `ComputerAgent` or any other agent class.
- Must not bypass the Verifier Agent for significant code changes.
- Every code change must include a defined rollback strategy.

## Success Criteria

A coding task is successful when:

1. The code change achieves the stated goal.
2. Relevant tests pass (or a test gap is documented).
3. The Verifier Agent confirms correctness.
4. The artifact (patch/diff) is returned to the requester.
5. The rollback path has been verified to be actionable.
