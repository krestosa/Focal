# GLCLI-008 reconciliation evidence

## Accepted implementation

- Functional pull request: [#103](https://github.com/krestosa/Focal/pull/103)
- Exact validated head: `611c77d9f88ee9306896b2343e77db1f09cb8a18`
- Validation run: `30581017694`
- Merge on `main`: `8f0bc9fa23bc3f20a03de08f832e2b84cc89e2f4`

## Accepted boundary

`GLCLI-008` is complete for the reproducible evidence packaging contract:

- Validation publishes the exact Mesa probe, compile/link and render/readback outputs;
- the deterministic manifest records environment identity, SHA-256 and byte length for each required result;
- generated image artifacts are retained with the JSON evidence;
- the physical-GPU procedure records one exact GPU, driver, operating system, backend and commit separately.

The existing `GL_RENDER_READBACK` claim remains limited to the accepted standalone Mesa fixtures. The manifest and hardware procedure are `STATIC` contracts. This evidence does not establish native WGL or CGL/NSOpenGL support, representative physical-GPU acceptance, Iris-patched provenance, Minecraft/Iris client integration or universal compatibility.

## Documentation reconciliation

- `docs/ROADMAP.md` advances to revision 20, marks `GLCLI-008` complete and selects native `GLCLI-002` platform and physical-GPU evidence as the next harness work.
- `docs/IRIS-CAPABILITY-MATRIX.md` records PR #103, its exact-head run, merge, retained artifact contract and the unchanged evidence limits.
