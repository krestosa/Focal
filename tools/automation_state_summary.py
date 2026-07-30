#!/usr/bin/env python3
"""Render the human-readable header of the canonical automation-state issue."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import quote

SUMMARY_START = "<!-- focal-summary:v1 -->"
SUMMARY_END = "<!-- /focal-summary -->"
COMMAND_START = "<!-- focal-command:v3 -->"
COMMAND_END = "<!-- /focal-command -->"
STATE_START = "<!-- focal-state:v3 -->"
STATE_END = "<!-- /focal-state -->"

RESULT_BADGES = {
    "PASS": "✅",
    "PARTIAL": "🟡",
    "BLOCKED": "🔴",
    "NO-OP": "⚪",
}

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_FULL_SHA_IN_TEXT_RE = re.compile(r"\b[0-9a-fA-F]{40}\b")
_PR_IN_TEXT_RE = re.compile(r"\bPR\s+#(\d+)\b")
_ISSUE_IN_TEXT_RE = re.compile(r"\bissue\s+#(\d+)\b", flags=re.IGNORECASE)
_RUN_IN_TEXT_RE = re.compile(r"\b((?:Validation\s+)?run)\s+(\d+)\b", flags=re.IGNORECASE)
_BRANCH_IN_TEXT_RE = re.compile(r"\b(branch|rama)\s+([A-Za-z0-9._/-]+)", flags=re.IGNORECASE)
_FILE_IN_TEXT_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:docs|tools|tests|scripts|shaderpacks?|prompts|\.github)/"
    r"[A-Za-z0-9._/-]+\.(?:md|py|json|ya?ml|properties|fsh|vsh|glsl|txt))\b"
)


def _cell(value: Any, fallback: str = "—") -> str:
    if value is None or value == "":
        return fallback
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _label(value: Any) -> str:
    return _cell(value).replace("[", "\\[").replace("]", "\\]")


def _link(label: Any, url: str) -> str:
    return f"[{_label(label)}]({url})"


def _repository(state: dict[str, Any]) -> str | None:
    value = state.get("repository")
    if isinstance(value, str) and _REPOSITORY_RE.fullmatch(value):
        return value
    return None


def _repository_url(state: dict[str, Any], suffix: str) -> str | None:
    repository = _repository(state)
    if repository is None:
        return None
    return f"https://github.com/{repository}/{suffix.lstrip('/')}"


def _commit(value: Any, state: dict[str, Any]) -> str:
    text = _cell(value)
    if text == "—":
        return text
    url = _repository_url(state, f"commit/{quote(text, safe='')}")
    label = f"`{text[:12]}`"
    if url is None or not _SHA_RE.fullmatch(text):
        return label
    return _link(label, url)


def _branch(state: dict[str, Any]) -> str:
    value = state.get("workBranch")
    text = _cell(value)
    if text == "—":
        return text
    url = _repository_url(state, f"tree/{quote(text, safe='/-._')}")
    label = f"`{text}`"
    return _link(label, url) if url is not None else label


def _pull_request(state: dict[str, Any]) -> str:
    value = state.get("pullRequest")
    if value is None or value == "":
        return "—"
    text = str(value)
    if not text.isdigit():
        return _cell(value)
    url = _repository_url(state, f"pull/{text}")
    label = f"PR #{text}"
    return _link(label, url) if url is not None else label


def _workflow(state: dict[str, Any]) -> str | None:
    value = state.get("workflowPath")
    if not isinstance(value, str) or not value:
        return None
    url = _repository_url(state, f"actions/workflows/{quote(value, safe='/-._')}")
    return _link(f"`{value}`", url) if url is not None else f"`{_cell(value)}`"


def _workflow_run(state: dict[str, Any]) -> str | None:
    value = state.get("workflowRun")
    if value is None or value == "":
        return None
    text = str(value)
    if not text.isdigit():
        return _cell(value)
    url = _repository_url(state, f"actions/runs/{text}")
    label = f"run {text}"
    return _link(label, url) if url is not None else label


def _result(value: Any) -> str:
    text = _cell(value)
    return f"{RESULT_BADGES.get(text, '⚪')} `{text}`"


def _linkify_note(value: Any, state: dict[str, Any]) -> str:
    text = _cell(value)
    if text == "—" or _repository(state) is None:
        return text

    ref = state.get("checkpointSha") or state.get("workBranch") or "main"
    ref_text = quote(str(ref), safe="/-._")

    def link_sha(match: re.Match[str]) -> str:
        sha = match.group(0)
        url = _repository_url(state, f"commit/{sha}")
        return _link(f"`{sha[:12]}`", url) if url is not None else f"`{sha[:12]}`"

    def link_pr(match: re.Match[str]) -> str:
        number = match.group(1)
        url = _repository_url(state, f"pull/{number}")
        return _link(f"PR #{number}", url) if url is not None else match.group(0)

    def link_issue(match: re.Match[str]) -> str:
        number = match.group(1)
        url = _repository_url(state, f"issues/{number}")
        return _link(f"issue #{number}", url) if url is not None else match.group(0)

    def link_run(match: re.Match[str]) -> str:
        prefix = match.group(1)
        number = match.group(2)
        url = _repository_url(state, f"actions/runs/{number}")
        label = f"{prefix} {number}"
        return _link(label, url) if url is not None else match.group(0)

    def link_branch(match: re.Match[str]) -> str:
        prefix = match.group(1)
        branch = match.group(2)
        url = _repository_url(state, f"tree/{quote(branch, safe='/-._')}")
        label = f"{prefix} `{branch}`"
        return _link(label, url) if url is not None else match.group(0)

    def link_file(match: re.Match[str]) -> str:
        path = match.group(1)
        url = _repository_url(state, f"blob/{ref_text}/{quote(path, safe='/-._')}")
        return _link(f"`{path}`", url) if url is not None else f"`{path}`"

    text = _FULL_SHA_IN_TEXT_RE.sub(link_sha, text)
    text = _PR_IN_TEXT_RE.sub(link_pr, text)
    text = _ISSUE_IN_TEXT_RE.sub(link_issue, text)
    text = _RUN_IN_TEXT_RE.sub(link_run, text)
    text = _BRANCH_IN_TEXT_RE.sub(link_branch, text)
    text = _FILE_IN_TEXT_RE.sub(link_file, text)
    return text


def _activity(state: dict[str, Any]) -> str:
    phase = str(state.get("phase") or "idle").upper()
    if state.get("mode") == "recovery" or "RECOVER" in phase:
        return "🟣 Recuperación"
    if "REMOTE" in phase:
        return "🌐 Operación remota"
    if any(token in phase for token in ("VALID", "TEST", "CI")):
        return "🧪 Validación"
    if any(token in phase for token in ("MERGE", "PUBLISH", "RELEASE")):
        return "🟠 Publicación"
    if state.get("status") == "working":
        return "🛠️ Implementación"
    return "💤 En espera"


def _status_callout(status: Any, mode: Any) -> str:
    if status == "working" and mode == "recovery":
        return "> [!WARNING]\n> Hay una recuperación activa. No inicies otra ejecución hasta que el estado vuelva a `IDLE`."
    if status == "working":
        return "> [!IMPORTANT]\n> Hay una lease activa. No inicies otra ejecución hasta que el estado vuelva a `IDLE`."
    if status == "idle":
        return "> [!TIP]\n> El coordinador está libre y puede aceptar una nueva ejecución."
    return "> [!CAUTION]\n> El estado no es válido. Revisá los datos técnicos antes de iniciar otra ejecución."


def render_summary(state: dict[str, Any]) -> str:
    status = state.get("status")
    mode = state.get("mode")
    if status == "working" and mode == "recovery":
        heading = "## 🟣 WORKING · Recuperación activa"
    elif status == "working":
        heading = "## 🔵 WORKING · Ejecución activa"
    elif status == "idle":
        heading = "## 🟢 IDLE · Disponible"
    else:
        heading = "## 🔴 UNKNOWN · Estado inválido"

    rows: list[tuple[str, str]] = [
        ("Estado", f"`{_cell(status).upper()}`"),
        ("Actividad", _activity(state)),
        ("Fase", f"`{_cell(state.get('phase'))}`"),
    ]
    if status == "working":
        rows.extend(
            [
                ("Inicio", _cell(state.get("startedAt"))),
                ("Último heartbeat", _cell(state.get("heartbeatAt"))),
                ("Lease hasta", _cell(state.get("leaseExpiresAt"))),
                ("Rama", _branch(state)),
                ("Pull request", _pull_request(state)),
            ]
        )
    else:
        rows.extend(
            [
                ("Último resultado", _result(state.get("lastResult"))),
                ("Última finalización", _cell(state.get("lastCompletedAt"))),
            ]
        )

    workflow = _workflow(state)
    if workflow is not None:
        rows.append(("Workflow", workflow))
    workflow_run = _workflow_run(state)
    if workflow_run is not None:
        rows.append(("Run", workflow_run))

    rows.extend(
        [
            ("Checkpoint", _commit(state.get("checkpointSha"), state)),
            ("Resumen", _linkify_note(state.get("note"), state)),
        ]
    )

    lines = [SUMMARY_START, heading, "", "| Campo | Resumen |", "|---|---|"]
    lines.extend(f"| **{name}** | {value} |" for name, value in rows)
    lines.extend(["", _status_callout(status, mode), "", SUMMARY_END])
    return "\n".join(lines)


def render_issue_body(command: dict[str, Any], state: dict[str, Any]) -> str:
    command_json = json.dumps(command, indent=2, sort_keys=False)
    state_json = json.dumps(state, indent=2, sort_keys=False)
    return f"""# Focal — Estado de ejecución

{render_summary(state)}

> [!NOTE]
> La cabecera es un resumen generado automáticamente. Los bloques JSON son la fuente canónica del coordinador y no deben editarse manualmente durante una lease activa.

<details>
<summary><strong>Datos técnicos del coordinador</strong></summary>

### Comando

{COMMAND_START}
```json
{command_json}
```
{COMMAND_END}

### Estado canónico

{STATE_START}
```json
{state_json}
```
{STATE_END}

</details>
"""


def has_single_managed_blocks(body: str) -> bool:
    markers = (SUMMARY_START, SUMMARY_END, COMMAND_START, COMMAND_END, STATE_START, STATE_END)
    return all(body.count(marker) == 1 for marker in markers)
