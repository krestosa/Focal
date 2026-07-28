# Focal master roadmap

## Objective and canonical evidence

Maintain one evidence-based plan for completing Focal as a safe, scalable Iris shader pack for the project target, currently declared as Minecraft Java 26.2 pending official version verification. Work not represented here must be added before implementation.

- Canonical Iris evidence: [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md)
- Audit UTC: `2026-07-28T23:23:00Z`
- Baseline audited: `e7a4eb6aaa125710dce5e6243bbb955cc1235b67`
- Roadmap schema revision: `2`
- Current stage: Phase 1 foundation, Iris capability inventory and static validation

## Status legend

- [ ] ⚪ PENDING — work not started.
- [ ] 🟡 IN PROGRESS — work started and preserved remotely.
- [x] ✅ COMPLETED — implementation and acceptance evidence verified on `main`.
- [ ] 🔁 REVALIDATE — evidence is stale, incomplete or version-sensitive.
- [ ] ⛔ BLOCKED — externally blocked with evidence.

A checked item requires implementation on `main`, applicable tests, green relevant checks, synchronized documentation and no invalidating known blocker.

## Compatibility status

| Component | State | Required next evidence |
|---|---|---|
| Minecraft Java 26.2 | 🔁 REVALIDATE | Verify official release metadata and integration viability. |
| Iris | 🔁 REVALIDATE | Pin exact stable release/tag/commit. |
| Sodium | 🔁 REVALIDATE | Pin the version required by the selected Iris release. |
| Fabric Loader/API | 🔁 REVALIDATE | Pin compatible versions and hashes. |
| Java | 🔁 REVALIDATE | Confirm the official runtime requirement. |
| OpenGL/GLSL | 🟡 IN PROGRESS | Define SAFE baseline and capability-gated advanced contexts. |
| Drivers/hardware | ⚪ PENDING | Establish representative Mesa and vendor evidence. |

## 1. Governance, coordination and recovery

- [x] ✅ COMPLETED — `GOV-001` Body-only lease coordinator. Evidence: issue #7 and `.github/workflows/automation-state.yml`.
- [ ] 🔁 REVALIDATE — `GOV-002` Coordinator regression suite: concurrent acquire, stale recovery, ownership loss, malformed/duplicate commands, heartbeat and release rejection.
- [x] ✅ COMPLETED — `GOV-003` Remote checkpoint discipline used by recent feature PRs.
- [ ] ⚪ PENDING — `GOV-004` Branch and PR recovery audit with explicit active-work links.

## 2. Bootstrap, structure, packaging and versions

- [x] ✅ COMPLETED — `BOOT-001` Repository foundation and base Validation workflow.
- [ ] 🔁 REVALIDATE — `BOOT-002` Exact pack structure audit covering root metadata, `shaders/`, `tools/`, `tests/`, `spec/`, `docs/`, packaging and workflows.
- [ ] ⚪ PENDING — `BOOT-003` Machine-readable dependency/version lock with URLs, review dates and hashes.
- [ ] ⚪ PENDING — `BOOT-004` Reproducible ZIP with `shaders/` at archive root and deterministic checksum.
- [ ] ⚪ PENDING — `BOOT-005` Release metadata, changelog, rollback and installation verification.

## 3. Iris audit and compatibility

- [ ] 🟡 IN PROGRESS — `IRIS-001` Program inventory.
  - Published evidence: [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md) records program order, families, stages, suffixes, direct geometry access, documented fallbacks, current Focal evidence and tests.
  - Acceptance remaining: machine-check every current Focal shader filename against the matrix and merge the matrix/roadmap reconciliation.
- [ ] ⚪ PENDING — `IRIS-002` Stage inventory: vertex, fragment, geometry, compute, tessellation, flags, OpenGL requirements and macOS fallback.
- [ ] ⚪ PENDING — `IRIS-003` Buffer/attachment inventory: colortex, depth, shadow, history, formats, clear, mipmaps, viewport, scaling, ping-pong and lifetime.
- [ ] ⚪ PENDING — `IRIS-004` Constants and directives including `DRAWBUFFERS`, `RENDERTARGETS`, formats, clears, blend and stage restrictions.
- [ ] ⚪ PENDING — `IRIS-005` Uniforms, attributes, matrices, camera/world/time/weather/entity data and reserved names.
- [ ] ⚪ PENDING — `IRIS-006` Complete `shaders.properties` directive matrix, feature flags, custom resources, SSBO and dispatch.
- [ ] ⚪ PENDING — `IRIS-007` Defines, sliders, profiles, screens, subscreens, columns and `.lang` localization.
- [ ] ⚪ PENDING — `IRIS-008` Block/item/entity/block-entity/biome mappings and dimension behavior.
- [ ] ⚪ PENDING — `IRIS-009` Unsupported, deprecated and Iris-exclusive features with adopt/defer/reject decisions and fallback.
- [ ] ⚪ PENDING — `IRIS-010` Iris Patcher, transformation rules, diagnostics and reproducible compile-failure evidence.

