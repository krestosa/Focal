# Focal master roadmap

## Objective and canonical evidence

Maintain one evidence-based plan for completing Focal as a safe, scalable Iris shader pack. Work not represented here must be added before implementation.

- Canonical Iris evidence: [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md)
- Canonical terminal OpenGL harness contract: [`OPENGL-RUNTIME-HARNESS.md`](OPENGL-RUNTIME-HARNESS.md)
- Audit UTC: `2026-07-30`
- Baseline audited: `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4`
- Roadmap schema revision: `20`
- Current stage: Phase 1 foundation, Iris contracts and terminal OpenGL runtime harness
- Runtime rule: no shader, buffer, multipass, temporal or profile feature may claim runtime acceptance without the evidence level declared in its row.
- Documentation rule: every feature row contains at least one direct official Iris documentation link, reviewed on `2026-07-30` UTC.

## Status legend

- [ ] ⚪ PENDIENTE
- [ ] 🟡 EN PROGRESO
- [x] 🟢 COMPLETADO
- [ ] 🟣 REVALIDAR
- [ ] 🔴 BLOQUEADO

A checked item requires implementation on `main`, applicable tests, green relevant checks, synchronized documentation, current Iris references and no invalidating blocker.

## Evidence levels

| Level | Meaning | Does not prove |
|---|---|---|
| `STATIC` | Structure, parsing, contracts, schemas and source analysis. | Driver acceptance or rendered output. |
| `GL_COMPILE_LINK` | Real OpenGL context compiled every stage and linked the program. | Correct pixels or Iris integration. |
| `GL_RENDER_READBACK` | Real OpenGL draw/dispatch, framebuffer execution and readback passed invariants. | Full Minecraft/Iris behavior. |
| `IRIS_PATCHED` | Iris-patched GLSL was inspected or executed. | Complete client integration. |
| `IRIS_CLIENT` | Locked Minecraft/Iris/Sodium client loaded and exercised the pack. | Universal hardware compatibility. |

## Compatibility status

| Component | State | Required next evidence | Iris docs |
|---|---|---|---|
| Minecraft Java 26.2 | 🟣 REVALIDAR | Verify official release metadata and integration viability. | [Iris repository][iris-repo] |
| Iris | 🟣 REVALIDAR | Pin exact stable release, tag or commit. | [Iris repository][iris-repo] |
| Sodium | 🟣 REVALIDAR | Pin the version required by the selected Iris release. | [Iris overview][iris-overview] |
| Fabric Loader/API | 🟣 REVALIDAR | Pin compatible versions and hashes. | [Iris repository][iris-repo] |
| Java | 🟣 REVALIDAR | Confirm the official runtime requirement. | [Iris repository][iris-repo] |
| OpenGL/GLSL | 🟡 EN PROGRESO | EGL and hidden GLFW create real Mesa llvmpipe contexts; PR #93 adds real stage compilation/program link, PR #97 adds deterministic framebuffer draw plus finite color/depth readback for representative gbuffers, composite and final-equivalent fixtures, PR #99 adds an isolated worker supervisor, and PR #103 publishes a deterministic Mesa evidence manifest and retained artifact bundle. Native WGL, CGL/NSOpenGL, representative physical-GPU evidence and comprehensive driver context-loss detection remain pending. | [Programs][iris-programs], [OpenGL extensions][iris-extensions], [macOS limits][iris-macos] |
| Drivers/hardware | ⚪ PENDIENTE | Preserve the reproducible Mesa software baseline and establish representative AMD, NVIDIA and Intel physical-GPU records using the declared procedure. | [Debugging][iris-debug] |

## Feature-row contract

Each row below is a feature unit. `Acceptance / tests` names the observable completion gate. `Iris docs` is a direct primary reference. A row cannot become `🟢 COMPLETADO` if either field is missing.

## 1. Governance, coordination and recovery

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [x] 🟢 `GOV-001` | P0 | Body-only lease coordinator prevents overlapping autonomous runs. | Issue #7 and `.github/workflows/automation-state.yml` on `main`; acquire/release evidence. | [Iris repository][iris-repo] | Preserve v3 state contract. |
| [x] 🟢 `GOV-002` | P0 | Regression suite for concurrency, stale recovery, ownership loss and malformed commands. | `tests/test_gov_002_acceptance.py` validates two contenders, expired inactive lease recovery, invalid command token and lost ownership on one exact head; PR #89 merged after Validation run `30519455484` succeeded. Supporting isolated fixtures from PRs #81, #82, #87 and #88 remain green in the same repository suite. | [Iris repository][iris-repo] | Preserve the aggregate acceptance matrix as coordinator and watchdog behavior evolves. |
| [x] 🟢 `GOV-003` | P0 | Remote checkpoint discipline keeps recoverable branches, PRs and reports. | Existing autonomous cycles show remote checkpoints before timeout. | [Iris repository][iris-repo] | Preserve policy. |
| [ ] ⚪ `GOV-004` | P1 | Branch and PR recovery audit classifies abandoned, active and merged work. | CLI/report lists remote branches and PR disposition without deleting active work. | [Iris repository][iris-repo] | Implement read-only audit then guarded cleanup. |

