"""Handles loading and saving marked dates to JSON file."""

import json
import os
from datetime import datetime

from .daytime import day_of_week_index


def _clamp_level(level: int) -> int:
    return max(0, min(4, level))


def _get_filepath(filename: str) -> str:
    """Resolve filepath: if filename contains '/', use as-is; otherwise prefix with 'plan/'."""
    if "/" in filename:
        return filename
    return f"plan/{filename}"


def load_marked_dates(filename: str = "data.json") -> dict[tuple[int, int], int]:
    """Loads marked dates and levels from JSON file.
    
    Args:
        filename: Simple filename (stored in plan/) or full path (used as-is)
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
        filename: Simple filename (stored in plan/) or full path (used as-is)
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
