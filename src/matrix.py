
"""Pygame-based UI for the 8-bit commit matrix editor."""

from .module.data_persistence import (
    load_marked_dates, save_marked_dates,
    load_git_config_profile, load_git_profile, save_git_profile
)
from .module.deploy import deploy_mock_repo
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
    pygame.key.set_repeat(350, 40)
    
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
    state = STATE_MATRIX

    default_year = 2026
    default_path = "data.json"
    
    # Settings state variables
    git_profile = load_git_profile()
    applied_year = git_profile.get("year", year)
    applied_file = git_profile.get("path", filename)
    if not isinstance(applied_file, str) or not applied_file.strip():
        applied_file = filename
    try:
        applied_year = int(applied_year)
    except (TypeError, ValueError):
        applied_year = year
    year = applied_year
    year_text = str(applied_year)
    file_text = applied_file
    user_text = git_profile.get("user", git_profile.get("username", ""))
    email_text = git_profile.get("email", "")
    token_text = git_profile.get("token", "")
    active_field = None

    settings_panel_width = 560
    settings_panel_height = 400
    settings_panel_x = (screen_width - settings_panel_width) // 2
    settings_panel_y = (screen_height - settings_panel_height) // 2
    label_x = settings_panel_x + 40
    field_x = settings_panel_x + 120
    app_settings_rect = pygame.Rect(settings_panel_x + 20, settings_panel_y + 45, settings_panel_width - 40, 120)
    profile_rect = pygame.Rect(settings_panel_x + 20, settings_panel_y + 180, settings_panel_width - 40, 155)
    year_field_rect = pygame.Rect(field_x, settings_panel_y + 78, 350, 30)
    file_field_rect = pygame.Rect(field_x, settings_panel_y + 118, 350, 30)
    user_field_rect = pygame.Rect(field_x, settings_panel_y + 213, 350, 30)
    email_field_rect = pygame.Rect(field_x, settings_panel_y + 253, 350, 30)
    token_field_rect = pygame.Rect(field_x, settings_panel_y + 293, 350, 30)
    default_settings_button_rect = pygame.Rect(settings_panel_x + 20, settings_panel_y + 345, 160, 40)
    apply_button_rect = pygame.Rect(settings_panel_x + 200, settings_panel_y + 345, 160, 40)
    close_button_rect = pygame.Rect(settings_panel_x + 380, settings_panel_y + 345, 160, 40)
    
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
    new_button_y = screen_height - (button_height * 6 + button_gap * 5 + bottom_margin)
    new_button_rect = pygame.Rect(button_x, new_button_y, button_width, button_height)
    save_button_rect = pygame.Rect(button_x, new_button_y + button_height + button_gap, button_width, button_height)
    deploy_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 2, button_width, button_height)
    default_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 3, button_width, button_height)
    settings_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 4, button_width, button_height)
    exit_button_rect = pygame.Rect(button_x, new_button_y + (button_height + button_gap) * 5, button_width, button_height)
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
    year_scroll_rect = pygame.Rect(0, 0, 0, 0)
    deploy_status = ""
    deploy_status_color = dark_gray
    
    # Initialize matrix view immediately on app start.
    matrix = generate_commit_matrix(year)
    marked = load_marked_dates(applied_file)

    def _set_active_field_value(value: str) -> None:
        nonlocal year_text, file_text, user_text, email_text, token_text
        if active_field == 0:
            year_text = "".join(ch for ch in value if ch.isdigit())[:4]
        elif active_field == 1:
            file_text = value[:100]
        elif active_field == 2:
            user_text = value[:50]
        elif active_field == 3:
            email_text = value[:100]
        elif active_field == 4:
            token_text = value[:120]

    def _get_active_field_value() -> str:
        if active_field == 0:
            return year_text
        if active_field == 1:
            return file_text
        if active_field == 2:
            return user_text
        if active_field == 3:
            return email_text
        if active_field == 4:
            return token_text
        return ""

    def _load_profile_fields() -> tuple[str, str, str]:
        current_profile = load_git_profile()
        return (
            current_profile.get("user", current_profile.get("username", "")),
            current_profile.get("email", ""),
            current_profile.get("token", ""),
        )

    def _load_default_profile_fields() -> tuple[str, str, str]:
        git_config_profile = load_git_config_profile()
        return (
            git_config_profile.get("user", ""),
            git_config_profile.get("email", ""),
            "",
        )

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
                        elif user_field_rect.collidepoint(pos):
                            active_field = 2
                        elif email_field_rect.collidepoint(pos):
                            active_field = 3
                        elif token_field_rect.collidepoint(pos):
                            active_field = 4
                        elif default_settings_button_rect.collidepoint(pos):
                            user_text, email_text, token_text = _load_default_profile_fields()
                            year_text = str(default_year)
                            file_text = default_path
                        elif apply_button_rect.collidepoint(pos):
                            try:
                                applied_year = int(year_text)
                                applied_file = file_text.strip() if file_text.strip() else default_path
                                year = applied_year
                                file_text = applied_file
                                # Save git profile
                                save_git_profile(
                                    user_text,
                                    email_text,
                                    token_text,
                                    year=applied_year,
                                    path=applied_file,
                                )
                                # Generate matrix and load marked dates
                                matrix = generate_commit_matrix(applied_year)
                                marked = load_marked_dates(applied_file)
                                state = STATE_MATRIX
                            except ValueError:
                                year_text = str(applied_year)
                        elif close_button_rect.collidepoint(pos):
                            # Return to matrix and discard unsaved settings edits
                            year_text = str(applied_year)
                            file_text = applied_file
                            git_profile = load_git_profile()
                            user_text = git_profile.get("user", git_profile.get("username", ""))
                            email_text = git_profile.get("email", "")
                            token_text = git_profile.get("token", "")
                            active_field = None
                            state = STATE_MATRIX
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Close settings without saving any pending edits.
                        year_text = str(applied_year)
                        file_text = applied_file
                        git_profile = load_git_profile()
                        user_text = git_profile.get("user", git_profile.get("username", ""))
                        email_text = git_profile.get("email", "")
                        token_text = git_profile.get("token", "")
                        active_field = None
                        state = STATE_MATRIX
                    elif event.key == pygame.K_TAB:
                        active_field = (active_field + 1) % 5 if active_field is not None else 0
                    elif event.key == pygame.K_RETURN and active_field is not None:
                        try:
                            applied_year = int(year_text)
                            applied_file = file_text.strip() if file_text.strip() else default_path
                            year = applied_year
                            file_text = applied_file
                            save_git_profile(
                                user_text,
                                email_text,
                                token_text,
                                year=applied_year,
                                path=applied_file,
                            )
                            matrix = generate_commit_matrix(applied_year)
                            marked = load_marked_dates(applied_file)
                            state = STATE_MATRIX
                        except ValueError:
                            year_text = str(applied_year)
                    elif event.key == pygame.K_BACKSPACE and active_field is not None:
                        _set_active_field_value(_get_active_field_value()[:-1])
                elif event.type == pygame.TEXTINPUT and active_field is not None:
                    if event.text and event.text.isprintable():
                        _set_active_field_value(_get_active_field_value() + event.text)
            
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
                            save_marked_dates(marked, year, applied_file)
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif save_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, applied_file)
                            deploy_status = f"Saved {applied_file}"
                            deploy_status_color = dark_gray
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif deploy_button_rect.collidepoint((x, y)):
                            deploy_status = "Deploying..."
                            deploy_status_color = green
                            try:
                                repo_path, commit_total = deploy_mock_repo(marked, year, applied_file)
                                deploy_status = f"Deployed {repo_path.name} with {commit_total} commits"
                                deploy_status_color = green
                            except Exception as exc:
                                deploy_status = f"Deploy failed: {exc}"
                                deploy_status_color = white
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif default_button_rect.collidepoint((x, y)):
                            marked = load_marked_dates("default-data.json")
                            deploy_status = "Loaded default-data.json"
                            deploy_status_color = dark_gray
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif exit_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, applied_file)
                            running = False
                        elif settings_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, applied_file)
                            state = STATE_SETTINGS
                            year_text = str(year)
                            file_text = applied_file
                            git_profile = load_git_profile()
                            user_text = git_profile.get("user", git_profile.get("username", ""))
                            email_text = git_profile.get("email", "")
                            token_text = git_profile.get("token", "")
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
                elif event.type == pygame.MOUSEWHEEL:
                    if year_scroll_rect.collidepoint(pygame.mouse.get_pos()) and event.y != 0:
                        save_marked_dates(marked, year, applied_file)
                        if event.y > 0:
                            year = min(9999, year + 1)
                        else:
                            year = max(1, year - 1)
                        applied_year = year
                        year_text = str(year)
                        matrix = generate_commit_matrix(year)
                        marked = load_marked_dates(applied_file)
                        drag_left_active = False
                        drag_right_active = False
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
                        save_marked_dates(marked, year, applied_file)
                        state = STATE_SETTINGS
                        year_text = str(applied_year)
                        file_text = applied_file
                        git_profile = load_git_profile()
                        user_text = git_profile.get("user", git_profile.get("username", ""))
                        email_text = git_profile.get("email", "")
                        token_text = git_profile.get("token", "")
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

            pygame.draw.rect(screen, gray, app_settings_rect, 1)
            app_settings_title = small_font.render("App Setting", True, green)
            screen.blit(app_settings_title, (app_settings_rect.x + 8, app_settings_rect.y + 6))

            pygame.draw.rect(screen, gray, profile_rect, 1)
            profile_title = small_font.render("Profile", True, green)
            screen.blit(profile_title, (profile_rect.x + 8, profile_rect.y + 6))
            
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
            
            user_label = small_font.render("User:", True, white)
            screen.blit(user_label, (label_x + 10, user_field_rect.y + 13))
            user_field_color = green if active_field == 2 else gray
            pygame.draw.rect(screen, user_field_color, user_field_rect, 2)
            user_display = small_font.render(user_text[-30:] if user_text else "", True, white)
            screen.blit(user_display, (user_field_rect.x + 10, user_field_rect.y + 13))
            
            email_label = small_font.render("Email:", True, white)
            screen.blit(email_label, (label_x + 5, email_field_rect.y + 13))
            email_field_color = green if active_field == 3 else gray
            pygame.draw.rect(screen, email_field_color, email_field_rect, 2)
            email_display = small_font.render(email_text[-30:] if email_text else "", True, white)
            screen.blit(email_display, (email_field_rect.x + 10, email_field_rect.y + 13))

            token_label = small_font.render("Token:", True, white)
            screen.blit(token_label, (label_x + 8, token_field_rect.y + 10))
            token_field_color = green if active_field == 4 else gray
            pygame.draw.rect(screen, token_field_color, token_field_rect, 2)
            token_masked = "*" * min(len(token_text), 30)
            token_display = small_font.render(token_masked, True, white)
            screen.blit(token_display, (token_field_rect.x + 10, token_field_rect.y + 10))

            # DEFAULT button
            default_settings_button_color = green if default_settings_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, default_settings_button_color, default_settings_button_rect, 2)
            default_settings_text = small_font.render("DEFAULT", True, default_settings_button_color)
            default_settings_rect = default_settings_text.get_rect(center=default_settings_button_rect.center)
            screen.blit(default_settings_text, default_settings_rect)
            
            # APPLY button
            apply_button_color = green if apply_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, apply_button_color, apply_button_rect, 2)
            apply_text = small_font.render("APPLY", True, apply_button_color)
            apply_rect = apply_text.get_rect(center=apply_button_rect.center)
            screen.blit(apply_text, apply_rect)
            
            # CLOSE button
            close_button_color = green if close_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, close_button_color, close_button_rect, 2)
            close_text = small_font.render("CLOSE", True, close_button_color)
            close_rect = close_text.get_rect(center=close_button_rect.center)
            screen.blit(close_text, close_rect)
            
            instructions = small_font.render("DEFAULT restores year/path and git profile | Enter to apply", True, dark_gray)
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
            title = font.render("Time Machine - Matrix", True, green)
            title_rect = title.get_rect(center=(screen_width // 2, 15))
            screen.blit(title, title_rect)

            year_value = font.render(str(year), True, green)
            year_value_rect = year_value.get_rect(center=(screen_width // 2, 36))
            screen.blit(year_value, year_value_rect)
            year_scroll_rect = year_value_rect.inflate(16, 8)

            # Settings button
            new_button_color = green if new_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, new_button_color, new_button_rect, 2)
            new_text = small_font.render("NEW", True, new_button_color)
            new_text_rect = new_text.get_rect(center=new_button_rect.center)
            screen.blit(new_text, new_text_rect)

            save_button_color = green if save_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, save_button_color, save_button_rect, 2)
            save_text = small_font.render("SAVE", True, save_button_color)
            save_text_rect = save_text.get_rect(center=save_button_rect.center)
            screen.blit(save_text, save_text_rect)

            deploy_button_color = green if deploy_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, deploy_button_color, deploy_button_rect, 2)
            deploy_text = small_font.render("DEPLOY", True, deploy_button_color)
            deploy_text_rect = deploy_text.get_rect(center=deploy_button_rect.center)
            screen.blit(deploy_text, deploy_text_rect)

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

            if deploy_status:
                status_surface = small_font.render(deploy_status[:72], True, deploy_status_color)
                status_rect = status_surface.get_rect(center=(screen_width // 2, screen_height - 28))
                screen.blit(status_surface, status_rect)
            
            instructions = small_font.render("Left drag:+level | Right drag:erase | Scroll on year number to change year", True, dark_gray)
            instructions_rect = instructions.get_rect(center=(screen_width // 2, screen_height - 12))
            screen.blit(instructions, instructions_rect)
        
        pygame.display.flip()
        clock.tick(30)
    
    # Save on exit
    if state == STATE_MATRIX and matrix is not None:
        save_marked_dates(marked, year, applied_file)
    
    pygame.quit()


