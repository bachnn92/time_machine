"""Handles loading and saving marked dates to JSON file."""

import json
import os
from datetime import datetime

from .daytime import day_of_week_index

def load_marked_dates(filename: str = "data.json") -> set[tuple[int, int]]:
    """Loads marked dates from JSON file and returns set of (week, day) tuples."""
    if not os.path.exists(f"plan/{filename}"):
        return set()
    try:
        with open(f"plan/{filename}", 'r') as f:
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
    """Saves marked (week, day) positions as dates to JSON file."""
    dates = []
    for week, day in marked:
        # Convert to date: day_of_week 0=Sun, isocalendar day 1=Mon, 7=Sun
        iso_day = 7 if day == 0 else day
        try:
            dt = datetime.fromisocalendar(year, week + 1, iso_day)
            dates.append(dt.isoformat())
        except:
            pass
    with open(f"plan/{filename}", 'w') as f:
        json.dump(dates, f)
