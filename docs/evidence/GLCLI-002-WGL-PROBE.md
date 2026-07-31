# GLCLI-002 native WGL probe evidence

## Accepted scope

PR #105 adds a native hidden Windows OpenGL context route for `focal-gl probe --backend wgl`.

The implementation:

- creates a hidden Win32 window and device context;
- selects and sets an OpenGL-capable pixel format;
- creates a legacy WGL bootstrap context;
- upgrades through `WGL_ARB_create_context` for requested modern/core contexts;
- queries the active context through the existing GLCLI capability contract;
- destroys the rendering context, device context, window and registered class on completion or failure;
- routes only an explicit WGL probe through the isolated worker;
- reports factual `UNSUPPORTED` outside Windows or when native context creation is unavailable.

## Validation

- Pull request: #105
- Validated head: `1259023ef67597b25894544934508b5ef27ba96c`
- Validation run: `30601640571`
- Repository policy and full `unittest` suite: passed
- Mesa EGL software probe: passed
- Mesa hidden GLFW probe, compile/link and render/readback: passed
- Merge commit: `1234c4c55f8990a92121065e3b85596374b162c6`

The first PR run (`30601584785`) exposed an undeclared `pytest` dependency in the new test file. The test was converted to the repository's existing `unittest` contract, after which all jobs passed on the exact replacement head.

## Evidence level and limits

The accepted WGL implementation evidence is `STATIC` plus cross-platform routing and failure-handling tests. The Linux CI run does not execute a native Windows driver context and therefore does not establish:

- a successful WGL context on a physical Windows GPU;
- AMD, NVIDIA or Intel driver compatibility;
- performance characteristics;
- CGL/NSOpenGL support;
- Iris-patched shader acceptance;
- Minecraft/Iris client acceptance;
- universal hardware compatibility.

A native Windows execution recorded through the GLCLI-008 hardware procedure remains required before promoting WGL evidence beyond this bounded implementation contract.
