# Iris capability matrix

Canonical capability evidence for Focal. This document is linked to [`ROADMAP.md`](ROADMAP.md) and records only capabilities supported by current primary Iris documentation or explicit pending verification.

## Audit metadata

- Reviewed UTC: `2026-07-31`
- Focal baseline: `d46a0649a67e8853a3646c6117d32ae63c2bd61a`
- Machine-readable stage contract: [`../spec/iris-stage-capabilities.json`](../spec/iris-stage-capabilities.json)
- Machine-readable buffer lifecycle contract: [`../spec/iris-buffer-lifecycle.json`](../spec/iris-buffer-lifecycle.json)
- Machine-readable output-directive contract: [`../spec/iris-output-directives.json`](../spec/iris-output-directives.json)
- Terminal OpenGL harness contract: [`OPENGL-RUNTIME-HARNESS.md`](OPENGL-RUNTIME-HARNESS.md)
- Merged EGL probe evidence: [`evidence/GLCLI-002-EGL-PROBE.md`](evidence/GLCLI-002-EGL-PROBE.md)
- Merged Mesa CI probe evidence: [`evidence/GLCLI-002-MESA-CI-PROBE.md`](evidence/GLCLI-002-MESA-CI-PROBE.md)
- Merged hidden GLFW probe evidence: [`evidence/GLCLI-002-GLFW-CI-PROBE.md`](evidence/GLCLI-002-GLFW-CI-PROBE.md)
- Merged native WGL implementation evidence: PR #105, Validation run `30601640571`, merge `1234c4c55f8990a92121065e3b85596374b162c6`, evidence PR #106, and [`evidence/GLCLI-002-WGL-PROBE.md`](evidence/GLCLI-002-WGL-PROBE.md)
- Merged Mesa framebuffer readback evidence: [`evidence/GLCLI-005-MESA-READBACK.md`](evidence/GLCLI-005-MESA-READBACK.md)
- Merged worker-isolation evidence: [`evidence/GLCLI-007-WORKER-ISOLATION.md`](evidence/GLCLI-007-WORKER-ISOLATION.md)
- Merged Mesa evidence manifest and physical-GPU procedure: PR #103, Validation run `30581017694`, merge `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4`, and [`GLCLI-008-HARDWARE-EVIDENCE.md`](GLCLI-008-HARDWARE-EVIDENCE.md)
- Iris Patcher transforms shader source before GPU compilation; standalone source evidence remains distinct from patched and client evidence.
- Version rule: exact Minecraft, Iris, Sodium, Fabric Loader and Java versions remain `PENDIENTE DE VERIFICAR` until a mutually compatible release set is pinned and exercised.

## Status vocabulary

- `SOPORTADA`: confirmed by a current primary source.
- `PARCIAL`: supported with a documented restriction or incomplete Focal evidence.
- `EXPERIMENTAL`: available but capability-gated or insufficiently accepted for a default path.
- `NO SOPORTADA`: explicitly rejected or unrecognized by Iris.
- `PENDIENTE DE VERIFICAR`: current primary evidence is insufficient.

## Primary sources

