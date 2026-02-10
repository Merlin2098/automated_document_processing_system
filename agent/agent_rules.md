# Agent Governance Rules

## Version

3.0.0

## Scope

GLOBAL GOVERNANCE DOCUMENT

This document defines the **global governance, security model, and workspace policies**
for all AI agents operating in this repository.

It is a **human-authoritative reference**, not an execution prompt.

---

## 1. Purpose

The purpose of this document is to:

- Establish a shared mental model of the repository
- Define immutable security and workspace boundaries
- Prevent unsafe or unintended agent behavior
- Serve as a reference for designing agent-specific contracts

Agent-specific behavior MUST be defined in:

- `agent/agent_inspector/agent_inspector.md`
- `agent/agent_executor/agent_executor.md`
- Other `agent_<name>.md` contracts

---

## 2. Governance Model

### 2.1 Authority Layers

| Layer               | Description                        | Mutability |
| ------------------- | ---------------------------------- | ---------- |
| Governance          | Repository-wide rules and security | Rare       |
| Agent Contract      | Role-specific operational rules    | Versioned  |
| Runtime Constraints | Per-execution limitations          | Ephemeral  |

No agent may operate under more than **one active contract** at runtime.

---

## 3. Repository Mental Model

### 3.1 `agent/` Directory

Purpose:

- Agent memory
- Agent outputs
- Agent logs
- Agent-readable documentation

Characteristics:

- Autonomous workspace
- Writable by agents (within constraints)
- NOT part of application runtime

Key subdirectories:

- `agent/agent_outputs/` — plans, reports, artifacts
- `agent/agent_logs/` — execution logs
- `agent/temp/` — temporary agent files

---

### 3.2 Application Source Code

Directories such as:

- `src/`
- `ui/`
- `tests/`

Are considered **PROTECTED APPLICATION CODE**.

Rules:

- Agents MUST NOT modify source code directly
- Source code changes require:
  - A validated plan
  - Explicit authorization
  - Human approval (unless otherwise stated)

---

## 4. Security and Protection Policy

### 4.1 Protected Files (GLOBAL BLACKLIST)

The following files and paths are IMMUTABLE by default:

```yaml
protected_files:
  documentation:
    - agent/agent_rules.md
    - agent/architecture_proposal.md
    - agent/agent_inspector/agent_inspector.md
    - agent/agent_executor/agent_executor.md
    - agent/agent_protocol/README.md
    - README.md

  configuration:
    - .git/**
    - .env
    - .env.*
    - credentials.json
    - secrets.*
    - requirements.txt
    - pyproject.toml
    - setup.py
    - .pre-commit-config.yaml
```

Any attempt to modify protected files MUST be rejected.


## 5. Workspace Persistence Policy

* Agent-generated plans MUST be persisted to disk
* Historical plans and reports MUST NOT be deleted
* Temporary files MAY be cleaned up by the agent
* Outputs MUST be stored under `agent/agent_outputs/`

Persistence guarantees:

* Auditability
* Traceability
* Reproducibility

---

## 6. Documentation Governance

Documentation generation is  **restricted by default** .

Rules:

* Agents MUST NOT generate new documentation unless:
  * Explicitly requested, OR
  * Strictly required to complete a task
* When authorized:
  * Documentation must be minimal
  * Documentation must be purpose-driven
  * Duplication is forbidden

---

## 7. Change Authority


| Change Type         | Authority           |
| ------------------- | ------------------- |
| Governance rules    | Human-only          |
| Agent contracts     | Human-reviewed      |
| Runtime constraints | User / Orchestrator |
| Execution plans     | Agent Inspector     |
| Execution           | Agent Executor      |


Agents MUST escalate ambiguity instead of guessing intent.

---

## 8. Conflict Resolution

If a conflict arises between:

* Governance rules
* Agent contracts
* Runtime constraints

Resolution order is:

1. Governance rules
2. Agent contract
3. Runtime constraints

---

## 9. Design Principle

> Governance defines **what is never allowed**
>
> Contracts define **what an agent may do**
>
> Constraints define **what is allowed right now**

---

## 10. Status

This document is:

* Informational for agents
* Authoritative for humans
* NOT intended to be injected into runtime prompts

---

**Version:** 3.0.0

**Last Updated:** 2026-02-06

**Classification:** GOVERNANCE-ONLY
