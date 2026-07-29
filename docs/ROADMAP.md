# Focal master roadmap

## Objective and canonical evidence

Maintain one evidence-based plan for completing Focal as a safe, scalable Iris shader pack. Work not represented here must be added before implementation.

- Canonical Iris evidence: [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md)
- Audit UTC: `2026-07-29T03:20:00Z`
- Baseline audited: `4d09aa437ae2702e30659f02a10fc21fe2480cbc`
- Roadmap schema revision: `5`
- Current stage: Phase 1 foundation, capability contracts and static validation

## Status legend

- [ ] ⚪ PENDIENTE
- [ ] 🟡 EN PROGRESO
- [x] 🟢 COMPLETADO
- [ ] 🟣 REVALIDAR
- [ ] 🔴 BLOQUEADO

A checked item requires implementation on `main`, applicable tests, green relevant checks, synchronized documentation and no invalidating blocker.

## Compatibility status

| Component | State | Required next evidence |
|---|---|---|
| Minecraft Java 26.2 | 🟣 REVALIDAR | Verify official release metadata and integration viability. |
| Iris | 🟣 REVALIDAR | Pin exact stable release, tag or commit. |
| Sodium | 🟣 REVALIDAR | Pin the version required by the selected Iris release. |
| Fabric Loader/API | 🟣 REVALIDAR | Pin compatible versions and hashes. |
| Java | 🟣 REVALIDAR | Confirm the official runtime requirement. |
| OpenGL/GLSL | 🟡 EN PROGRESO | SAFE stage and buffer lifecycle baselines are specified; runtime contexts remain unverified. |
| Drivers/hardware | ⚪ PENDIENTE | Establish representative Mesa and vendor evidence. |

## 1. Governance, coordination and recovery

- [x] 🟢 COMPLETADO — `GOV-001` Body-only lease coordinator. Evidence: issue #7 and `.github/workflows/automation-state.yml`.
- [ ] 🟣 REVALIDAR — `GOV-002` Coordinator regression suite for concurrency, stale recovery, ownership loss and malformed commands.
- [x] 🟢 COMPLETADO — `GOV-003` Remote checkpoint discipline.
- [ ] ⚪ PENDIENTE — `GOV-004` Branch and PR recovery audit.

## 2. Bootstrap, structure, packaging and versions

- [x] 🟢 COMPLETADO — `BOOT-001` Repository foundation and Validation workflow.
- [ ] 🟣 REVALIDAR — `BOOT-002` Exact pack structure audit.
- [ ] ⚪ PENDIENTE — `BOOT-003` Machine-readable dependency/version lock.
- [ ] ⚪ PENDIENTE — `BOOT-004` Reproducible ZIP and checksum.
- [ ] ⚪ PENDIENTE — `BOOT-005` Release metadata, changelog, rollback and installation verification.

## 3. Iris audit and compatibility

- [x] 🟢 COMPLETADO — `IRIS-001` Program inventory. Evidence: matrix, `tools/shader_inventory.py`, `tests/test_shader_inventory.py`, PR #53 and Validation run `30410900109`.
- [x] 🟢 COMPLETADO — `IRIS-002` Stage inventory. Evidence: `spec/iris-stage-capabilities.json`, `tests/test_iris_stage_capabilities.py`, [`IRIS-CAPABILITY-MATRIX.md`](IRIS-CAPABILITY-MATRIX.md) and PR #55. Acceptance covers vertex, fragment, geometry, compute and tessellation scope; feature flags; OpenGL 4.3 and macOS limits; 27-file compute bound; paired triangle tessellation; and deterministic SAFE fallbacks.
- [ ] 🟡 EN PROGRESO — `IRIS-003` Buffer and attachment lifecycle. Branch `docs/iris-buffer-lifecycle-contract` defines and tests colortex, depth, shadow, history, formats, clear, mipmaps, viewport, scaling and ping-pong; merge and runtime framebuffer acceptance remain.
- [ ] ⚪ PENDIENTE — `IRIS-004` Constants and directives including `DRAWBUFFERS`, `RENDERTARGETS`, formats, clears and blend.
- [ ] ⚪ PENDIENTE — `IRIS-005` Uniforms, attributes, matrices, camera/world/time/weather/entity data and reserved names.
- [ ] ⚪ PENDIENTE — `IRIS-006` Complete `shaders.properties` directive matrix, feature flags, resources, SSBO and dispatch.
- [ ] ⚪ PENDIENTE — `IRIS-007` Defines, sliders, profiles, screens, columns and `.lang` localization.
- [ ] ⚪ PENDIENTE — `IRIS-008` Block/item/entity/block-entity/biome mappings and dimensions.
- [ ] ⚪ PENDIENTE — `IRIS-009` Unsupported, deprecated and Iris-exclusive features with decisions and fallbacks.
- [ ] ⚪ PENDIENTE — `IRIS-010` Iris Patcher, transformation rules and reproducible diagnostics.

