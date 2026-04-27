import random
from datetime import datetime, timedelta
import json
import os

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

def random_binary(probability_of_1: float) -> int:
    """Returns 1 with given probability, 0 otherwise."""
    return 1 if random.random() < probability_of_1 else 0

def load_marked_dates(filename: str = "date_data.json") -> set[tuple[int, int]]:
    """Loads marked dates from JSON file and returns set of (week, day) tuples."""
    if not os.path.exists(filename):
        return set()
    try:
        with open(filename, 'r') as f:
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

def save_marked_dates(marked: set[tuple[int, int]], year: int, filename: str = "date_data.json") -> None:
    """Saves marked (week, day) positions as dates to JSON file."""
    dates = []
    for week, day in marked:
        # Convert to date: day_of_week 0=Sun, isocalendar day 1=Mon, 7=Sun
        iso_day = (day + 1) % 7 + 1  # 0->1 (Mon? Wait no
        # day 0=Sun -> iso_day 7
        # day 1=Mon -> 1
        # ...
        # day 6=Sat -> 6
        iso_day = 7 if day == 0 else day
        try:
            dt = datetime.fromisocalendar(year, week + 1, iso_day)
            dates.append(dt.isoformat())
        except:
            pass
    with open(filename, 'w') as f:
        json.dump(dates, f)

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

def plot_matrix(matrix: list[list[int]]) -> None:
    """Plots the commit matrix as a heatmap using matplotlib."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib and numpy are required for plotting. Install with: pip install matplotlib numpy")
        return
    
    # Convert to numpy array for easier plotting
    data = np.array(matrix)
    
    plt.figure(figsize=(12, 2))
    plt.imshow(data, cmap='Greens', aspect='auto')
    plt.colorbar(label='Commits')
    plt.title('Commit Activity Heatmap')
    plt.xlabel('Week of Year')
    plt.ylabel('Day of Week')
    plt.yticks(range(7), ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"])
    plt.xticks(range(0, 52, 4), range(1, 53, 4))  # Show every 4th week
    plt.show()

def create_8bit_ui(matrix: list[list[int]], year: int) -> None:
    """Creates an 8-bit style UI using Pygame to display the commit matrix."""
    try:
        import pygame
        import pygame.font
        pygame.font.init()
    except ImportError:
        print("pygame is required for the 8-bit UI. Install with: pip install pygame")
        return
    
    pygame.init()
    
    # Dimensions: 52 weeks * 10px, 7 days * 10px, plus space for labels
    cell_size = 10
    label_width = 40
    label_height = 20
    width = 52 * cell_size + label_width
    height = 7 * cell_size + label_height
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("8-Bit Commit Matrix")
    
    # Load marked dates
    marked = load_marked_dates()
    
    # Colors
    black = (0, 0, 0)
    green = (0, 255, 0)
    white = (255, 255, 255)
    
    # Font
    font = pygame.font.SysFont('monospace', 12)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_marked_dates(marked, year)
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    x, y = event.pos
                    # Adjust for labels
                    if x >= label_width and y >= label_height:
                        week = (x - label_width) // cell_size
                        day = (y - label_height) // cell_size
                        if 0 <= week < 52 and 0 <= day < 7:
                            pos = (week, day)
                            if pos in marked:
                                marked.remove(pos)
                            else:
                                marked.add(pos)
        
        screen.fill(black)
        
        # Draw grid lines
        for i in range(8):  # 7 days + 1
            pygame.draw.line(screen, green, (label_width, label_height + i * cell_size), (width, label_height + i * cell_size))
        for i in range(53):  # 52 weeks + 1
            pygame.draw.line(screen, green, (label_width + i * cell_size, label_height), (label_width + i * cell_size, height))
        
        # Draw cells
        for day in range(7):
            for week in range(52):
                color = green if (week, day) in marked else black
                rect = pygame.Rect(label_width + week * cell_size, label_height + day * cell_size, cell_size, cell_size)
                pygame.draw.rect(screen, color, rect)
        
        # Draw labels
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days):
            text = font.render(day, True, white)
            screen.blit(text, (5, label_height + i * cell_size + 2))
        
        for week in range(0, 52, 4):  # Every 4 weeks
            text = font.render(str(week), True, white)
            screen.blit(text, (label_width + week * cell_size + 2, 5))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    # Example usage
    year = 2020
    matrix = generate_commit_matrix(year)
    create_8bit_ui(matrix, year)