# GLCLI-002 EGL probe evidence

## Scope

This record reconciles the first merged runtime portion of roadmap unit `GLCLI-002`.

## Remote evidence

- Pull request: `#71` — Add real EGL context probe.
- Feature head: `53aa34ec686a79bbc9991ceff9816735d8424b2e`.
- Merge on `main`: `d466d6bca8d4e6ad2bfc40d94bc0338c54bf0895`.
- Validation: run `30480734608`, run number `178`, conclusion `success` on the exact feature head.
- Implementation commits: `be95b1868dd393b7b256a07c55f402842bcf9b0e` and `53aa34ec686a79bbc9991ceff9816735d8424b2e`.

## Implemented behavior

- Creates a real OpenGL context through EGL surfaceless when available, with an EGL default-display pbuffer fallback.
- Reports EGL, OpenGL and GLSL versions, requested profile, vendor, renderer, selected limits, extensions and derived capability flags.
- Returns factual `UNSUPPORTED` when the requested backend, EGL, OpenGL or context is unavailable.
- Preserves the stable exit-code meanings and keeps `compile`, `render` and `suite` explicitly unsupported.

## Evidence classification

Current evidence remains `STATIC` in the canonical Focal vocabulary because no shader stage was compiled or linked. The real context metadata is factual implementation evidence but does not satisfy `GL_COMPILE_LINK`.

## Remaining GLCLI-002 acceptance

- Controlled hidden GLFW fallback.
- WGL and CGL/NSOpenGL routes where supported.
- Robust core-profile extension enumeration.
- Explicit Mesa software probe in CI.
- Roadmap and capability-matrix synchronization.

## Limits

This evidence does not prove shader compile/link, framebuffer render/readback, Iris-patched source acceptance, Minecraft/Iris integration or vendor-independent compatibility.
