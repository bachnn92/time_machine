"""Handles loading and saving marked dates to JSON file."""

import json
import os
import re
import subprocess
from datetime import datetime

from .daytime import date_from_year_grid_position, year_grid_position


def _clamp_level(level: int, max_level: int = 8) -> int:
    return max(0, min(max_level, level))


def _get_filepath(filename: str) -> str:
    """Resolve filepath: if filename contains '/', use as-is; otherwise prefix with 'schema/'."""
    if "/" in filename:
        return filename
    return f"schema/{filename}"


def _load_git_config_defaults() -> dict[str, str]:
    """Read git user defaults from the current environment, if available."""

    def _read_git_value(key: str) -> str:
        try:
            result = subprocess.run(
                ["git", "config", "--get", key],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return ""
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

    return {
        "user": _read_git_value("user.name"),
        "email": _read_git_value("user.email"),
    }


def _default_git_profile() -> dict:
    git_defaults = _load_git_config_defaults()
    return {
        "user": git_defaults["user"],
        "owner": "",
        "email": git_defaults["email"],
        "token": "",
        "year": 2026,
        "path": "data.json",
        "url": "",
        "force_push": False,
        "debug": False,
        "random": False,
        "drag_lock": False,
        "highlight_year_bounds": False,
        "max_level": 8,
    }


def load_git_config_profile() -> dict[str, str]:
    """Load git identity directly from local git config."""
    return _load_git_config_defaults()


def load_commit_schedule(filename: str = "data.json") -> list[tuple[datetime, int]]:
    """Load saved dates as a sorted commit schedule of (datetime, level)."""
    filepath = _get_filepath(filename)
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        schedule: list[tuple[datetime, int]] = []
        if isinstance(data, list) and (not data or isinstance(data[0], str)):
            for date_str in data:
                schedule.append((datetime.fromisoformat(date_str), 4))
        elif isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                date_str = item.get("date")
                if not isinstance(date_str, str):
                    continue
                try:
                    level = _clamp_level(int(item.get("level", 4)), max_level=8)
                except (TypeError, ValueError):
                    level = 4
                if level <= 0:
                    continue
                schedule.append((datetime.fromisoformat(date_str), level))

        schedule.sort(key=lambda item: item[0])
        return schedule
    except:
        return []


def load_marked_dates(filename: str = "data.json") -> dict[tuple[int, int], int]:
    """Loads marked dates and levels from JSON file.
    
    Args:
        filename: Simple filename (stored in schema/) or full path (used as-is)
    """
    filepath = _get_filepath(filename)
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        marked: dict[tuple[int, int], int] = {}

        if not isinstance(data, list):
            return {}

        for item in data:
            if isinstance(item, str):
                dt = datetime.fromisoformat(item)
                week, day = year_grid_position(dt.year, dt.month, dt.day)
                marked[(week, day)] = 4
                continue

            if not isinstance(item, dict):
                continue

            try:
                level = _clamp_level(int(item.get("level", 4)), max_level=8)
            except (TypeError, ValueError):
                level = 4
            if level <= 0:
                continue

            coordinate_data = item.get("coordinate", item.get("cordinate"))
            if isinstance(coordinate_data, dict):
                week = coordinate_data.get("week")
                day = coordinate_data.get("day")
                if isinstance(week, int) and isinstance(day, int):
                    marked[(week, day)] = level
                    continue
            elif isinstance(coordinate_data, list) and len(coordinate_data) == 2:
                first, second = coordinate_data
                if isinstance(first, int) and isinstance(second, int):
                    if 0 <= first <= 7 and second >= 0:
                        day, week = first, second
                    else:
                        week, day = first, second
                    marked[(week, day)] = level
                    continue
            elif isinstance(coordinate_data, str):
                match = re.match(r"\s*\[?\s*(\d+)\s*,\s*(\d+)\s*\]?\s*$", coordinate_data)
                if match:
                    first = int(match.group(1))
                    second = int(match.group(2))
                    if 0 <= first <= 7 and second >= 0:
                        day, week = first, second
                    else:
                        week, day = first, second
                    marked[(week, day)] = level
                    continue

            date_str = item.get("date")
            if not isinstance(date_str, str):
                continue
            dt = datetime.fromisoformat(date_str)
            week, day = year_grid_position(dt.year, dt.month, dt.day)
            marked[(week, day)] = level

        return marked
    except:
        return {}


def save_marked_dates(marked: dict[tuple[int, int], int], year: int, filename: str = "data.json") -> None:
    """Saves marked (week, day) positions and levels to JSON file.
    
    Args:
        marked: Mapping of (week, day) -> level (1..4)
        year: Year for date conversion
        filename: Simple filename (stored in schema/) or full path (used as-is)
    """
    entries: list[tuple[datetime, dict[str, object]]] = []
    for (week, day), level in marked.items():
        level = _clamp_level(level, max_level=8)
        if level <= 0:
            continue
        dt = date_from_year_grid_position(year, week, day)
        if dt is None:
            continue
        entries.append(
            (
                datetime(dt.year, dt.month, dt.day),
                {
                    "cordinate": f"[{day}, {week}]",
                    "date": dt.isoformat(),
                    "level": level,
                },
            )
        )
    entries.sort(key=lambda item: item[0])
    dates = [entry for _, entry in entries]
    
    filepath = _get_filepath(filename)
    # Create parent directories if they don't exist
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("[\n")
        for index, entry in enumerate(dates):
            suffix = "," if index < len(dates) - 1 else ""
            f.write(f"  {json.dumps(entry, ensure_ascii=False)}{suffix}\n")
        f.write("]\n")


def load_git_profile(filename: str = "settings.json") -> dict:
    """Loads git profile and app settings from JSON file.
    
    Args:
        filename: Simple filename (stored in schema/) or full path (used as-is)
    
    Returns:
        Dictionary with user/profile values and settings fields
    """
    filepath = _get_filepath(filename)
    # Backward compatibility: transparently read legacy configs.json.
    if filename == "settings.json" and not os.path.exists(filepath):
        legacy_filepath = _get_filepath("configs.json")
        if os.path.exists(legacy_filepath):
            filepath = legacy_filepath
    defaults = _default_git_profile()
    if not os.path.exists(filepath):
        return defaults
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        profile_data = data.get("profile", data)
        settings_data = data.get("cofiguration", data.get("settings", data))

        year_value = settings_data.get("year", 2026)
        path_value = settings_data.get("path", "data.json")
        url_value = profile_data.get("url", settings_data.get("url", ""))
        force_push_value = settings_data.get("force_push", False)
        debug_value = settings_data.get("debug", False)
        random_value = settings_data.get("random", False)
        drag_lock_value = settings_data.get("drag_lock", False)
        highlight_year_bounds_value = settings_data.get("highlight_year_bounds", False)
        max_level_value = settings_data.get("max_level", 8)
        try:
            year_value = int(year_value)
        except (TypeError, ValueError):
            year_value = defaults["year"]
        if not isinstance(path_value, str) or not path_value.strip():
            path_value = defaults["path"]
        if not isinstance(url_value, str):
            url_value = defaults["url"]
        user_value = profile_data.get("user", profile_data.get("username", ""))
        owner_value = profile_data.get("owner", "")
        email_value = profile_data.get("email", "")
        return {
            "user": user_value.strip() if isinstance(user_value, str) and user_value.strip() else defaults["user"],
            "owner": owner_value.strip() if isinstance(owner_value, str) else defaults["owner"],
            "email": email_value.strip() if isinstance(email_value, str) and email_value.strip() else defaults["email"],
            "token": profile_data.get("token", ""),
            "year": year_value,
            "path": path_value,
            "url": url_value.strip() if isinstance(url_value, str) else defaults["url"],
            "force_push": bool(force_push_value),
            "debug": bool(debug_value),
            "random": bool(random_value),
            "drag_lock": bool(drag_lock_value),
            "highlight_year_bounds": bool(highlight_year_bounds_value),
            "max_level": int(max_level_value) if isinstance(max_level_value, (int, str)) else 8,
        }
    except:
        return defaults


def save_git_profile(
    user: str,
    email: str,
    token: str = "",
    owner: str = "",
    year: int = 2026,
    path: str = "data.json",
    url: str = "",
    force_push: bool = False,
    debug: bool = False,
    random: bool = False,
    drag_lock: bool = False,
    highlight_year_bounds: bool = False,
    max_level: int = 8,
    filename: str = "settings.json",
) -> None:
    """Saves git profile and app settings to JSON file.
    
    Args:
        user: Git user name
        email: Git email address
        token: Git access token
        year: Selected matrix year
        path: Selected data file path
        filename: Simple filename (stored in schema/) or full path (used as-is)
    """
    profile = {
        "profile": {
            "user": user.strip(),
            "owner": owner.strip(),
            "email": email.strip(),
            "token": token.strip(),
            "url": url.strip() if isinstance(url, str) and url.strip() else "",
        },
        "cofiguration": {
            "year": int(year),
            "path": path.strip() if isinstance(path, str) and path.strip() else "data.json",
            "force_push": bool(force_push),
            "debug": bool(debug),
            "random": bool(random),
            "drag_lock": bool(drag_lock),
            "highlight_year_bounds": bool(highlight_year_bounds),
            "max_level": int(max_level),
        },
    }
    
    filepath = _get_filepath(filename)
    # Create parent directories if they don't exist
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(profile, f, indent=2)
