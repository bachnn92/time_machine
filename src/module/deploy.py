"""Deployment helpers for generating mock git repositories from saved matrix data."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from .data_persistence import load_commit_schedule, load_git_profile, save_marked_dates


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "matrix"


def _build_repo_path(workspace_root: Path, year: int, data_file: str) -> Path:
    repo_root = workspace_root / "mock-repos"
    repo_root.mkdir(exist_ok=True)
    stem = Path(data_file).stem or "data"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return repo_root / f"{year}-{_slugify(stem)}-{timestamp}"


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
    if not user_name or not user_email:
        raise ValueError("Missing git user or email in schema/configs.json")

    save_marked_dates(marked, year, data_file)
    schedule = load_commit_schedule(data_file)
    if not schedule:
        raise ValueError("No marked dates available to deploy")

    root = Path(workspace_root or os.getcwd())
    repo_path = _build_repo_path(root, year, data_file)
    repo_path.mkdir(parents=True, exist_ok=False)

    _run_git(["git", "init"], cwd=repo_path)
    _run_git(["git", "branch", "-m", "main"], cwd=repo_path)
    _run_git(["git", "config", "user.name", user_name], cwd=repo_path)
    _run_git(["git", "config", "user.email", user_email], cwd=repo_path)

    history_file = repo_path / "history.log"
    history_file.write_text("Mock commit history\n", encoding="utf-8")
    _run_git(["git", "add", "history.log"], cwd=repo_path)

    commit_total = 0
    for entry_date, level in schedule:
        for index in range(level):
            commit_total += 1
            commit_time = entry_date.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(minutes=index)
            iso_timestamp = commit_time.isoformat()
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
            _run_git(
                [
                    "git",
                    "commit",
                    "-m",
                    f"mock commit {commit_total} for {entry_date.date().isoformat()} level {level}",
                ],
                cwd=repo_path,
                env=env,
            )

    return repo_path, commit_total