## 2. Bootstrap, structure, packaging and versions

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [x] 🟢 `BOOT-001` | P0 | Repository foundation and Validation workflow. | Validation runs on relevant changes with pinned actions and timeouts. | [File structure][iris-overview] | Preserve. |
| [ ] 🟣 `BOOT-002` | P0 | Exact pack structure and include-root audit. | Machine check confirms `shaders/` root, valid program names, includes and dimension folders. | [File structure][iris-overview], [Programs][iris-programs] | Extend inventory to package layout. |
| [ ] ⚪ `BOOT-003` | P0 | Machine-readable lock for Minecraft, Iris, Sodium, Fabric, Java and GL baseline. | Lock contains versions, URLs, hashes and compatibility evidence; client fixture consumes it. | [Iris repository][iris-repo], [Feature flags][iris-flags] | Research current mutually compatible releases. |
| [ ] ⚪ `BOOT-004` | P1 | Reproducible ZIP and checksum. | Two clean builds produce identical archive bytes and SHA-256 with `shaders/` at archive root. | [File structure][iris-overview] | Add deterministic packager. |
| [ ] ⚪ `BOOT-005` | P1 | Release metadata, changelog, rollback and installation verification. | Release candidate installs from ZIP, loads in locked client and documents rollback. | [Iris overview][iris-overview], [Debugging][iris-debug] | Depends on `BOOT-003`, `INT-001`. |

## 3. Iris audit and compatibility

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [x] 🟢 `IRIS-001` | P0 | Program inventory and required vertex/fragment pairing. | `tools/shader_inventory.py` and tests cover recognized program families; PR #53 and run `30410900109`. | [Programs][iris-programs] | Preserve inventory. |
| [x] 🟢 `IRIS-002` | P0 | Stage inventory for vertex, fragment, geometry, compute and tessellation. | Machine contract and tests enforce scope, flags, GL 4.3 compute, macOS fallback, 27-file compute bound and paired triangle tessellation; PR #55. | [Programs][iris-programs], [Feature flags][iris-flags], [macOS limits][iris-macos] | Preserve the contract; representative runtime compile/link acceptance is recorded in `GLCLI-004`. |
| [x] 🟢 `IRIS-003` | P0 | Buffer and attachment lifecycle contract. | Static contract covers color, depth, shadow, clear, formats, mipmaps, scaling, ping-pong and history preconditions; PR #56 and run `30419514264`. `GLCLI-005` now proves a bounded standalone color/depth attachment lifecycle on exact Mesa fixtures. | [Buffers][iris-buffers], [ColorTex][iris-colortex], [Rendering properties][iris-rendering] | Extend runtime evidence to the actual HDR schema, ping-pong, mipmaps and Iris-patched sources. |
| [x] 🟢 `IRIS-004` | P0 | Output constants and directives: `RENDERTARGETS`, `DRAWBUFFERS`, formats, clears, clear colors and blend. | `spec/iris-output-directives.json` and `tests/test_iris_output_directives.py` are merged through PR #58 with Validation run `30421966410`; `GLCLI-005` adds standalone framebuffer completion and color/depth readback evidence without claiming Iris directive execution. | [Constants][iris-constants], [RENDERTARGETS][iris-rendertargets], [DRAWBUFFERS][iris-drawbuffers], [Buffer format][iris-buffer-format] | Preserve the static contract and connect real directives to future Iris-patched/client fixtures. |
| [ ] ⚪ `IRIS-005` | P0 | Uniforms, attributes, matrices, camera, world, weather, IDs and reserved names. | Generated fixture schema validates type, stage availability and required defaults; compile fixtures bind all declared inputs. | [Uniforms][iris-uniforms], [Attributes][iris-attributes], [Patcher][iris-patcher] | Build machine-readable input catalog. |
| [ ] ⚪ `IRIS-006` | P0 | Complete `shaders.properties` matrix: flags, resources, textures, images, SSBO and dispatch. | Parser and fixtures cover supported directives, capability gates, bounds and deterministic fallback. | [`shaders.properties`][iris-properties], [Feature flags][iris-flags], [Rendering properties][iris-rendering] | Inventory directives and add negative tests. |
| [ ] ⚪ `IRIS-007` | P1 | Defines, sliders, profiles, screens, columns and `.lang`. | SAFE/BALANCED/HIGH/ULTRA appear correctly; options round-trip; localization keys are complete. | [Shader settings][iris-settings], [`shaders.properties`][iris-properties] | Depends on profile contracts. |
| [ ] ⚪ `IRIS-008` | P1 | Block, item, entity, block-entity, biome and dimension mappings. | Mapping files parse, IDs resolve in locked client and unknown content follows fallback. | [`shaders.properties`][iris-properties], [Uniforms][iris-uniforms] | Add schemas and client fixture. |
| [ ] ⚪ `IRIS-009` | P1 | Unsupported, deprecated and Iris-exclusive features with explicit decisions. | Matrix names every used divergence and links fallback or rejection evidence. | [ShaderDoc unsupported features][shaderdoc-unsupported], [Iris macro][iris-is-iris] | Audit current source and pack usage. |
| [ ] ⚪ `IRIS-010` | P0 | Iris Patcher transformation, reserved names and reproducible diagnostics. | Debug-mode patched output is captured; errors map to source context; reserved identifiers are statically rejected. | [Iris Patcher][iris-patcher], [Debugging][iris-debug] | Required for `IRIS_PATCHED` evidence and `GLCLI-003`. |

