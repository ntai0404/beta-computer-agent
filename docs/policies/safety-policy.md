# Safety Policy

This document defines the safety classification system for Beta Computer Agent.

---

## Risk Levels

### Low Risk

Actions that are fully reversible, affect only the local session state,
and pose no data loss or privacy risk.

Examples:

- reading a file;
- taking a screenshot;
- switching application focus;
- querying environment state;
- reading clipboard content (local, not transmitted).

**Approval required:** None. Logged automatically.

---

### Medium Risk

Actions that have side effects that are not immediately reversible,
or that affect user data or system configuration.

Examples:

- writing a new file;
- editing an existing file;
- creating a directory;
- sending a local notification;
- submitting a form within an already-open app;
- running a sandboxed terminal command with no network access.

**Approval required:** Automatic approval if within pre-authorized scope.
Out-of-scope actions require explicit user confirmation.

---

### High Risk

Actions that are potentially irreversible, affect external systems,
involve other people's data, or have financial implications.

Examples:

- deleting a file or directory;
- sending an email or message;
- posting to an external service;
- running a terminal command with network access;
- modifying version-controlled files (push/merge);
- accessing credentials or secrets;
- making a purchase or payment.

**Approval required:** Explicit user approval for each action.
A checkpoint must be created before execution.

---

### Blocked

Actions that are never permitted regardless of approval.

Examples:

- transmitting secrets or credentials to external services without explicit consent;
- disabling or modifying the safety policy;
- self-merging changes to core safety or MAS runtime code;
- deleting audit logs;
- executing unsigned or unverified code from an external source;
- actions that would compromise other users' accounts or data.

**Approval required:** Cannot be unblocked via normal approval flow.
Requires a deliberate policy change by the owner.

---

## Permission Scope

Each agent declares its tool permissions in its `AgentCard`.

Permissions are:

- **Explicit** — only declared tools are permitted.
- **Scoped** — permissions are bounded to the current task's workspace.
- **Revocable** — the safety policy may restrict permissions at any time.

Agents may not acquire permissions beyond their declared scope without
an explicit approval-gated escalation.

---

## Approval Requirements

| Risk Level | Auto-approved | Requires Confirmation | Checkpoint |
|---|---|---|---|
| Low | Yes (if in scope) | No | No |
| Medium | Yes (if in scope) | Only if out of scope | Recommended |
| High | No | Always | Required |
| Blocked | Never | Cannot be approved | N/A |

Approval is presented to the user through the Interaction layer.
Agents do not present approval dialogs directly.

---

## Secret Protection

- Secrets (API keys, passwords, tokens) must never appear in agent messages,
  task context, or logs.
- Secrets are accessed only via the infrastructure layer through a secrets adapter.
- Secrets are never transmitted over A2A to external agents.
- Logging must redact secrets automatically.

---

## Destructive Action Rules

Any action that permanently deletes data, sends data externally, or modifies
shared state for other users is classified as High Risk at minimum, and requires:

1. A checkpoint before execution.
2. Explicit user confirmation.
3. Verifier Agent evaluation of the post-condition.

---

## Send / Delete / Push / Payment Rules

| Action Type | Risk Level | Approval |
|---|---|---|
| Send email or message | High | Explicit per-action |
| Delete file (recoverable) | High | Explicit per-action |
| Delete file (permanent) | Blocked | Cannot be approved via normal flow |
| Git push to remote | High | Explicit per-action |
| Git merge to main | High | Explicit per-action |
| API call (read-only) | Medium | Auto if in scope |
| API call (write) | High | Explicit per-action |
| Payment or purchase | Blocked | Cannot be approved via normal flow |
