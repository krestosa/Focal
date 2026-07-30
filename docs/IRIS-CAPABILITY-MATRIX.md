# Iris capability matrix

Canonical capability evidence for Focal. This document is linked to [`ROADMAP.md`](ROADMAP.md) and records only capabilities supported by current primary Iris documentation or explicit pending verification.

## Audit metadata

- Reviewed UTC: `2026-07-30`
- Focal baseline: `66652dec9471b23f34bd3ad63aeb1d07716ec203`
- Machine-readable stage contract: [`../spec/iris-stage-capabilities.json`](../spec/iris-stage-capabilities.json)
- Machine-readable buffer lifecycle contract: [`../spec/iris-buffer-lifecycle.json`](../spec/iris-buffer-lifecycle.json)
- Machine-readable output-directive contract: [`../spec/iris-output-directives.json`](../spec/iris-output-directives.json)
- Terminal OpenGL harness contract: [`OPENGL-RUNTIME-HARNESS.md`](OPENGL-RUNTIME-HARNESS.md)
- Merged EGL probe evidence: [`evidence/GLCLI-002-EGL-PROBE.md`](evidence/GLCLI-002-EGL-PROBE.md)
- Merged Mesa CI probe evidence: [`evidence/GLCLI-002-MESA-CI-PROBE.md`](evidence/GLCLI-002-MESA-CI-PROBE.md)
- Merged hidden GLFW probe evidence: [`evidence/GLCLI-002-GLFW-CI-PROBE.md`](evidence/GLCLI-002-GLFW-CI-PROBE.md)
- Iris Patcher transforms shader source before GPU compilation; standalone source evidence remains distinct from patched and client evidence.
- Version rule: exact Minecraft, Iris, Sodium, Fabric Loader and Java versions remain `PENDIENTE DE VERIFICAR` until a mutually compatible release set is pinned and exercised.

## Status vocabulary

- `SOPORTADA`: confirmed by a current primary source.
- `PARCIAL`: supported with a documented restriction or incomplete Focal evidence.
- `EXPERIMENTAL`: available but capability-gated or insufficiently accepted for a default path.
- `NO SOPORTADA`: explicitly rejected or unrecognized by Iris.
- `PENDIENTE DE VERIFICAR`: current primary evidence is insufficient.

## Primary sources

Reviewed on `2026-07-30` UTC:

