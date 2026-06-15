
"""Pygame-based UI for the 8-bit commit matrix editor."""

from .module.data_persistence import load_marked_dates, save_marked_dates
from .module.matrix_logic import generate_commit_matrix
from .module.visualization import plot_matrix


def run_app(year: int = 2015, filename: str = "data.json") -> None:
    """Runs the complete app (settings + matrix editor) in a single pygame window.
    
    Args:
        year: Default year for the matrix
        filename: Default JSON file name or path
    """
    try:
        import pygame
        import pygame.font
        pygame.font.init()
    except ImportError:
        print("pygame is required. Install with: pip install pygame")
        return
    
    pygame.init()
    
    # Screen setup
    screen_width, screen_height = 760, 420
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Time Machine")
    
    # Colors
    black = (0, 0, 0)
    white = (255, 255, 255)
    green = (0, 255, 0)
    gray = (100, 100, 100)
    dark_gray = (50, 50, 50)
    cell_border = (35, 35, 35)
    
    # Fonts
    font = pygame.font.SysFont('monospace', 16)
    small_font = pygame.font.SysFont('monospace', 12)
    
    # State machine
    STATE_SETTINGS = 0
    STATE_MATRIX = 1
    state = STATE_SETTINGS
    
    # Settings state variables
    year_text = str(year)
    file_text = filename
    active_field = None

    settings_panel_width = 560
    settings_panel_height = 280
    settings_panel_x = (screen_width - settings_panel_width) // 2
    settings_panel_y = (screen_height - settings_panel_height) // 2
    label_x = settings_panel_x + 40
    field_x = settings_panel_x + 120
    year_field_rect = pygame.Rect(field_x, settings_panel_y + 70, 350, 35)
    file_field_rect = pygame.Rect(field_x, settings_panel_y + 140, 350, 35)
    start_button_rect = pygame.Rect(settings_panel_x + (settings_panel_width - 200) // 2, settings_panel_y + 210, 200, 50)
    
    # Matrix state variables
    matrix = None
    marked: dict[tuple[int, int], int] = {}
    cell_size = 10
    label_width = 40
    label_height = 20
    button_width = 120
    button_height = 28
    button_gap = 8
    button_x = screen_width - button_width - 12
    bottom_margin = 46
    new_button_y = screen_height - (button_height * 4 + button_gap * 3 + bottom_margin)
    new_button_rect = pygame.Rect(button_x, new_button_y, button_width, button_height)
    default_button_rect = pygame.Rect(button_x, new_button_y + button_height + button_gap, button_width, button_height)
    settings_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 2, button_width, button_height)
    exit_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 3, button_width, button_height)
    level_colors = [
        (20, 20, 20),
        (0, 70, 0),
        (0, 110, 0),
        (0, 160, 0),
        (0, 220, 0),
    ]

    drag_left_active = False
    drag_right_active = False
    drag_last_cell: tuple[int, int] | None = None
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if state == STATE_SETTINGS:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pos = event.pos
                        if year_field_rect.collidepoint(pos):
                            active_field = 0
                        elif file_field_rect.collidepoint(pos):
                            active_field = 1
                        elif start_button_rect.collidepoint(pos):
                            try:
                                year = int(year_text)
                                # Generate matrix and load marked dates
                                matrix = generate_commit_matrix(year)
                                marked = load_marked_dates(file_text)
                                state = STATE_MATRIX
                            except ValueError:
                                year_text = str(year)
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        active_field = 1 - active_field if active_field is not None else 0
                    elif event.key == pygame.K_RETURN and active_field is not None:
                        try:
                            year = int(year_text)
                            matrix = generate_commit_matrix(year)
                            marked = load_marked_dates(file_text)
                            state = STATE_MATRIX
                        except ValueError:
                            year_text = str(year)
                    elif active_field == 0:
                        if event.key == pygame.K_BACKSPACE:
                            year_text = year_text[:-1] if year_text else year_text
                        elif event.unicode.isdigit():
                            if len(year_text) < 4:
                                year_text += event.unicode
                    elif active_field == 1:
                        if event.key == pygame.K_BACKSPACE:
                            file_text = file_text[:-1] if file_text else file_text
                        elif event.unicode.isprintable():
                            if len(file_text) < 100:
                                file_text += event.unicode
            
            elif state == STATE_MATRIX:
                grid_width = 52 * cell_size
                grid_height = 7 * cell_size
                matrix_width = label_width + grid_width
                matrix_height = label_height + grid_height
                matrix_x = max((screen_width - matrix_width) // 2, 0)
                matrix_y = max((screen_height - matrix_height) // 3, 0)
                grid_x = matrix_x + label_width
                grid_y = matrix_y + label_height

                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if event.button == 1:
                        if new_button_rect.collidepoint((x, y)):
                            marked.clear()
                            save_marked_dates(marked, year, file_text)
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif default_button_rect.collidepoint((x, y)):
                            marked = load_marked_dates("default-data.json")
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif exit_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, file_text)
                            running = False
                        elif settings_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, file_text)
                            state = STATE_SETTINGS
                            year_text = str(year)
                            active_field = None
                        elif grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                            week = (x - grid_x) // cell_size
                            day = (y - grid_y) // cell_size
                            if 0 <= week < 52 and 0 <= day < 7:
                                pos = (week, day)
                                new_level = min(marked.get(pos, 0) + 1, 4)
                                marked[pos] = new_level
                                drag_left_active = True
                                drag_last_cell = pos
                    elif event.button == 3:
                        if grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                            week = (x - grid_x) // cell_size
                            day = (y - grid_y) // cell_size
                            if 0 <= week < 52 and 0 <= day < 7:
                                pos = (week, day)
                                marked.pop(pos, None)
                                drag_right_active = True
                                drag_last_cell = pos
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        drag_left_active = False
                    elif event.button == 3:
                        drag_right_active = False
                    if not drag_left_active and not drag_right_active:
                        drag_last_cell = None
                elif event.type == pygame.MOUSEMOTION:
                    if not (drag_left_active or drag_right_active):
                        continue
                    x, y = event.pos
                    if grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                        week = (x - grid_x) // cell_size
                        day = (y - grid_y) // cell_size
                        if 0 <= week < 52 and 0 <= day < 7:
                            pos = (week, day)
                            if pos != drag_last_cell:
                                if drag_left_active:
                                    marked[pos] = min(marked.get(pos, 0) + 1, 4)
                                elif drag_right_active:
                                    marked.pop(pos, None)
                                drag_last_cell = pos
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Save and return to settings
                        save_marked_dates(marked, year, file_text)
                        state = STATE_SETTINGS
                        year_text = str(year)
                        file_text = filename
                        active_field = None
                        drag_left_active = False
                        drag_right_active = False
                        drag_last_cell = None
        
        screen.fill(black)
        
        if state == STATE_SETTINGS:
            # Draw settings screen
            title = font.render("Time Machine Settings", True, green)
            title_rect = title.get_rect(center=(screen_width // 2, settings_panel_y + 20))
            screen.blit(title, title_rect)
            
            year_label = small_font.render("Year:", True, white)
            screen.blit(year_label, (label_x, year_field_rect.y + 13))
            year_field_color = green if active_field == 0 else gray
            pygame.draw.rect(screen, year_field_color, year_field_rect, 2)
            year_display = small_font.render(year_text, True, white)
            screen.blit(year_display, (year_field_rect.x + 10, year_field_rect.y + 13))
            
            file_label = small_font.render("File:", True, white)
            screen.blit(file_label, (label_x, file_field_rect.y + 13))
            file_field_color = green if active_field == 1 else gray
            pygame.draw.rect(screen, file_field_color, file_field_rect, 2)
            file_display = small_font.render(file_text[-30:], True, white)
            screen.blit(file_display, (file_field_rect.x + 10, file_field_rect.y + 13))
            
            button_color = green if start_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, button_color, start_button_rect, 2)
            start_text = font.render("START", True, button_color)
            start_rect = start_text.get_rect(center=start_button_rect.center)
            screen.blit(start_text, start_rect)
            
            instructions = small_font.render("Click/Tab to switch | Enter/Click START to begin", True, dark_gray)
            instructions_rect = instructions.get_rect(center=(screen_width // 2, screen_height - 12))
            screen.blit(instructions, instructions_rect)
        
        elif state == STATE_MATRIX:
            # Draw matrix screen
            grid_width = 52 * cell_size
            grid_height = 7 * cell_size
            matrix_width = label_width + grid_width
            matrix_height = label_height + grid_height
            matrix_x = max((screen_width - matrix_width) // 2, 0)
            matrix_y = max((screen_height - matrix_height) // 3, 0)
            grid_x = matrix_x + label_width
            grid_y = matrix_y + label_height
            
            # Draw cells
            for day in range(7):
                for week in range(52):
                    level = marked.get((week, day), 0)
                    color = level_colors[level]
                    rect = pygame.Rect(grid_x + week * cell_size, grid_y + day * cell_size, cell_size, cell_size)
                    pygame.draw.rect(screen, color, rect)
                    pygame.draw.rect(screen, cell_border, rect, 1)
            
            # Draw labels
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            for i, day in enumerate(days):
                text = small_font.render(day, True, white)
                screen.blit(text, (matrix_x + 5, grid_y + i * cell_size + 2))
            
            for week in range(0, 52, 4):
                text = small_font.render(str(week), True, white)
                screen.blit(text, (grid_x + week * cell_size + 2, matrix_y + 5))
            
            # Title and instructions
            title = font.render(f"Time Machine - Matrix", True, green)
            title_rect = title.get_rect(center=(screen_width // 2, 15))
            screen.blit(title, title_rect)

            # Settings button
            new_button_color = green if new_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, new_button_color, new_button_rect, 2)
            new_text = small_font.render("NEW", True, new_button_color)
            new_text_rect = new_text.get_rect(center=new_button_rect.center)
            screen.blit(new_text, new_text_rect)

            default_button_color = green if default_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, default_button_color, default_button_rect, 2)
            default_text = small_font.render("DEFAULT", True, default_button_color)
            default_text_rect = default_text.get_rect(center=default_button_rect.center)
            screen.blit(default_text, default_text_rect)

            settings_button_color = green if settings_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, settings_button_color, settings_button_rect, 2)
            settings_text = small_font.render("SETTINGS", True, settings_button_color)
            settings_text_rect = settings_text.get_rect(center=settings_button_rect.center)
            screen.blit(settings_text, settings_text_rect)

            exit_button_color = green if exit_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, exit_button_color, exit_button_rect, 2)
            exit_text = small_font.render("EXIT", True, exit_button_color)
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            screen.blit(exit_text, exit_text_rect)
            
            instructions = small_font.render("Left drag:+level | Right drag:erase | DEFAULT restores default-data.json", True, dark_gray)
            instructions_rect = instructions.get_rect(center=(screen_width // 2, screen_height - 12))
            screen.blit(instructions, instructions_rect)
        
        pygame.display.flip()
        clock.tick(30)
    
    # Save on exit
    if state == STATE_MATRIX and matrix is not None:
        save_marked_dates(marked, year, file_text)
    
    pygame.quit()


