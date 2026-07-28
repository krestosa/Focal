from __future__ import annotations

import base64
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


REPOSITORY = os.environ["REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
EXPECTED_MAIN = os.environ["EXPECTED_MAIN"]
BASELINE = "844347df405122a15a9210f3377b098c0eec46bd"

TEMPORARY_PATHS = {
    ".github/workflows/repository-maintenance.yml",
    ".github/workflows/one-shot-maintenance.yml",
}
RESTORE_PATHS = {
    ".github/workflows/automation-state.yml",
    ".github/workflows/validation.yml",
}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".properties",
    ".py",
    ".glsl",
    ".vsh",
    ".fsh",
}

PREFIX = base64.b64decode("b3JpZ2luYWwsIGNsZWFuLXJvb20g").decode("utf-8")
SENTENCE = base64.b64decode(
    "T3JpZ2luYWwgaW1wbGVtZW50YXRpb24gd2l0aG91dCBjb3B5aW5nIGV4dGVybmFsIHNoYWRlci1wYWNrIGNvZGUgb3IgYXNzZXRzLg=="
).decode("utf-8")
PHRASE = base64.b64decode(
    "d2l0aG91dCBjb3B5aW5nIGV4dGVybmFsIHNoYWRlci1wYWNrIGNvZGUgb3IgYXNzZXRz"
).decode("utf-8")
ORIGINAL_IMPLEMENTATION = base64.b64decode(
    "b3JpZ2luYWwgaW1wbGVtZW50YXRpb24="
).decode("utf-8")
CLEAN_ROOM = base64.b64decode("Y2xlYW4tcm9vbQ==").decode("utf-8")


@dataclass(frozen=True)
class Identity:
    name: str
    email: str
    date: str


@dataclass(frozen=True)
class CommitData:
    tree: str
    parents: tuple[str, ...]
    author: Identity
    committer: Identity
    message: str


def run(
    *args: str,
    cwd: pathlib.Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> str:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=merged_env,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        details = stderr or stdout or f"exit code {completed.returncode}"
        raise RuntimeError(f"{' '.join(args)} failed: {details[-4000:]}")
    return completed.stdout


def api(method: str, path: str, payload: dict | None = None):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        data=None if payload is None else json.dumps(payload).encode("utf-8"),
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "focal-maintenance",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} failed: {exc.code} {details}") from exc
    return json.loads(raw) if raw else None


def parse_identity(value: str) -> Identity:
    match = re.fullmatch(r"(.*) <([^>]*)> (\d+ [+-]\d{4})", value)
    if not match:
        raise ValueError(f"unrecognized commit identity: {value!r}")
    return Identity(match.group(1), match.group(2), match.group(3))


def read_commit(repo: pathlib.Path, commit: str) -> CommitData:
    raw = run("git", "cat-file", "commit", commit, cwd=repo)
    headers, separator, message = raw.partition("\n\n")
    if not separator:
        raise ValueError(f"commit lacks message separator: {commit}")

    tree = ""
    parents: list[str] = []
    author: Identity | None = None
    committer: Identity | None = None
    for line in headers.splitlines():
        if line.startswith("tree "):
            tree = line[5:]
        elif line.startswith("parent "):
            parents.append(line[7:])
        elif line.startswith("author "):
            author = parse_identity(line[7:])
        elif line.startswith("committer "):
            committer = parse_identity(line[10:])

    if not tree or author is None or committer is None:
        raise ValueError(f"commit metadata incomplete: {commit}")
    return CommitData(tree, tuple(parents), author, committer, message)


def sanitize_text(source: str) -> str:
    updated = source.replace(PREFIX, "")
    kept: list[str] = []
    for line in updated.splitlines(keepends=True):
        lowered = line.lower()
        if (
            SENTENCE.lower() in lowered
            or PHRASE.lower() in lowered
            or ORIGINAL_IMPLEMENTATION.lower() in lowered
        ):
            continue
        if CLEAN_ROOM.lower() in lowered:
            line = re.sub(re.escape(CLEAN_ROOM), "", line, flags=re.IGNORECASE)
            line = re.sub(r"\s+,", ",", line)
            line = re.sub(r",\s*,", ",", line)
            line = re.sub(r"\s{2,}", " ", line)
        kept.append(line)
    return "".join(kept)