- https://shaders.properties/current/reference/overview/
- https://shaders.properties/current/reference/programs/overview/
- https://shaders.properties/current/reference/programs/gbuffers/
- https://shaders.properties/current/reference/programs/setup/
- https://shaders.properties/current/reference/programs/final/
- https://shaders.properties/current/reference/shadersproperties/flags/
- https://shaders.properties/current/reference/shadersproperties/overview/
- https://shaders.properties/current/reference/shadersproperties/rendering/
- https://shaders.properties/current/reference/buffers/overview/
- https://shaders.properties/current/reference/buffers/colortex/
- https://shaders.properties/current/reference/buffers/depthtex/
- https://shaders.properties/current/reference/buffers/shadowtex/
- https://shaders.properties/current/reference/constants/overview/
- https://shaders.properties/current/reference/constants/rendertargets/
- https://shaders.properties/current/reference/constants/drawbuffers/
- https://shaders.properties/current/reference/constants/buffer_format/
- https://shaders.properties/current/reference/constants/buffer_clear/
- https://shaders.properties/current/reference/constants/buffer_clear_color/
- https://shaders.properties/current/reference/constants/colortex_mipmaps/
- https://shaders.properties/current/reference/constants/shadow_mipmaps/
- https://shaders.properties/current/reference/uniforms/overview/
- https://shaders.properties/current/reference/attributes/overview/
- https://shaders.properties/current/reference/macros/supported_extensions/
- https://shaders.properties/current/reference/miscellaneous/patcher/
- https://shaders.properties/current/reference/miscellaneous/debugging_shaders/
- https://shaders.properties/current/reference/miscellaneous/macos/
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
| `IRIS-GL-005` | Terminal OpenGL compile/link/render harness | PARCIAL | The stable `focal-gl` command contract is merged through PR #62. PR #91 added the GLCLI-003 source adapter with stage discovery, safe include/define preprocessing, explicit patched-source consumption and stable source hashes; Validation run `30521453670` succeeded. PR #93 added real hidden-GLFW stage compilation and complete program link with driver logs; Validation run `30523122062` succeeded after Mesa llvmpipe compiled and linked representative gbuffers-style, composite-style and final-equivalent fixtures and classified an invalid vertex stage with exit 4. PR #71 merged a real EGL surfaceless/default-display pbuffer context probe with Validation run `30480734608` and merge `d466d6bca8d4e6ad2bfc40d94bc0338c54bf0895`. PR #74 added an explicit Ubuntu 24.04 Mesa llvmpipe EGL gate at feature head `bbe2ed5883a298f16853eb2477dbde0e82909296`; Validation run `30490039060` succeeded and merge `70d0e31f76cd4ede71876b44e5f1966788d81d0a` is on `main`. PR #75 published the canonical Mesa evidence at merge `f8390b650455eebfb74ad332d8a9b91eff9f2495`. PR #77 added robust core-profile extension enumeration through `GL_NUM_EXTENSIONS` and `glGetStringi`, retained a controlled legacy fallback, passed Validation run `30493688616`, and merged as `d66834fc9cff7375da50930c3572eaaa55cdd008`. PR #79 merged the controlled hidden-window GLFW backend. PR #80 published the canonical hidden GLFW evidence at validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7` with successful Validation run `30500297439`. The documented EGL and hidden GLFW probes created real contexts on Mesa llvmpipe, queried vendor, renderer, GL/GLSL versions, limits and extensions, and preserved factual `UNSUPPORTED` behavior. The GLCLI-003 adapter remains `STATIC`; PR #93 establishes `GL_COMPILE_LINK` only for the exact hidden-GLFW Mesa llvmpipe fixtures. This is not native WGL or CGL/NSOpenGL evidence, representative physical-GPU evidence, framebuffer render/readback evidence, proof that an export was produced by Iris Patcher, or Iris-client evidence. | Preserve the real EGL and Mesa llvmpipe routes, controlled hidden GLFW route, indexed extension enumeration and factual failure classification. `GL_COMPILE_LINK` may be claimed only for the exact accepted fixtures and backend; do not claim `GL_RENDER_READBACK`, `IRIS_PATCHED` or `IRIS_CLIENT`. Native platform routes and physical-GPU evidence remain separate requirements. | Complete native WGL and CGL/NSOpenGL capability routes and representative physical-GPU evidence while advancing `GLCLI-005` framebuffer render/readback fixtures, followed by GL error, NaN/Inf, determinism, patched-output and locked-client checks. | `QA-003`, `GLCLI-001`–`GLCLI-008`, `INT-001` |
| `IRIS-BUFFER-001` | Color attachment lifecycle | PARCIAL | Iris exposes at least 16 `colortex` attachments; defaults are display-sized RGBA, configurable for format, clear, size and flip. Resized attachments cannot be gbuffers outputs. | SAFE requires only indices 0–7, default-compatible formats and no resized gbuffers targets. | Machine-readable lifecycle contract plus `focal-gl` framebuffer validation. | `IRIS-003`, `PIPE-005`, `PROFILE-001`, `GLCLI-005` |
| `IRIS-BUFFER-002` | Depth attachment lifecycle | SOPORTADA | `depthtex0`–`2` are display-sized, non-flipping, fixed-clear depth buffers with progressively narrower geometry coverage. | Treat precision as driver-dependent; never persist or resize depth attachments. | Static contract plus depth coverage and readback fixture. | `IRIS-003`, `TEMP-001`, `GLCLI-005` |
| `IRIS-BUFFER-003` | Shadow depth lifecycle | PARCIAL | `shadowtex0`–`1` use shadow resolution, fixed clear, no flipping and optional mipmaps/hardware comparison. | SAFE cannot depend on hardware comparison or shadowcolor mipmaps. | Static contract plus shadow pass framebuffer fixture. | `IRIS-003`, `SHADOW-001`, `PROFILE-001`, `GLCLI-006` |
| `IRIS-OUTPUT-001` | Fragment output directives and constants | SOPORTADA | `RENDERTARGETS` maps fragment outputs in declared order; legacy `DRAWBUFFERS` is limited to indices 0–9. Formats, clears and clear colors are pack-global constants. | SAFE prefers `RENDERTARGETS`, requires every bound output to be initialized and limits required color attachments to `colortex0`–`7`. | Machine-readable output-directive contract, regression tests and later `focal-gl` framebuffer validation. | `IRIS-004`, `PIPE-005`, `PROFILE-001`, `SAFE-001`, `GLCLI-005` |
| `IRIS-OUTPUT-002` | Per-buffer blending | PARCIAL | Program-level blending is supported; per-buffer blending depends on `PER_BUFFER_BLENDING`. | SAFE treats per-buffer blending as optional and falls back to program-level blending or disabled blending. | Static contract plus a runtime fixture comparing per-buffer and fallback paths. | `IRIS-004`, `PROFILE-001`, `GLCLI-005` |

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

