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

def load_marked_dates(filename: str = "date_data.json") -> dict[datetime, int]:
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return {datetime.fromisoformat(d["date"]): d["level"] for d in data}
    except:
        return {}

def save_marked_dates(marked: dict[datetime, int], year: int, filename: str = "date_data.json") -> None:
    filtered = [{"date": dt.isoformat(), "level": lvl}
                for dt, lvl in marked.items() if dt.year == year]
    with open(filename, 'w') as f:
        json.dump(filtered, f)

def create_8bit_ui(year: int) -> None:
    try:
        import pygame
        import pygame.font
        pygame.font.init()
    except ImportError:
        print("pygame is required. Install with: pip install pygame")
        return
    
    pygame.init()
    
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    first_sunday = start_date - timedelta(days=day_of_week_index(start_date.year, start_date.month, start_date.day))
    last_saturday = end_date + timedelta(days=(6 - day_of_week_index(end_date.year, end_date.month, end_date.day)))
    total_days = (last_saturday - first_sunday).days + 1
    all_days = [first_sunday + timedelta(days=i) for i in range(total_days)]
    
    cell_size = 10
    label_width = 40
    top_padding = 30
    bot_padding = 70
    right_padding = 20
    weeks = total_days // 7
    grid_width = weeks * cell_size
    grid_height = 7 * cell_size
    width = grid_width + label_width + right_padding
    height = grid_height + top_padding + bot_padding
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("8-Bit Commit Matrix (4-Level Green)")
    
    marked = load_marked_dates()
    
    black = (0, 0, 0)
    white = (255, 255, 255)
    gray = (100, 100, 100)
    line_gray = (60, 60, 60)  # subtle grid lines
    
    green_levels = {
        1: (0, 100, 0),
        2: (0, 160, 0),
        3: (0, 200, 0),
        4: (0, 255, 0),
    }
    
    font = pygame.font.SysFont('monospace', 12)
    
    # Buttons
    new_text = font.render("New", True, white)
    exit_text = font.render("Exit", True, white)
    draw_text = font.render("Draw Mode", True, white)
    new_rect = new_text.get_rect(midleft=(width//2 - 100, height - 25))
    exit_rect = exit_text.get_rect(midleft=(width//2, height - 25))
    draw_rect = draw_text.get_rect(midleft=(width//2 + 100, height - 25))
    
    draw_mode = False
    dragging = False
    drag_clean = False
    visited_cells = set()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_marked_dates(marked, year)
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Buttons first
                if new_rect.collidepoint(x, y):
                    marked = {dt: lvl for dt, lvl in marked.items() if dt.year != year}
                    continue
                elif exit_rect.collidepoint(x, y):
                    save_marked_dates(marked, year)
                    running = False
                    continue
                elif draw_rect.collidepoint(x, y):
                    draw_mode = not draw_mode
                    continue
                # Grid clicks
                if x >= label_width and y >= top_padding and y < top_padding + grid_height:
                    week = (x - label_width) // cell_size
                    day = (y - top_padding) // cell_size
                    idx = week * 7 + day
                    if 0 <= idx < len(all_days):
                        pos = all_days[idx]
                        if pos.year == year:
                            if event.button == 1:
                                current = marked.get(pos, 0)
                                if current < 4:
                                    marked[pos] = current + 1
                                if draw_mode:
                                    dragging = True
                                    drag_clean = False
                                    visited_cells = {pos}
                            elif event.button == 3:
                                if pos in marked:
                                    del marked[pos]
                                if draw_mode:
                                    dragging = True
                                    drag_clean = True
                                    visited_cells = {pos}
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                visited_cells.clear()
            elif event.type == pygame.MOUSEMOTION and dragging and draw_mode:
                x, y = event.pos
                if x >= label_width and y >= top_padding and y < top_padding + grid_height:
                    week = (x - label_width) // cell_size
                    day = (y - top_padding) // cell_size
                    idx = week * 7 + day
                    if 0 <= idx < len(all_days):
                        pos = all_days[idx]
                        if pos.year == year and pos not in visited_cells:
                            if not drag_clean:  # draw
                                current = marked.get(pos, 0)
                                if current < 4:
                                    marked[pos] = current + 1
                            else:  # clean
                                if pos in marked:
                                    del marked[pos]
                            visited_cells.add(pos)
        
        screen.fill(black)
        
        # Year label
        year_text = font.render(str(year), True, white)
        screen.blit(year_text, (5, 5))
        
        # Month labels
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for idx, dt in enumerate(all_days):
            if dt.day == 1 and dt.year == year:
                week = idx // 7
                text = font.render(months[dt.month - 1], True, white)
                screen.blit(text, (label_width + week * cell_size + 2, top_padding - 15))
        
        # Draw cells with subtle grid lines
        for idx, dt in enumerate(all_days):
            week = idx // 7
            day = idx % 7
            if dt.year == year:
                level = marked.get(dt, 0)
                color = green_levels.get(level, black)
            else:
                color = gray
            rect = pygame.Rect(label_width + week * cell_size, top_padding + day * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, line_gray, rect, 1)  # subtle grid line
        
        # Day labels aligned
        days_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days_labels):
            text = font.render(day, True, white)
            y_offset = (cell_size - font.get_height()) // 2
            screen.blit(text, (5, top_padding + i * cell_size + y_offset))
        
        # Draw buttons
        pygame.draw.rect(screen, gray, new_rect.inflate(20, 10))
        pygame.draw.rect(screen, gray, exit_rect.inflate(20, 10))
        pygame.draw.rect(screen, (0,200,0) if draw_mode else gray, draw_rect.inflate(30, 10))
        screen.blit(new_text, new_rect)
        screen.blit(exit_text, exit_rect)
        screen.blit(draw_text, draw_rect)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    year = 2016
    create_8bit_ui(year)
