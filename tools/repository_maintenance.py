#!/usr/bin/env python3
"""Permanent, scoped repository maintenance for Focal.

Administrative cleanup is intentionally separate from ``FOCAL_CYCLE``. It may be
requested through the existing issue command ingress or invoked by the permanent
workflow. A maintenance execution can delete branches or allowlisted files, but it
must never create a branch, pull request, or workflow.
"""

from __future__ import annotations

import argparse
import base64
import fnmatch
import json
import os
import sys
import urllib.parse
from datetime import datetime, timezone
from typing import Any

from tools.automation_state_v4 import StateStore, _issue_snapshot, mirror_state
from tools.stale_lease_watchdog import GitHubApi, now_iso

TEMPORARY_WORKFLOW_MARKER = "# focal-temporary-workflow: true"
MAINTENANCE_OPERATION = "repository_maintenance"
VALID_SCOPES = ("branches", "garbage", "temporary_workflows", "all")
PROCESSED_MAINTENANCE_LIMIT = 64
ALWAYS_GARBAGE_PATTERNS = (
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/*.orig",
    "**/*.rej",
    "**/__pycache__/*.pyc",
    "**/.pytest_cache/**",
)
_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def api_pages(api: GitHubApi, path: str) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    page = 1
    separator = "&" if "?" in path else "?"
    while True:
        batch = api.request("GET", f"{path}{separator}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError(f"paginated endpoint did not return a list: {path}")
        values.extend(item for item in batch if isinstance(item, dict))
        if len(batch) < 100:
            return values
        page += 1


def validate_scope(scope: str) -> str:
    if scope not in VALID_SCOPES:
        raise ValueError(f"invalid maintenance scope: {scope}")
    return scope


def _scope_includes(scope: str, capability: str) -> bool:
    return scope == "all" or scope == capability


def _matches_always_garbage(path: str) -> bool:
    normalized = f"/{path}"
    return any(fnmatch.fnmatch(normalized, f"/{pattern}") for pattern in ALWAYS_GARBAGE_PATTERNS)


def _blob_text(api: GitHubApi, repository: str, sha: str) -> str:
    payload = api.request("GET", f"/repos/{repository}/git/blobs/{sha}")
    encoded = (payload or {}).get("content")
    if not isinstance(encoded, str):
        return ""
    return base64.b64decode(encoded).decode("utf-8", errors="replace")


def garbage_paths(
    api: GitHubApi,
    repository: str,
    tree: list[dict[str, Any]],
    *,
    scope: str = "all",
) -> list[str]:
    validate_scope(scope)
    include_garbage = _scope_includes(scope, "garbage")
    include_workflows = _scope_includes(scope, "temporary_workflows")
    if not include_garbage and not include_workflows:
        return []

    result: list[str] = []
    for entry in tree:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path")
        sha = entry.get("sha")
        if not isinstance(path, str) or not isinstance(sha, str):
            continue
        if include_garbage and _matches_always_garbage(path):
            result.append(path)
            continue
        if (
            include_workflows
            and path.startswith(".github/workflows/")
            and path.endswith((".yml", ".yaml"))
            and TEMPORARY_WORKFLOW_MARKER in _blob_text(api, repository, sha)
        ):
            result.append(path)
    return sorted(set(result))


def _branch_infos(api: GitHubApi, repository: str) -> list[dict[str, Any]]:
    return api_pages(api, f"/repos/{repository}/branches")


def _branch_names(infos: list[dict[str, Any]]) -> set[str]:
    return {name for item in infos if isinstance((name := item.get("name")), str)}


def branch_cleanup_plan(
    api: GitHubApi,
    repository: str,
    *,
    default_branch: str,
    protected_names: set[str],
    branch_infos: list[dict[str, Any]] | None = None,
) -> tuple[list[str], list[dict[str, str]]]:
    owner = repository.split("/", 1)[0]
    deletable: list[str] = []
    skipped: list[dict[str, str]] = []
    for info in branch_infos if branch_infos is not None else _branch_infos(api, repository):
        branch = info.get("name")
        tip = ((info.get("commit") or {}).get("sha"))
        if not isinstance(branch, str) or not isinstance(tip, str):
            continue
        if branch == default_branch or branch in protected_names:
            skipped.append({"branch": branch, "reason": "PROTECTED_CONTROL_BRANCH"})
            continue
        if info.get("protected"):
            skipped.append({"branch": branch, "reason": "PROTECTED"})
            continue

        query = urllib.parse.urlencode({"state": "open", "head": f"{owner}:{branch}"})
        if api_pages(api, f"/repos/{repository}/pulls?{query}"):
            skipped.append({"branch": branch, "reason": "OPEN_PULL_REQUEST"})
            continue

        base = urllib.parse.quote(branch, safe="")
        head = urllib.parse.quote(default_branch, safe="")
        comparison = api.request("GET", f"/repos/{repository}/compare/{base}...{head}")
        fully_behind = (comparison or {}).get("status") in {"ahead", "identical"}
        if fully_behind:
            deletable.append(branch)
        else:
            skipped.append({"branch": branch, "reason": "UNMERGED_WORK_PRESERVED"})
    return sorted(deletable), skipped


def _guard_mutation(method: str, path: str, payload: Any = None) -> None:
    if method not in _WRITE_METHODS:
        return
    if method == "POST" and path.endswith("/git/refs"):
        raise RuntimeError("MAINTENANCE_CREATED_REF: branch creation is forbidden")
    if "/pulls" in path:
        raise RuntimeError("MAINTENANCE_CREATED_PR: pull-request mutation is forbidden")
    if method == "POST" and path.endswith("/git/trees"):
        tree_entries = (payload or {}).get("tree") if isinstance(payload, dict) else None
        if not isinstance(tree_entries, list):
            raise RuntimeError("maintenance tree mutation requires explicit entries")
        for entry in tree_entries:
            if not isinstance(entry, dict):
                raise RuntimeError("maintenance tree entry is invalid")
            entry_path = entry.get("path")
            if (
                isinstance(entry_path, str)
                and entry_path.startswith(".github/workflows/")
                and entry.get("sha") is not None
            ):
                raise RuntimeError("MAINTENANCE_CREATED_WORKFLOW: workflow creation is forbidden")


def _mutate(api: GitHubApi, method: str, path: str, payload: Any = None) -> Any:
    _guard_mutation(method, path, payload)
    return api.request(method, path, payload)


def delete_paths_in_one_commit(
    api: GitHubApi,
    repository: str,
    *,
    default_branch: str,
    head_sha: str,
    tree_sha: str,
    paths: list[str],
) -> str:
    if not paths:
        return head_sha
    tree = _mutate(
        api,
        "POST",
        f"/repos/{repository}/git/trees",
        {
            "base_tree": tree_sha,
            "tree": [
                {"path": path, "mode": "100644", "type": "blob", "sha": None}
                for path in paths
            ],
        },
    )
    new_tree_sha = (tree or {}).get("sha")
    if not isinstance(new_tree_sha, str):
        raise ValueError("maintenance tree SHA unavailable")
    commit = _mutate(
        api,
        "POST",
        f"/repos/{repository}/git/commits",
        {
            "message": "Remove allowlisted repository garbage",
            "tree": new_tree_sha,
            "parents": [head_sha],
        },
    )
    commit_sha = (commit or {}).get("sha")
    if not isinstance(commit_sha, str):
        raise ValueError("maintenance commit SHA unavailable")
    _mutate(
        api,
        "PATCH",
        f"/repos/{repository}/git/refs/heads/{urllib.parse.quote(default_branch, safe='')}",
        {"sha": commit_sha, "force": False},
    )
    return commit_sha


def _maintenance_request_from_issue(
    api: GitHubApi,
    repository: str,
    issue_number: int,
) -> dict[str, Any] | None:
    command, _ = _issue_snapshot(api, repository, issue_number)
    if command.get("operation") != MAINTENANCE_OPERATION:
        return None
    if command.get("schemaVersion") != 3:
        raise ValueError("maintenance command schemaVersion 3 is required")
    command_id = command.get("commandId")
    if not isinstance(command_id, str) or not command_id:
        raise ValueError("maintenance commandId is required")
    scope = command.get("scope")
    if not isinstance(scope, str):
        raise ValueError("maintenance scope is required")
    validate_scope(scope)
    dry_run = command.get("dryRun", True)
    if not isinstance(dry_run, bool):
        raise ValueError("maintenance dryRun must be boolean")
    return command


def _bounded_maintenance_ids(state: dict[str, Any], command_id: str | None) -> list[str]:
    current = state.get("processedMaintenanceCommandIds")
    values = [item for item in current if isinstance(item, str)] if isinstance(current, list) else []
    if command_id and command_id not in values:
        values.append(command_id)
    return values[-PROCESSED_MAINTENANCE_LIMIT:]


def _require_existing_state_branch(api: GitHubApi, repository: str, state_branch: str) -> None:
    encoded = urllib.parse.quote(state_branch, safe="")
    api.request("GET", f"/repos/{repository}/git/ref/heads/{encoded}")


def _record_maintenance(
    api: GitHubApi,
    store: StateStore,
    repository: str,
    issue_number: int,
    summary: dict[str, Any],
    command_id: str | None,
) -> None:
    refreshed = store.read()
    if refreshed.state.get("status") != "idle" or refreshed.state.get("runId") is not None:
        raise RuntimeError("ACTIVE_LEASE: maintenance result cannot be recorded")
    state = dict(refreshed.state)
    state["lastRepositoryMaintenanceAt"] = now_iso(datetime.now(timezone.utc))
    state["lastRepositoryMaintenance"] = summary
    state["lastRepositoryMaintenanceCommandId"] = command_id
    state["lastRepositoryMaintenanceReason"] = (
        "MAINTENANCE_DRY_RUN" if summary.get("action") == "dry-run" else "MAINTENANCE_COMPLETED"
    )
    state["processedMaintenanceCommandIds"] = _bounded_maintenance_ids(state, command_id)
    state["version"] = int(state.get("version", 0)) + 1
    written = store.write(state, refreshed.blob_sha, message="Record repository maintenance")
    mirror_state(api, repository, issue_number, written.state)


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    command_id = args.command_id
    scope = validate_scope(args.scope)
    dry_run = args.dry_run
    if args.from_issue:
        request = _maintenance_request_from_issue(api, repository, args.issue)
        if request is None:
            print(json.dumps({"action": "skipped", "reason": "NO_MAINTENANCE_REQUEST"}, sort_keys=True))
            return 0
        command_id = request["commandId"]
        scope = validate_scope(request["scope"])
        dry_run = request.get("dryRun", True)

    _require_existing_state_branch(api, repository, args.state_branch)
    _, issue_state = _issue_snapshot(api, repository, args.issue)
    store = StateStore(api, repository, branch=args.state_branch, path=args.state_path)
    stored = store.read(bootstrap=issue_state)
    processed_ids = stored.state.get("processedMaintenanceCommandIds")
    if command_id and isinstance(processed_ids, list) and command_id in processed_ids:
        print(
            json.dumps(
                {"action": "skipped", "reason": "MAINTENANCE_ALREADY_PROCESSED", "commandId": command_id},
                sort_keys=True,
            )
        )
        return 0
    if args.require_idle and not (
        stored.state.get("status") == "idle" and stored.state.get("runId") is None
    ):
        print(json.dumps({"action": "skipped", "reason": "ACTIVE_LEASE"}, sort_keys=True))
        return 0

    repo = api.request("GET", f"/repos/{repository}")
    default_branch = (repo or {}).get("default_branch")
    if not isinstance(default_branch, str) or not default_branch:
        raise ValueError("default branch unavailable")
    ref = api.request(
        "GET",
        f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(default_branch, safe='')}",
    )
    head_sha = ((ref or {}).get("object") or {}).get("sha")
    if not isinstance(head_sha, str):
        raise ValueError("default branch head unavailable")
    commit = api.request("GET", f"/repos/{repository}/git/commits/{head_sha}")
    tree_sha = ((commit or {}).get("tree") or {}).get("sha")
    if not isinstance(tree_sha, str):
        raise ValueError("default branch tree unavailable")
    tree_payload = api.request("GET", f"/repos/{repository}/git/trees/{tree_sha}?recursive=1")
    tree = (tree_payload or {}).get("tree")
    if not isinstance(tree, list):
        raise ValueError("recursive tree unavailable")

    branch_infos_before = _branch_infos(api, repository)
    branch_names_before = _branch_names(branch_infos_before)
    paths = garbage_paths(api, repository, tree, scope=scope)
    if _scope_includes(scope, "branches"):
        branches, skipped = branch_cleanup_plan(
            api,
            repository,
            default_branch=default_branch,
            protected_names={args.state_branch},
            branch_infos=branch_infos_before,
        )
    else:
        branches, skipped = [], []

    summary: dict[str, Any] = {
        "action": "dry-run" if dry_run else "completed",
        "scope": scope,
        "commandId": command_id,
        "garbagePaths": paths,
        "branches": branches,
        "skippedBranches": skipped,
        "defaultBranchHeadBefore": head_sha,
        "branchCountBefore": len(branch_names_before),
    }
    if not dry_run:
        new_head = delete_paths_in_one_commit(
            api,
            repository,
            default_branch=default_branch,
            head_sha=head_sha,
            tree_sha=tree_sha,
            paths=paths,
        )
        for branch in branches:
            _mutate(
                api,
                "DELETE",
                f"/repos/{repository}/git/refs/heads/{urllib.parse.quote(branch, safe='')}",
            )

        branch_names_after = _branch_names(_branch_infos(api, repository))
        created_branches = sorted(branch_names_after - branch_names_before)
        missing_branches = branch_names_before - branch_names_after
        unexpected_deletions = sorted(missing_branches - set(branches))
        if created_branches:
            raise RuntimeError(f"MAINTENANCE_CREATED_REF: {created_branches}")
        if unexpected_deletions:
            raise RuntimeError(f"MAINTENANCE_UNPLANNED_BRANCH_DELETION: {unexpected_deletions}")
        if len(branch_names_after) > len(branch_names_before):
            raise RuntimeError("MAINTENANCE_BRANCH_COUNT_INCREASED")

        default_ref_after = api.request(
            "GET",
            f"/repos/{repository}/git/ref/heads/{urllib.parse.quote(default_branch, safe='')}",
        )
        observed_head_after = ((default_ref_after or {}).get("object") or {}).get("sha")
        if observed_head_after != new_head:
            raise RuntimeError("MAINTENANCE_DEFAULT_HEAD_MISMATCH")
        if scope == "branches" and observed_head_after != head_sha:
            raise RuntimeError("MAINTENANCE_BRANCH_SCOPE_MODIFIED_DEFAULT_HEAD")

        summary.update(
            {
                "defaultBranchHeadAfter": new_head,
                "branchCountAfter": len(branch_names_after),
                "createdBranches": created_branches,
                "deletedBranches": sorted(missing_branches),
            }
        )
    else:
        summary["branchCountAfter"] = len(branch_names_before)
        summary["createdBranches"] = []
        summary["deletedBranches"] = []

    _record_maintenance(api, store, repository, args.issue, summary, command_id)
    print(json.dumps(summary, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    parser.add_argument("--state-branch", default="automation/state-v4")
    parser.add_argument("--state-path", default=".focal/automation-state.json")
    parser.add_argument("--require-idle", action="store_true")
    parser.add_argument("--from-issue", action="store_true")
    parser.add_argument("--scope", choices=VALID_SCOPES, default="all")
    parser.add_argument("--command-id")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        return run(build_parser().parse_args(argv))
    except Exception as exc:
        print(f"repository maintenance failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