## Output directive contract

The authoritative machine-readable contract is `spec/iris-output-directives.json`, covered by `tests/test_iris_output_directives.py`.

- `RENDERTARGETS` is the preferred fragment-output directive. Its comma-separated attachment indices map outputs by declaration order.
- When neither `RENDERTARGETS` nor `DRAWBUFFERS` is present, the first eight color attachments are bound by default.
- Every bound fragment output must be written; unwritten outputs are undefined and are rejected by the Focal contract.
- Legacy `DRAWBUFFERS` uses compact decimal indices and cannot address attachments above index 9.
- Buffer formats, clear enablement and clear colors are pack-global constants and must have one effective definition.
- Persistent buffers require clearing disabled and explicit initialization before first use; persistence does not by itself establish valid history.
- Per-buffer blending is capability-gated. SAFE falls back to program-level blending or disabled blending.

## Terminal OpenGL runtime evidence

The canonical command surface is:

```text
focal-gl probe
focal-gl compile
focal-gl render
focal-gl suite
```

Every result must declare one evidence level:

1. `STATIC`;
2. `GL_COMPILE_LINK`;
3. `GL_RENDER_READBACK`;
4. `IRIS_PATCHED`;
5. `IRIS_CLIENT`.

The JSON result must record harness version, shader-pack hash, command, fixture, program, profile, dimension, `sourceMode`, context backend, vendor, renderer, OpenGL/GLSL versions, extensions, limits, stages, link status, attachments, draw or dispatch count, GL errors, debug messages, readback statistics, NaN/Inf count, invariant results, timings, artifacts and exit code.

Merged `GLCLI-002` evidence establishes that the implementation can create and interrogate real EGL and controlled hidden GLFW contexts on documented Mesa llvmpipe routes. PR #77 additionally establishes robust indexed extension enumeration for core profiles with a controlled compatibility fallback. PR #79/#80 establish hidden GLFW context creation and capability reporting under Xvfb at validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7` and Validation run `30500297439`. This does not raise the canonical evidence level above `STATIC`: no shader stage or complete program was compiled and linked, no framebuffer render/readback was accepted, and no native WGL/CGL, representative physical-GPU, patched-source or client evidence was produced.

Minimum runtime sequence before `QA-003` can complete:

1. create a real offscreen context and report capabilities;
2. compile/link one gbuffers-style vertex/fragment program;
3. compile/link one composite-style program;
4. create color/depth framebuffer attachments;
5. render deterministic geometry;
6. execute a composite pass;
7. execute a final-equivalent pass;
8. read color/depth and validate finite values and expected ranges;
9. repeat to verify determinism;
10. execute in an isolated worker with watchdog;
11. run the SAFE subset on Mesa software in CI.

Standalone limits:

- source accepted by a driver may still be transformed differently by Iris;
- uniforms, attributes and render states may be fixture approximations rather than live Minecraft values;
- software Mesa evidence does not establish vendor performance;
- one vendor GPU result does not establish universal compatibility;
- integration claims require `IRIS_PATCHED` and `IRIS_CLIENT` evidence where applicable.

## Gbuffers inventory status

Current program-name acceptance and vertex/fragment pair validation are implemented by `tools/shader_inventory.py` and `tests/test_shader_inventory.py`. Existing files are foundation evidence, not runtime acceptance. Unsupported `gbuffers_entities_glowing` must not be added; supported render-state data or the documented entity fallback must be used.

## `shaders.properties` capability summary

Current documentation confirms feature flags, program ordering, custom uniforms, textures, images, SSBOs, profiles, screens, sliders and `.lang` localization. Exact directives, bounds and tests remain assigned to `IRIS-006` and `IRIS-007`.

## Acceptance and next work

`IRIS-001`, `IRIS-002`, `IRIS-003`, `IRIS-004` and the `GLCLI-001` command contract are complete at their current `STATIC` evidence level. `GLCLI-002` remains `EN PROGRESO`: real EGL and controlled hidden GLFW context/probe evidence on Mesa llvmpipe plus robust indexed core-profile extension enumeration are merged. Native WGL/CGL routes, representative physical-GPU evidence, shader compile/link and framebuffer render/readback remain unaccepted.

Next prioritized unit: complete native WGL and CGL/NSOpenGL capability routes and representative physical-GPU evidence without blocking the `GLCLI-003/004/005` source-mode, minimum real-context compile/link and render/readback path. `IRIS-005` remains the next Iris-format contract and may proceed only when it does not delay the harness foundation.