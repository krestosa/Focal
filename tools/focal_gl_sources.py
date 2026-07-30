"""Deterministic shader-source preparation for ``focal-gl``.

This module implements the GLCLI-003 source boundary only. It discovers stages,
loads original or explicitly exported source, resolves includes for the
preprocessed mode, injects bounded harness defines, and reports stable hashes.
It does not create an OpenGL context or claim compile/link acceptance.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

STAGE_SUFFIXES = ("vsh", "fsh", "gsh", "tcs", "tes", "csh")
_DEFINE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_INCLUDE = re.compile(r'^\s*#\s*include\s*(["<])([^">]+)[">]\s*$', re.MULTILINE)


class SourceResolutionError(ValueError):
    """Raised when a source request is incomplete, unsafe or ambiguous."""


@dataclass(frozen=True)
class PreparedStage:
    stage: str
    path: str
    byteLength: int
    sha256: str
    source: str


@dataclass(frozen=True)
class PreparedProgram:
    sourceMode: str
    sourceRoot: str
    program: str
    includesResolved: bool
    defines: dict[str, str]
    stages: tuple[PreparedStage, ...]

    def metadata(self) -> dict[str, object]:
        payload = asdict(self)
        for stage in payload["stages"]:
            stage.pop("source", None)
        return payload


def parse_defines(values: Iterable[str]) -> dict[str, str]:
    defines: dict[str, str] = {}
    for item in values:
        name, separator, value = item.partition("=")
        if not _DEFINE_NAME.fullmatch(name):
            raise SourceResolutionError(f"invalid define name: {name!r}")
        normalized = value if separator else "1"
        if "\n" in normalized or "\r" in normalized:
            raise SourceResolutionError(f"define {name!r} contains a newline")
        if name in defines and defines[name] != normalized:
            raise SourceResolutionError(f"define {name!r} has conflicting values")
        defines[name] = normalized
    return dict(sorted(defines.items()))


def resolve_source_root(pack: Path, source_mode: str, explicit_root: Path | None) -> Path:
    pack = pack.resolve()
    if explicit_root is not None:
        root = explicit_root.resolve()
    elif source_mode in ("source", "preprocessed"):
        root = (pack / "shaders") if (pack / "shaders").is_dir() else pack
    else:
        raise SourceResolutionError("iris-patched mode requires --source-root pointing to exported patched shaders")
    if not root.is_dir():
        raise SourceResolutionError(f"source root is not a directory: {root}")
    return root


def _contained(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SourceResolutionError(f"include escapes source root: {candidate}") from exc
    return resolved


def _expand_includes(path: Path, root: Path, stack: tuple[Path, ...]) -> str:
    path = _contained(root, path)
    if path in stack:
        chain = " -> ".join(item.relative_to(root).as_posix() for item in (*stack, path))
        raise SourceResolutionError(f"include cycle: {chain}")
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SourceResolutionError(f"missing shader source: {path.relative_to(root).as_posix()}") from exc
    except UnicodeDecodeError as exc:
        raise SourceResolutionError(f"shader source is not UTF-8: {path.relative_to(root).as_posix()}") from exc

    def replace(match: re.Match[str]) -> str:
        delimiter, requested = match.groups()
        requested_path = Path(requested)
        candidate = (path.parent / requested_path) if delimiter == '"' else (root / requested_path)
        included = _expand_includes(candidate, root, (*stack, path))
        relative = _contained(root, candidate).relative_to(root).as_posix()
        return f"// focal-gl include begin: {relative}\n{included}\n// focal-gl include end: {relative}"

    return _INCLUDE.sub(replace, text)


def _inject_defines(source: str, defines: dict[str, str]) -> str:
    if not defines:
        return source
    block = "\n".join(f"#define {name} {value}" for name, value in defines.items())
    lines = source.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("#version"):
            lines.insert(index + 1, block + "\n")
            return "".join(lines)
    return block + "\n" + source


def _read_stage(path: Path, root: Path, source_mode: str, defines: dict[str, str]) -> str:
    if source_mode == "preprocessed":
        return _inject_defines(_expand_includes(path, root, ()), defines)
    try:
        source = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SourceResolutionError(f"missing shader source: {path.relative_to(root).as_posix()}") from exc
    except UnicodeDecodeError as exc:
        raise SourceResolutionError(f"shader source is not UTF-8: {path.relative_to(root).as_posix()}") from exc
    if source_mode == "iris-patched" and _INCLUDE.search(source):
        raise SourceResolutionError(f"patched source retains an unresolved include: {path.relative_to(root).as_posix()}")
    if defines:
        raise SourceResolutionError("--define is only valid with --source-mode preprocessed")
    return source


def prepare_program(
    *,
    pack: Path,
    program: str,
    source_mode: str,
    source_root: Path | None = None,
    define_values: Iterable[str] = (),
) -> PreparedProgram:
    if not program or Path(program).name != program:
        raise SourceResolutionError("program must be a single shader program name")
    root = resolve_source_root(pack, source_mode, source_root)
    defines = parse_defines(define_values)
    paths = [root / f"{program}.{suffix}" for suffix in STAGE_SUFFIXES]
    present = [path for path in paths if path.is_file()]
    if not present:
        raise SourceResolutionError(f"program {program!r} has no shader stages in {root}")

    stages: list[PreparedStage] = []
    for path in present:
        source = _read_stage(path, root, source_mode, defines)
        encoded = source.encode("utf-8")
        stages.append(
            PreparedStage(
                stage=path.suffix.lstrip("."),
                path=path.relative_to(root).as_posix(),
                byteLength=len(encoded),
                sha256=hashlib.sha256(encoded).hexdigest(),
                source=source,
            )
        )
    return PreparedProgram(
        sourceMode=source_mode,
        sourceRoot=str(root),
        program=program,
        includesResolved=source_mode in ("preprocessed", "iris-patched"),
        defines=defines,
        stages=tuple(stages),
    )
