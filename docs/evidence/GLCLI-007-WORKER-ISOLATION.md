# GLCLI-007 worker isolation evidence

- Reviewed UTC: `2026-07-30`
- Functional merge: [`27fd2b16a3472b5588a3a69e6aba6f93b345f80b`](https://github.com/krestosa/Focal/commit/27fd2b16a3472b5588a3a69e6aba6f93b345f80b)
- Pull request: [#99](https://github.com/krestosa/Focal/pull/99)
- Exact validated head: [`7791428a603525b6a1001c6541973ec35f607665`](https://github.com/krestosa/Focal/commit/7791428a603525b6a1001c6541973ec35f607665)
- Validation: [run 30547008215](https://github.com/krestosa/Focal/actions/runs/30547008215) — `success`
- Evidence level: `STATIC`

## Accepted capability

The public `focal-gl` entrypoint now supervises runtime commands in an isolated child process. The supervisor applies the existing `--timeout` value as a hard deadline, starts a distinct process group/session, terminates the process tree on timeout, escalates to a kill after a bounded grace period, and relays normal output and exit codes unchanged.

Timeout and POSIX signal termination are classified with stable exit code `7`. When `--artifacts` is supplied, the supervisor preserves `worker.stdout.log`, `worker.stderr.log`, and `worker-execution.json`, including timeout and signal metadata.

Regression tests force a hanging child, confirm termination and artifact persistence, classify signal termination, and verify normal exit propagation. The first CI attempt exposed a `TimeoutExpired` partial-output bytes/string mismatch; commit `7791428a603525b6a1001c6541973ec35f607665` normalizes partial output and the exact-head Validation run passed.

## Limits

This evidence proves worker lifecycle, timeout enforcement, crash classification, and artifact preservation at the Python process boundary. It does not prove OpenGL context-loss detection on every driver, descendant cleanup semantics on every Windows configuration, or Iris-client behavior. Existing `GL_COMPILE_LINK` and `GL_RENDER_READBACK` claims remain limited to their previously accepted fixtures.

## Required roadmap reconciliation

`GLCLI-007` and `SAFE-002` can be marked complete only when this evidence link, PR #99, the exact-head successful run, and the functional merge are incorporated into `docs/ROADMAP.md`; the Iris capability matrix should record process isolation as accepted standalone harness evidence while preserving the limits above.
