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