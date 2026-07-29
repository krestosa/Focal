# Iris capability matrix

Canonical capability evidence for Focal. This document is linked to [`ROADMAP.md`](ROADMAP.md) and records only capabilities supported by current primary Iris documentation or explicit pending verification.

## Audit metadata

- Reviewed UTC: `2026-07-29`
- Focal baseline: `4d09aa437ae2702e30659f02a10fc21fe2480cbc`
- Machine-readable stage contract: [`../spec/iris-stage-capabilities.json`](../spec/iris-stage-capabilities.json)
- Machine-readable buffer lifecycle contract: [`../spec/iris-buffer-lifecycle.json`](../spec/iris-buffer-lifecycle.json)
- Version rule: exact Minecraft, Iris, Sodium, Fabric Loader and Java versions remain `PENDIENTE DE VERIFICAR` until a mutually compatible release set is pinned and exercised.

## Status vocabulary

- `SOPORTADA`: confirmed by a current primary source.
- `PARCIAL`: supported with a documented restriction or incomplete Focal evidence.
- `EXPERIMENTAL`: available but capability-gated or insufficiently accepted for a default path.
- `NO SOPORTADA`: explicitly rejected or unrecognized by Iris.
- `PENDIENTE DE VERIFICAR`: current primary evidence is insufficient.

## Primary sources

Reviewed on `2026-07-29` UTC:

- https://shaders.properties/current/reference/programs/overview/
- https://shaders.properties/current/reference/programs/gbuffers/
- https://shaders.properties/current/reference/programs/setup/
- https://shaders.properties/current/reference/shadersproperties/flags/
- https://shaders.properties/current/reference/buffers/overview/
- https://shaders.properties/current/reference/buffers/colortex/
- https://shaders.properties/current/reference/buffers/depthtex/
- https://shaders.properties/current/reference/buffers/shadowtex/
- https://shaders.properties/current/reference/shadersproperties/rendering/
- https://shaders.properties/current/reference/constants/buffer_format/
- https://shaders.properties/current/reference/constants/buffer_clear/
- https://shaders.properties/current/reference/constants/buffer_clear_color/
- https://shaders.properties/current/reference/constants/colortex_mipmaps/
- https://shaders.properties/current/reference/constants/shadow_mipmaps/
- https://github.com/IrisShaders/Iris
- https://github.com/IrisShaders/docs
- https://github.com/IrisShaders/ShaderDoc

## Version and runtime matrix

| ID | Capability | State | Factual evidence | Focal impact and fallback | Test strategy | Roadmap |
|---|---|---|---|---|---|---|
| `IRIS-COMPAT-001` | Exact Minecraft/Iris/Sodium/Fabric/Java set | PENDIENTE DE VERIFICAR | No mutually compatible release set is locked in the repository. | Do not claim runtime compatibility; keep SAFE independent of advanced stages. | Pin releases, hashes and Java requirement; exercise a client fixture. | `BOOT-003`, `INT-001`, `INT-003` |
| `IRIS-GL-001` | Compute shaders | PARCIAL | Setup and composite-style only; OpenGL 4.3; unavailable through macOS OpenGL. | Optional only; SAFE never requires compute. | Static contract plus capability-gated runtime fixture. | `IRIS-002`, `PROFILE-001`, `GI-002` |
| `IRIS-GL-002` | Tessellation shaders | EXPERIMENTAL | Gbuffers-style only, triangles only, `TESSELLATION_SHADERS` required. | Optional HIGH/ULTRA path with vertex/fragment fallback. | Minimal paired `.tcs`/`.tes` fixture and fallback test. | `IRIS-002`, `PROFILE-003`, `PROFILE-004` |
| `IRIS-GL-003` | Geometry shaders | SOPORTADA | Optional for gbuffers and composite-style programs. | Optional bounded amplification; omission is the deterministic fallback. | Compile/link fixture and amplification budget. | `IRIS-002`, `SAFE-001` |
| `IRIS-GL-004` | SSBO, images and indirect dispatch | EXPERIMENTAL | Feature flags and properties exist, but exact release/hardware acceptance is not locked. | Never required by SAFE; resource budgets required before adoption. | Binding, lifetime, dispatch and memory fixtures. | `IRIS-006`, `GI-002`, `SAFE-002` |
| `IRIS-BUFFER-001` | Color attachment lifecycle | PARCIAL | Iris exposes at least 16 `colortex` attachments; defaults are display-sized RGBA, configurable for format, clear, size and flip. Resized attachments cannot be gbuffers outputs. | SAFE requires only indices 0–7, default-compatible formats and no resized gbuffers targets. | Machine-readable lifecycle contract, regression tests and later runtime framebuffer validation. | `IRIS-003`, `PIPE-005`, `PROFILE-001` |
| `IRIS-BUFFER-002` | Depth attachment lifecycle | SOPORTADA | `depthtex0`–`2` are display-sized, non-flipping, fixed-clear depth buffers with progressively narrower geometry coverage. | Treat precision as driver-dependent; never persist or resize depth attachments. | Static contract plus later depth coverage fixture. | `IRIS-003`, `TEMP-001`, `QA-003` |
| `IRIS-BUFFER-003` | Shadow depth lifecycle | PARCIAL | `shadowtex0`–`1` use shadow resolution, fixed clear, no flipping and optional mipmaps/hardware comparison. | SAFE cannot depend on hardware comparison or shadowcolor mipmaps. | Static contract plus shadow pass framebuffer fixture. | `IRIS-003`, `SHADOW-001`, `PROFILE-001` |