Reviewed on `2026-07-31` UTC:

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
| `IRIS-GL-005` | Terminal OpenGL compile/link/render harness | PARCIAL | The stable `focal-gl` command contract is merged through PR #62. PR #91 added the GLCLI-003 source adapter with stage discovery, safe include/define preprocessing, explicit patched-source consumption and stable source hashes; Validation run `30521453670` succeeded. PR #93 added real hidden-GLFW stage compilation and complete program link with driver logs; Validation run `30523122062` succeeded after Mesa llvmpipe compiled and linked representative gbuffers-style, composite-style and final-equivalent fixtures and classified an invalid vertex stage with exit 4. PR #97 added real hidden-GLFW framebuffer execution and merged as `cc85e7c4f221ad7f4298f5a96ea34f3c227ac314` after exact-head Validation run `30544545413` succeeded on `53756e93b12ce3ce8b8b1f7d48f67f5ddeceb9b1`. The accepted Mesa llvmpipe/Xvfb fixtures completed RGBA32F color plus depth framebuffers, deterministic geometry/fullscreen draws, sampler binding, finite normalized color/depth readback, changed-attachment invariants and PPM/PGM/JSON artifacts for representative gbuffers, composite and final-equivalent programs. Earlier PRs #71, #74, #75, #77, #79 and #80 preserve real EGL/hidden-GLFW context probing and indexed extension enumeration. PR #99 merged the `GLCLI-007` worker supervisor as `27fd2b16a3472b5588a3a69e6aba6f93b345f80b` after exact-head Validation run `30547008215` succeeded on `7791428a603525b6a1001c6541973ec35f607665`. It isolates runtime commands in a child process group/session, enforces the CLI timeout as a hard deadline, applies bounded terminate/kill escalation, classifies timeout and POSIX signals with exit code 7 and preserves worker logs plus `worker-execution.json`. PR #103 merged GLCLI-008 as `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4` after exact-head Validation run `30581017694` succeeded on `611c77d9f88ee9306896b2343e77db1f09cb8a18`. Validation now publishes a retained Mesa bundle containing probe, compile/link, render/readback, generated image artifacts and a deterministic manifest with artifact SHA-256, byte lengths and explicit evidence boundaries. The separate physical-GPU procedure records vendor, model, driver, operating system, backend and exact fixture without converting one machine into a universal claim. PR #105 added a native hidden WGL adapter, explicit worker routing and bounded failure mapping; exact-head Validation run `30601640571` succeeded and merge `1234c4c55f8990a92121065e3b85596374b162c6` is on `main`. PR #106 published the canonical WGL evidence. This establishes `STATIC` implementation and cross-platform routing evidence, not successful execution on a native Windows driver. `GL_RENDER_READBACK` remains limited to the exact standalone Mesa fixtures and does not establish native Windows WGL execution, CGL/NSOpenGL execution, representative physical-GPU acceptance, proof that an export was produced by Iris Patcher, or Iris-client evidence. | Preserve the real context, source, compile/link, framebuffer, factual failure, worker-supervision, deterministic evidence-manifest and native WGL adapter paths. `GL_RENDER_READBACK` may be claimed only for the exact accepted fixtures and backend; do not claim `IRIS_PATCHED` or `IRIS_CLIENT`. Native Windows execution, CGL/NSOpenGL, physical-GPU records, actual Iris directive/program sequencing and broader platform/driver fault coverage remain separate requirements. | Execute the WGL route on representative native Windows hardware, implement and exercise CGL/NSOpenGL where supported, collect representative physical-GPU records under the GLCLI-008 procedure, then advance `GLCLI-006` multipass/history, patched-output and locked-client checks. | `QA-003`, `GLCLI-001`–`GLCLI-008`, `INT-001` |
| `IRIS-BUFFER-001` | Color attachment lifecycle | PARCIAL | Iris exposes at least 16 `colortex` attachments; defaults are display-sized RGBA, configurable for format, clear, size and flip. Resized attachments cannot be gbuffers outputs. PR #97 proves one bounded standalone RGBA32F attachment path, not the complete Iris lifecycle. | SAFE requires only indices 0–7, default-compatible formats and no resized gbuffers targets. | Extend accepted `GLCLI-005` framebuffer mechanics to the actual attachment schema, flips, sizes, clears and Iris-patched sources. | `IRIS-003`, `PIPE-005`, `PROFILE-001`, `GLCLI-005/006` |
| `IRIS-BUFFER-002` | Depth attachment lifecycle | SOPORTADA | `depthtex0`–`2` are display-sized, non-flipping, fixed-clear depth buffers with progressively narrower geometry coverage. PR #97 proves finite normalized standalone depth readback, not Iris geometry coverage semantics. | Treat precision as driver-dependent; never persist or resize depth attachments. | Extend the accepted depth mechanism with Iris-patched coverage and client fixtures. | `IRIS-003`, `TEMP-001`, `GLCLI-005/006` |
| `IRIS-BUFFER-003` | Shadow depth lifecycle | PARCIAL | `shadowtex0`–`1` use shadow resolution, fixed clear, no flipping and optional mipmaps/hardware comparison. | SAFE cannot depend on hardware comparison or shadowcolor mipmaps. | Static contract plus shadow pass framebuffer fixture. | `IRIS-003`, `SHADOW-001`, `PROFILE-001`, `GLCLI-006` |
| `IRIS-OUTPUT-001` | Fragment output directives and constants | SOPORTADA | `RENDERTARGETS` maps fragment outputs in declared order; legacy `DRAWBUFFERS` is limited to indices 0–9. Formats, clears and clear colors are pack-global constants. PR #97 validates generic attachment execution but does not execute Iris directive mapping. | SAFE prefers `RENDERTARGETS`, requires every bound output to be initialized and limits required color attachments to `colortex0`–`7`. | Machine-readable contract plus Iris-patched framebuffer fixtures built on `GLCLI-005`. | `IRIS-004`, `PIPE-005`, `PROFILE-001`, `SAFE-001`, `GLCLI-005/006` |
| `IRIS-OUTPUT-002` | Per-buffer blending | PARCIAL | Program-level blending is supported; per-buffer blending depends on `PER_BUFFER_BLENDING`. | SAFE treats per-buffer blending as optional and falls back to program-level blending or disabled blending. | Runtime fixture comparing per-buffer and fallback paths after the minimum framebuffer path. | `IRIS-004`, `PROFILE-001`, `GLCLI-006` |

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