## 4. Pipeline, programs and resources

- [x] ✅ COMPLETED — `PIPE-001` Minimal geometry foundations merged through PRs #41–#50; these are not full runtime acceptance.
- [ ] 🔁 REVALIDATE — `PIPE-002` Machine-readable inventory of every existing stage mapped to recognized Iris names and fallback graph.
- [ ] ⚪ PENDING — `PIPE-003` Remaining required gbuffers programs: basic, line, textured, lit, entities, block entities, hand, clouds, sky, water, portal and supported special effects.
- [ ] ⚪ PENDING — `PIPE-004` Dimension-specific program selection and deterministic fallback.
- [ ] ⚪ PENDING — `PIPE-005` HDR G-buffer schema for albedo, normals, material data, emission, depth, motion and history.
- [ ] ⚪ PENDING — `PIPE-006` `shaders.properties`, profiles, screens and localization.
- [ ] ⚪ PENDING — `PIPE-007` Bounded shadowcomp/prepare/deferred/composite/final foundation.

## 5. Materials, lighting, shadows and occlusion

- [ ] ⚪ PENDING — `MAT-001` Albedo and non-PBR fallback.
- [ ] ⚪ PENDING — `MAT-002` Normal/specular resource-pack support and applicable labPBR interpretation.
- [ ] ⚪ PENDING — `MAT-003` Roughness, metallic, emission, porosity, subsurface and AO validation.
- [ ] ⚪ PENDING — `MAT-004` Bounded POM and optional parallax shadows.
- [ ] ⚪ PENDING — `LIGHT-001` Solar/lunar direct lighting and continuous time transition.
- [ ] ⚪ PENDING — `LIGHT-002` Block light, held light and colored emission.
- [ ] ⚪ PENDING — `SHADOW-001` Directional shadow maps, bias, filtering and stabilization.
- [ ] ⚪ PENDING — `SHADOW-002` Entities, block entities, translucent/colored shadows and contact fallback.
- [ ] ⚪ PENDING — `AO-001` Bounded ambient occlusion with quantitative tests.

## 6. World, atmosphere and translucency

- [ ] ⚪ PENDING — `ATM-001` Rayleigh/Mie sky, sun, moon, stars and dimension fallbacks.
- [ ] ⚪ PENDING — `ATM-002` Fog, aerial perspective, bounded volumetrics and shafts.
- [ ] ⚪ PENDING — `CLOUD-001` Scalable cloud layers and shadow response.
- [ ] 🟡 IN PROGRESS — `WEATHER-001` Rain/snow geometry foundation from PR #42; atmospheric integration pending.
- [ ] ⚪ PENDING — `WATER-001` Fresnel, reflection, refraction, absorption, scattering and bounded waves.
- [ ] ⚪ PENDING — `WATER-002` Underwater camera, caustics and history reset.
- [ ] ⚪ PENDING — `TRANS-001` Glass, ice and translucency ordering/lighting.
- [ ] 🟡 IN PROGRESS — `PART-001` Particle foundation from PR #43; material, weather and emissive integration pending.

## 7. Reflections, GI, temporal and post-processing

- [ ] ⚪ PENDING — `SSR-001` Bounded SSR with roughness and environment fallback.
- [ ] ⚪ PENDING — `GI-001` Bounded SSGI and denoising.
- [ ] ⚪ PENDING — `GI-002` Optional capability-gated voxel lighting with memory budgets.
- [ ] ⚪ PENDING — `TEMP-001` Motion vectors, history validity and discontinuity reset.
- [ ] ⚪ PENDING — `POST-001` HDR exposure, adaptation and documented tonemapping.
- [ ] ⚪ PENDING — `POST-002` Bloom, TAA, FXAA fallback, sharpen and dithering.
- [ ] ⚪ PENDING — `POST-003` Optional DOF and motion blur, disabled by default.
- [ ] ⚪ PENDING — `DEBUG-001` Buffer, NaN/Inf and pass-cost debug views.

## 8. Render coverage and dimensions

