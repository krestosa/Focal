# Autonomy control plane

Focal uses one serialized lease authority and several permanent execution domains. It does not create temporary workflows to perform ordinary Git operations.

## Architecture

| Component | Responsibility |
|---|---|
| `automation-state.yml` | Serializes functional lease commands and mirrors canonical state into issue #7. |
| `automation/state-v4` | Dedicated branch containing the transactional canonical state file. |
| issue #101 | Dedicated ingress for administrative repository-maintenance commands. |
| `stale-lease-watchdog.yml` | Independently releases expired inactive leases and enforces the hard deadline. |
| `repository-maintenance.yml` | Performs scoped branch, garbage-file and temporary-workflow cleanup while the coordinator is idle. |
| `validation.yml` | Runs repository, unit, Mesa context and compile-link acceptance checks. |

The lease coordinator is unique because lease ownership and command ordering require a single serialized authority. Validation, terminal recovery and maintenance are separate permanent workflows because they have different permissions, triggers and failure domains.

Administrative maintenance does not acquire a functional lease. It reads both the transactional state and its issue #7 mirror, requires both to be `IDLE`, and shares `concurrency.group: focal-automation-state` so it cannot overlap a functional state transition.

## Reliability fixes

1. **Mandatory terminal recovery.** The independent terminal guard forces a `PARTIAL` release at `hardKillAt`, preserving branch, PR and checkpoint information in `pendingRecovery`.
2. **Terminal report gate.** A cycle must submit `assert_terminal` after `release`. It is accepted only when canonical state is `idle`, `runId` is null and the requested run matches `lastRunId`.
3. **Functional delivery and reconciliation are independent.** A release may record `functionalCheckpointSha` and a pending `reconciliation` object without retaining the lease.
4. **Independent watchdog.** The terminal guard runs every five minutes under the same concurrency lock but in a separate workflow.
5. **Transactional state.** Canonical state lives at `.focal/automation-state.json` on `automation/state-v4`. Updates use the current blob SHA as compare-and-swap. Issue #7 is the functional command surface and human-readable mirror, not the persistent store.
6. **Permanent scoped maintenance.** Repository cleanup is performed by one reviewed workflow. It accepts `branches`, `garbage`, `temporary_workflows` or `all`; issue #101 makes the existing workflow invocable by an issue edit without introducing a transport branch.
7. **Replay-safe checkpoints.** Functional commands retain `processedCommandIds`; maintenance commands retain `processedMaintenanceCommandIds` and are applied once per `commandId`.

## Required terminal sequence

A lease-owning cycle must use this sequence regardless of `PASS`, `PARTIAL`, `NO-OP` or error outcome:

1. Preserve the latest remote checkpoint.
2. Submit `release` with the terminal result and any reconciliation handoff.
3. Wait for `LEASE_RELEASED`.
4. Submit `assert_terminal` with the completed `runId`.
5. Wait for `TERMINAL_STATE_CONFIRMED`.
6. Produce the terminal report.

The terminal guard is a recovery mechanism, not a replacement for this sequence.

## Administrative maintenance command

Issue #101 contains one managed JSON command:

```json
{
  "schemaVersion": 1,
  "commandId": "<unique>",
  "operation": "repository_maintenance",
  "scope": "branches | garbage | temporary_workflows | all",
  "dryRun": true
}
```

A user request to delete branches already absorbed by `main` maps to `scope: branches`. It is an execution request, not a request to implement another workflow. The route must use issue #101 or the permanent workflow dispatch; it must not create a branch, commit, pull request or workflow merely to invoke maintenance.

## Maintenance safety

Maintenance may delete:

- branches fully behind the default branch, provided they are not protected, do not have an open pull request and are not the state branch;
- `.DS_Store`, `Thumbs.db`, `*.orig`, `*.rej`, Python bytecode caches and pytest caches;
- workflow files containing the explicit temporary marker.

It preserves unmerged work, open-PR branches, protected branches, the default branch, the transactional state branch and unmarked workflows.

For `scope: branches`, the following postconditions are mandatory:

- no branch was created;
- no pull request or workflow was created;
- the default-branch head is unchanged;
- the final branch count is less than or equal to the initial branch count;
- every deleted branch was present in the precomputed deletion plan.

If the permanent execution route is unavailable, the operation stops as unavailable. It does not repair or extend the workflow unless the user explicitly requested implementation or repair rather than execution.