Merged `GLCLI-002` evidence establishes real EGL and controlled hidden GLFW context interrogation on Mesa llvmpipe. PR #105 and evidence PR #106 additionally establish a native hidden WGL adapter, explicit worker routing and bounded failure handling at `STATIC`; they do not establish successful execution against a native Windows driver. `GLCLI-003` establishes deterministic source preparation at `STATIC`. `GLCLI-004` establishes `GL_COMPILE_LINK` for exact representative hidden-GLFW fixtures. `GLCLI-005`, through PR #97, exact-head run `30544545413` and merge `cc85e7c4f221ad7f4298f5a96ea34f3c227ac314`, establishes `GL_RENDER_READBACK` for exact representative Mesa llvmpipe fixtures: framebuffer completion, gbuffers geometry draw, composite/final-equivalent fullscreen draws, sampler binding, finite normalized color/depth readback, changed attachments and emitted artifacts. `GLCLI-007`, through PR #99, exact-head run `30547008215` and merge `27fd2b16a3472b5588a3a69e6aba6f93b345f80b`, establishes `STATIC` worker lifecycle, hard-timeout enforcement, bounded termination escalation, stable timeout/signal classification and artifact preservation at the Python process boundary. `GLCLI-008`, through PR #103, exact-head run `30581017694` and merge `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4`, publishes the exact Mesa probe, compile/link and render/readback outputs together with generated image artifacts and a deterministic manifest containing hashes, lengths, environment identity and explicit claim boundaries. Its hardware procedure is `STATIC`; it records one exact physical configuration without asserting vendor-wide or universal compatibility. These claims do not establish native Windows WGL execution, CGL/NSOpenGL execution, physical-GPU acceptance until records exist, comprehensive Windows descendant cleanup, every driver context-loss path, Iris-patched provenance or Iris-client acceptance.

Minimum runtime sequence before `QA-003` can complete:

1. create a real offscreen context and report capabilities — accepted for EGL/hidden GLFW Mesa routes;
2. compile/link one gbuffers-style vertex/fragment program — accepted on the exact Mesa fixture;
3. compile/link one composite-style program — accepted on the exact Mesa fixture;
4. create color/depth framebuffer attachments — accepted on the exact Mesa fixture;
5. render deterministic geometry — accepted on the exact Mesa fixture;
6. execute a composite pass — accepted on the exact Mesa fixture;
7. execute a final-equivalent pass — accepted on the exact Mesa fixture;
8. read color/depth and validate finite values and expected ranges — accepted on the exact Mesa fixture;
9. repeat to verify determinism — pending;
10. execute in an isolated worker with watchdog — accepted at the standalone Python process boundary through PR #99;
11. publish the exact Mesa outputs and deterministic evidence manifest in CI — accepted through PR #103 and Validation run `30581017694`;
12. run the SAFE aggregate subset on Mesa software in CI — pending aggregate suite.

Standalone limits:

- source accepted by a driver may still be transformed differently by Iris;
- uniforms, attributes and render states may be fixture approximations rather than live Minecraft values;
- software Mesa evidence does not establish vendor performance;
- one vendor GPU result does not establish universal compatibility;
- integration claims require `IRIS_PATCHED` and `IRIS_CLIENT` evidence where applicable.

## Gbuffers inventory status

Current program-name acceptance and vertex/fragment pair validation are implemented by `tools/shader_inventory.py` and `tests/test_shader_inventory.py`. Existing files are foundation evidence, not Iris-client runtime acceptance. Unsupported `gbuffers_entities_glowing` must not be added; supported render-state data or the documented entity fallback must be used.

## `shaders.properties` capability summary

Current documentation confirms feature flags, program ordering, custom uniforms, textures, images, SSBOs, profiles, screens, sliders and `.lang` localization. Exact directives, bounds and tests remain assigned to `IRIS-006` and `IRIS-007`.

## Acceptance and next work

`IRIS-001`, `IRIS-002`, `IRIS-003`, `IRIS-004`, `GLCLI-001`, `GLCLI-003`, `GLCLI-004`, `GLCLI-005`, `GLCLI-007`, `GLCLI-008` and `SAFE-002` are complete at their declared evidence boundaries. `GLCLI-002` remains `EN PROGRESO`: real EGL and controlled hidden GLFW context/probe evidence on Mesa llvmpipe, robust indexed core-profile extension enumeration, and the native hidden WGL implementation at bounded `STATIC` evidence are merged. Native Windows driver execution, CGL/NSOpenGL and representative physical-GPU evidence remain unaccepted. Standalone framebuffer readback and the retained manifest are accepted only for the exact PR #103 Mesa bundle. Worker isolation is accepted only at the process boundary proven by PR #99; broader platform cleanup and driver context-loss coverage remain pending. Iris-patched and client evidence remain pending.

Next prioritized unit: execute native `GLCLI-002` WGL on representative Windows hardware, implement and exercise CGL/NSOpenGL where supported, and collect representative physical-GPU records using the merged GLCLI-008 procedure. Preserve the completed worker supervisor, WGL adapter and deterministic Mesa evidence bundle. `IRIS-005` remains the next Iris-format contract and may proceed only when it does not delay the harness foundation.
