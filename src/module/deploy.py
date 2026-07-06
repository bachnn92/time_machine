"""Deployment helpers for generating mock git repositories from saved matrix data."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from urllib.parse import quote, urlparse, urlunparse
from datetime import datetime, timedelta
from pathlib import Path

from .data_persistence import load_commit_schedule, load_git_profile, save_marked_dates


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "matrix"


def _build_repo_path(workspace_root: Path, year: int, data_file: str) -> Path:
    return workspace_root / "workspace"


def _run_git(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)


def _build_authenticated_url(remote_url: str, login: str, token: str) -> str:
    parsed = urlparse(remote_url)
    if parsed.scheme not in {"http", "https"}:
        return remote_url
    if not token.strip():
        return remote_url
    netloc = parsed.netloc
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]
    auth_user = quote(login.strip() or "oauth2", safe="")
    auth_token = quote(token.strip(), safe="")
    auth_netloc = f"{auth_user}:{auth_token}@{netloc}"
    return urlunparse((parsed.scheme, auth_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def _sanitize_remote_url(remote_url: str) -> str:
    """Return a display-safe remote URL with credentials removed."""
    parsed = urlparse(remote_url)
    if not parsed.scheme:
        return remote_url
    netloc = parsed.netloc
    if "@" in netloc:
        netloc = netloc.split("@", 1)[1]
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def _clean_workspace(repo_path: Path) -> None:
    if repo_path.is_dir():
        shutil.rmtree(repo_path)
    elif repo_path.exists():
        repo_path.unlink()


def deploy_mock_repo(
    marked: dict[tuple[int, int], int],
    year: int,
    data_file: str,
    workspace_root: str | os.PathLike[str] | None = None,
) -> tuple[Path, int]:
    """Create a new mock repository and replay saved matrix dates as commits."""
    profile = load_git_profile()
    user_name = profile.get("user", "").strip()
    user_email = profile.get("email", "").strip()
    debug_mode = bool(profile.get("debug", False))
    if not user_name or not user_email:
        raise ValueError("Missing git user or email in schema/settings.json")

    save_marked_dates(marked, year, data_file)
    schedule = load_commit_schedule(data_file)
    if not schedule:
        raise ValueError("No marked dates available to deploy")

    root = Path(workspace_root or os.getcwd())
    repo_path = _build_repo_path(root, year, data_file)
    _clean_workspace(repo_path)
    repo_path.mkdir(parents=True, exist_ok=True)

    _run_git(["git", "init"], cwd=repo_path)
    _run_git(["git", "branch", "-m", "main"], cwd=repo_path)
    _run_git(["git", "config", "user.name", user_name], cwd=repo_path)
    _run_git(["git", "config", "user.email", user_email], cwd=repo_path)

    history_file: Path | None = None
    if debug_mode:
        history_file = repo_path / "history.log"
        history_file.write_text("Mock commit history\n", encoding="utf-8")
        _run_git(["git", "add", "history.log"], cwd=repo_path)

    commit_total = 0
    for entry_date, level in schedule:
        for index in range(level):
            commit_total += 1
            commit_time = entry_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(minutes=index)
            iso_timestamp = commit_time.isoformat()
            if history_file is not None:
                with history_file.open("a", encoding="utf-8") as handle:
                    handle.write(f"{iso_timestamp} | level={level} | commit={index + 1}\n")
                _run_git(["git", "add", "history.log"], cwd=repo_path)
            env = os.environ.copy()
            env.update(
                {
                    "GIT_AUTHOR_NAME": user_name,
                    "GIT_AUTHOR_EMAIL": user_email,
                    "GIT_COMMITTER_NAME": user_name,
                    "GIT_COMMITTER_EMAIL": user_email,
                    "GIT_AUTHOR_DATE": iso_timestamp,
                    "GIT_COMMITTER_DATE": iso_timestamp,
                }
            )
            commit_command = [
                "git",
                "commit",
                "-m",
                f"mock commit {commit_total} for {entry_date.date().isoformat()} level {level}",
            ]
            if not debug_mode:
                commit_command.insert(2, "--allow-empty")
            _run_git(
                commit_command,
                cwd=repo_path,
                env=env,
            )

    return repo_path, commit_total


def push_workspace_repo(workspace_root: str | os.PathLike[str] | None = None) -> str:
    """Push the workspace repository to the configured remote URL."""
    profile = load_git_profile()
    user_name = profile.get("user", "").strip()
    user_email = profile.get("email", "").strip()
    remote_url = profile.get("url", "").strip()
    token = profile.get("token", "").strip()
    force_push = bool(profile.get("force_push", False))
    if not remote_url:
        raise ValueError("Missing remote URL in schema/settings.json")

    root = Path(workspace_root or os.getcwd())
    repo_path = _build_repo_path(root, 0, "data.json")
    repo_path.mkdir(parents=True, exist_ok=True)
    if not (repo_path / ".git").exists():
        _run_git(["git", "init"], cwd=repo_path)

    if user_name:
        _run_git(["git", "config", "user.name", user_name], cwd=repo_path)
    if user_email:
        _run_git(["git", "config", "user.email", user_email], cwd=repo_path)

    authenticated_url = _build_authenticated_url(remote_url, user_email, token)
    remote_check = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_path,
        check=False,
        capture_output=True,
        text=True,
    )
    if remote_check.returncode == 0:
        _run_git(["git", "remote", "set-url", "origin", authenticated_url], cwd=repo_path)
    else:
        _run_git(["git", "remote", "add", "origin", authenticated_url], cwd=repo_path)
    _run_git(["git", "branch", "-M", "main"], cwd=repo_path)
    push_command = ["git", "push"]
    if force_push:
        push_command.append("--force")
    push_command.extend(["-u", "origin", "main"])
    _run_git(push_command, cwd=repo_path)
    return _sanitize_remote_url(remote_url)


def archive_workspace_repo(workspace_root: str | os.PathLike[str] | None = None) -> Path:
    """Archive the current workspace repository to a zip file."""
    root = Path(workspace_root or os.getcwd())
    repo_path = _build_repo_path(root, 0, "data.json")
    if not repo_path.exists():
        raise ValueError("Workspace repository does not exist")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = root / f"archive_{timestamp}.zip"
    if archive_path.exists():
        archive_path.unlink()

    extra_files = [root / "schema" / "data.json", root / "schema" / "settings.json"]
    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in repo_path.rglob("*"):
            if path.is_file():
                archive.write(path, arcname=path.relative_to(repo_path))
        for path in extra_files:
            if path.is_file():
                archive.write(path, arcname=path.relative_to(root))
    return archive_path