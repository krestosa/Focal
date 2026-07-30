#!/usr/bin/env python3
"""Render the human-readable header of the canonical automation-state issue."""

from __future__ import annotations

import json
import re
from typing import Any

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


def _sha(value: Any) -> str:
    text = _cell(value)
    if text == "—":
        return text
    return f"`{text[:12]}`"


def _result(value: Any) -> str:
    text = _cell(value)
    return f"{RESULT_BADGES.get(text, '⚪')} `{text}`"


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
                ("Rama", f"`{_cell(state.get('workBranch'))}`"),
                ("Pull request", _cell(state.get("pullRequest"))),
            ]
        )
    else:
        rows.extend(
            [
                ("Último resultado", _result(state.get("lastResult"))),
                ("Última finalización", _cell(state.get("lastCompletedAt"))),
            ]
        )
    rows.extend(
        [
            ("Checkpoint", _sha(state.get("checkpointSha"))),
            ("Resumen", _cell(state.get("note"))),
        ]
    )

    lines = [SUMMARY_START, heading, ""]
    if status == "working":
        lines.append("> [!IMPORTANT]\n> Hay una lease activa. No inicies otra ejecución hasta que el estado vuelva a `IDLE`.")
    else:
        lines.append("> [!TIP]\n> El coordinador está libre y puede aceptar una nueva ejecución.")
    lines.extend(["", "| Campo | Resumen |", "|---|---|"])
    lines.extend(f"| **{name}** | {value} |" for name, value in rows)
    lines.extend(["", SUMMARY_END])
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
