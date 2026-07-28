# Iris capability matrix

Canonical capability evidence for Focal. This document is linked to [`ROADMAP.md`](ROADMAP.md) and records only capabilities supported by current primary Iris documentation or explicit pending verification.

## Audit metadata

- Reviewed UTC: `2026-07-28`
- Focal baseline: `e7a4eb6aaa125710dce5e6243bbb955cc1235b67`
- Evidence scope: current Iris shader-pack documentation and official Iris repositories
- Version rule: exact Minecraft, Iris, Sodium, Fabric Loader and Java versions remain `PENDIENTE DE VERIFICAR` until a mutually compatible release set is pinned and exercised

## Status vocabulary

- `SOPORTADA`: confirmed by a current primary source.
- `PARCIAL`: supported with a documented restriction or incomplete Focal evidence.
- `EXPERIMENTAL`: available but capability-gated or insufficiently accepted for a default path.
- `NO SOPORTADA`: explicitly rejected or unrecognized by Iris.
- `PENDIENTE DE VERIFICAR`: current primary evidence is insufficient.

## Primary sources

Reviewed on `2026-07-28` UTC:

- https://shaders.properties/current/reference/programs/overview/
- https://shaders.properties/current/reference/programs/gbuffers/
- https://shaders.properties/current/reference/programs/shadow/
- https://shaders.properties/current/reference/programs/setup/
- https://shaders.properties/current/reference/programs/begin/
- https://shaders.properties/current/reference/programs/prepare/
- https://shaders.properties/current/reference/programs/deferred/
- https://shaders.properties/current/reference/programs/composite/
- https://shaders.properties/current/reference/programs/final/
- https://shaders.properties/current/reference/shadersproperties/overview/
- https://shaders.properties/current/reference/shadersproperties/flags/
- https://github.com/IrisShaders/Iris
- https://github.com/IrisShaders/docs
- https://github.com/IrisShaders/ShaderDoc

## Version and runtime matrix

| ID | Capability | State | Confirmed versions | Factual evidence | Focal impact and fallback | Test strategy | Roadmap |
|---|---|---|---|---|---|---|---|
| `IRIS-COMPAT-001` | Exact Minecraft/Iris/Sodium/Fabric/Java set | PENDIENTE DE VERIFICAR | None pinned | The project target is declared as Minecraft Java 26.2, but no mutually compatible release set is locked in the repository. | Do not claim runtime compatibility; keep static SAFE paths independent of advanced features. | Pin releases, hashes and Java requirement; build a client integration fixture. | `BOOT-003`, `INT-001`, `INT-003` |
| `IRIS-GL-001` | Compute shaders | PARCIAL | Current docs; exact Iris release pending | Compute is accepted in setup and composite-style passes, requires OpenGL 4.3 and is unavailable on macOS OpenGL. | Optional only; SAFE must not require compute. | Static stage validation plus capability-gated runtime test. | `IRIS-002`, `PROFILE-001`, `GI-002` |
| `IRIS-GL-002` | Tessellation shaders | EXPERIMENTAL | Current docs; exact Iris release pending | Tessellation is accepted only in gbuffers-style passes, triangles only, with the `TESSELLATION_SHADERS` feature flag. | Optional HIGH/ULTRA path; vertex/fragment fallback required. | Compile a minimal `.tcs`/`.tes` fixture and verify fallback without the flag. | `IRIS-002`, `PROFILE-003`, `PROFILE-004` |
| `IRIS-GL-003` | SSBO, custom images and indirect dispatch | EXPERIMENTAL | Exact release and hardware pending | Iris exposes feature flags and `shaders.properties` directives for SSBOs, custom images and indirect compute dispatch. | Never required by SAFE; define memory and dispatch bounds before adoption. | Capability fixtures, binding validation and hard resource budgets. | `IRIS-006`, `GI-002`, `SAFE-002` |

## Program execution order

The documented high-level order is:

