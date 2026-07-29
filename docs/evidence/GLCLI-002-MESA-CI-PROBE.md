# GLCLI-002 Mesa CI probe evidence

## Scope

This record captures the explicit Mesa software OpenGL context probe merged through PR #74. It is evidence for the Linux software route of `GLCLI-002`; it is not evidence for shader compile/link, rendering, readback, patched-source execution or client integration.

## Remote evidence

- Pull request: `#74` — `Add explicit Mesa EGL probe gate`
- Feature head: `bbe2ed5883a298f16853eb2477dbde0e82909296`
- Merge on `main`: `70d0e31f76cd4ede71876b44e5f1966788d81d0a`
- Validation workflow run: `30490039060`
- Validation run number: `186`
- Result: `success`
- Runner image: Ubuntu 24.04

## Exercised route

The validation workflow:

1. installs `libegl1`, `libgl1`, `libgl1-mesa-dri` and `mesa-utils`;
2. sets `EGL_PLATFORM=surfaceless`;
3. sets `LIBGL_ALWAYS_SOFTWARE=true`;
4. sets `MESA_LOADER_DRIVER_OVERRIDE=llvmpipe`;
5. executes `python tools/focal_gl.py probe --backend egl --gl-version 3.3 --gl-profile core --size 64x64 --json`;
6. requires a successful JSON result with a real EGL backend, vendor, renderer, OpenGL version, GLSL version and reported limits.

## Recovered failure

Validation run `30489947842` initially failed with exit code `3` because the base runner did not expose the required Mesa/EGL runtime. The workflow was repaired in place by installing the runtime packages explicitly. The exact repaired head then passed run `30490039060`.

## Evidence classification

Canonical evidence level remains `STATIC`.

The run proves that the current probe implementation can create and interrogate a real Mesa llvmpipe EGL context in the declared CI environment. It does not compile or link a shader stage, render a framebuffer, perform readback, consume Iris-patched source or run inside Minecraft/Iris.

## Remaining GLCLI-002 acceptance

- controlled hidden GLFW fallback;
- WGL hidden-context route where supported;
- CGL/NSOpenGL or permitted macOS equivalent where supported;
- robust core-profile extension enumeration;
- representative hardware/driver evidence kept distinct from llvmpipe;
- final synchronization of `docs/ROADMAP.md` and `docs/IRIS-CAPABILITY-MATRIX.md`.