## 4. Pipeline, programs and resources

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [x] 🟢 `PIPE-001` | P0 | Minimal geometry foundations for current gbuffers files. | Source exists on `main`; static pair validation passes; representative standalone runtime fixtures are accepted by `GLCLI-004/005`. | [Gbuffers programs][iris-gbuffers], [Attributes][iris-attributes] | Add actual pack programs to Iris-patched/client validation. |
| [x] 🟢 `PIPE-002` | P0 | Machine-readable shader program inventory and pair validation. | Every current program/stage is classified and paired where required. | [Programs][iris-programs] | Extend as files are added. |
| [ ] ⚪ `PIPE-003` | P0 | Remaining required gbuffers programs for terrain, entities, hand, weather and special render paths. | Every selected program compiles/links; locked client proves render-state coverage. | [Programs][iris-programs], [Gbuffers programs][iris-gbuffers] | Depends on `IRIS-005`, `GLCLI-004`. |
| [ ] ⚪ `PIPE-004` | P0 | Dimension-specific program selection and deterministic fallback. | Overworld, Nether, End and unknown dimension select expected folders without missing programs. | [Programs][iris-programs], [Uniforms][iris-uniforms] | Add dimension fixture manifest. |
| [ ] ⚪ `PIPE-005` | P0 | HDR G-buffer schema with documented channels, formats and precision. | `GL_RENDER_READBACK` writes/reads every attachment; finite values and precision tolerances pass. | [Buffers][iris-buffers], [Buffer format][iris-buffer-format], [RENDERTARGETS][iris-rendertargets] | `GLCLI-005` provides the minimum mechanism; define and validate the actual HDR attachment schema next. |
| [ ] ⚪ `PIPE-006` | P1 | `shaders.properties`, profiles, screens and localization integration. | Options control programs/budgets and produce valid UI in Iris. | [`shaders.properties`][iris-properties], [Shader settings][iris-settings] | Depends on `IRIS-006/007`. |
| [ ] ⚪ `PIPE-007` | P0 | Bounded shadowcomp, prepare, deferred, composite and final foundation. | Multipass sequence renders offscreen with correct order, flips, clears and final output. | [Programs][iris-programs], [Final program][iris-final], [Rendering properties][iris-rendering] | Depends on `GLCLI-005/006`. |

## 5. Materials

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `MAT-001` | P0 | Linear albedo path plus deterministic non-PBR fallback. | Fixture preserves expected base color within tolerance with and without material maps. | [Gbuffers programs][iris-gbuffers], [Attributes][iris-attributes] | Depends on `PIPE-005`. |
| [ ] ⚪ `MAT-002` | P0 | Normal and specular resource-pack support. | Flat, tangent-space normal and missing-map fixtures produce finite normalized outputs. | [Buffers][iris-buffers], [Uniforms][iris-uniforms] | Define material packing. |
| [ ] ⚪ `MAT-003` | P1 | Roughness, metallic, emission, porosity, subsurface and AO channels. | Each channel has range, default, debug view and fallback; energy tests pass. | [Buffer format][iris-buffer-format], [Buffers][iris-buffers] | Depends on `MAT-001/002`. |
| [ ] ⚪ `MAT-004` | P2 | Bounded parallax occlusion mapping. | Sample count and displacement are capped; grazing-angle and missing-height fixtures remain stable. | [Uniforms][iris-uniforms], [Feature flags][iris-flags] | HIGH/ULTRA only; fallback disables POM. |

## 6. Lighting, shadows and occlusion

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `LIGHT-001` | P0 | Solar and lunar direct lighting with physically plausible BRDF inputs. | Deterministic normals/light directions match reference equations and remain finite. | [Uniforms][iris-uniforms], [Attributes][iris-attributes] | Depends on materials and HDR schema. |
| [ ] ⚪ `LIGHT-002` | P1 | Block light, held light and colored emission. | Locked client validates IDs/intensity; standalone fixture validates accumulation and clamping. | [Uniforms][iris-uniforms], [Feature flags][iris-flags] | Depends on mappings and material emission. |
| [ ] ⚪ `SHADOW-001` | P0 | Directional shadow maps, bias, filtering and stabilization. | Shadow framebuffer completes; acne/peter-panning fixtures stay within thresholds; camera motion is stable. | [Programs][iris-programs], [Buffers][iris-buffers], [Rendering properties][iris-rendering] | Depends on `PIPE-007`, `GLCLI-006`. |
| [ ] ⚪ `SHADOW-002` | P1 | Entity, translucent and contact shadow paths. | Client scenes cover entities/translucency; unsupported paths degrade deterministically. | [`shaders.properties`][iris-properties], [Feature flags][iris-flags] | Depends on render coverage. |
| [ ] ⚪ `AO-001` | P1 | Bounded ambient occlusion with material and vanilla fallback. | Occlusion range, radius and sample budget are capped; no halos beyond tolerance. | [Features/options][iris-features], [Attributes][iris-attributes] | Depends on depth/normal schema. |

## 7. World, atmosphere and translucency

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `ATM-001` | P0 | Sky, sun, moon and stars with dimension fallbacks. | Client scenes and deterministic sky fixtures cover day/night and no-skylight dimensions. | [Features/options][iris-features], [Uniforms][iris-uniforms] | Depends on dimension selection. |
| [ ] ⚪ `ATM-002` | P1 | Fog, aerial perspective and bounded volumetrics. | Depth ramps are monotonic, finite and capped by sample budget. | [Uniforms][iris-uniforms], [Rendering properties][iris-rendering] | Depends on depth and lighting. |
| [ ] ⚪ `CLOUD-001` | P2 | Scalable cloud rendering. | SAFE disables or simplifies; other profiles respect resolution/sample budgets. | [Features/options][iris-features] | Depends on atmosphere. |
| [ ] 🟡 `WEATHER-001` | P1 | Rain and snow geometry foundation plus atmospheric integration. | Existing geometry source is retained; client and offscreen fixtures validate depth/order and wet response. | [Features/options][iris-features], [Rendering properties][iris-rendering] | Integrate materials and fog. |
| [ ] ⚪ `WATER-001` | P1 | Fresnel, reflection, refraction, absorption and bounded waves. | Angle/medium fixtures match invariants; no invalid refraction or unbounded displacement. | [Uniforms][iris-uniforms], [Buffers][iris-buffers] | Depends on SSR and translucency order. |
| [ ] ⚪ `WATER-002` | P1 | Underwater camera, caustics and history reset. | Enter/exit water resets history; view remains finite through resize and teleport. | [Uniforms][iris-uniforms], [Features/options][iris-features] | Depends on temporal framework. |
| [ ] ⚪ `TRANS-001` | P1 | Glass, ice and translucency ordering. | Client scenes prove depth/blend order; offscreen blend fixtures match expected composition. | [Rendering properties][iris-rendering], [`shaders.properties`][iris-properties] | Depends on `IRIS-004`, `PIPE-007`. |
| [ ] 🟡 `PART-001` | P1 | Particle foundation plus material, weather and deferred ordering. | Existing programs compile; client verifies particle ordering and fallback. | [`shaders.properties`][iris-properties], [Programs][iris-programs] | Integrate after `IRIS-006`. |