1. `setup` — compute-only, during shader-pack load and resize.
2. `begin` — composite-style before shadow.
3. `shadow` — gbuffers-style shadow geometry.
4. `shadowcomp` — composite-style after shadow.
5. `prepare` — composite-style before world gbuffers.
6. opaque `gbuffers_*`.
7. `deferred` — composite-style between most opaque and translucent geometry.
8. translucent `gbuffers_*`.
9. `composite` — composite-style after world geometry.
10. `final` — composite-style output to the backbuffer.

The order of individual gbuffers programs is not globally fixed. Geometry ordering depends on program category and directives such as particle ordering and separated translucent entity draws.

## Program family matrix

| ID | Program family | State | Required stages | Optional stages | Suffixes | Direct geometry attributes | Outputs | Fallback / restriction | Existing Focal evidence | Required test | Roadmap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `IRIS-PROG-SETUP` | `setup`, `setup1`–`setup99` | SOPORTADA | compute | none | none, 1–99 | no | images/SSBO side effects; no direct color attachment writes | OpenGL 4.3; macOS-safe non-compute fallback required | none accepted | load/resize execution and bounded dispatch fixture | `IRIS-001`, `IRIS-002` |
| `IRIS-PROG-BEGIN` | `begin`, `begin1`–`begin99` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | none, 1–99 | no | `colortex` | Composite-style fullscreen pass before shadow | none accepted | stage discovery, ordering and render-target test | `IRIS-001` |
| `IRIS-PROG-SHADOW` | `shadow` | SOPORTADA | vertex + fragment | geometry, tessellation | no suffix | yes | `shadowcolor`, `shadowtex` | Base shadow program; default shader if absent | no accepted shadow implementation | compile/link and deterministic shadow fixture | `IRIS-001`, `SHADOW-001` |
| `IRIS-PROG-SHADOW-SPLIT` | `shadow_solid`, `shadow_cutout`, `shadow_water`, `shadow_entities`, `shadow_block` | PARCIAL | vertex + fragment | geometry, tessellation | no suffix | yes | `shadowcolor`, `shadowtex` | Documented for Iris 1.8+; each falls back to `shadow` | none accepted | pin Iris release, compile each present pair and verify fallback | `IRIS-001`, `SHADOW-001`, `SHADOW-002` |
| `IRIS-PROG-SHADOWCOMP` | `shadowcomp`, `shadowcomp1`–`shadowcomp99` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | none, 1–99 | no | `colortex` | Composite-style after shadow | none accepted | ordering and attachment test | `IRIS-001` |
| `IRIS-PROG-PREPARE` | `prepare`, `prepare1`–`prepare99` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | none, 1–99 | no | `colortex` | Composite-style before gbuffers | none accepted | ordering and attachment test | `IRIS-001` |
| `IRIS-PROG-GBUFFERS` | `gbuffers_*` | SOPORTADA | vertex + fragment | geometry, tessellation | no numeric suffix | yes | `colortex`, depth | Geometry-specific fallbacks apply; compute is not supported | multiple text-level foundation programs in PRs #41–#50 | enumerate names, compile/link every pair and validate fallback graph | `IRIS-001`, `PIPE-002`, `PIPE-003` |
| `IRIS-PROG-DEFERRED` | `deferred`, `deferred1`–`deferred99` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | none, 1–99 | no | `colortex` | Runs between most opaque and translucent gbuffers | none accepted | ordering, flip and attachment tests | `IRIS-001`, `PIPE-007` |
| `IRIS-PROG-COMPOSITE` | `composite`, `composite1`–`composite99` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | none, 1–99 | no | `colortex` | Runs after all gbuffers programs | none accepted | ordering, flip and attachment tests | `IRIS-001`, `PIPE-007` |
| `IRIS-PROG-FINAL` | `final` | SOPORTADA | vertex + fragment unless compute-only form | geometry, compute | no suffix | no | backbuffer | Exactly one final program; output resolution is window resolution | none accepted | final-output compile/link and resize test | `IRIS-001`, `PIPE-007` |

## Gbuffers program inventory

The following entries are recognized by current Iris documentation. A Focal file being present is foundation evidence only; it is not runtime acceptance.

