# GLCLI-002 core-profile extension evidence

- Evidence level: `STATIC`
- Functional pull request: #77
- Validation run: `30493688616` (run 192, success)
- Functional merge: `d66834fc9cff7375da50930c3572eaaa55cdd008`
- Harness version: `0.3.0`

The merged probe enumerates OpenGL extensions through `GL_NUM_EXTENSIONS` and `glGetStringi` when indexed enumeration is available, with a controlled legacy `GL_EXTENSIONS` fallback for compatibility contexts. Regression coverage verifies indexed enumeration, sorting and deduplication, the legacy fallback, and factual failure when neither route is available.

This evidence does not establish shader compile/link, framebuffer render/readback, Iris-patched execution, client integration, hardware performance, or universal compatibility. Hidden GLFW, WGL and CGL/NSOpenGL context routes remain pending where supported.
