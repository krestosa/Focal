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

## Exact canonical reconciliation contract

The next documentation mutation must update `docs/ROADMAP.md` and `docs/IRIS-CAPABILITY-MATRIX.md` in the same branch and PR. The following replacements are normative for that mutation.

### `docs/ROADMAP.md`

1. Set metadata to:

```markdown
- Audit UTC: `2026-07-30`
- Baseline audited: `cc243812bd225f7c26aa4fbae818c11c0f12e839`
- Roadmap schema revision: `14`
```

2. Replace the OpenGL/GLSL compatibility row with:

```markdown
| OpenGL/GLSL | 🟡 EN PROGRESO | The merged EGL and controlled hidden-window GLFW probes report real contexts on Mesa llvmpipe, and PR #77 provides indexed core-profile extension enumeration; complete native WGL and CGL/NSOpenGL routes plus representative physical-GPU evidence. | [Programs][iris-programs], [OpenGL extensions][iris-extensions], [macOS limits][iris-macos] |
```

3. Keep `GOV-002` as `🟣 REVALIDAR`. Append PR #81 and PR #82 as concrete regression evidence, but do not mark it complete until all acceptance fixtures in the row are proven by the exact validation head.

4. Replace the `GLCLI-002` row with text that includes all existing EGL, Mesa and extension evidence plus:

```markdown
PR #79 merged the controlled hidden-window GLFW backend. PR #80 published [`docs/evidence/GLCLI-002-GLFW-CI-PROBE.md`](evidence/GLCLI-002-GLFW-CI-PROBE.md), recording validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7` and successful Validation run `30500297439`. The GLFW fixture created a real hidden context on Mesa llvmpipe under Xvfb and reported capabilities. Evidence remains context/probe evidence only: no shader stage was compiled or linked and no framebuffer render/readback was accepted.
```

5. Its remaining-action cell must be:

```markdown
Complete native WGL and CGL/NSOpenGL routes where supported and collect representative physical-GPU evidence; then advance to the minimum `GLCLI-003/004/005` source, compile/link and render/readback path.
```

6. Append audit revision 14:

```markdown
- `2026-07-30` — Revision 14 reconciled the controlled hidden GLFW route from PR #79, canonical evidence from PR #80 and watchdog/coordinator hardening from PR #81/#82 against baseline `cc243812bd225f7c26aa4fbae818c11c0f12e839`; `GLCLI-002` remains `EN PROGRESO` without compile/link or render/readback claims.
```

7. Replace the next prioritized unit with:

```markdown
`GLCLI-002 boundary completion and GLCLI-003/004 entry`: finish native WGL and CGL/NSOpenGL capability routes and representative physical-GPU evidence without blocking implementation of the source-mode adapter and minimum real-context compile/link fixtures. Do not begin visual shader features before the `GLCLI-004/005` minimum path is established.
```

### `docs/IRIS-CAPABILITY-MATRIX.md`

1. Set metadata to:

```markdown
- Reviewed UTC: `2026-07-30`
- Focal baseline: `cc243812bd225f7c26aa4fbae818c11c0f12e839`
```

2. Add this canonical evidence entry after the Mesa evidence entry:

```markdown
- Merged hidden GLFW probe evidence: [`evidence/GLCLI-002-GLFW-CI-PROBE.md`](evidence/GLCLI-002-GLFW-CI-PROBE.md)
```

3. Extend `IRIS-GL-005` factual evidence with PR #79, PR #80, validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7`, Validation run `30500297439`, and the explicit limitation that hidden GLFW under Xvfb/llvmpipe is not native WGL/CGL, physical-GPU, compile/link, render/readback, patched-source or client evidence.

4. Keep `IRIS-GL-005` state `PARCIAL` and preserve the distinction among `STATIC`, `GL_COMPILE_LINK`, `GL_RENDER_READBACK`, `IRIS_PATCHED` and `IRIS_CLIENT`.

## Evidence classification after reconciliation

| Item | Required state | Highest established evidence | Explicitly not established |
|---|---|---|---|
| `GLCLI-002` | `🟡 EN PROGRESO` | Real EGL and hidden GLFW context/probe on Mesa llvmpipe | Native WGL/CGL, representative physical GPU, compile/link, render/readback, Iris Patcher, Iris client |
| `IRIS-GL-005` | `PARCIAL` | Real context creation and capability reporting on documented software routes | Universal driver compatibility or shader runtime acceptance |
| `GOV-002` | `🟣 REVALIDAR` | Additional stale-lease and race-regression coverage from PR #81/#82 | Full row acceptance unless every listed fixture is confirmed |

## Validation required before canonical merge

- `python -m unittest tests.test_roadmap_runtime_contract`
- roadmap/matrix cross-reference and evidence-path checks
- Markdown and link validation applicable in the repository
- full `Validation` workflow on the exact head
- diff review confirming no status was elevated beyond observed evidence

## Continuation rule

This file remains a non-canonical checkpoint. A following cycle must resume PR #83 rather than create a parallel branch, apply the two canonical document updates atomically, remove any obsolete checkpoint-only wording if appropriate, validate the exact head, merge only with green required checks, reconcile `main`, and release the lease.