| Program | Geometry / role | Documented fallback | Focal state |
|---|---|---|---|
| `gbuffers_basic` | leash and debug chunk-border overlay | none | present generic foundation requires compile audit |
| `gbuffers_line` | block outline and fishing line | `gbuffers_basic` | pending inventory |
| `gbuffers_textured` | world border and unlit particles | `gbuffers_basic` | pending inventory |
| `gbuffers_textured_lit` | lit particles | `gbuffers_textured` | pending inventory |
| `gbuffers_particles` | particles | `gbuffers_textured_lit` | foundation merged in PR #43 |
| `gbuffers_particles_translucent` | translucent-capable particles with mixed ordering | `gbuffers_particles` | pending |
| `gbuffers_block` | block entities | documented fallback chain requires source-level expansion | pending |
| `gbuffers_block_translucent` | translucent block entities | `gbuffers_block` | pending |
| `gbuffers_entities` | entities | documented fallback chain requires source-level expansion | pending |
| `gbuffers_entities_translucent` | translucent entities | `gbuffers_entities` | pending |
| `gbuffers_terrain` | general terrain fallback | base terrain path | present generic foundation requires compile audit |
| `gbuffers_terrain_solid` | solid terrain | `gbuffers_terrain` | foundation merged in PR #48 |
| `gbuffers_terrain_cutout` | cutout terrain | `gbuffers_terrain` | foundation merged in PR #49 |
| `gbuffers_terrain_translucent` | translucent terrain | project naming requires source verification | foundation merged in PR #50; authoritative recognition remains to verify |
| `gbuffers_water` | translucent terrain rendered after deferred by default | documented gbuffers fallback graph | pending |
| `gbuffers_weather` | rain and snow geometry | documented gbuffers fallback graph | foundation merged in PR #42 |
| `gbuffers_hand` | solid/cutout held geometry | documented gbuffers fallback graph | pending |
| `gbuffers_hand_water` | translucent held geometry after deferred | documented gbuffers fallback graph | foundation merged in PR #41 |
| `gbuffers_beaconbeam` | beacon beam | documented gbuffers fallback graph | foundation merged in PR #44 |
| `gbuffers_damagedblock` | block-damage overlay | documented gbuffers fallback graph | foundation merged in PR #46 |
| `gbuffers_spidereyes` | emissive spider/enderman eyes | documented gbuffers fallback graph | foundation merged in PR #47 |
| `gbuffers_lightning` | lightning and dragon death-beam color | `gbuffers_entities` | pending |
| `gbuffers_entities_glowing` | OptiFine spectral-effect program | NO SOPORTADA by Iris | do not create; use supported render-state data/fallback |

## Stage and compute constraints

| Capability | State | Constraint | Focal rule |
|---|---|---|---|
| Vertex `.vsh` | SOPORTADA | required for gbuffers-style; normally paired with fragment in composite-style | baseline stage |
| Fragment `.fsh` | SOPORTADA | writes configured color outputs | baseline stage |
| Geometry `.gsh` | SOPORTADA | optional in gbuffers and composite-style programs | optional, bounded amplification only |
| Compute `.csh` | PARCIAL | setup/composite-style only; up to suffixless plus `_a`–`_z`; executes before graphics stages; OpenGL 4.3 | optional capability-gated path |
| Tessellation `.tcs`/`.tes` | EXPERIMENTAL | gbuffers-style only, triangles only, feature flag required | HIGH/ULTRA optional with non-tessellated fallback |

## `shaders.properties` capability summary

Current documentation confirms user settings (`screen`, `sliders`, `profile`, `.lang`) and internal directives for feature flags, program ordering, rendering, custom uniforms, custom textures, images and SSBOs. These capabilities remain distributed across `IRIS-006` and `IRIS-007`; this matrix does not mark them accepted for Focal until exact directives, bounds and tests are recorded.

## Acceptance and next work

`IRIS-001` is documentarily complete when this matrix is linked from the roadmap, the program-family order and stage/suffix rules are checked in CI, and every current Focal shader filename is mapped to a recognized Iris program or explicitly marked for correction. Runtime compatibility remains unclaimed until `INT-001` and `INT-002` are complete.

Next unit: `PIPE-002` should generate a machine-readable inventory of current shader programs and compare it with the program names and fallback constraints recorded here.