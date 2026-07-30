# Autonomy control plane

Focal uses one command ingress and several permanent execution domains. It does not create temporary workflows to perform individual Git operations.

## Architecture

| Component | Responsibility |
|---|---|
| `automation-state.yml` | Serializes lease commands and mirrors canonical state into issue #7. |
| `automation/state-v4` | Dedicated branch containing the transactional canonical state file. |
| `stale-lease-watchdog.yml` | Independently releases expired inactive leases and enforces the hard deadline. |
| `repository-maintenance.yml` | Deletes only allowlisted garbage and fully obsolete branches while the coordinator is idle. |
| `validation.yml` | Runs repository, unit, Mesa context and compile-link acceptance checks. |

The coordinator is unique because lease ownership and command ordering require a single serialized authority. Validation, terminal recovery and maintenance are separate permanent workflows because they have different permissions, triggers and failure domains.

## Reliability fixes

1. **Mandatory terminal recovery.** The independent terminal guard forces a `PARTIAL` release at `hardKillAt`, preserving branch, PR and checkpoint information in `pendingRecovery`.
2. **Terminal report gate.** A cycle must submit `assert_terminal` after `release`. It is accepted only when canonical state is `idle`, `runId` is null and the requested run matches `lastRunId`.
3. **Functional delivery and reconciliation are independent.** A release may record `functionalCheckpointSha` and a pending `reconciliation` object without retaining the lease.
4. **Independent watchdog.** The terminal guard runs every five minutes under the same concurrency lock but in a separate workflow.
5. **Transactional state.** Canonical state lives at `.focal/automation-state.json` on `automation/state-v4`. Updates use the current blob SHA as compare-and-swap. Issue #7 is a command surface and human-readable mirror, not the authoritative store.
6. **Permanent maintenance.** Repository cleanup is performed by one reviewed workflow. Temporary workflows are deleted only when their contents include `# focal-temporary-workflow: true`; common generated garbage is allowlisted. Open-PR, protected, default and state branches are preserved.
7. **Replay-safe checkpoints.** Commands support optional `expectedStateVersion` and `expectedCheckpointSha`, retain a bounded `processedCommandIds` ledger and record per-phase checkpoint metadata.

## Required terminal sequence

A lease-owning cycle must use this sequence regardless of `PASS`, `PARTIAL`, `NO-OP` or error outcome:

1. Preserve the latest remote checkpoint.
2. Submit `release` with the terminal result and any reconciliation handoff.
3. Wait for `LEASE_RELEASED`.
4. Submit `assert_terminal` with the completed `runId`.
5. Wait for `TERMINAL_STATE_CONFIRMED`.
6. Produce the terminal report.

The terminal guard is a recovery mechanism, not a replacement for this sequence.

## Maintenance safety

Scheduled maintenance shares the `focal-automation-state` concurrency group and requires `IDLE`. It may delete:

- branches fully behind the default branch, provided they are not protected, do not have an open pull request and are not the state branch;
- `.DS_Store`, `Thumbs.db`, `*.orig`, `*.rej`, Python bytecode caches and pytest caches;
- workflow files containing the explicit temporary marker.

Unmerged work and unmarked workflows are preserved.