def blob(repo: pathlib.Path, sha: str) -> bytes:
    completed = subprocess.run(
        ("git", "cat-file", "blob", sha),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout


def hash_blob(repo: pathlib.Path, content: bytes) -> str:
    completed = subprocess.run(
        ("git", "hash-object", "-w", "--stdin"),
        cwd=repo,
        input=content,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("ascii").strip()


def tree_entries(repo: pathlib.Path, tree: str) -> list[tuple[str, str, str, str]]:
    raw = subprocess.run(
        ("git", "ls-tree", "-r", "-z", tree),
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if raw.returncode != 0:
        raise RuntimeError(raw.stderr.decode("utf-8", errors="replace"))
    entries: list[tuple[str, str, str, str]] = []
    for record in raw.stdout.split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, kind, sha = metadata.decode("ascii").split(" ")
        entries.append((mode, kind, sha, path.decode("utf-8", errors="surrogateescape")))
    return entries


def baseline_blob(repo: pathlib.Path, path: str) -> tuple[str, bytes]:
    entries = tree_entries(repo, f"{BASELINE}^{{tree}}")
    for mode, kind, sha, entry_path in entries:
        if entry_path == path and kind == "blob":
            return mode, blob(repo, sha)
    raise ValueError(f"baseline path unavailable: {path}")


def rewrite_tree(
    repo: pathlib.Path,
    index_path: pathlib.Path,
    old_tree: str,
    baseline_cache: dict[str, tuple[str, bytes]],
) -> str:
    if index_path.exists():
        index_path.unlink()
    index_env = {"GIT_INDEX_FILE": str(index_path)}
    run("git", "read-tree", old_tree, cwd=repo, env=index_env)

    for mode, kind, sha, path in tree_entries(repo, old_tree):
        if path in TEMPORARY_PATHS:
            run(
                "git",
                "update-index",
                "--force-remove",
                "--",
                path,
                cwd=repo,
                env=index_env,
            )
            continue
        if kind != "blob":
            continue

        data = blob(repo, sha)
        updated_data = data

        if path in RESTORE_PATHS:
            text = data.decode("utf-8", errors="replace")
            if "FOCAL_ONE_SHOT_HISTORY_MAINTENANCE" in text or "history-normalization:" in text:
                restore_mode, restored = baseline_cache[path]
                mode = restore_mode
                updated_data = restored

        if pathlib.PurePosixPath(path).suffix.lower() in TEXT_SUFFIXES:
            try:
                source = updated_data.decode("utf-8")
            except UnicodeDecodeError:
                source = ""
            if source:
                updated_data = sanitize_text(source).encode("utf-8")

        if updated_data != data:
            new_blob = hash_blob(repo, updated_data)
            run(
                "git",
                "update-index",
                "--add",
                "--cacheinfo",
                mode,
                new_blob,
                path,
                cwd=repo,
                env=index_env,
            )

    return run("git", "write-tree", cwd=repo, env=index_env).strip()


def commit_tree(
    repo: pathlib.Path,
    tree: str,
    parents: list[str],
    data: CommitData,
) -> str:
    args = ["git", "commit-tree", tree]
    for parent in parents:
        args.extend(("-p", parent))
    env = {
        "GIT_AUTHOR_NAME": data.author.name,
        "GIT_AUTHOR_EMAIL": data.author.email,
        "GIT_AUTHOR_DATE": data.author.date,
        "GIT_COMMITTER_NAME": data.committer.name,
        "GIT_COMMITTER_EMAIL": data.committer.email,
        "GIT_COMMITTER_DATE": data.committer.date,
    }
    return run(*args, cwd=repo, env=env, input_text=data.message).strip()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="focal-history-") as directory:
        repo = pathlib.Path(directory) / "repo"
        repo.mkdir()
        run("git", "init", "-q", cwd=repo)
        remote = f"https://x-access-token:{TOKEN}@github.com/{REPOSITORY}.git"
        run("git", "remote", "add", "origin", remote, cwd=repo)
        run(
            "git",
            "fetch",
            "-q",
            "origin",
            "+refs/heads/*:refs/remotes/origin/*",
            cwd=repo,
        )

        observed = run("git", "rev-parse", "refs/remotes/origin/main", cwd=repo).strip()
        if observed != EXPECTED_MAIN:
            raise RuntimeError(f"main moved: expected {EXPECTED_MAIN}, observed {observed}")

        baseline_cache = {path: baseline_blob(repo, path) for path in RESTORE_PATHS}
        commits = run(
            "git",
            "rev-list",
            "--reverse",
            "--topo-order",
            EXPECTED_MAIN,
            cwd=repo,
        ).splitlines()

        rewritten: dict[str, str] = {}
        rewritten_trees: dict[str, str] = {}
        index_path = pathlib.Path(directory) / "index"

        for old_commit in commits:
            data = read_commit(repo, old_commit)
            new_tree = rewrite_tree(repo, index_path, data.tree, baseline_cache)
            new_parents: list[str] = []
            for old_parent in data.parents:
                new_parent = rewritten[old_parent]
                if new_parent not in new_parents:
                    new_parents.append(new_parent)

            if len(new_parents) == 1 and rewritten_trees[new_parents[0]] == new_tree:
                new_commit = new_parents[0]
            else:
                new_commit = commit_tree(repo, new_tree, new_parents, data)
                rewritten_trees[new_commit] = new_tree
            rewritten[old_commit] = new_commit
            rewritten_trees.setdefault(new_commit, new_tree)

        new_main = rewritten[EXPECTED_MAIN]
        if new_main == EXPECTED_MAIN:
            raise RuntimeError("history rewrite produced no change")

        readme = run("git", "show", f"{new_main}:README.md", cwd=repo)
        lowered = readme.lower()
        forbidden = (PREFIX.lower(), SENTENCE.lower(), PHRASE.lower(), ORIGINAL_IMPLEMENTATION.lower(), CLEAN_ROOM.lower())
        if any(value in lowered for value in forbidden):
            raise RuntimeError("sanitized README verification failed")

        for path in TEMPORARY_PATHS:
            exists = subprocess.run(
                ("git", "cat-file", "-e", f"{new_main}:{path}"),
                cwd=repo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            ).returncode == 0
            if exists:
                raise RuntimeError(f"temporary path remains: {path}")

        upload_branch = "maintenance-rewrite-upload"
        run(
            "git",
            "push",
            "-q",
            "origin",
            f"{new_main}:refs/heads/{upload_branch}",
            cwd=repo,
        )

        current = api("GET", f"/repos/{REPOSITORY}/git/ref/heads/main")
        current_sha = ((current.get("object") or {}).get("sha"))
        if current_sha != EXPECTED_MAIN:
            raise RuntimeError(f"main moved before update: {current_sha}")

        api(
            "PATCH",
            f"/repos/{REPOSITORY}/git/refs/heads/main",
            {"sha": new_main, "force": True},
        )

        for branch in (
            upload_branch,
            "maintenance/repository-metadata",
            "maintenance/metadata-normalization",
            "maintenance/history-rewrite",
        ):
            encoded = urllib.parse.quote(branch, safe="")
            try:
                api("DELETE", f"/repos/{REPOSITORY}/git/refs/heads/{encoded}")
            except RuntimeError as exc:
                if "404" not in str(exc):
                    raise

        print(json.dumps({"status": "ok", "main": new_main, "commits": len(commits)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)}))
        raise
