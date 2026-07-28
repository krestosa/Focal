from __future__ import annotations

import json
import os
import pathlib
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request


REPOSITORY = os.environ["REPOSITORY"]
TOKEN = os.environ["GH_TOKEN"]
EXPECTED_MAIN = os.environ["EXPECTED_MAIN"]


def run(*args: str, cwd: pathlib.Path, input_text: str | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        details = completed.stderr.strip() or completed.stdout.strip()
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


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="focal-readme-") as directory:
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
        run("git", "checkout", "-q", "-B", "main", "refs/remotes/origin/main", cwd=repo)

        filter_script = pathlib.Path(directory) / "normalize.py"
        filter_script.write_text(
            "from pathlib import Path\n"
            "path = Path('README.md')\n"
            "if path.is_file():\n"
            "    source = path.read_text(encoding='utf-8')\n"
            "    updated = source.replace('Focal is an shader pack project', 'Focal is a shader pack project')\n"
            "    if updated != source:\n"
            "        path.write_text(updated, encoding='utf-8')\n",
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["FILTER_BRANCH_SQUELCH_WARNING"] = "1"
        completed = subprocess.run(
            (
                "git",
                "filter-branch",
                "--force",
                "--prune-empty",
                "--tree-filter",
                f"python {filter_script}",
                "--",
                "main",
            ),
            cwd=repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(f"history rewrite failed: {details[-4000:]}")

        rewritten_main = run("git", "rev-parse", "main", cwd=repo).strip()
        if rewritten_main == EXPECTED_MAIN:
            raise RuntimeError("history rewrite produced no change")
        readme = run("git", "show", f"{rewritten_main}:README.md", cwd=repo)
        if "Focal is a shader pack project" not in readme:
            raise RuntimeError("README verification failed")
        if "Focal is an shader pack project" in readme:
            raise RuntimeError("obsolete README wording remains")

        upload_branch = "maintenance-readme-upload"
        run(
            "git",
            "push",
            "-q",
            "origin",
            f"{rewritten_main}:refs/heads/{upload_branch}",
            cwd=repo,
        )

        current = api("GET", f"/repos/{REPOSITORY}/git/ref/heads/main")
        current_sha = ((current.get("object") or {}).get("sha"))
        if current_sha != EXPECTED_MAIN:
            raise RuntimeError(f"main moved before update: {current_sha}")
        api(
            "PATCH",
            f"/repos/{REPOSITORY}/git/refs/heads/main",
            {"sha": rewritten_main, "force": True},
        )

        for branch in (upload_branch, "maintenance/readme-normalization"):
            encoded = urllib.parse.quote(branch, safe="")
            try:
                api("DELETE", f"/repos/{REPOSITORY}/git/refs/heads/{encoded}")
            except RuntimeError as exc:
                if "404" not in str(exc):
                    raise

        print(json.dumps({"status": "ok", "main": rewritten_main}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "error", "type": type(exc).__name__, "message": str(exc)}))
        raise
