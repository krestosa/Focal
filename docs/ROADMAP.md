# Focal master roadmap

## Objective

Maintain a single evidence-based plan for completing Focal as a safe, scalable Iris shader pack for Minecraft Java 26.2. This document is the required gate for autonomous implementation: work not represented here must be added before implementation, and status changes require remote evidence.

## Status legend

- [ ] ⚪ PENDING — work not started.
- [ ] 🟡 IN PROGRESS — work started and preserved remotely.
- [x] ✅ COMPLETED — implementation and acceptance evidence verified.
- [ ] 🔁 REVALIDATE — evidence is stale, incomplete, or version-sensitive.
- [ ] ⛔ BLOCKED — externally blocked with evidence.

## Audit metadata

- Audit timestamp: `2026-07-28T22:18:00Z`
- Baseline `main`: `a336c40cca65bf70e09b2c5f4559b5a402df0785`
- Roadmap schema revision: `1`
- Current stage: Phase 1 foundation and Iris capability inventory
- Completion rule: a checked item requires implementation, tests or equivalent evidence, green relevant checks, and synchronized documentation/configuration.

## Verified official sources

Consulted on `2026-07-28` UTC:

- https://shaders.properties/current/
- https://shaders.properties/current/reference/overview/
- https://shaders.properties/current/reference/programs/overview/
- https://shaders.properties/current/reference/shadersproperties/overview/
- https://shaders.properties/current/reference/shadersproperties/shader_settings/
- https://github.com/IrisShaders/Iris
- https://github.com/IrisShaders/docs
- https://github.com/IrisShaders/ShaderDoc

The current Iris documentation identifies gbuffers-style, composite-style and compute-only program families; vertex, fragment, geometry, compute and tessellation stages; suffix-based program expansion; feature flags; render-target directives; shader settings, profiles and language files. Compute and tessellation paths require explicit capability and fallback treatment.

## Compatibility matrix

| Component | Target | Evidence state | Next action |
|---|---|---|---|
| Minecraft Java | 26.2 | Fixed project target; runtime evidence pending | Resolve official release metadata and integration fixture |
| Iris | Latest stable mutually compatible release | 🔁 REVALIDATE | Pin exact release/tag/commit and supported feature matrix |
| Sodium | Stable version required by pinned Iris | 🔁 REVALIDATE | Record exact compatibility evidence |
| Fabric Loader/API | Stable compatible combination | 🔁 REVALIDATE | Pin versions and hashes |
| Java | Version required by Minecraft/Fabric toolchain | 🔁 REVALIDATE | Confirm official requirement |
| Gradle/Loom | Reproducible harness toolchain | 🔁 REVALIDATE | Pin versions and dependency locks |
| OpenGL/GLSL | SAFE baseline plus capability-gated advanced paths | 🟡 IN PROGRESS | Define minimum contexts and per-profile limits |
| Drivers | Mesa plus representative vendor matrix | ⚪ PENDING | Establish CI and manual evidence matrix |

## Coverage summary

- Governance and lease coordination: implemented and exercised through issue #7; full regression evidence remains subject to periodic revalidation.
- Base CI: present and producing green Validation runs for recent PR heads.
- Runtime guard foundation: present according to merged history; full current test inventory must be audited.
- Geometry foundation: several gbuffers fallbacks exist and have green PR evidence.
- Materials, lighting, atmosphere, water, indirect lighting and post-processing: not yet accepted as complete.
- Iris capability inventory: initiated by this roadmap; detailed feature-by-feature audit remains pending.
- Minecraft/Iris client integration: no accepted evidence yet.

## 1. Governance, coordination and source of truth

- [x] ✅ COMPLETED — `GOV-001` Body-only lease coordinator.
  - Scope: issue #7 command/state blocks and Automation State Coordinator workflow.
  - Acceptance: acquire/release correlation, owner verification, future lease, final idle state, zero operational comments and commits.
  - Evidence: issue #7; repeated successful cycles through state version 98.
- [ ] 🔁 REVALIDATE — `GOV-002` Full coordinator regression suite.
  - Tests: simultaneous acquire, stale lease recovery, ownership loss, malformed command, duplicate command, heartbeat and release rejection.
  - Acceptance: deterministic fixtures and green CI.
- [x] ✅ COMPLETED — `GOV-003` Remote checkpoint and one-path-per-commit policy used by recent feature PRs.
  - Evidence: PRs #41–#50, each feature split into individual file commits.
- [ ] ⚪ PENDING — `GOV-004` Branch and PR recovery audit.
  - Steps: enumerate open/recoverable branches and PRs each cycle; link active work here.

## 2. Bootstrap, structure, packaging and versions

