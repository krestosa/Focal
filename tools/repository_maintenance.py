#!/usr/bin/env python3
"""Permanent, conservative repository maintenance for Focal.

The workflow deletes only objectively disposable branches and files. Temporary
workflow files require the marker ``# focal-temporary-workflow: true``. All
maintenance is skipped while the transactional coordinator reports an active lease.
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

from tools.automation_state_v4 import StateStore, _issue_snapshot
from tools.stale_lease_watchdog import GitHubApi, now_iso

TEMPORARY_WORKFLOW_MARKER = "# focal-temporary-workflow: true"
ALWAYS_GARBAGE_PATTERNS = (
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/*.orig",
    "**/*.rej",
    "**/__pycache__/*.pyc",
    "**/.pytest_cache/**",
)


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
) -> list[str]:
    result: list[str] = []
    for entry in tree:
        if entry.get("type") != "blob":
            continue
        path = entry.get("path")
        sha = entry.get("sha")
        if not isinstance(path, str) or not isinstance(sha, str):
            continue
        if _matches_always_garbage(path):
            result.append(path)
            continue
        if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            if TEMPORARY_WORKFLOW_MARKER in _blob_text(api, repository, sha):
                result.append(path)
    return sorted(set(result))


def branch_cleanup_plan(
    api: GitHubApi,
    repository: str,
    *,
    default_branch: str,
    protected_names: set[str],
) -> tuple[list[str], list[dict[str, str]]]:
    owner = repository.split("/", 1)[0]
    deletable: list[str] = []
    skipped: list[dict[str, str]] = []
    for info in api_pages(api, f"/repos/{repository}/branches"):
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
    tree = api.request(
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
    commit = api.request(
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
    api.request(
        "PATCH",
        f"/repos/{repository}/git/refs/heads/{urllib.parse.quote(default_branch, safe='')}",
        {"sha": commit_sha, "force": False},
    )
    return commit_sha


def run(args: argparse.Namespace) -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    if not repository:
        raise RuntimeError("repository is required")

    api = GitHubApi(token)
    _, issue_state = _issue_snapshot(api, repository, args.issue)
    store = StateStore(api, repository, branch=args.state_branch, path=args.state_path)
    stored = store.read(bootstrap=issue_state)
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

    paths = garbage_paths(api, repository, tree)
    branches, skipped = branch_cleanup_plan(
        api,
        repository,
        default_branch=default_branch,
        protected_names={args.state_branch},
    )

    summary: dict[str, Any] = {
        "action": "dry-run" if args.dry_run else "completed",
        "garbagePaths": paths,
        "branches": branches,
        "skippedBranches": skipped,
        "defaultBranchHeadBefore": head_sha,
    }
    if not args.dry_run:
        new_head = delete_paths_in_one_commit(
            api,
            repository,
            default_branch=default_branch,
            head_sha=head_sha,
            tree_sha=tree_sha,
            paths=paths,
        )
        for branch in branches:
            api.request(
                "DELETE",
                f"/repos/{repository}/git/refs/heads/{urllib.parse.quote(branch, safe='')}",
            )
        summary["defaultBranchHeadAfter"] = new_head

        refreshed = store.read()
        if refreshed.state.get("status") == "idle" and refreshed.state.get("runId") is None:
            state = dict(refreshed.state)
            state["lastRepositoryMaintenanceAt"] = now_iso(datetime.now(timezone.utc))
            state["lastRepositoryMaintenance"] = summary
            state["version"] = int(state.get("version", 0)) + 1
            store.write(state, refreshed.blob_sha, message="Record repository maintenance")

    print(json.dumps(summary, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository")
    parser.add_argument("--issue", type=int, default=7)
    parser.add_argument("--state-branch", default="automation/state-v4")
    parser.add_argument("--state-path", default=".focal/automation-state.json")
    parser.add_argument("--require-idle", action="store_true")
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
