# GLCLI-008 physical GPU evidence procedure

This procedure records evidence from one declared physical GPU and driver. It does not establish universal compatibility or performance.

## Preconditions

- Run from a clean checkout of an exact Focal commit.
- Use a physical GPU rather than llvmpipe or another software renderer.
- Record the operating system, GPU model, driver version, OpenGL version, GLSL version and backend.
- Keep `LIBGL_ALWAYS_SOFTWARE` unset and do not force a Mesa software driver.

## Commands

```text
python focal-gl probe --backend auto --gl-version 3.3 --gl-profile core --size 64x64 --json
python focal-gl compile --pack . --program gbuffers_basic --backend auto --gl-version 3.3 --gl-profile core --json
python focal-gl render --pack . --fixture gbuffers-basic --backend auto --gl-version 3.3 --gl-profile core --size 64x64 --frames 2 --artifacts artifacts --json
```

The exact program and fixture names may be adjusted to the repository's accepted representative fixtures. Record every command verbatim.

## Required record

Create one JSON record containing:

- `schemaVersion`: `1`;
- exact Focal commit SHA;
- UTC execution timestamp;
- operating system and architecture;
- GPU vendor and model;
- driver package and version;
- OpenGL vendor, renderer, version and GLSL version reported by `focal-gl probe`;
- backend and requested context profile;
- command lines and exit codes;
- SHA-256 and byte length for each JSON, log and image artifact;
- explicit `PASS`, `FAIL`, `UNSUPPORTED` or `SKIP` outcome per command;
- factual notes for warnings, fallback or capability limits.

## Acceptance boundary

A record is usable evidence only when the probe identifies a physical renderer, the exact command outputs are retained and every artifact hash can be reproduced. One passing record proves only that exact hardware, driver, operating system, backend, commit and fixture combination.

The record does not prove:

- performance on another GPU or driver;
- native WGL or CGL/NSOpenGL unless that backend was used;
- Iris-patched shader acceptance;
- Minecraft/Iris client integration;
- universal vendor compatibility.

Hardware records remain separate from the Mesa software artifact published by CI. They may be referenced by later evidence documents, but they must not replace the reproducible software baseline.
