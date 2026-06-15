"""Handles loading and saving marked dates to JSON file."""

import json
import os
from datetime import datetime

from .daytime import day_of_week_index


def _get_filepath(filename: str) -> str:
    """Resolve filepath: if filename contains '/', use as-is; otherwise prefix with 'plan/'."""
    if "/" in filename:
        return filename
    return f"plan/{filename}"


def load_marked_dates(filename: str = "data.json") -> set[tuple[int, int]]:
    """Loads marked dates from JSON file and returns set of (week, day) tuples.
    
    Args:
        filename: Simple filename (stored in plan/) or full path (used as-is)
    """
    filepath = _get_filepath(filename)
    if not os.path.exists(filepath):
        return set()
    try:
        with open(filepath, 'r') as f:
            dates = json.load(f)
        marked = set()
        for date_str in dates:
            dt = datetime.fromisoformat(date_str)
            week = min(dt.isocalendar()[1] - 1, 51)
            day = day_of_week_index(dt.year, dt.month, dt.day)
            marked.add((week, day))
        return marked
    except:
        return set()


def save_marked_dates(marked: set[tuple[int, int]], year: int, filename: str = "data.json") -> None:
    """Saves marked (week, day) positions as dates to JSON file.
    
    Args:
        marked: Set of (week, day) tuples to save
        year: Year for date conversion
        filename: Simple filename (stored in plan/) or full path (used as-is)
    """
    dates = []
    for week, day in marked:
        # Convert to date: day_of_week 0=Sun, isocalendar day 1=Mon, 7=Sun
        iso_day = 7 if day == 0 else day
        try:
            dt = datetime.fromisocalendar(year, week + 1, iso_day)
            dates.append(dt.isoformat())
        except:
            pass
    
    filepath = _get_filepath(filename)
    # Create parent directories if they don't exist
    dirpath = os.path.dirname(filepath)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(dates, f)
