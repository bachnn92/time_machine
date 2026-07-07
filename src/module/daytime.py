from datetime import datetime, timedelta


def day_of_week_index(year: int, month: int, day: int) -> int:
    """Returns the day of the week index for a given date using Zeller's Congruence.
    
    Returns 0 for Sunday, 1 for Monday, ..., 6 for Saturday.
    """
    if month < 3:
        month += 12
        year -= 1
    k: int = year % 100
    j: int = year // 100
    h: int = (day + (13*(month + 1)) // 5 + k + k//4 + j//4 + 5*j) % 7
    # Adjust to 0=Sunday, 6=Saturday
    return (h - 1) % 7


def days_in_year(year: int) -> int:
    """Return day count for a year (365 or 366)."""
    start = datetime(year, 1, 1)
    return 366 if datetime(year + 1, 1, 1) - start == timedelta(days=366) else 365


def year_grid_position(year: int, month: int, day: int) -> tuple[int, int]:
    """Map a date to matrix coordinates in a 7x53 Jan-1-anchored grid.

    Returns (week, day_index) where day_index is 0=Sun .. 6=Sat.
    """
    jan1 = datetime(year, 1, 1)
    first_day_index = day_of_week_index(year, 1, 1)
    day_offset = (datetime(year, month, day) - jan1).days
    cell_index = first_day_index + day_offset
    return (cell_index // 7, cell_index % 7)


def date_from_year_grid_position(year: int, week: int, day_index: int) -> datetime | None:
    """Map matrix coordinates back to a date, or None for out-of-year cells."""
    if not (0 <= week <= 52 and 0 <= day_index <= 6):
        return None

    jan1 = datetime(year, 1, 1)
    first_day_index = day_of_week_index(year, 1, 1)
    day_offset = week * 7 + day_index - first_day_index
    if day_offset < 0 or day_offset >= days_in_year(year):
        return None
    return jan1 + timedelta(days=day_offset)