# Focal terminal OpenGL runtime harness

## Purpose

`focal-gl` is the canonical command-line program for validating Focal shaders in a real OpenGL context outside Minecraft. It is a required validation layer between static source checks and full Iris client integration.

The harness must not claim to reproduce all Minecraft or Iris behavior. Iris patches shader source before GPU compilation, and the client supplies geometry, states, resources and uniforms that a standalone fixture can only model explicitly.

Primary Iris references, reviewed `2026-07-29` UTC:

- https://shaders.properties/current/reference/programs/overview/
- https://shaders.properties/current/reference/programs/gbuffers/
- https://shaders.properties/current/reference/programs/final/
- https://shaders.properties/current/reference/buffers/overview/
- https://shaders.properties/current/reference/buffers/colortex/
- https://shaders.properties/current/reference/constants/rendertargets/
- https://shaders.properties/current/reference/uniforms/overview/
- https://shaders.properties/current/reference/attributes/overview/
- https://shaders.properties/current/reference/macros/supported_extensions/
- https://shaders.properties/current/reference/miscellaneous/patcher/
- https://shaders.properties/current/reference/miscellaneous/debugging_shaders/
- https://shaders.properties/current/reference/miscellaneous/macos/

## Stable command surface

```text
focal-gl probe
focal-gl compile
focal-gl render
focal-gl suite
```

Required common options:

- `--pack <path>`;
- `--program <name>`;
- `--fixture <name>`;
- `--profile SAFE|BALANCED|HIGH|ULTRA`;
- `--dimension <id>`;
- `--backend <auto|egl|glfw|wgl|cgl>`;
- `--gl-version <major.minor>`;
- `--gl-profile <core|compatibility>`;
- `--size <width>x<height>`;
- `--frames <count>`;
- `--timeout <seconds>`;
- `--artifacts <path>`;
- `--json`.

## Evidence levels

Every result must declare one level:

1. `STATIC`;
2. `GL_COMPILE_LINK`;
3. `GL_RENDER_READBACK`;
4. `IRIS_PATCHED`;
5. `IRIS_CLIENT`.

A higher level does not erase the need to record the lower-level facts.

## Context probe

`focal-gl probe` must create a real context and report:

- context backend;
- `GL_VENDOR`;
- `GL_RENDERER`;
- `GL_VERSION`;
- GLSL version;
- core or compatibility profile;
- relevant extensions;
- maximum color attachments and draw buffers;
- texture, image, UBO and SSBO limits;
- support for geometry, compute and tessellation stages;
- framebuffer and debug-output support;
- factual unsupported reasons.

Expected context routes:

- EGL surfaceless or pbuffer on Linux;
- hidden GLFW context as controlled fallback;
- hidden WGL context on Windows;
- CGL or NSOpenGL route on macOS;
- Mesa software renderer for reproducible CI;
- real GPU/driver for hardware evidence.

A parser, compiler mock or emulated response does not satisfy this requirement.

## Source modes

Every compile or render result must record `sourceMode`:

- `source`: original pack source;
- `preprocessed`: includes and harness defines resolved;
- `iris-patched`: output produced by Iris Patcher.

Standalone acceptance of `source` does not prove Iris acceptance. Iris Patcher evidence is tracked separately because the transformed code is the source actually sent toward GPU compilation by Iris.

## Compile and link

`focal-gl compile` must:

- discover the selected program and applicable stages;
- resolve includes and defines for the fixture;
- compile each stage in a real context;
- link the complete program;
- capture full compiler and linker logs;
- record stage, file and source mode;
- validate required stages;
- validate varyings and output bindings;
- distinguish unsupported capability from invalid shader source;
- emit machine-readable results.

## Render and readback

`focal-gl render` must:

- create deterministic geometry or a fullscreen triangle/quad;
- create VAO, vertex/index buffers and required attributes;
- create textures, samplers and buffer objects;
- create framebuffer attachments with declared formats and dimensions;
- initialize clears and fixture data;
- provide required uniforms and matrices;
- execute real draw or dispatch commands;
- apply barriers, mipmaps and ping-pong when the fixture requires them;
- check framebuffer completeness;
- collect OpenGL errors and debug messages;
- read color and depth output;
- count NaN and Inf values;
- compare ranges, tolerances or reference hashes;
- save images and raw diagnostics;
- repeat when determinism is required.

Minimum initial render path:

1. one gbuffers-style vertex/fragment program over deterministic geometry;
2. one composite-style program reading a produced attachment;
3. one final-equivalent pass;
4. color and depth readback;
5. finite-value and expected-range checks.

## Multipass suite

`focal-gl suite` must consume declarative fixtures describing:

- program order;
- stages;
- inputs and attributes;
- uniforms and matrices;
- textures and samplers;
- attachments and formats;
- clear behavior;
- viewport and scaling;
- buffer flips and ping-pong;
- mipmap timing;
- frame count;
- expected invariants;
- required evidence level;
- supported and fallback capability sets.

The suite result must include the shader-pack hash, harness version, platform, driver, timings, artifacts, outcome and exit code.

## Isolation and safety

OpenGL work must run in an isolated worker process with:

- watchdog;
- hard timeout;
- bounded framebuffer size;
- bounded frames, samples and dispatch dimensions;
- cleanup after failure;
- partial artifact retention;
- separate classification for context unavailable, compile/link failure, OpenGL execution failure, invariant mismatch and timeout/context loss.

## Exit codes

- `0`: all required checks passed;
- `2`: invalid usage or configuration;
- `3`: OpenGL context unavailable;
- `4`: shader compilation or link failure;
- `5`: OpenGL, framebuffer or execution failure;
- `6`: output invariant failure;
- `7`: timeout, worker termination or context loss;
- `8`: required capability unsupported and no accepted fallback.

Meanings are versioned and must not be reassigned silently.

## CI and hardware evidence

The reproducible CI baseline must use Mesa software OpenGL and run:

- context probe;
- SAFE compile/link fixtures;
- minimum render/readback path;
- deterministic repeat;
- timeout and failure-classification tests.

Mesa software proves only that the tested route works in that renderer. Separate evidence is required for AMD, NVIDIA and Intel drivers, and performance claims must name the exact backend, GPU, driver, operating system, resolution, profile and scene.

## Completion gates

`QA-003` cannot become complete until:

- `GLCLI-001` through `GLCLI-008` meet their roadmap acceptance criteria;
- the minimum gbuffers/composite/final path renders and reads back successfully;
- JSON and artifact formats are documented;
- isolation and timeout tests pass;
- Mesa CI is green;
- limitations relative to Iris and Minecraft are stated explicitly.