## 8. Reflections, GI, temporal and post-processing

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `SSR-001` | P1 | Bounded screen-space reflections with confidence and fallback. | Deterministic depth/normal scene validates hit/miss, edge fade and max steps. | [Buffers][iris-buffers], [Uniforms][iris-uniforms] | Depends on HDR/depth schema. |
| [ ] ⚪ `GI-001` | P2 | Bounded screen-space GI. | Sample count, radius and temporal reuse are capped; light leakage fixtures pass thresholds. | [Buffers][iris-buffers], [Uniforms][iris-uniforms] | Depends on temporal and material schema. |
| [ ] ⚪ `GI-002` | P2 | Optional capability-gated voxel lighting. | Compute/images/SSBO path runs only when supported; SAFE fallback remains functional. | [Programs compute][iris-programs], [Feature flags][iris-flags], [macOS limits][iris-macos] | Depends on `IRIS-006`, `GLCLI-002/006`. |
| [ ] ⚪ `TEMP-001` | P0 | Motion vectors, history validity, reprojection and reset. | Multiframe fixtures cover stable motion, disocclusion, resize, teleport and dimension change. | [Uniforms][iris-uniforms], [Buffers][iris-buffers] | Depends on `GLCLI-006`. |
| [ ] ⚪ `POST-001` | P0 | HDR exposure, tonemapping and color-space handling. | Luminance ramps remain monotonic; no clipping outside declared policy; final pass outputs finite display values. | [Final program][iris-final], [Features/options][iris-features], [Uniforms][iris-uniforms] | Depends on HDR schema. |
| [ ] ⚪ `POST-002` | P1 | Bloom, TAA, FXAA fallback, sharpen and dithering. | Each effect has independent toggle, bounded budget and deterministic reference fixture. | [Shader settings][iris-settings], [Programs][iris-programs] | Depends on `TEMP-001`, `POST-001`. |
| [ ] ⚪ `POST-003` | P2 | Optional depth of field and motion blur. | Disabled by default; capped samples; focus and velocity fixtures avoid NaN/ghost trails beyond threshold. | [Uniforms][iris-uniforms], [Shader settings][iris-settings] | HIGH/ULTRA only. |
| [ ] ⚪ `DEBUG-001` | P1 | Debug views for buffers, NaN/Inf, clipping and pass cost. | CLI and client can select each view; artifacts identify failed attachment/pass. | [Debugging][iris-debug], [Buffers][iris-buffers] | Integrate with `focal-gl` artifacts. |

## 9. Render coverage and dimensions

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] 🟡 `TERRAIN-001` | P0 | Solid, cutout and translucent terrain paths. | Existing programs compile; client scenes cover alpha test, materials, shadows and translucency. | [Gbuffers programs][iris-gbuffers], [Rendering properties][iris-rendering] | Add runtime fixtures. |
| [ ] 🟡 `HAND-001` | P1 | Base hand, underwater hand and held-item integration. | Existing underwater foundation plus base/held paths compile and render in client. | [Programs][iris-programs], [Uniforms][iris-uniforms] | Add missing programs and uniforms. |
| [ ] ⚪ `ENTITY-001` | P1 | Entity programs, IDs, materials and translucency. | Representative living, item and translucent entities pass client scenes. | [Gbuffers programs][iris-gbuffers], [Uniforms][iris-uniforms] | Depends on mappings. |
| [ ] ⚪ `BLOCKENTITY-001` | P1 | Block-entity programs and special materials. | Chests, signs, banners and emissive block entities render without missing states. | [Gbuffers programs][iris-gbuffers], [`shaders.properties`][iris-properties] | Depends on mappings. |
| [ ] 🟡 `SPECIAL-001` | P1 | Beacon, damaged block, spider eyes, portals and glint. | Existing foundations compile; missing portal/glint paths are added and client-validated. | [Programs][iris-programs], [`shaders.properties`][iris-properties] | Expand inventory and fixtures. |
| [ ] ⚪ `DIM-001` | P0 | Overworld acceptance. | Locked scene suite covers day/night, weather, water and profile changes. | [Uniforms][iris-uniforms], [Features/options][iris-features] | Depends on core pipeline. |
| [ ] ⚪ `DIM-002` | P0 | Nether acceptance and no-skylight fallback. | No sky-dependent feature leaks; fog, lighting and particles remain stable. | [Uniforms][iris-uniforms], [Features/options][iris-features] | Depends on dimension selection. |
| [ ] ⚪ `DIM-003` | P0 | End acceptance and End-specific events. | Sky, fog, portals and flashes follow documented states or fallback. | [Features/options][iris-features], [Uniforms][iris-uniforms] | Depends on dimension selection. |
| [ ] ⚪ `DIM-004` | P1 | Unknown or modded dimension fallback. | Missing mappings never crash; SAFE behavior uses declared defaults. | [Uniforms][iris-uniforms], [`shaders.properties`][iris-properties] | Add synthetic dimension fixture. |

