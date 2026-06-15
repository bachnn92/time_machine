"""Core matrix generation logic for commit tracking."""

from datetime import datetime, timedelta

from .daytime import day_of_week_index
from .random import random_binary
import random


def generate_commit_matrix(year: int) -> list[list[int]]:
    """Generates a 7x52 matrix of commits per day of week per week of the year.
    
    Rows: 0=Sunday, 1=Monday, ..., 6=Saturday
    Columns: weeks 0 to 51 (approximately weeks of the year)
    """
    start_date = datetime(year, 1, 1)
    num_days = 366 if start_date.replace(year=year+1, month=1, day=1) - start_date == timedelta(days=366) else 365
    matrix = [[0 for _ in range(52)] for _ in range(7)]
    
    for i in range(num_days):
        current = start_date + timedelta(days=i)
        day_of_week = day_of_week_index(current.year, current.month, current.day)
        # Get week of year (1-53), but cap at 52
        week = min(current.isocalendar()[1] - 1, 51)  # 0-based, max 51
        
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
