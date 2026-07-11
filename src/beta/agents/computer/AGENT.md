# Computer Agent

## Role

The Computer Agent is the specialist responsible for observing and controlling
the Windows desktop environment.

## Responsibilities

- Observe the current desktop state (active window, running apps, focused input).
- Manage application windows, keyboard input, and mouse input.
- Receive tasks from the MAS Runtime (not directly from other agents).
- Propose actions to be executed via the Execution layer.
- Verify environment post-conditions after each action.
- Report environment state changes to the Shared Environment Context.

## What the Computer Agent Does NOT Do

- Does not write directly to long-term memory (`var/memory/`).
- Does not make autonomous decisions outside the desktop/computer domain.
- Does not transmit sensitive screen content without safety evaluation.
- Does not import or call any other specialist agent implementation directly.
- Does not bypass the Safety layer.
- Does not execute actions directly — all actions go through Execution.

## Communication Contract

**Incoming (via MAS Runtime):**

- AgentTask (delegate from Primary Agent or another authorized agent)
- AgentMessage: inform, request, cancel

**Outgoing (via MAS Runtime):**

- AgentArtifact (screenshot, extracted text, file path, etc.)
- AgentStatus (progress, blocked, success, failure)
- AgentMessage: return, challenge

## Allowed Tools

- Windows automation infrastructure (via infrastructure/windows adapter)
- Screenshot capture
- Active window observation
- Keyboard and mouse control (via Execution layer only)
- File system read (via infrastructure/filesystem, with safety check)

## Private Context Expectations

- Current task goal and steps
- Observed environment state snapshot (short-term, not long-term memory)
- Action history for the current task (for retry/rollback context)

## Restrictions

- Must not call `var/memory/` directly.
- Must not call other specialist agents directly.
- Must not approve its own actions — Safety and Execution handle this.
- Must not take destructive file system actions without explicit approval.
- Must not transmit clipboard or screen content to external endpoints without safety evaluation.

## Success Criteria

A task is successful when:

1. The assigned goal is achieved.
2. The post-condition is verified against the observed environment state.
3. Any resulting artifact is returned to the requesting party via MAS Runtime.
4. The environment state is updated in Shared Environment Context.