## 10. Profiles, performance and safety

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `PROFILE-001` | P0 | SAFE profile without mandatory compute, SSBO, tessellation or advanced images. | `focal-gl suite --profile SAFE` passes on baseline GL path and client loads on fallback hardware. | [Feature flags][iris-flags], [macOS limits][iris-macos], [Shader settings][iris-settings] | Build before advanced defaults. |
| [ ] ⚪ `PROFILE-002` | P0 | BALANCED budgets and recommended defaults. | Every enabled feature has measured cost and fallback; no unsupported required flags. | [Shader settings][iris-settings], [Feature flags][iris-flags] | Depends on core effects. |
| [ ] ⚪ `PROFILE-003` | P1 | HIGH capability gates and budgets. | Optional stages/resources are checked by `probe`; unsupported hardware falls to BALANCED. | [Feature flags][iris-flags], [OpenGL extensions][iris-extensions] | Depends on harness capability report. |
| [ ] ⚪ `PROFILE-004` | P2 | ULTRA hard limits and HIGH fallback. | No unlimited setting; memory, samples and dispatch remain within declared caps. | [Shader settings][iris-settings], [Feature flags][iris-flags] | Depends on measured HIGH. |
| [ ] ⚪ `PERF-001` | P1 | Per-pass timing, memory, samples and permutation budgets. | Reports separate compile, upload, draw/dispatch, sync and readback; baseline comparisons are reproducible. | [Debugging][iris-debug] | Integrate timer queries and client metrics. |
| [ ] ⚪ `SAFE-001` | P0 | Static checks for loops, division, normalization, indices and initialization. | Negative fixtures fail with actionable diagnostics; all shaders pass policy. | [Programs][iris-programs], [Patcher][iris-patcher] | Extend validation scripts. |
| [x] 🟢 `SAFE-002` | P0 | Isolated processes, watchdogs and no-driver-hang policy. | PR #99 merged the isolated `focal-gl` worker supervisor after exact-head Validation run `30547008215` succeeded on `7791428a603525b6a1001c6541973ec35f607665`. Forced timeout and POSIX signal fixtures terminate the worker, return stable exit code 7 and preserve `worker.stdout.log`, `worker.stderr.log` and `worker-execution.json`; see [`docs/evidence/GLCLI-007-WORKER-ISOLATION.md`](evidence/GLCLI-007-WORKER-ISOLATION.md). Evidence is `STATIC` at the Python process boundary and does not prove every Windows descendant-cleanup configuration or driver context-loss path. | [Debugging][iris-debug] | Preserve the supervisor boundary; extend platform-specific cleanup and context-loss coverage through `QA-005`. |

## 11. Terminal OpenGL harness and validation

