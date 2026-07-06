"""Handles loading and saving marked dates to JSON file."""

import json
import os
from datetime import datetime

from .daytime import day_of_week_index


def _clamp_level(level: int) -> int:
    return max(0, min(4, level))


def _get_filepath(filename: str) -> str:
    """Resolve filepath: if filename contains '/', use as-is; otherwise prefix with 'schema/'."""
    if "/" in filename:
        return filename
    return f"schema/{filename}"


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

        # Backward-compatible format: ["ISO_DATE", ...]
        if isinstance(data, list) and (not data or isinstance(data[0], str)):
            for date_str in data:
                dt = datetime.fromisoformat(date_str)
                week = min(dt.isocalendar()[1] - 1, 51)
                day = day_of_week_index(dt.year, dt.month, dt.day)
                marked[(week, day)] = 4
            return marked

        # New format: [{"date": "ISO_DATE", "level": N}, ...]
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                date_str = item.get("date")
                if not isinstance(date_str, str):
                    continue
                level = _clamp_level(int(item.get("level", 4)))
                if level <= 0:
                    continue
                dt = datetime.fromisoformat(date_str)
                week = min(dt.isocalendar()[1] - 1, 51)
                day = day_of_week_index(dt.year, dt.month, dt.day)
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
    dates = []
    for (week, day), level in marked.items():
        level = _clamp_level(level)
        if level <= 0:
            continue
        # Convert to date: day_of_week 0=Sun, isocalendar day 1=Mon, 7=Sun
        iso_day = 7 if day == 0 else day
        try:
            dt = datetime.fromisocalendar(year, week + 1, iso_day)
            dates.append({"date": dt.isoformat(), "level": level})
        except:
            pass
    
    filepath = _get_filepath(filename)
    # Create parent directories if they don't exist
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(dates, f)


def load_git_profile(filename: str = "configs.json") -> dict:
    """Loads git profile and app settings from JSON file.
    
    Args:
        filename: Simple filename (stored in schema/) or full path (used as-is)
    
    Returns:
        Dictionary with 'username', 'email', 'token', 'year', and 'path' keys
    """
    filepath = _get_filepath(filename)
    if not os.path.exists(filepath):
        return {
            "username": "",
            "email": "",
            "token": "",
            "year": 2026,
            "path": "data.json",
        }
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        profile_data = data.get("profile", data)
        settings_data = data.get("settings", data)

        year_value = settings_data.get("year", 2026)
        path_value = settings_data.get("path", "data.json")
        try:
            year_value = int(year_value)
        except (TypeError, ValueError):
            year_value = 2026
        if not isinstance(path_value, str) or not path_value.strip():
            path_value = "data.json"
        return {
            "username": profile_data.get("username", ""),
            "email": profile_data.get("email", ""),
            "token": profile_data.get("token", ""),
            "year": year_value,
            "path": path_value,
        }
    except:
        return {
            "username": "",
            "email": "",
            "token": "",
            "year": 2026,
            "path": "data.json",
        }


def save_git_profile(
    username: str,
    email: str,
    token: str = "",
    year: int = 2026,
    path: str = "data.json",
    filename: str = "configs.json",
) -> None:
    """Saves git profile and app settings to JSON file.
    
    Args:
        username: Git username
        email: Git email address
        token: Git access token
        year: Selected matrix year
        path: Selected data file path
        filename: Simple filename (stored in schema/) or full path (used as-is)
    """
    profile = {
        "profile": {
            "username": username.strip(),
            "email": email.strip(),
            "token": token.strip(),
        },
        "settings": {
            "year": int(year),
            "path": path.strip() if isinstance(path, str) and path.strip() else "data.json",
        },
    }
    
    filepath = _get_filepath(filename)
    # Create parent directories if they don't exist
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(profile, f, indent=2)
