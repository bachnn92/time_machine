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
    """Resolve filepath: absolute paths stay as-is; otherwise prefix with 'schema/'."""
    if os.path.isabs(filename) or "/" in filename or "\\" in filename:
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


def summarize_commit_schedule(filename: str = "data.json") -> tuple[int, int]:
    """Return (entry_count, total_commit_count) based on the saved JSON schedule."""
    schedule = load_commit_schedule(filename)
    return len(schedule), sum(level for _, level in schedule)


def _normalize_coordinate_pair(first: int, second: int, fallback_date: datetime | None = None) -> tuple[int, int] | None:
    """Normalize coordinate pairs to the matrix grid format (week, day)."""
    if not isinstance(first, int) or not isinstance(second, int):
        return None

    if fallback_date is not None:
        expected_week, expected_day = year_grid_position(
            fallback_date.year,
            fallback_date.month,
            fallback_date.day,
        )
        if (first, second) == (expected_week, expected_day):
            return expected_week, expected_day
        if (first, second) == (expected_day, expected_week):
            return expected_week, expected_day
        if (first, second) == (expected_day + 1, expected_week + 1):
            return expected_week, expected_day

    if 0 <= first <= 52 and 0 <= second <= 6:
        return first, second
    if 0 <= first <= 6 and 0 <= second <= 52:
        return second, first
    if 1 <= first <= 7 and 1 <= second <= 53:
        return second - 1, first - 1

    if fallback_date is not None:
        return year_grid_position(fallback_date.year, fallback_date.month, fallback_date.day)
    return None


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
            date_str = item.get("date")
            fallback_date = None
            if isinstance(date_str, str):
                try:
                    fallback_date = datetime.fromisoformat(date_str)
                except ValueError:
                    fallback_date = None

            if isinstance(coordinate_data, dict):
                week = coordinate_data.get("week")
                day = coordinate_data.get("day")
                if isinstance(week, int) and isinstance(day, int):
                    marked[(week, day)] = level
                    continue
            elif isinstance(coordinate_data, list) and len(coordinate_data) == 2:
                normalized = _normalize_coordinate_pair(coordinate_data[0], coordinate_data[1], fallback_date)
                if normalized is not None:
                    week, day = normalized
                    marked[(week, day)] = level
                    continue
            elif isinstance(coordinate_data, str):
                match = re.match(r"\s*\[?\s*(\d+)\s*,\s*(\d+)\s*\]?\s*$", coordinate_data)
                if match:
                    normalized = _normalize_coordinate_pair(
                        int(match.group(1)),
                        int(match.group(2)),
                        fallback_date,
                    )
                    if normalized is not None:
                        week, day = normalized
                        marked[(week, day)] = level
                        continue

            if fallback_date is not None:
                week, day = year_grid_position(fallback_date.year, fallback_date.month, fallback_date.day)
                marked[(week, day)] = level

        return marked
    except:
        return {}


def set_marked_cell_level(marked: dict[tuple[int, int], int], pos: tuple[int, int], level: int, year: int, filename: str = "data.json") -> None:
    """Update a single cell's level and persist the change immediately."""
    normalized_level = _clamp_level(level, max_level=8)
    if normalized_level <= 0:
        marked.pop(pos, None)
    else:
        marked[pos] = normalized_level
    save_marked_dates(marked, year, filename)


def clear_marked_cell(marked: dict[tuple[int, int], int], pos: tuple[int, int], year: int, filename: str = "data.json") -> None:
    """Clear a single cell and persist the change immediately."""
    marked.pop(pos, None)
    save_marked_dates(marked, year, filename)


def load_marked_dates_into(marked: dict[tuple[int, int], int], source_filename: str, year: int, target_filename: str = "data.json") -> dict[tuple[int, int], int]:
    """Load data from another file into the provided mapping and persist it to the target file."""
    loaded = load_marked_dates(source_filename)
    marked.clear()
    marked.update(loaded)
    save_marked_dates(marked, year, target_filename)
    return marked


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
                    "cordinate": f"[{day + 1}, {week + 1}]",
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