The canonical CLI is `focal-gl`. It must create a real context; a parser, transpiler or mock is not a substitute. Standalone evidence remains distinct from Iris client evidence because Iris patches shader source before GPU compilation. See [Iris Patcher][iris-patcher].

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `QA-001` | P0 | Python tests and Validation workflow for current static contracts. | Existing suite remains green; shader compile/link coverage is added through `focal-gl`. | [Programs][iris-programs] | Preserve and extend. |
| [ ] ⚪ `QA-002` | P0 | Unified `shadercheck` CLI orchestrates static, OpenGL and client-capable checks. | One command selects applicable layers and returns machine-readable summary. | [Debugging][iris-debug], [Patcher][iris-patcher] | Wrap `focal-gl` without hiding exit codes. |
| [ ] ⚪ `QA-003` | P0 | Aggregate headless OpenGL acceptance gate. | `GLCLI-001` through `GLCLI-008` satisfy minimum compile/link/render/readback and safety contract. | [Programs][iris-programs], [Buffers][iris-buffers], [Final program][iris-final] | Cannot complete before all child gates. |
| [x] 🟢 `GLCLI-001` | P0 | Stable terminal interface: `probe`, `compile`, `render`, `suite`, human output, `--json`, artifacts and versioned exit codes. | Merged PR #62 provides `focal-gl`, `tools/focal_gl.py` and subprocess regression tests; exit codes 0/2/3/4/5/6/7/8 are locked. Evidence level is `STATIC`; runtime context remains outside this unit. | [Programs][iris-programs], [Debugging][iris-debug] | Preserve contract; continue with `GLCLI-002`. |
| [ ] 🟡 `GLCLI-002` | P0 | Real offscreen context creation and capability probe across EGL/hidden-window backends. | PR #71 merged the real EGL pbuffer probe with Validation run `30480734608` and evidence in [`docs/evidence/GLCLI-002-EGL-PROBE.md`](evidence/GLCLI-002-EGL-PROBE.md). PR #74 added the explicit Mesa llvmpipe EGL gate; Validation run `30490039060` succeeded, merge `70d0e31f76cd4ede71876b44e5f1966788d81d0a` is on `main`, and PR #75 published [`docs/evidence/GLCLI-002-MESA-CI-PROBE.md`](evidence/GLCLI-002-MESA-CI-PROBE.md). PR #77 added `GL_NUM_EXTENSIONS` plus `glGetStringi` enumeration with a controlled legacy fallback; Validation run `30493688616` succeeded and merge `d66834fc9cff7375da50930c3572eaaa55cdd008` is on `main`. PR #79 merged the controlled hidden-window GLFW backend. PR #80 published [`docs/evidence/GLCLI-002-GLFW-CI-PROBE.md`](evidence/GLCLI-002-GLFW-CI-PROBE.md), recording validated head `12dc8e24f9339193743f2372b2b8e785ebc60aa7` and successful Validation run `30500297439`. The GLFW fixture created a real hidden context on Mesa llvmpipe under Xvfb and reported capabilities. GLCLI-002 remains context/probe evidence only; `GLCLI-004` covers representative compilation/link and `GLCLI-005` covers representative framebuffer draw/readback. | [OpenGL extensions][iris-extensions], [macOS limits][iris-macos] | Complete native WGL and CGL/NSOpenGL routes where supported and collect representative physical-GPU evidence. |
| [x] 🟢 `GLCLI-003` | P0 | Source-mode adapter for original, preprocessed and Iris-patched GLSL. | PR #91 merged `tools/focal_gl_sources.py` and CLI integration after Validation run `30521453670` succeeded. Tests cover stage discovery, stable hashes, relative/root includes, deterministic defines, include cycles, path escapes and explicit patched exports. Evidence is `STATIC`; no OpenGL compile/link or Iris-client acceptance is claimed. | [Iris Patcher][iris-patcher], [Macros][iris-macros] | Preserve source preparation as input to `GLCLI-004/005`; patched-source provenance remains a separate Iris gate. |
| [x] 🟢 `GLCLI-004` | P0 | Stage compilation and program link with complete diagnostics. | PR #93 merged real hidden-GLFW compilation/link after Validation run `30523122062` succeeded. Mesa llvmpipe compiled and linked gbuffers-style, composite-style and final-equivalent vertex/fragment fixtures; an invalid vertex fixture returned exit 4 with a non-empty driver log. Evidence is `GL_COMPILE_LINK` for these exact fixtures and backend, not render/readback or Iris-client acceptance. | [Programs][iris-programs], [Gbuffers programs][iris-gbuffers], [Final program][iris-final] | Preserve diagnostics and source preparation; render/readback continuation is accepted in `GLCLI-005`. |
| [x] 🟢 `GLCLI-005` | P0 | Offscreen framebuffer render and color/depth readback. | PR #97 merged at `cc85e7c4f221ad7f4298f5a96ea34f3c227ac314` after Validation run `30544545413` succeeded on exact head `53756e93b12ce3ce8b8b1f7d48f67f5ddeceb9b1`. Mesa llvmpipe under hidden GLFW/Xvfb completed RGBA32F color plus depth framebuffers, deterministic geometry/fullscreen draws, sampler binding, finite normalized color/depth readback, changed-attachment invariants and PPM/PGM/JSON artifacts for representative gbuffers, composite and final-equivalent fixtures. Evidence is `GL_RENDER_READBACK` only for these exact standalone fixtures; see [`docs/evidence/GLCLI-005-MESA-READBACK.md`](evidence/GLCLI-005-MESA-READBACK.md). | [Buffers][iris-buffers], [ColorTex][iris-colortex], [RENDERTARGETS][iris-rendertargets], [Final program][iris-final] | Preserve the minimum path; multipass/history remains `GLCLI-006`. |
| [ ] ⚪ `GLCLI-006` | P0 | Declarative multipass fixtures, ping-pong, mipmaps, barriers, multiframe history and deterministic invariants. | Repeated suite runs produce stable results within tolerance; temporal reset fixtures pass. | [Programs][iris-programs], [Rendering properties][iris-rendering], [Buffers][iris-buffers] | Depends on completed `GLCLI-005` and pending `TEMP-001`. |
| [x] 🟢 `GLCLI-007` | P0 | Isolated worker process, watchdog, timeout, crash/context-loss classification and cleanup. | PR #99 merged as `27fd2b16a3472b5588a3a69e6aba6f93b345f80b` after exact-head Validation run `30547008215` succeeded on `7791428a603525b6a1001c6541973ec35f607665`. The public entrypoint supervises runtime commands in a separate process group/session, applies the existing timeout as a hard deadline, terminates then escalates after a bounded grace period, relays normal output/exit codes and persists worker logs plus `worker-execution.json`. Forced hangs and POSIX signals return stable exit code 7. Evidence is `STATIC` at the process boundary; see [`docs/evidence/GLCLI-007-WORKER-ISOLATION.md`](evidence/GLCLI-007-WORKER-ISOLATION.md). | [Debugging][iris-debug] | Preserve isolation; platform-specific descendant cleanup and comprehensive OpenGL context-loss detection remain scoped to `QA-005`. |
| [x] 🟢 `GLCLI-008` | P1 | CI matrix and evidence manifest for Mesa software versus real GPU/driver. | PR #103 merged as `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4` after exact-head Validation run `30581017694` succeeded on `611c77d9f88ee9306896b2343e77db1f09cb8a18`. Validation publishes `focal-gl-mesa-evidence-<sha>` with probe, compile/link, render/readback, deterministic manifest and generated image artifacts. The manifest records hashes, byte lengths, backend, vendor, renderer, OpenGL/GLSL versions and explicit claim boundaries. [`docs/GLCLI-008-HARDWARE-EVIDENCE.md`](GLCLI-008-HARDWARE-EVIDENCE.md) defines a separate physical-GPU record and rejects universal compatibility claims. Evidence remains `GL_RENDER_READBACK` only for the exact Mesa fixtures and `STATIC` for the manifest/procedure. | [Debugging][iris-debug], [macOS limits][iris-macos] | Preserve artifact determinism and retention; collect representative physical-GPU records under `GLCLI-002` without widening claims. |
| [ ] ⚪ `QA-004` | P1 | Deterministic visual scenes and invariants. | Fixtures define geometry, textures, uniforms, expected ranges and tolerances. | [Uniforms][iris-uniforms], [Attributes][iris-attributes] | Extend accepted `GLCLI-005` fixtures into `GLCLI-006`. |
| [ ] ⚪ `QA-005` | P1 | NaN/Inf, context-loss, timeout and determinism regression suite. | Fault injection produces expected classification without hanging CI. | [Debugging][iris-debug] | Depends on `GLCLI-006/007`. |
| [ ] ⚪ `QA-006` | P1 | Repeatable profile benchmarks. | Same fixture/profile/backend yields comparable timing and memory records; regressions have thresholds. | [Debugging][iris-debug], [Shader settings][iris-settings] | Depends on profiles and timer support. |