## 4. Pipeline, programs and resources

- [x] 🟢 COMPLETADO — `PIPE-001` Minimal geometry foundations merged through PRs #41–#50; runtime acceptance remains separate.
- [x] 🟢 COMPLETADO — `PIPE-002` Machine-readable shader program inventory and pair validation.
- [ ] ⚪ PENDIENTE — `PIPE-003` Remaining required gbuffers programs.
- [ ] ⚪ PENDIENTE — `PIPE-004` Dimension-specific selection and deterministic fallback.
- [ ] ⚪ PENDIENTE — `PIPE-005` HDR G-buffer schema.
- [ ] ⚪ PENDIENTE — `PIPE-006` `shaders.properties`, profiles, screens and localization.
- [ ] ⚪ PENDIENTE — `PIPE-007` Bounded shadowcomp/prepare/deferred/composite/final foundation.

## 5. Materials, lighting, shadows and occlusion

- [ ] ⚪ PENDIENTE — `MAT-001` Albedo and non-PBR fallback.
- [ ] ⚪ PENDIENTE — `MAT-002` Normal/specular resource-pack support.
- [ ] ⚪ PENDIENTE — `MAT-003` Roughness, metallic, emission, porosity, subsurface and AO.
- [ ] ⚪ PENDIENTE — `MAT-004` Bounded POM.
- [ ] ⚪ PENDIENTE — `LIGHT-001` Solar/lunar direct lighting.
- [ ] ⚪ PENDIENTE — `LIGHT-002` Block light, held light and colored emission.
- [ ] ⚪ PENDIENTE — `SHADOW-001` Directional shadow maps and stabilization.
- [ ] ⚪ PENDIENTE — `SHADOW-002` Entity, translucent and contact shadow paths.
- [ ] ⚪ PENDIENTE — `AO-001` Bounded ambient occlusion.

## 6. World, atmosphere and translucency

- [ ] ⚪ PENDIENTE — `ATM-001` Sky, sun, moon, stars and dimension fallbacks.
- [ ] ⚪ PENDIENTE — `ATM-002` Fog, aerial perspective and bounded volumetrics.
- [ ] ⚪ PENDIENTE — `CLOUD-001` Scalable clouds.
- [ ] 🟡 EN PROGRESO — `WEATHER-001` Rain/snow geometry foundation; atmospheric integration pending.
- [ ] ⚪ PENDIENTE — `WATER-001` Fresnel, reflection, refraction, absorption and waves.
- [ ] ⚪ PENDIENTE — `WATER-002` Underwater camera, caustics and history reset.
- [ ] ⚪ PENDIENTE — `TRANS-001` Glass, ice and translucency ordering.
- [ ] 🟡 EN PROGRESO — `PART-001` Particle foundation; material and weather integration pending.

## 7. Reflections, GI, temporal and post-processing

- [ ] ⚪ PENDIENTE — `SSR-001` Bounded SSR.
- [ ] ⚪ PENDIENTE — `GI-001` Bounded SSGI.
- [ ] ⚪ PENDIENTE — `GI-002` Optional capability-gated voxel lighting.
- [ ] ⚪ PENDIENTE — `TEMP-001` Motion vectors, history validity and reset.
- [ ] ⚪ PENDIENTE — `POST-001` HDR exposure and tonemapping.
- [ ] ⚪ PENDIENTE — `POST-002` Bloom, TAA, FXAA fallback, sharpen and dithering.
- [ ] ⚪ PENDIENTE — `POST-003` Optional DOF and motion blur.
- [ ] ⚪ PENDIENTE — `DEBUG-001` Buffer, NaN/Inf and pass-cost debug views.

## 8. Render coverage and dimensions