- [ ] 🟡 IN PROGRESS — `TERRAIN-001` Solid, cutout and translucent foundations merged in PRs #48–#50; authoritative naming, water separation, materials and shadow integration remain.
- [ ] 🟡 IN PROGRESS — `HAND-001` Underwater-hand foundation from PR #41; base hand and held-item integration remain.
- [ ] ⚪ PENDING — `ENTITY-001` Entity and translucent-entity paths.
- [ ] ⚪ PENDING — `BLOCKENTITY-001` Block-entity paths and ordering.
- [ ] 🟡 IN PROGRESS — `SPECIAL-001` Beacon, damaged-block and spider-eyes foundations from PRs #44, #46 and #47; portals, glint/enchants and End effects remain.
- [ ] ⚪ PENDING — `DIM-001` Overworld pipeline and acceptance scenes.
- [ ] ⚪ PENDING — `DIM-002` Nether pipeline and acceptance scenes.
- [ ] ⚪ PENDING — `DIM-003` End pipeline and acceptance scenes.

## 9. Profiles, performance and safety

- [ ] ⚪ PENDING — `PROFILE-001` SAFE without mandatory compute, SSBO, tessellation or advanced images.
- [ ] ⚪ PENDING — `PROFILE-002` BALANCED budgets and defaults.
- [ ] ⚪ PENDING — `PROFILE-003` HIGH capability gates and budgets.
- [ ] ⚪ PENDING — `PROFILE-004` ULTRA hard limits and HIGH fallback.
- [ ] ⚪ PENDING — `PERF-001` Per-pass timing, memory, samples, steps and permutation budgets.
- [ ] ⚪ PENDING — `SAFE-001` Static checks for unbounded loops, unsafe division, zero normalization, invalid indices and uninitialized values.
- [ ] ⚪ PENDING — `SAFE-002` Isolated test processes, watchdogs, memory limits and no-driver-hang policy.

## 10. Validation, integration and release

- [ ] 🟡 IN PROGRESS — `QA-001` Python foundation tests and Validation workflow; exact coverage and compile/link behavior remain.
- [ ] ⚪ PENDING — `QA-002` `python -m tools.shadercheck` include, name, stage, profile, dimension, interface and safety validation.
- [ ] ⚪ PENDING — `QA-003` Headless OpenGL harness using available Mesa backends.
- [ ] ⚪ PENDING — `QA-004` Deterministic visual scenes and quantitative invariants.
- [ ] ⚪ PENDING — `QA-005` NaN/Inf, context-loss, timeout, cleanup and determinism tests.
- [ ] ⚪ PENDING — `QA-006` Repeatable profile benchmarks and regression thresholds.
- [ ] ⚪ PENDING — `INT-001` Locked client integration harness without redistributing game assets.
- [ ] ⚪ PENDING — `INT-002` Load/reload/resize/dimension/camera/profile/log/screenshot acceptance.
- [ ] ⚪ PENDING — `INT-003` Sodium compatibility matrix and regression evidence.
- [ ] ⚪ PENDING — `INT-004` Distant Horizons evaluation only after core acceptance.
- [ ] 🔁 REVALIDATE — `CI-001` Workflow coverage, permissions, pinned actions and timeouts.
- [ ] ⚪ PENDING — `CI-002` Upstream capability/version drift workflow.
- [ ] ⚪ PENDING — `CI-003` Benchmark workflow and reproducible artifacts.
- [ ] ⚪ PENDING — `REL-001` Release workflow, checksums, reproducibility and rollback.

## 11. Documentation and completeness

- [ ] ⚪ PENDING — `DOC-001` Installation, profiles, compatibility claims and limitations.
- [ ] ⚪ PENDING — `DOC-002` Architecture, buffer schema, program order and fallbacks.
- [ ] ⚪ PENDING — `DOC-003` Troubleshooting, debug mode, logs and issue evidence template.
- [ ] ⚪ PENDING — `DOC-004` Performance and hardware guidance constrained to measured evidence.
- [ ] ⚪ PENDING — `DONE-001` Release-candidate audit against every item and acceptance gate.

## Ordering, risks and fallbacks

1. Complete the Iris inventory and exact version lock before advanced programs.
2. Define buffer schema and SAFE/BALANCED profiles before material/lighting expansion.
3. Require static compile/link validation before accepting visual subsystems.
4. Require headless OpenGL and client integration before runtime compatibility claims.
5. Keep compute, SSBO, images and tessellation optional and capability-gated.
6. Preserve checkpoints when CI or time prevents completion; never merge unknown checks.
7. Degrade unsupported hardware deterministically to a lower profile or SAFE.

## Audit history

- `2026-07-28` — Revision 1 created from merged governance, CI and geometry evidence.
- `2026-07-28` — Revision 2 linked the canonical Iris matrix, reconciled program-family evidence and selected machine-readable shader inventory as the next acceptance gate.

## Next prioritized unit

`PIPE-002 — Existing program inventory`: implement a machine-readable scan of current `shaders/` stages, compare every filename and stage pair against [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md), report unsupported or ambiguous names, and add CI coverage before any new shader feature.