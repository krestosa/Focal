# GLCLI-005 Mesa framebuffer render/readback evidence

## Accepted boundary

This record accepts `GL_RENDER_READBACK` only for the exact standalone Mesa llvmpipe fixtures implemented by [PR #97](https://github.com/krestosa/Focal/pull/97).

- Validated head: [`53756e93b12ce3ce8b8b1f7d48f67f5ddeceb9b1`](https://github.com/krestosa/Focal/commit/53756e93b12ce3ce8b8b1f7d48f67f5ddeceb9b1)
- Validation: [run `30544545413`](https://github.com/krestosa/Focal/actions/runs/30544545413), conclusion `success`
- Merge on `main`: [`cc85e7c4f221ad7f4298f5a96ea34f3c227ac314`](https://github.com/krestosa/Focal/commit/cc85e7c4f221ad7f4298f5a96ea34f3c227ac314)
- Runtime: Ubuntu 24.04, Xvfb, hidden GLFW context, Mesa llvmpipe
- Context request: OpenGL 3.3 core
- Fixture size: `32x32`

## Implemented path

`tools/focal_gl_render.py` and `tools/focal_gl_dispatch.py` now provide the minimum real render path behind `focal-gl render`:

1. compile and link the selected vertex/fragment stages in a real hidden context;
2. create a framebuffer with an `RGBA32F` color texture and 24-bit depth renderbuffer;
3. require `GL_FRAMEBUFFER_COMPLETE`;
4. provide deterministic geometry or a fullscreen triangle;
5. provide a deterministic 2×2 texture and bind `sourceTexture` when declared;
6. clear color/depth, draw, finish and reject OpenGL errors;
7. read color and depth as floats;
8. reject NaN/Inf, values outside the normalized range and unchanged color/depth attachments;
9. emit stable SHA-256 statistics and optional PPM, PGM and JSON artifacts.

Readback is bounded to at most 1,048,576 pixels per invocation.

## Accepted fixtures

The CI acceptance script executes three representative programs:

| Fixture | Input | Sampler | Observable acceptance |
|---|---|---:|---|
| `gbuffers_fixture` | vertex buffer triangle | no | geometry draw changes both color and depth |
| `composite_fixture` | fullscreen triangle | yes | deterministic source texture is sampled and read back |
| `final_fixture` | fullscreen triangle | yes | final-equivalent color transform is rendered and read back |

For every fixture, the JSON result reports:

- outcome `PASS`;
- exit code `0`;
- evidence level `GL_RENDER_READBACK`;
- backend `glfw-hidden`;
- framebuffer status `GL_FRAMEBUFFER_COMPLETE`;
- finite color/depth statistics;
- non-zero changed-pixel counts for color and depth;
- generated color, depth and report artifacts.

## Validation history

The first exact-head run, [run `30544225156`](https://github.com/krestosa/Focal/actions/runs/30544225156), proved that the real Mesa render/readback job passed but exposed one stale CLI regression that still expected `render` to be unsupported. The test contract was corrected without changing the runtime scope. The replacement exact-head [run `30544545413`](https://github.com/krestosa/Focal/actions/runs/30544545413) passed all repository-policy, EGL probe, GLFW probe, compile/link and render/readback jobs.

## Explicit non-claims

This evidence does not establish:

- native WGL or CGL/NSOpenGL support;
- AMD, NVIDIA, Intel or Apple physical-GPU behavior or performance;
- full Iris attachment flipping, resizing, mipmaps, blending or multipass sequencing;
- provenance from an Iris Patcher debug export;
- live Minecraft uniforms, attributes or render states;
- `IRIS_PATCHED` or `IRIS_CLIENT` acceptance;
- repeated-run determinism, context-loss recovery or isolated-worker watchdog behavior.

Those remain assigned to `GLCLI-002`, `GLCLI-006`, `GLCLI-007`, `GLCLI-008`, `IRIS-010` and `INT-001/002`.