## Program execution order

1. `setup` — compute-only during load and resize.
2. `begin` — composite-style before shadow.
3. `shadow` — gbuffers-style shadow geometry.
4. `shadowcomp` — composite-style after shadow.
5. `prepare` — composite-style before world gbuffers.
6. opaque `gbuffers_*`.
7. `deferred` — between most opaque and translucent geometry.
8. translucent `gbuffers_*`.
9. `composite` — after world geometry.
10. `final` — output to the backbuffer.

Individual gbuffers ordering is category-dependent rather than globally fixed.

## Program family matrix

| Family | State | Required stages | Optional stages | Suffixes | Restriction / fallback |
|---|---|---|---|---|---|
| `setup` | SOPORTADA | compute | none | 1–99 programs; each pass may use suffixless and `_a`–`_z` compute files | OpenGL 4.3; disabled or non-compute fallback on unsupported contexts |
| composite-style (`begin`, `shadowcomp`, `prepare`, `deferred`, `composite`, `final`) | SOPORTADA | vertex + fragment unless compute-only | geometry, compute | 1–99 except `final` | Compute executes before graphics; geometry may be omitted |
| `shadow` and gbuffers-style | SOPORTADA | vertex + fragment | geometry, tessellation | program-specific; no generic numeric gbuffers suffix | Compute unsupported; tessellation must be paired, triangle-based and capability-gated |

## Stage capability contract

The authoritative machine-readable contract is `spec/iris-stage-capabilities.json`, covered by `tests/test_iris_stage_capabilities.py`.

| Stage | State | Scope | Required gate | SAFE rule | Deterministic fallback |
|---|---|---|---|---|---|
| Vertex `.vsh` | SOPORTADA | gbuffers and composite-style | none | baseline | none |
| Fragment `.fsh` | SOPORTADA | gbuffers and composite-style | none | baseline | none |
| Geometry `.gsh` | SOPORTADA | gbuffers and composite-style | none | optional | omit geometry stage |
| Compute `.csh` | PARCIAL | setup and composite-style only | `COMPUTE_SHADERS`, OpenGL 4.3 | prohibited as a dependency | vertex/fragment implementation or disabled pass |
| Tessellation control `.tcs` | EXPERIMENTAL | gbuffers-style only, triangles | `TESSELLATION_SHADERS` | prohibited as a dependency | vertex/fragment path |
| Tessellation evaluation `.tes` | EXPERIMENTAL | gbuffers-style only, triangles | `TESSELLATION_SHADERS` | prohibited as a dependency | vertex/fragment path |

Additional invariants:

- compute is not valid for gbuffers-style programs;
- a compute-capable pass supports at most 27 compute files: suffixless plus `_a` through `_z`;
- compute executes before graphics stages and does not directly write color attachments;
- `.tcs` and `.tes` are treated as a paired optional path;
- macOS OpenGL uses the non-compute, non-tessellated fallback;
- current Focal shader-stage extensions must remain a subset of the declared contract.

## Buffer and attachment lifecycle contract

The authoritative machine-readable contract is `spec/iris-buffer-lifecycle.json`, covered by `tests/test_iris_buffer_lifecycle.py`.

- `colortex` attachments are double-buffered. Composite-style fragment passes read main, write alt and flip by default; compute-only passes do not trigger a flip.
- `colortex0`–`3` cannot be sampled as color attachments from gbuffers programs. SAFE therefore avoids read-after-write assumptions in gbuffers.
- Resizing a `colortex` attachment through `size.buffer` prevents gbuffers from writing to it, and one pass may only render to attachments with identical dimensions.
- Persistent history requires clearing disabled, explicit initialization and a future discontinuity/reset protocol; persistence alone is not acceptance.
- `depthtex0`–`2` and `shadowtex0`–`1` do not flip and use fixed clear behavior. Their depth precision remains driver-dependent.
- Colortex mipmaps are generated immediately before a declaring composite-style fragment pass. Shadow depth mipmaps are generated after shadow and before shadowcomp.
- Documented shadowcolor mipmap directives are currently unreliable; no Focal profile may depend on them.
- Hardware shadow comparison is optional. Separate raw and comparison samplers require `SEPARATE_HARDWARE_SAMPLERS`.

## Gbuffers inventory status

Current program-name acceptance and vertex/fragment pair validation are implemented by `tools/shader_inventory.py` and `tests/test_shader_inventory.py`. Existing files are foundation evidence, not runtime acceptance. Unsupported `gbuffers_entities_glowing` must not be added; supported render-state data or the documented entity fallback must be used.

## `shaders.properties` capability summary

Current documentation confirms feature flags, program ordering, custom uniforms, textures, images, SSBOs, profiles, screens, sliders and `.lang` localization. Exact directives, bounds and tests remain assigned to `IRIS-006` and `IRIS-007`.

## Acceptance and next work

`IRIS-001` and `IRIS-002` are complete through their machine-readable contracts, regression tests and synchronized roadmap evidence. `IRIS-003` is complete only when the buffer lifecycle contract, tests, this matrix update and the synchronized roadmap are merged with green Validation. Runtime framebuffer acceptance remains assigned to `QA-003` and client integration items.

Next unit after `IRIS-003`: `IRIS-004` — define and validate constants and output directives including `RENDERTARGETS`, legacy `DRAWBUFFERS`, formats, clears and blend behavior.
