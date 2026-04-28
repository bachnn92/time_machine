import random
from datetime import datetime, timedelta
import json
import os

def day_of_week_index(year: int, month: int, day: int) -> int:
    if month < 3:
        month += 12
        year -= 1
    k: int = year % 100
    j: int = year // 100
    h: int = (day + (13*(month + 1)) // 5 + k + k//4 + j//4 + 5*j) % 7
    return (h - 1) % 7

def load_marked_dates(filename: str = "date_data.json") -> set[datetime]:
    if not os.path.exists(filename):
        return set()
    try:
        with open(filename, 'r') as f:
            dates = json.load(f)
        return {datetime.fromisoformat(d) for d in dates}
    except:
        return set()

def save_marked_dates(marked: set[datetime], year: int, filename: str = "date_data.json") -> None:
    # Keep only dates from the selected year
    filtered = {dt for dt in marked if dt.year == year}
    dates = [dt.isoformat() for dt in filtered]
    with open(filename, 'w') as f:
        json.dump(dates, f)

def create_8bit_ui(year: int) -> None:
    try:
        import pygame
        import pygame.font
        pygame.font.init()
    except ImportError:
        print("pygame is required. Install with: pip install pygame")
        return
    
    pygame.init()
    
    # Generate all days for display
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    num_days = (end_date - start_date).days
    
    # Align to full weeks
    first_sunday = start_date - timedelta(days=day_of_week_index(start_date.year, start_date.month, start_date.day))
    last_saturday = end_date + timedelta(days=(6 - day_of_week_index(end_date.year, end_date.month, end_date.day)))
    total_days = (last_saturday - first_sunday).days + 1
    all_days = [first_sunday + timedelta(days=i) for i in range(total_days)]
    
    # UI dimensions
    cell_size = 10
    label_width = 40
    top_padding = 30  # extra space for month labels
    bot_padding = 10
    right_padding = 20
    weeks = total_days // 7
    grid_width = weeks * cell_size
    grid_height = 7 * cell_size
    width = grid_width + label_width + right_padding
    height = grid_height + top_padding + bot_padding
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("8-Bit Commit Matrix")
    
    marked = load_marked_dates()
    
    black = (0, 0, 0)
    green = (0, 255, 0)
    white = (255, 255, 255)
    gray = (100, 100, 100)
    
    font = pygame.font.SysFont('monospace', 12)
    
    dragging = False
    drag_state = True
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_marked_dates(marked, year)
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if x >= label_width and y >= top_padding:
                    week = (x - label_width) // cell_size
                    day = (y - top_padding) // cell_size
                    idx = week * 7 + day
                    if 0 <= idx < len(all_days):
                        pos = all_days[idx]
                        # Only allow marking if the date belongs to the selected year
                        if pos.year == year:
                            if event.button == 1:  # Left click → mark
                                dragging = True
                                drag_state = True
                                marked.add(pos)
                            elif event.button == 3:  # Right click → unmark
                                dragging = True
                                drag_state = False
                                marked.discard(pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 3):
                    dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                x, y = event.pos
                if x >= label_width and y >= top_padding:
                    week = (x - label_width) // cell_size
                    day = (y - top_padding) // cell_size
                    idx = week * 7 + day
                    if 0 <= idx < len(all_days):
                        pos = all_days[idx]
                        if pos.year == year:  # Only mark within year
                            if drag_state:
                                marked.add(pos)
                            else:
                                marked.discard(pos)
        
        screen.fill(black)
        
        # Year label
        year_text = font.render(str(year), True, white)
        screen.blit(year_text, (5, 5))
        
        # Month labels on top
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for idx, dt in enumerate(all_days):
            if dt.day == 1 and dt.year == year:  # first day of month
                week = idx // 7
                text = font.render(months[dt.month - 1], True, white)
                screen.blit(text, (label_width + week * cell_size + 2, top_padding - 15))
        
        # Draw cells
        for idx, dt in enumerate(all_days):
            week = idx // 7
            day = idx % 7
            if dt.year == year:
                color = green if dt in marked else black
            else:
                color = gray
            rect = pygame.Rect(label_width + week * cell_size, top_padding + day * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, color, rect)
        
        # Day labels aligned with matrix rows
        days_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days_labels):
            text = font.render(day, True, white)
            y_offset = (cell_size - font.get_height()) // 2
            screen.blit(text, (5, top_padding + i * cell_size + y_offset))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    year = 2015
    create_8bit_ui(year)