- [x] ✅ COMPLETED — `BOOT-001` Repository foundation and base Validation workflow.
- [ ] 🔁 REVALIDATE — `BOOT-002` Exact repository structure against required pack layout.
  - Inspect: `shaders/`, `tools/`, `tests/`, `spec/`, `docs/`, `packaging/`, workflows and root metadata.
- [ ] ⚪ PENDING — `BOOT-003` Machine-readable dependency/version lock.
  - Include: Minecraft, Fabric Loader/API, Iris, Sodium, Java, Gradle, Loom, Mesa/harness dependencies, source URL, date and hashes.
- [ ] ⚪ PENDING — `BOOT-004` Reproducible ZIP packaging.
  - Acceptance: `shaders/` at archive root, excluded development/runtime files, deterministic checksum.
- [ ] ⚪ PENDING — `BOOT-005` Release metadata, changelog, rollback and installation verification.

## 3. Complete Iris audit and compatibility

- [ ] 🟡 IN PROGRESS — `IRIS-001` Program inventory.
  - Enumerate and classify `setup`, `begin`, `shadow`, `shadowcomp`, `prepare`, all documented `gbuffers_*`, `deferred`, `composite` and `final` variants, suffix limits and execution order.
  - Record required/optional stages, direct geometry access, fallback and tests.
- [ ] ⚪ PENDING — `IRIS-002` Stage capability inventory.
  - Cover vertex, fragment, geometry, compute, tessellation control/evaluation, feature flags, OpenGL requirements and macOS-safe fallback.
- [ ] ⚪ PENDING — `IRIS-003` Buffer and attachment inventory.
  - Cover colortex/depth/shadow/history buffers, formats, clear, mipmaps, scaling, viewport, ping-pong and lifetime.
- [ ] ⚪ PENDING — `IRIS-004` Constants and directives.
  - Cover `DRAWBUFFERS`, `RENDERTARGETS`, render-target formats, clears, mipmaps, blend rules and stage restrictions.
- [ ] ⚪ PENDING — `IRIS-005` Uniforms, attributes and vertex-format extensions.
  - Cover matrices, camera, time, weather, world, entity, lighting, render state, reserved names and patched shader behavior.
- [ ] ⚪ PENDING — `IRIS-006` `shaders.properties` complete directive matrix.
  - Cover required/optional feature flags, program ordering, custom uniforms/textures/images, SSBO, indirect dispatch, culling and render options.
- [ ] ⚪ PENDING — `IRIS-007` User options and localization.
  - Cover defines, sliders, profiles, screens, subscreens, columns and `.lang` labels/tooltips.
- [ ] ⚪ PENDING — `IRIS-008` Mapping files and dimensions.
  - Cover blocks, items, entities, block entities, biomes, Overworld, Nether, End and custom dimensions.
- [ ] ⚪ PENDING — `IRIS-009` Unsupported, deprecated and Iris-exclusive features.
  - Acceptance: explicit adopt/defer/reject state and deterministic fallback for every applicable capability.
- [ ] ⚪ PENDING — `IRIS-010` Iris Patcher and diagnostics.
  - Cover transformation rules, reserved identifiers, debug mode, compile logs and reproducible failure evidence.

## 4. Pipeline, programs, buffers, uniforms and properties

- [x] ✅ COMPLETED — `PIPE-001` Minimal geometry fallback set currently merged.
  - Evidence: hand-water PR #41, weather #42, particles #43, beacon beam #44, damaged block #46, spider eyes #47, terrain solid #48, terrain cutout #49 and terrain translucent #50; each reported green Validation evidence.
- [ ] 🔁 REVALIDATE — `PIPE-002` Existing generic terrain/entity/hand program inventory.
  - Acceptance: all present stages mapped to Iris program names and shader checker coverage.
- [ ] ⚪ PENDING — `PIPE-003` Remaining required gbuffers programs.
  - Include basic/textured/textured_lit, terrain variants, entities, block entities, hand, armor glint, clouds, sky, water, portal and special effects where supported.
- [ ] ⚪ PENDING — `PIPE-004` Dimension-specific program selection and fallbacks.
- [ ] ⚪ PENDING — `PIPE-005` HDR G-buffer schema.
  - Define albedo, normals, material parameters, emission, depth/motion/history and profile-dependent formats.
- [ ] ⚪ PENDING — `PIPE-006` `shaders.properties`, profiles, screens and localization.
- [ ] ⚪ PENDING — `PIPE-007` Composite/deferred/final foundation with bounded passes.

## 5. Materials, PBR, lighting, shadows and occlusion