## 12. Client integration, CI and release

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `INT-001` | P0 | Locked Minecraft/Iris/Sodium client integration harness. | Dependency lock launches a clean client fixture and captures logs, versions and patched shaders. | [Iris repository][iris-repo], [Patcher][iris-patcher], [Debugging][iris-debug] | Depends on `BOOT-003`. |
| [ ] ⚪ `INT-002` | P0 | Load, reload, resize, dimension, profile and log acceptance. | Automated or reproducible procedure exercises all transitions with no compile/runtime errors. | [Setup program][iris-setup], [Debugging][iris-debug] | Depends on `INT-001`, core pipeline. |
| [ ] ⚪ `INT-003` | P0 | Sodium compatibility matrix. | Locked compatible releases pass representative scenes and profile switches. | [Iris overview][iris-overview], [Iris repository][iris-repo] | Depends on `BOOT-003`, `INT-001`. |
| [ ] ⚪ `INT-004` | P2 | Distant Horizons evaluation after core acceptance. | Compatibility is measured and classified; unsupported result has explicit fallback. | [ShaderDoc DH support][shaderdoc-dh] | Do not start before core client acceptance. |
| [ ] 🟣 `CI-001` | P0 | Workflow coverage, permissions, pinned actions and timeouts. | Audit confirms all workflows and relevant paths; required checks are green. | [Iris repository][iris-repo] | Revalidate after harness workflow is added. |
| [ ] ⚪ `CI-002` | P1 | Upstream drift workflow for version and documentation changes. | Scheduled job reports new Iris/Sodium releases or broken primary links without auto-claiming compatibility. | [Iris repository][iris-repo], [Iris docs][iris-overview] | Depends on version lock. |
| [ ] ⚪ `CI-003` | P1 | Benchmark workflow and artifacts. | Publishes harness JSON, logs, images and baseline comparison with retention policy. | [Debugging][iris-debug] | Depends on `GLCLI-008`, `QA-006`. |
| [ ] ⚪ `REL-001` | P1 | Release workflow, checksums and rollback. | Only validated commit produces deterministic ZIP, hashes, notes and rollback instructions. | [File structure][iris-overview] | Depends on all release gates. |

## 13. Documentation and completeness

| State / ID | Priority | Feature and observable scope | Acceptance / tests | Iris docs | Dependencies / next action |
|---|---:|---|---|---|---|
| [ ] ⚪ `DOC-001` | P1 | Installation, profiles, compatibility claims and limitations. | Every claim names evidence level, versions and hardware scope. | [Iris overview][iris-overview], [Shader settings][iris-settings] | Update continuously. |
| [ ] ⚪ `DOC-002` | P1 | Architecture, buffer schema, program order and fallbacks. | Diagrams/tables match machine contracts and actual files. | [Programs][iris-programs], [Buffers][iris-buffers] | Depends on pipeline contracts. |
| [ ] ⚪ `DOC-003` | P1 | Troubleshooting, debug mode, `focal-gl` usage and issue evidence template. | Fresh user can run `probe/compile/render/suite`, find artifacts and report environment. | [Debugging][iris-debug], [Patcher][iris-patcher] | Depends on `GLCLI-001/008`. |
| [ ] ⚪ `DOC-004` | P1 | Measured performance and hardware guidance. | Tables identify scene, profile, backend, GPU, driver, resolution and date. | [Debugging][iris-debug], [macOS limits][iris-macos] | Depends on benchmarks. |
| [ ] ⚪ `DONE-001` | P0 | Release-candidate completeness audit. | Every roadmap item is completed, explicitly deferred with rationale or rejected; all links and evidence are current. | [Iris docs][iris-overview], [Iris repository][iris-repo] | Final gate. |

## Ordering, risks and fallbacks

1. Preserve the completed `GLCLI-007` isolation boundary while finishing native `GLCLI-002` WGL and CGL/NSOpenGL routes plus representative physical-GPU evidence; do not bypass the worker supervisor for risky visual shader or multipass work.
2. Continue Iris-format work only when it does not delay the harness foundation.
3. Pin the version lock before client compatibility claims.
4. Define HDR buffers and SAFE/BALANCED profiles before broad material and lighting expansion.
5. Require the evidence level in each feature row before changing its status to complete.
6. Keep compute, SSBO, images and tessellation optional and capability-gated.
7. Preserve remote checkpoints when CI or time prevents completion.
8. Degrade unsupported hardware deterministically to a lower profile or SAFE.
9. Treat llvmpipe as reproducible functional evidence, not vendor performance evidence.
10. Treat standalone OpenGL as necessary but insufficient for Iris client acceptance.

## Audit history

