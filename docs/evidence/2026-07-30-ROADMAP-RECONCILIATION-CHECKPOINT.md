# Roadmap reconciliation checkpoint — 2026-07-30

## Scope

This checkpoint records remote evidence that is already present on `main` but is not yet reflected in the canonical roadmap and Iris capability matrix.

Baseline inspected: `cc243812bd225f7c26aa4fbae818c11c0f12e839`.

## Confirmed merged evidence

### Hidden GLFW context route

- PR #79 merged the controlled hidden-window GLFW backend.
- PR #80 merged the canonical evidence note at `docs/evidence/GLCLI-002-GLFW-CI-PROBE.md`.
- PR #80 records merge `6eee1e86eeb2f77f81d5e06a7fd3e148579b0c30`, validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7`, and Validation run `30500297439`.
- The evidence proves real context creation and capability query on Mesa llvmpipe under Xvfb.
- It does not prove shader compile/link, render/readback, physical GPU coverage, native WGL/CGL routes, or Iris-client integration.

### Coordinator and stale-lease watchdog hardening

- PR #81 merged immediate stale-lease reconciliation after coordinator command processing while retaining the scheduled watchdog fallback.
- PR #82 merged shared workflow serialization and optimistic state revalidation before watchdog writes.
- Current `main` is `cc243812bd225f7c26aa4fbae818c11c0f12e839`.

## Required canonical reconciliation

The next documentation mutation must update `docs/ROADMAP.md` and `docs/IRIS-CAPABILITY-MATRIX.md` together:

1. Set audit date to `2026-07-30` and baseline to `cc243812bd225f7c26aa4fbae818c11c0f12e839`.
2. Add the GLFW evidence note to the canonical evidence lists.
3. Update the OpenGL compatibility summary to state that EGL and controlled hidden GLFW are merged.
4. Update `GLCLI-002` evidence with PR #79, PR #80, run `30500297439`, and the GLFW evidence path.
5. Keep `GLCLI-002` as `🟡 EN PROGRESO`; remaining platform work is native WGL and CGL/NSOpenGL plus representative physical GPU evidence.
6. Do not claim `GL_COMPILE_LINK` or `GL_RENDER_READBACK`; current evidence remains context/probe evidence only.
7. Reconcile governance evidence for PR #81 and PR #82 without marking unrelated roadmap items complete unless their acceptance criteria are fully satisfied.
8. Advance the next functional priority toward the minimum `GLCLI-004` compile/link path once the remaining `GLCLI-002` platform boundary is explicitly scoped.

## Validation required before merge

- Roadmap runtime-contract tests.
- Documentation-link and Markdown validation.
- Matrix/roadmap cross-reference checks.
- Full repository Validation workflow on the exact documentation head.

This checkpoint is intentionally non-canonical. It preserves the audit result remotely so a subsequent cycle can update both canonical documents atomically without repeating the remote reconstruction.