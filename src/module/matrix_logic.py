"""Core matrix generation logic for commit tracking."""

from datetime import datetime, timedelta

from .daytime import days_in_year, year_grid_position
from .random import random_binary
import random


def generate_commit_matrix(year: int) -> list[list[int]]:
    """Generates a 7x53 matrix of commits per day of week per week of the year.
    
    Rows: 0=Sunday, 1=Monday, ..., 6=Saturday
    Columns: weeks 0 to 52 (approximately weeks of the year)
    """
    start_date = datetime(year, 1, 1)
    num_days = days_in_year(year)
    matrix = [[0 for _ in range(53)] for _ in range(7)]
    
    for day_offset in range(num_days):
        current = start_date + timedelta(days=day_offset)
        week, day_of_week = year_grid_position(current.year, current.month, current.day)
        
        # Determine commit count based on day
        if day_of_week in [0, 6]:  # Weekend: Sun and Sat
            rate, range_val = 0.2, 3
        else:  # Weekday
            rate, range_val = 0.8, 9
        
        commits = 0
        if random_binary(rate):
            commits = random.randint(1, range_val)
        
        matrix[day_of_week][week] += commits
    
    return matrix


def generate_random_marked_dates(
    year: int,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    max_level: int = 8,
) -> dict[tuple[int, int], int]:
    """Generate random marked dates across an inclusive date range."""
    range_start = start_date or datetime(year, 1, 1)
    range_end = end_date or datetime(year, 12, 31)
    if range_end < range_start:
        raise ValueError("end_date must be on or after start_date")

    marked: dict[tuple[int, int], int] = {}
    current = range_start
    while current <= range_end:
        if current.year != year:
            current += timedelta(days=1)
            continue

        week, day_of_week = year_grid_position(current.year, current.month, current.day)
        rate = 0.2 if day_of_week in [0, 6] else 0.8

        if random_binary(rate):
            marked[(week, day_of_week)] = random.randint(1, max_level)

        current += timedelta(days=1)

    return marked