- [ ] ⚪ PENDING — `MAT-001` Albedo and non-PBR fallback.
- [ ] ⚪ PENDING — `MAT-002` Normal/specular resource-pack support and labPBR-compatible channel interpretation where applicable.
- [ ] ⚪ PENDING — `MAT-003` Roughness, metallic, emission, porosity, subsurface and AO validation.
- [ ] ⚪ PENDING — `MAT-004` Bounded POM and optional parallax shadows.
- [ ] ⚪ PENDING — `LIGHT-001` Solar/lunar direct lighting and continuous time transition.
- [ ] ⚪ PENDING — `LIGHT-002` Block light, held light and colored emission.
- [ ] ⚪ PENDING — `SHADOW-001` Directional shadow maps, bias, filtering and stabilization.
- [ ] ⚪ PENDING — `SHADOW-002` Entities, block entities, translucent/colored shadows and contact shadow fallback.
- [ ] ⚪ PENDING — `AO-001` Bounded ambient occlusion with quantitative tests.

## 6. Sky, atmosphere, climate, water, glass, translucency and particles

- [ ] ⚪ PENDING — `ATM-001` Rayleigh/Mie sky, sun, moon, stars and dimension-specific fallback.
- [ ] ⚪ PENDING — `ATM-002` Fog, aerial perspective, volumetrics and bounded shafts.
- [ ] ⚪ PENDING — `CLOUD-001` Scalable cloud layers and shadow response.
- [ ] 🟡 IN PROGRESS — `WEATHER-001` Rain/snow geometry fallback.
  - Evidence: PR #42 covers the weather program foundation; atmospheric integration remains pending.
- [ ] ⚪ PENDING — `WATER-001` Fresnel, reflection, refraction, absorption, scattering and multi-scale waves.
- [ ] ⚪ PENDING — `WATER-002` Underwater camera, caustics and history reset.
- [ ] ⚪ PENDING — `TRANS-001` Glass/ice/translucency ordering and lighting.
- [ ] 🟡 IN PROGRESS — `PART-001` Particle fallback.
  - Evidence: PR #43; full material, weather and emissive integration pending.

## 7. Reflections, GI, screen-space, voxelization, temporal and post-processing

- [ ] ⚪ PENDING — `SSR-001` Bounded SSR with refinement, roughness, off-screen rejection and environment fallback.
- [ ] ⚪ PENDING — `GI-001` Bounded SSGI and spatial/temporal denoising.
- [ ] ⚪ PENDING — `GI-002` Optional capability-gated voxel lighting with memory budgets.
- [ ] ⚪ PENDING — `TEMP-001` Motion vectors, history validity, resize/reload/dimension/FOV/teleport reset.
- [ ] ⚪ PENDING — `POST-001` HDR exposure, robust adaptation and documented tonemapping.
- [ ] ⚪ PENDING — `POST-002` Bloom, TAA, FXAA fallback, sharpen, dithering and optional upscaling.
- [ ] ⚪ PENDING — `POST-003` Optional DOF and motion blur, disabled by default.
- [ ] ⚪ PENDING — `DEBUG-001` Debug views for every major buffer, NaN/Inf and pass cost.

## 8. Terrain, entities, hand, block entities and dimensions

- [ ] 🟡 IN PROGRESS — `TERRAIN-001` Terrain program family.
  - Completed foundations: solid, cutout and translucent PRs #48–#50.
  - Remaining: authoritative Iris naming audit, water separation, moving terrain where applicable, material outputs and shadow integration.
- [ ] 🟡 IN PROGRESS — `HAND-001` Hand and underwater hand paths.
  - Evidence: hand-water PR #41; base hand and held-item material/lighting integration pending.
- [ ] ⚪ PENDING — `ENTITY-001` Entity and translucent entity paths.
- [ ] ⚪ PENDING — `BLOCKENTITY-001` Block entity paths and ordering.
- [ ] 🟡 IN PROGRESS — `SPECIAL-001` Special geometry passes.
  - Evidence: beacon beam #44, damaged block #46 and spider eyes #47.
  - Remaining: portals, armor glint/enchants, End effects and other documented programs.
- [ ] ⚪ PENDING — `DIM-001` Overworld pipeline and acceptance scenes.
- [ ] ⚪ PENDING — `DIM-002` Nether pipeline and acceptance scenes.
- [ ] ⚪ PENDING — `DIM-003` End pipeline and acceptance scenes.

## 9. Profiles, performance and CPU/GPU safety

- [ ] ⚪ PENDING — `PROFILE-001` SAFE profile without mandatory compute, SSBO, tessellation or advanced custom images.
- [ ] ⚪ PENDING — `PROFILE-002` BALANCED profile and budgets.
- [ ] ⚪ PENDING — `PROFILE-003` HIGH profile and capability gates.
- [ ] ⚪ PENDING — `PROFILE-004` ULTRA profile with hard limits and HIGH fallback.
- [ ] ⚪ PENDING — `PERF-001` Per-pass timing, memory, samples, steps and permutation budgets.
- [ ] ⚪ PENDING — `SAFE-001` Static checks for unbounded loops, unsafe division, zero normalization, invalid indexing and uninitialized values.
- [ ] ⚪ PENDING — `SAFE-002` Watchdog, isolated test processes, memory limits and no-driver-hang test policy.