- [ ] 🟡 EN PROGRESO — `TERRAIN-001` Solid, cutout and translucent foundations; materials and shadow integration remain.
- [ ] 🟡 EN PROGRESO — `HAND-001` Underwater-hand foundation; base hand and held-item integration remain.
- [ ] ⚪ PENDIENTE — `ENTITY-001` Entity paths.
- [ ] ⚪ PENDIENTE — `BLOCKENTITY-001` Block-entity paths.
- [ ] 🟡 EN PROGRESO — `SPECIAL-001` Beacon, damaged-block and spider-eyes foundations; portals and glint remain.
- [ ] ⚪ PENDIENTE — `DIM-001` Overworld acceptance.
- [ ] ⚪ PENDIENTE — `DIM-002` Nether acceptance.
- [ ] ⚪ PENDIENTE — `DIM-003` End acceptance.

## 9. Profiles, performance and safety

- [ ] ⚪ PENDIENTE — `PROFILE-001` SAFE without mandatory compute, SSBO, tessellation or advanced images.
- [ ] ⚪ PENDIENTE — `PROFILE-002` BALANCED budgets and defaults.
- [ ] ⚪ PENDIENTE — `PROFILE-003` HIGH capability gates and budgets.
- [ ] ⚪ PENDIENTE — `PROFILE-004` ULTRA hard limits and HIGH fallback.
- [ ] ⚪ PENDIENTE — `PERF-001` Per-pass timing, memory, samples and permutation budgets.
- [ ] ⚪ PENDIENTE — `SAFE-001` Static checks for loops, division, normalization, indices and initialization.
- [ ] ⚪ PENDIENTE — `SAFE-002` Isolated processes, watchdogs and no-driver-hang policy.

## 10. Validation, integration and release

- [ ] 🟡 EN PROGRESO — `QA-001` Python tests and Validation workflow; compile/link coverage remains.
- [ ] ⚪ PENDIENTE — `QA-002` Unified shadercheck CLI.
- [ ] ⚪ PENDIENTE — `QA-003` Headless OpenGL harness.
- [ ] ⚪ PENDIENTE — `QA-004` Deterministic visual scenes and invariants.
- [ ] ⚪ PENDIENTE — `QA-005` NaN/Inf, context-loss, timeout and determinism tests.
- [ ] ⚪ PENDIENTE — `QA-006` Repeatable profile benchmarks.
- [ ] ⚪ PENDIENTE — `INT-001` Locked client integration harness.
- [ ] ⚪ PENDIENTE — `INT-002` Load/reload/resize/dimension/profile/log acceptance.
- [ ] ⚪ PENDIENTE — `INT-003` Sodium compatibility matrix.
- [ ] ⚪ PENDIENTE — `INT-004` Distant Horizons evaluation after core acceptance.
- [ ] 🟣 REVALIDAR — `CI-001` Workflow coverage, permissions, pinned actions and timeouts.
- [ ] ⚪ PENDIENTE — `CI-002` Upstream drift workflow.
- [ ] ⚪ PENDIENTE — `CI-003` Benchmark workflow and artifacts.
- [ ] ⚪ PENDIENTE — `REL-001` Release workflow, checksums and rollback.

## 11. Documentation and completeness

- [ ] ⚪ PENDIENTE — `DOC-001` Installation, profiles, compatibility claims and limitations.
- [ ] ⚪ PENDIENTE — `DOC-002` Architecture, buffer schema, program order and fallbacks.
- [ ] ⚪ PENDIENTE — `DOC-003` Troubleshooting, debug mode and issue evidence template.
- [ ] ⚪ PENDIENTE — `DOC-004` Measured performance and hardware guidance.
- [ ] ⚪ PENDIENTE — `DONE-001` Release-candidate audit.

## Ordering, risks and fallbacks

1. Complete the Iris inventory and version lock before advanced programs.
2. Define buffer schema and SAFE/BALANCED profiles before material and lighting expansion.
3. Require static compile/link validation before visual acceptance.
4. Require headless OpenGL and client integration before runtime compatibility claims.
5. Keep compute, SSBO, images and tessellation optional and capability-gated.
6. Preserve remote checkpoints when CI or time prevents completion.
7. Degrade unsupported hardware deterministically to a lower profile or SAFE.

## Audit history

- `2026-07-28` — Revision 1 created from merged governance, CI and geometry evidence.
- `2026-07-28` — Revision 2 linked the canonical Iris matrix.
- `2026-07-29` — Revision 3 accepted the machine-readable shader inventory.
- `2026-07-29` — Revision 4 accepted the stage capability contract, tests and canonical matrix update from PR #55.
- `2026-07-29` — Revision 5 began the buffer lifecycle contract with primary-source evidence and static regression coverage.

## Next prioritized unit

Complete `IRIS-003 — Buffer and attachment lifecycle contract`, merge the specification and tests with green Validation, then reconcile its evidence on `main` before selecting `IRIS-004`.