- `2026-07-28` — Revision 1 created from merged governance, CI and geometry evidence.
- `2026-07-28` — Revision 2 linked the canonical Iris matrix.
- `2026-07-29` — Revision 3 accepted the machine-readable shader inventory.
- `2026-07-29` — Revision 4 accepted the stage capability contract, tests and canonical matrix update from PR #55.
- `2026-07-29` — Revision 5 began the buffer lifecycle contract with primary-source evidence and static regression coverage.
- `2026-07-29` — Revision 6 accepted the buffer lifecycle contract, tests and matrix update from PR #56.
- `2026-07-29` — Revision 7 began the output-directive contract and its validation.
- `2026-07-29` — Revision 8 accepted the merged output-directive contract and advanced Iris-format work to `IRIS-005`.
- `2026-07-29` — Revision 9 expanded every roadmap feature with observable scope, acceptance/tests and direct Iris documentation; added the mandatory `focal-gl` OpenGL runtime harness family.
- `2026-07-29` — Revision 10 reconciled merged PR #62, marked `GLCLI-001` complete at `STATIC` evidence and advanced the next unit to `GLCLI-002`.
- `2026-07-29` — Revision 11 reconciled merged PR #71 and evidence PR #72, marked `GLCLI-002` `EN PROGRESO`, and retained the remaining backend, extension and Mesa CI gates without claiming compile/link evidence.
- `2026-07-29` — Revision 12 reconciled the explicit Mesa llvmpipe probe from PR #74 and evidence PR #75, removed the satisfied Mesa CI gate from pending work, and retained `GLCLI-002` `EN PROGRESO` at `STATIC` evidence.
- `2026-07-29` — Revision 13 reconciled PR #77 and Validation run `30493688616`, recorded robust indexed core-profile extension enumeration, and retained only hidden GLFW, WGL and CGL/NSOpenGL routes plus representative hardware evidence as pending `GLCLI-002` work.
- `2026-07-30` — Revision 14 reconciled the controlled hidden GLFW route from PR #79, canonical evidence from PR #80 and watchdog/coordinator hardening from PR #81/#82 against baseline `cc243812bd225f7c26aa4fbae818c11c0f12e839`; `GLCLI-002` remains `EN PROGRESO` without compile/link or render/readback claims.
- `2026-07-30` — Revision 15 reconciled the exact-head `GOV-002` acceptance matrix from PR #89 and successful Validation run `30519455484`, marking the coordinator regression contract complete at `STATIC` evidence.
- `2026-07-30` — Revision 16 reconciled PR #91 and Validation run `30521453670`, completed `GLCLI-003` at `STATIC` evidence, and preserved compile/link and render/readback as `GLCLI-004/005`.
- `2026-07-30` — Revision 17 reconciled PR #93 and Validation run `30523122062`, completed `GLCLI-004` at `GL_COMPILE_LINK` evidence on exact Mesa llvmpipe fixtures, and retained framebuffer render/readback as `GLCLI-005`.
- `2026-07-30` — Revision 18 reconciled PR #97, exact-head Validation run `30544545413` and merge `cc85e7c4f221ad7f4298f5a96ea34f3c227ac314`, completing `GLCLI-005` at bounded `GL_RENDER_READBACK` evidence for representative Mesa llvmpipe/hidden-GLFW fixtures.
- `2026-07-30` — Revision 19 reconciled PR #99, exact-head Validation run `30547008215`, merge `27fd2b16a3472b5588a3a69e6aba6f93b345f80b` and the canonical worker-isolation evidence, completing `GLCLI-007` and `SAFE-002` at `STATIC` process-boundary evidence while retaining platform and driver limits.
- `2026-07-30` — Revision 20 reconciled PR #103, exact-head Validation run `30581017694`, merge `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4`, the deterministic Mesa evidence manifest and the physical-GPU evidence procedure, completing `GLCLI-008` without widening standalone evidence into Iris-client or universal hardware claims.

## Next prioritized unit

`GLCLI-002 native platform and physical-GPU evidence`: complete native WGL and CGL/NSOpenGL capability routes where supported and collect representative physical-GPU records under the GLCLI-008 procedure; preserve the completed worker and evidence-manifest boundaries.

## Official Iris documentation references

[iris-overview]: https://shaders.properties/current/reference/overview/
[iris-programs]: https://shaders.properties/current/reference/programs/overview/
[iris-gbuffers]: https://shaders.properties/current/reference/programs/gbuffers/
[iris-setup]: https://shaders.properties/current/reference/programs/setup/
[iris-final]: https://shaders.properties/current/reference/programs/final/
[iris-buffers]: https://shaders.properties/current/reference/buffers/overview/
[iris-colortex]: https://shaders.properties/current/reference/buffers/colortex/
[iris-buffer-format]: https://shaders.properties/current/reference/constants/buffer_format/
[iris-uniforms]: https://shaders.properties/current/reference/uniforms/overview/
[iris-attributes]: https://shaders.properties/current/reference/attributes/overview/
[iris-constants]: https://shaders.properties/current/reference/constants/overview/
[iris-rendertargets]: https://shaders.properties/current/reference/constants/rendertargets/
[iris-drawbuffers]: https://shaders.properties/current/reference/constants/drawbuffers/
[iris-properties]: https://shaders.properties/current/reference/shadersproperties/overview/
[iris-rendering]: https://shaders.properties/current/reference/shadersproperties/rendering/
[iris-settings]: https://shaders.properties/current/reference/shadersproperties/shader_settings/
[iris-features]: https://shaders.properties/current/reference/shadersproperties/features/
[iris-flags]: https://shaders.properties/current/reference/shadersproperties/flags/
[iris-patcher]: https://shaders.properties/current/reference/miscellaneous/patcher/
[iris-debug]: https://shaders.properties/current/reference/miscellaneous/debugging_shaders/
[iris-macos]: https://shaders.properties/current/reference/miscellaneous/macos/
[iris-extensions]: https://shaders.properties/current/reference/macros/supported_extensions/
[iris-macros]: https://shaders.properties/current/reference/macros/overview/
[iris-is-iris]: https://shaders.properties/current/reference/macros/is_iris/
[iris-repo]: https://github.com/IrisShaders/Iris
[shaderdoc-unsupported]: https://github.com/IrisShaders/ShaderDoc/blob/master/unsupported-features.md
[shaderdoc-dh]: https://github.com/IrisShaders/ShaderDoc/blob/master/dh-support.md