## 10. Compilation, static analysis, OpenGL, visual tests and benchmarks

- [ ] 🟡 IN PROGRESS — `QA-001` Existing Python foundation tests and Validation workflow.
  - Acceptance remaining: inventory exact coverage and eliminate tests that only assert text without compiling/linking behavior.
- [ ] ⚪ PENDING — `QA-002` `python -m tools.shadercheck` include resolver, pairwise profile/dimension compilation, interface/link and safety checks.
- [ ] ⚪ PENDING — `QA-003` Headless OpenGL harness using EGL/OSMesa/Xvfb/Mesa where available.
- [ ] ⚪ PENDING — `QA-004` Deterministic visual scenes and quantitative invariants.
- [ ] ⚪ PENDING — `QA-005` NaN/Inf, context-loss, timeout, cleanup and determinism tests.
- [ ] ⚪ PENDING — `QA-006` Repeatable profile benchmarks and regression thresholds.

## 11. Minecraft/Iris/Sodium integration, CI, recovery and releases

- [ ] ⚪ PENDING — `INT-001` Locked client integration harness in virtual graphics environment; do not redistribute game assets.
- [ ] ⚪ PENDING — `INT-002` Load, reload, resize, dimension change, camera path, profile switch, logs and screenshots.
- [ ] ⚪ PENDING — `INT-003` Sodium compatibility matrix and regression evidence.
- [ ] ⚪ PENDING — `INT-004` Distant Horizons evaluation only after core acceptance; no assumed support.
- [ ] 🔁 REVALIDATE — `CI-001` Validation workflow coverage, permissions, pinned action SHAs and timeouts.
- [ ] ⚪ PENDING — `CI-002` Upstream version/capability drift workflow.
- [ ] ⚪ PENDING — `CI-003` Benchmark workflow and reproducible artifacts.
- [ ] ⚪ PENDING — `REL-001` Release workflow, checksums, reproducibility and rollback.

## 12. Documentation, support and definition of completeness

- [ ] ⚪ PENDING — `DOC-001` Installation, profiles, compatibility claims and limitations.
- [ ] ⚪ PENDING — `DOC-002` Architecture, buffer schema, program order and capability fallbacks.
- [ ] ⚪ PENDING — `DOC-003` Troubleshooting, debug mode, logs and issue evidence template.
- [ ] ⚪ PENDING — `DOC-004` Performance and hardware guidance constrained to measured evidence.
- [ ] ⚪ PENDING — `DONE-001` Release-candidate audit against every roadmap item and acceptance gate.

## Dependencies and ordering

1. Finish `IRIS-001` through `IRIS-010` and pin versions before expanding advanced programs.
2. Define the buffer schema and SAFE/BALANCED profiles before material and lighting expansion.
3. Complete shader compilation/link validation before accepting visual subsystems.
4. Complete headless OpenGL tests before claiming runtime correctness.
5. Complete Minecraft/Iris integration before claiming in-game compatibility.
6. Complete packaging and release gates only after profiles and integration are green.

## Risks and fallbacks

- Version drift: mark affected items `REVALIDATE`; never preserve a completed state without current evidence.
- Unsupported hardware capability: degrade deterministically to the next lower profile or SAFE path.
- CI delay: preserve branch/PR checkpoint and finish `INCOMPLETE` rather than merge without evidence.
- Invalid roadmap evidence: uncheck the item and record the exact missing acceptance gate.
- Compute/SSBO/tessellation limitations: optional only; never required by SAFE.
- Resource-pack incompleteness: use bounded defaults and prevent NaN/Inf.

## Decisions

- The roadmap is a mandatory implementation gate and must be reconciled at the beginning and end of every autonomous cycle.
- Recent geometry PRs are recorded as foundations, not proof that complete material, lighting or in-game integration exists.
- Text-presence tests are useful bootstrap checks but cannot substitute for compilation, linking or runtime evidence.
- Advanced Iris-exclusive features remain deferred until exact version and capability evidence is pinned.

## Audit history

- `2026-07-28` — Created roadmap revision 1 from baseline `a336c40cca65bf70e09b2c5f4559b5a402df0785`; recorded current governance, CI and merged geometry evidence; opened full Iris capability inventory.

## Next prioritized unit

`IRIS-001 — Program inventory`: expand this document with a complete table of official Iris program names, execution order, required/optional stages, suffix ranges, direct geometry access, capability requirements, existing Focal files, fallback, test coverage and acceptance state. No new shader feature should be started until that table is published and validated.