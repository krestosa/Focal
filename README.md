# Focal

Focal is an shader pack project targeting Minecraft Java 26.2 through Iris and Sodium.

## Project status

The repository is in the bootstrap phase. Runtime coordination is maintained outside Git history through issue #7 and the `Automation State Coordinator` workflow; functional development occurs only on reviewed branches and pull requests.

No in-game compatibility, performance, or visual-quality claim is made until the corresponding automated and client-integration evidence exists.

## Design constraints

- Physically plausible HDR lighting and color management.
- Deterministic SAFE, BALANCED, HIGH, and ULTRA quality profiles.
- Bounded GPU memory, samples, loops, and ray-march steps.
- Explicit capability detection and deterministic fallbacks.
- Reproducible validation, packaging, and provenance auditing.

## Development policy

Every functional change is developed on a dedicated branch, committed one tracked path at a time, validated, and submitted through a pull request. Direct pushes to `main` are not part of the autonomous workflow.
