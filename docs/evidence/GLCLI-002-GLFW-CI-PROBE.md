# GLCLI-002 — Mesa GLFW hidden-window probe evidence

## Scope

This document records the real-context evidence introduced by PR #79 for the controlled hidden GLFW backend of `focal-gl probe`.

## Remote evidence

- Pull request: #79, `Add controlled hidden GLFW context adapter`
- Merged into `main`: `6eee1e86eeb2f77f81d5e06a7fd3e148579b0c30`
- Validated head: `12dc8e24f9339193743f2372b2b8e785ebc60aa7`
- Validation run: `30500297439`
- Job: `Mesa GLFW hidden-window probe`
- Result: success

## Executed route

The workflow installed Mesa llvmpipe, `libglfw3` and Xvfb, then executed:

```text
python focal-gl probe --backend glfw --gl-version 3.3 --gl-profile core --size 64x64 --json
```

The job required:

- `outcome == PASS`;
- `exitCode == 0`;
- backend `glfw-hidden`;
- non-empty OpenGL vendor, renderer, version and GLSL version;
- a populated limits object.

## Evidence classification

The run proves that the hidden GLFW route can create and query a real OpenGL context on the declared Mesa llvmpipe and virtual-display stack. It does not prove:

- shader stage compilation or program link;
- framebuffer rendering or color/depth readback;
- physical AMD, NVIDIA or Intel driver behavior;
- WGL or CGL/NSOpenGL support;
- Iris-patched or Minecraft client integration.

The repository therefore retains `GLCLI-002` as `EN PROGRESO`. The next runtime acceptance layers remain `GLCLI-004` compile/link and `GLCLI-005` render/readback, while native Windows and macOS routes remain separate platform work.
