
"""Pygame-based UI for the 8-bit commit matrix editor."""

from datetime import date

from .module.data_persistence import (
    load_marked_dates, save_marked_dates,
    load_git_config_profile, load_git_profile, save_git_profile
)
from .module.daytime import date_from_year_grid_position, year_grid_position
from .module.deploy import archive_workspace_repo, deploy_mock_repo, push_workspace_repo
from .module.matrix_logic import generate_commit_matrix, generate_random_marked_dates
from .module.visualization import plot_matrix


def run_app(year: int = 2025, filename: str = "data.json") -> None:
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
    screen_width, screen_height = 920, 580
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Time Machine")
    
    # Colors
    black = (0, 0, 0)
    white = (255, 255, 255)
    green = (38, 228, 118)
    tip_green = (38, 228, 118)
    gray = (100, 100, 100)
    dark_gray = (50, 50, 50)
    cell_border = black
    available_cell = (35, 35, 35)
    out_of_year_cell = gray
    
    # Fonts
    font = pygame.font.SysFont('monospace', 16)
    small_font = pygame.font.SysFont('monospace', 12)
    title_font = pygame.font.SysFont('monospace', 24, bold=True)
    year_font = pygame.font.SysFont('monospace', 32, bold=True)
    
    # State machine
    STATE_SETTINGS = 0
    STATE_MATRIX = 1
    state = STATE_MATRIX

    default_year = 2025
    default_path = "data.json"
    
    # Settings state variables
    git_profile = load_git_profile()
    applied_year = git_profile.get("year", year)
    applied_file = git_profile.get("path", filename)
    applied_url = git_profile.get("url", "")
    applied_force_push = bool(git_profile.get("force_push", False))
    applied_debug = bool(git_profile.get("debug", False))
    applied_random = bool(git_profile.get("random", False))
    applied_highlight_year_bounds = bool(git_profile.get("highlight_year_bounds", False))
    applied_max_level = git_profile.get("max_level", 8)
    if not isinstance(applied_file, str) or not applied_file.strip():
        applied_file = filename
    if not isinstance(applied_url, str):
        applied_url = ""
    try:
        applied_year = int(applied_year)
    except (TypeError, ValueError):
        applied_year = year
    year = applied_year
    year_text = str(applied_year)
    file_text = applied_file
    url_text = applied_url
    force_push_enabled = applied_force_push
    debug_enabled = applied_debug
    random_enabled = applied_random
    highlight_year_bounds_enabled = applied_highlight_year_bounds
    max_level_text = str(applied_max_level)
    user_text = git_profile.get("user", git_profile.get("username", ""))
    email_text = git_profile.get("email", "")
    token_text = git_profile.get("token", "")
    active_field = None

    settings_panel_width = min(860, screen_width - 40)
    settings_panel_height = min(520, screen_height - 30)
    settings_panel_x = (screen_width - settings_panel_width) // 2
    settings_panel_y = (screen_height - settings_panel_height) // 2
    label_x = settings_panel_x + 28
    field_x = settings_panel_x + 150
    field_width = settings_panel_width - 230
    settings_button_width = 100
    settings_button_height = 28
    visible_text_chars = max(36, (field_width - 30) // 8)
    profile_rect = pygame.Rect(settings_panel_x + 20, settings_panel_y + 45, settings_panel_width - 40, 175)
    app_settings_rect = pygame.Rect(settings_panel_x + 20, settings_panel_y + 237, settings_panel_width - 40, 197)
    config_content_width = app_settings_rect.width - 36
    config_left_rect = pygame.Rect(
        app_settings_rect.x + 12,
        app_settings_rect.y + 28,
        config_content_width // 3,
        app_settings_rect.height - 40,
    )
    config_right_rect = pygame.Rect(
        config_left_rect.right + 12,
        app_settings_rect.y + 28,
        config_content_width - config_left_rect.width,
        app_settings_rect.height - 40,
    )
    user_field_rect = pygame.Rect(field_x, settings_panel_y + 78, field_width, 30)
    email_field_rect = pygame.Rect(field_x, settings_panel_y + 112, field_width, 30)
    url_field_rect = pygame.Rect(field_x, settings_panel_y + 146, field_width, 30)
    token_field_rect = pygame.Rect(field_x, settings_panel_y + 180, field_width, 30)
    config_left_field_x = config_left_rect.x + 122
    config_left_field_width = config_left_rect.width - 134
    toggle_box_x = config_right_rect.x + 16
    year_field_rect = pygame.Rect(config_left_field_x, config_left_rect.y + 18, config_left_field_width, 30)
    max_level_field_rect = pygame.Rect(config_left_field_x, config_left_rect.y + 64, config_left_field_width, 30)
    force_push_rect = pygame.Rect(toggle_box_x, config_right_rect.y + 18, 24, 24)
    debug_rect = pygame.Rect(toggle_box_x, config_right_rect.y + 52, 24, 24)
    random_rect = pygame.Rect(toggle_box_x, config_right_rect.y + 86, 24, 24)
    highlight_year_bounds_rect = pygame.Rect(toggle_box_x, config_right_rect.y + 120, 24, 24)
    settings_button_row_width = settings_button_width * 3 + 20 * 2
    settings_button_row_x = settings_panel_x + settings_panel_width - 20 - settings_button_row_width
    settings_button_row_y = settings_panel_y + settings_panel_height - 64
    default_settings_button_rect = pygame.Rect(settings_button_row_x, settings_button_row_y, settings_button_width, settings_button_height)
    apply_button_rect = pygame.Rect(settings_button_row_x + settings_button_width + 20, settings_button_row_y, settings_button_width, settings_button_height)
    close_button_rect = pygame.Rect(settings_button_row_x + (settings_button_width + 20) * 2, settings_button_row_y, settings_button_width, settings_button_height)
    
    # Matrix state variables
    matrix = None
    marked: dict[tuple[int, int], int] = {}
    matrix_columns = 53
    cell_size = 14
    label_width = 40
    label_height = 20
    button_height = 28
    button_width = 100
    row1_count = 4
    button_gap = 16
    row_gap = 14
    row1_total_width = row1_count * button_width + (row1_count - 1) * button_gap
    row1_x = (screen_width - row1_total_width) // 2
    row1_y = screen_height - 224
    row2_y = row1_y + button_height + row_gap
    row3_y = row2_y + button_height + row_gap
    row2_total_width = button_width * 3 + button_gap * 2
    row2_x = (screen_width - row2_total_width) // 2
    row3_total_width = button_width * 2 + button_gap
    row3_x = (screen_width - row3_total_width) // 2

    new_button_rect = pygame.Rect(row1_x, row1_y, button_width, button_height)
    template_button_rect = pygame.Rect(row1_x + (button_width + button_gap), row1_y, button_width, button_height)
    random_button_rect = pygame.Rect(row1_x + (button_width + button_gap) * 2, row1_y, button_width, button_height)
    default_button_rect = pygame.Rect(row1_x + (button_width + button_gap) * 3, row1_y, button_width, button_height)

    deploy_button_rect = pygame.Rect(row2_x, row2_y, button_width, button_height)
    push_button_rect = pygame.Rect(row2_x + button_width + button_gap, row2_y, button_width, button_height)
    archive_button_rect = pygame.Rect(row2_x + (button_width + button_gap) * 2, row2_y, button_width, button_height)

    settings_button_rect = pygame.Rect(row3_x, row3_y, button_width, button_height)
    exit_button_rect = pygame.Rect(row3_x + button_width + button_gap, row3_y, button_width, button_height)

    settings_panel_open = False
    template_panel_open = False
    template_panel_rect = pygame.Rect(screen_width // 2 - 230, screen_height // 2 - 150, 460, 300)
    template_close_rect = pygame.Rect(template_panel_rect.right - 110, template_panel_rect.y + 16, 86, 30)
    template_load_rects = [
        pygame.Rect(template_panel_x + 240, template_panel_y + 58 + i * 42, 86, 30)
        for i, (template_panel_x, template_panel_y) in enumerate(
            [(template_panel_rect.x, template_panel_rect.y)] * 5
        )
    ]
    template_save_rects = [
        pygame.Rect(template_panel_x + 338, template_panel_y + 58 + i * 42, 86, 30)
        for i, (template_panel_x, template_panel_y) in enumerate(
            [(template_panel_rect.x, template_panel_rect.y)] * 5
        )
    ]
    level_colors = [
        available_cell,
        (10, 57, 30),
        (19, 114, 59),
        (29, 171, 88),
        (33, 200, 103),
        (38, 228, 118),
        (38, 228, 118),
        (38, 228, 118),
        (38, 228, 118),
    ]

    drag_left_active = False
    drag_right_active = False
    drag_last_cell: tuple[int, int] | None = None
    year_scroll_rect = pygame.Rect(0, 0, 0, 0)
    matrix_status = ""
    matrix_status_color = dark_gray
    
    # Initialize matrix view immediately on app start.
    matrix = generate_commit_matrix(year)
    marked = load_marked_dates(applied_file)

    def _set_active_field_value(value: str) -> None:
        nonlocal year_text, url_text, user_text, email_text, token_text, max_level_text
        if active_field == 0:
            year_text = "".join(ch for ch in value if ch.isdigit())[:4]
        elif active_field == 1:
            url_text = value[:200]
        elif active_field == 2:
            user_text = value[:50]
        elif active_field == 3:
            email_text = value[:100]
        elif active_field == 4:
            token_text = value[:120]
        elif active_field == 5:
            max_level_text = "".join(ch for ch in value if ch.isdigit())[:1]

    def _get_active_field_value() -> str:
        if active_field == 0:
            return year_text
        if active_field == 1:
            return url_text
        if active_field == 2:
            return user_text
        if active_field == 3:
            return email_text
        if active_field == 4:
            return token_text
        if active_field == 5:
            return max_level_text
        return ""

    def _load_profile_fields() -> tuple[str, str, str]:
        current_profile = load_git_profile()
        return (
            current_profile.get("user", current_profile.get("username", "")),
            current_profile.get("email", ""),
            current_profile.get("token", ""),
        )

    def _load_default_profile_fields() -> tuple[str, str, str, str]:
        git_profile_defaults = load_git_profile()
        return (
            git_profile_defaults.get("user", ""),
            git_profile_defaults.get("email", ""),
            git_profile_defaults.get("url", ""),
            git_profile_defaults.get("token", ""),
        )

    def _extract_push_reject_reason(exc: Exception) -> str:
        """Return the most useful one-line reason from a git push failure."""
        raw = str(exc)
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        if not lines:
            return "unknown reason"

        keywords = (
            "rejected",
            "non-fast-forward",
            "denied",
            "failed to push",
            "fetch first",
            "updates were rejected",
            "error",
            "fatal",
        )
        for line in lines:
            lower = line.lower()
            if any(keyword in lower for keyword in keywords):
                return line
        return lines[0]

    def _draw_matrix_status_box() -> None:
        if not matrix_status:
            return
        status_box_rect = pygame.Rect(screen_width // 2 - 240, screen_height - 86, 480, 38)
        pygame.draw.rect(screen, black, status_box_rect)
        status_surface = small_font.render(matrix_status[:80], True, matrix_status_color)
        status_rect = status_surface.get_rect(midleft=(status_box_rect.x + 10, status_box_rect.centery))
        screen.blit(status_surface, status_rect)

    def _draw_settings_button(rect: pygame.Rect, text: str) -> None:
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill_color = (18, 34, 24) if hovered else (8, 8, 8)
        border_color = green if hovered else gray
        text_color = green if hovered else white
        pygame.draw.rect(screen, fill_color, rect, border_radius=6)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=6)
        label = small_font.render(text, True, text_color)
        label_rect = label.get_rect(center=rect.center)
        screen.blit(label, label_rect)

    def _draw_settings_input(
        label: str,
        label_right_x: int,
        rect: pygame.Rect,
        value: str,
        field_id: int,
        masked: bool = False,
        placeholder: str = "",
    ) -> pygame.Rect:
        label_surface = small_font.render(label, True, white)
        label_x_pos = label_right_x - label_surface.get_width()
        label_y_pos = rect.y + 13
        screen.blit(label_surface, (label_x_pos, label_y_pos))
        border_color = green if active_field == field_id else gray
        pygame.draw.rect(screen, (14, 14, 14), rect, border_radius=5)
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=5)
        display_text = value[-visible_text_chars:] if value else ""
        if masked and value:
            display_text = "*" * min(len(value), visible_text_chars)
        if display_text:
            text_surface = small_font.render(display_text, True, white)
        else:
            text_surface = small_font.render(placeholder, True, gray)
        screen.blit(text_surface, (rect.x + 10, rect.y + 13))
        return pygame.Rect(label_x_pos, label_y_pos, label_surface.get_width(), label_surface.get_height())

    def _draw_settings_toggle(
        label: str,
        label_right_x: int,
        rect: pygame.Rect,
        enabled: bool,
        label_on_right: bool = False,
    ) -> pygame.Rect:
        label_surface = small_font.render(label, True, white)
        if label_on_right:
            label_x_pos = rect.right + 10
        else:
            label_x_pos = label_right_x - label_surface.get_width()
        label_y_pos = rect.y + 8
        screen.blit(label_surface, (label_x_pos, label_y_pos))
        pygame.draw.rect(screen, (14, 14, 14), rect, border_radius=4)
        pygame.draw.rect(screen, green if enabled else gray, rect, 2, border_radius=4)
        if enabled:
            mark_rect = rect.inflate(-10, -10)
            pygame.draw.rect(screen, green, mark_rect, border_radius=2)
        return pygame.Rect(label_x_pos, label_y_pos, label_surface.get_width(), label_surface.get_height())

    def _draw_settings_form(panel_title_text: str, close_label_text: str, hint_center_y: int) -> None:
        panel_rect = pygame.Rect(settings_panel_x, settings_panel_y, settings_panel_width, settings_panel_height)
        shadow_rect = panel_rect.move(6, 6)
        pygame.draw.rect(screen, (6, 6, 6), shadow_rect, border_radius=10)
        pygame.draw.rect(screen, (12, 16, 14), panel_rect, border_radius=10)
        pygame.draw.rect(screen, green, panel_rect, 2, border_radius=10)

        panel_title = font.render(panel_title_text, True, green)
        screen.blit(panel_title, (settings_panel_x + 18, settings_panel_y + 12))

        pygame.draw.rect(screen, (10, 10, 10), profile_rect, border_radius=8)
        pygame.draw.rect(screen, gray, profile_rect, 1, border_radius=8)
        profile_title = small_font.render("Profile", True, green)
        screen.blit(profile_title, (profile_rect.x + 10, profile_rect.y + 6))

        pygame.draw.rect(screen, (10, 10, 10), app_settings_rect, border_radius=8)
        pygame.draw.rect(screen, gray, app_settings_rect, 1, border_radius=8)
        app_settings_title = small_font.render("Configuration", True, green)
        screen.blit(app_settings_title, (app_settings_rect.x + 10, app_settings_rect.y + 6))

        pygame.draw.rect(screen, (12, 12, 12), config_left_rect, border_radius=6)

        pygame.draw.rect(screen, (12, 12, 12), config_right_rect, border_radius=6)

        profile_label_right_x = field_x - 12
        config_left_label_right_x = year_field_rect.x - 12
        config_right_label_right_x = force_push_rect.x - 12
        label_help_items: list[tuple[pygame.Rect, str]] = []

        label_help_items.append((_draw_settings_input("User", profile_label_right_x, user_field_rect, user_text, 2, placeholder="<user>"), "Git author username used for commits."))
        label_help_items.append((_draw_settings_input("Email", profile_label_right_x, email_field_rect, email_text, 3), "Git author email used for commits."))
        label_help_items.append((_draw_settings_input("URL", profile_label_right_x, url_field_rect, url_text, 1, placeholder="<url>"), "Remote repository URL for push operations."))
        label_help_items.append((_draw_settings_input("Token", profile_label_right_x, token_field_rect, token_text, 4, masked=True, placeholder="<token>"), "Access token used for authenticated git actions."))

        label_help_items.append((_draw_settings_input("Year", config_left_label_right_x, year_field_rect, year_text, 0), "Target year for the contribution matrix."))
        label_help_items.append((_draw_settings_input("Max Commit", config_left_label_right_x, max_level_field_rect, max_level_text, 5), "Maximum commit intensity level (1-8)."))
        label_help_items.append((_draw_settings_toggle("Force Push", config_right_label_right_x, force_push_rect, force_push_enabled, label_on_right=True), "Allow force-push when updating remote history."))
        label_help_items.append((_draw_settings_toggle("Debug", config_right_label_right_x, debug_rect, debug_enabled, label_on_right=True), "Enable verbose debug output for operations."))
        label_help_items.append((_draw_settings_toggle("Random", config_right_label_right_x, random_rect, random_enabled, label_on_right=True), "Allow RANDOM button to auto-fill commits."))
        label_help_items.append((_draw_settings_toggle("Year Ends", config_right_label_right_x, highlight_year_bounds_rect, highlight_year_bounds_enabled, label_on_right=True), "Highlight Jan 1 and Dec 31 cells on the grid."))

        help_box_rect = pygame.Rect(settings_panel_x + 20, settings_button_row_y, settings_button_row_x - settings_panel_x - 32, settings_button_height)

        hovered_help = "Hover a setting label to view help."
        mouse_pos = pygame.mouse.get_pos()
        for label_rect, help_text in label_help_items:
            if label_rect.collidepoint(mouse_pos):
                hovered_help = help_text
                break

        help_display = hovered_help
        while small_font.size(help_display)[0] > help_box_rect.width - 16 and len(help_display) > 4:
            help_display = help_display[:-4] + "..."
        help_surface = small_font.render(help_display, True, tip_green)
        help_surface_rect = help_surface.get_rect(midleft=(help_box_rect.x + 8, help_box_rect.centery))
        screen.blit(help_surface, help_surface_rect)

        _draw_settings_button(default_settings_button_rect, "DEFAULT")
        _draw_settings_button(apply_button_rect, "APPLY")
        _draw_settings_button(close_button_rect, close_label_text)

        settings_hint = small_font.render("Enter to apply | Esc to cancel", True, tip_green)
        settings_hint_rect = settings_hint.get_rect(center=(screen_width // 2, hint_center_y))
        screen.blit(settings_hint, settings_hint_rect)

    def _open_settings_panel() -> None:
        nonlocal settings_panel_open, year_text, file_text, url_text
        nonlocal force_push_enabled, debug_enabled, random_enabled, highlight_year_bounds_enabled, max_level_text
        nonlocal user_text, email_text, token_text, active_field
        nonlocal template_panel_open, matrix_status, matrix_status_color
        save_marked_dates(marked, year, applied_file)
        matrix_status = "Opening settings..."
        matrix_status_color = dark_gray
        settings_panel_open = True
        template_panel_open = False
        pygame.key.start_text_input()
        year_text = str(year)
        file_text = applied_file
        git_profile_local = load_git_profile()
        url_text = git_profile_local.get("url", "") or applied_url
        user_text = git_profile_local.get("user", git_profile_local.get("username", "")) or user_text
        email_text = git_profile_local.get("email", "") or email_text
        token_text = git_profile_local.get("token", "") or token_text
        force_push_enabled = bool(git_profile_local.get("force_push", False))
        debug_enabled = bool(git_profile_local.get("debug", False))
        random_enabled = bool(git_profile_local.get("random", False))
        highlight_year_bounds_enabled = bool(git_profile_local.get("highlight_year_bounds", False))
        max_level_text = str(git_profile_local.get("max_level", 8))
        active_field = None

    def _cancel_settings_panel() -> None:
        nonlocal settings_panel_open, year_text, file_text, url_text
        nonlocal force_push_enabled, debug_enabled, random_enabled, highlight_year_bounds_enabled, max_level_text
        nonlocal user_text, email_text, token_text, active_field
        nonlocal matrix_status, matrix_status_color
        year_text = str(applied_year)
        file_text = applied_file
        git_profile_local = load_git_profile()
        url_text = git_profile_local.get("url", "")
        force_push_enabled = bool(git_profile_local.get("force_push", False))
        debug_enabled = bool(git_profile_local.get("debug", False))
        random_enabled = bool(git_profile_local.get("random", False))
        highlight_year_bounds_enabled = bool(git_profile_local.get("highlight_year_bounds", False))
        max_level_text = str(git_profile_local.get("max_level", 8))
        user_text = git_profile_local.get("user", git_profile_local.get("username", ""))
        email_text = git_profile_local.get("email", "")
        token_text = git_profile_local.get("token", "")
        active_field = None
        settings_panel_open = False
        pygame.key.stop_text_input()

    def _apply_settings_panel() -> bool:
        nonlocal applied_year, applied_url
        nonlocal applied_force_push, applied_debug, applied_random, applied_highlight_year_bounds, applied_max_level
        nonlocal year, year_text, matrix, marked, settings_panel_open
        nonlocal matrix_status, matrix_status_color
        try:
            applied_year = int(year_text)
            applied_url = url_text.strip()
            applied_force_push = force_push_enabled
            applied_debug = debug_enabled
            applied_random = random_enabled
            applied_highlight_year_bounds = highlight_year_bounds_enabled
            applied_max_level = int(max_level_text) if max_level_text.isdigit() else 8
            applied_max_level = max(1, min(8, applied_max_level))
            year = applied_year
            save_git_profile(
                user_text,
                email_text,
                token_text,
                year=applied_year,
                path=applied_file,
                url=url_text,
                force_push=force_push_enabled,
                debug=debug_enabled,
                random=random_enabled,
                highlight_year_bounds=highlight_year_bounds_enabled,
                max_level=applied_max_level,
            )
            matrix = generate_commit_matrix(applied_year)
            marked = load_marked_dates(applied_file)
            matrix_status = "Settings applied"
            matrix_status_color = green
            settings_panel_open = False
            pygame.key.stop_text_input()
            return True
        except ValueError:
            matrix_status = "Apply failed: year must be a number"
            matrix_status_color = white
            year_text = str(applied_year)
            return False

    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.key.stop_text_input()
                running = False
            
            if state == STATE_SETTINGS:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        pos = event.pos
                        if year_field_rect.collidepoint(pos):
                            active_field = 0
                        elif force_push_rect.collidepoint(pos):
                            force_push_enabled = not force_push_enabled
                            active_field = None
                        elif debug_rect.collidepoint(pos):
                            debug_enabled = not debug_enabled
                            active_field = None
                        elif random_rect.collidepoint(pos):
                            random_enabled = not random_enabled
                            active_field = None
                        elif highlight_year_bounds_rect.collidepoint(pos):
                            highlight_year_bounds_enabled = not highlight_year_bounds_enabled
                            active_field = None
                        elif max_level_field_rect.collidepoint(pos):
                            active_field = 5
                        elif url_field_rect.collidepoint(pos):
                            active_field = 1
                        elif user_field_rect.collidepoint(pos):
                            active_field = 2
                        elif email_field_rect.collidepoint(pos):
                            active_field = 3
                        elif token_field_rect.collidepoint(pos):
                            active_field = 4
                        elif default_settings_button_rect.collidepoint(pos):
                            default_user_text, default_email_text, default_url_text, default_token_text = _load_default_profile_fields()
                            if default_user_text:
                                user_text = default_user_text
                            if default_email_text:
                                email_text = default_email_text
                            if default_url_text:
                                url_text = default_url_text
                            if default_token_text:
                                token_text = default_token_text
                            year_text = str(default_year)
                            force_push_enabled = False
                            debug_enabled = False
                            random_enabled = False
                            highlight_year_bounds_enabled = False
                            max_level_text = "8"
                        elif apply_button_rect.collidepoint(pos):
                            try:
                                applied_year = int(year_text)
                                applied_url = url_text.strip()
                                applied_force_push = force_push_enabled
                                applied_debug = debug_enabled
                                applied_random = random_enabled
                                applied_highlight_year_bounds = highlight_year_bounds_enabled
                                applied_max_level = int(max_level_text) if max_level_text.isdigit() else 8
                                applied_max_level = max(1, min(8, applied_max_level))
                                year = applied_year
                                # Save git profile
                                save_git_profile(
                                    user_text,
                                    email_text,
                                    token_text,
                                    year=applied_year,
                                    path=applied_file,
                                    url=url_text,
                                    force_push=force_push_enabled,
                                    debug=debug_enabled,
                                    random=random_enabled,
                                    highlight_year_bounds=highlight_year_bounds_enabled,
                                    max_level=applied_max_level,
                                )
                                # Generate matrix and load marked dates
                                matrix = generate_commit_matrix(applied_year)
                                marked = load_marked_dates(applied_file)
                                matrix_status = "Settings applied"
                                matrix_status_color = green
                                state = STATE_MATRIX
                            except ValueError:
                                matrix_status = "Apply failed: year must be a number"
                                matrix_status_color = white
                                year_text = str(applied_year)
                        elif close_button_rect.collidepoint(pos):
                            # Return to matrix and discard unsaved settings edits
                            year_text = str(applied_year)
                            file_text = applied_file
                            git_profile = load_git_profile()
                            url_text = git_profile.get("url", "")
                            force_push_enabled = bool(git_profile.get("force_push", False))
                            debug_enabled = bool(git_profile.get("debug", False))
                            random_enabled = bool(git_profile.get("random", False))
                            highlight_year_bounds_enabled = bool(git_profile.get("highlight_year_bounds", False))
                            max_level_text = str(git_profile.get("max_level", 8))
                            user_text = git_profile.get("user", git_profile.get("username", ""))
                            email_text = git_profile.get("email", "")
                            token_text = git_profile.get("token", "")
                            active_field = None
                            matrix_status = "Settings canceled"
                            matrix_status_color = dark_gray
                            pygame.key.stop_text_input()
                            state = STATE_MATRIX
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Close settings without saving any pending edits.
                        year_text = str(applied_year)
                        file_text = applied_file
                        git_profile = load_git_profile()
                        url_text = git_profile.get("url", "")
                        force_push_enabled = bool(git_profile.get("force_push", False))
                        debug_enabled = bool(git_profile.get("debug", False))
                        random_enabled = bool(git_profile.get("random", False))
                        highlight_year_bounds_enabled = bool(git_profile.get("highlight_year_bounds", False))
                        user_text = git_profile.get("user", git_profile.get("username", ""))
                        email_text = git_profile.get("email", "")
                        token_text = git_profile.get("token", "")
                        active_field = None
                        matrix_status = "Settings canceled"
                        matrix_status_color = dark_gray
                        pygame.key.stop_text_input()
                        state = STATE_MATRIX
                    elif event.key == pygame.K_TAB:
                        active_field = (active_field + 1) % 6 if active_field is not None else 0
                    elif event.key == pygame.K_RETURN:
                        try:
                            applied_year = int(year_text)
                            applied_url = url_text.strip()
                            applied_force_push = force_push_enabled
                            applied_debug = debug_enabled
                            applied_random = random_enabled
                            applied_highlight_year_bounds = highlight_year_bounds_enabled
                            year = applied_year
                            save_git_profile(
                                user_text,
                                email_text,
                                token_text,
                                year=applied_year,
                                path=applied_file,
                                url=url_text,
                                force_push=force_push_enabled,
                                debug=debug_enabled,
                                random=random_enabled,
                                highlight_year_bounds=highlight_year_bounds_enabled,
                            )
                            matrix = generate_commit_matrix(applied_year)
                            marked = load_marked_dates(applied_file)
                            matrix_status = "Settings applied"
                            matrix_status_color = green
                            pygame.key.stop_text_input()
                            state = STATE_MATRIX
                        except ValueError:
                            matrix_status = "Apply failed: year must be a number"
                            matrix_status_color = white
                            year_text = str(applied_year)
                    elif event.key == pygame.K_BACKSPACE and active_field is not None:
                        _set_active_field_value(_get_active_field_value()[:-1])
                elif event.type == pygame.TEXTINPUT and active_field is not None:
                    if event.text and event.text.isprintable():
                        _set_active_field_value(_get_active_field_value() + event.text)
            
            elif state == STATE_MATRIX:
                grid_width = matrix_columns * cell_size
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
                        if settings_panel_open:
                            pos = event.pos
                            if year_field_rect.collidepoint(pos):
                                active_field = 0
                            elif force_push_rect.collidepoint(pos):
                                force_push_enabled = not force_push_enabled
                                active_field = None
                            elif debug_rect.collidepoint(pos):
                                debug_enabled = not debug_enabled
                                active_field = None
                            elif random_rect.collidepoint(pos):
                                random_enabled = not random_enabled
                                active_field = None
                            elif highlight_year_bounds_rect.collidepoint(pos):
                                highlight_year_bounds_enabled = not highlight_year_bounds_enabled
                                active_field = None
                            elif max_level_field_rect.collidepoint(pos):
                                active_field = 5
                            elif url_field_rect.collidepoint(pos):
                                active_field = 1
                            elif user_field_rect.collidepoint(pos):
                                active_field = 2
                            elif email_field_rect.collidepoint(pos):
                                active_field = 3
                            elif token_field_rect.collidepoint(pos):
                                active_field = 4
                            elif default_settings_button_rect.collidepoint(pos):
                                default_user_text, default_email_text, default_url_text, default_token_text = _load_default_profile_fields()
                                if default_user_text:
                                    user_text = default_user_text
                                if default_email_text:
                                    email_text = default_email_text
                                if default_url_text:
                                    url_text = default_url_text
                                if default_token_text:
                                    token_text = default_token_text
                                year_text = str(default_year)
                                force_push_enabled = False
                                debug_enabled = False
                                random_enabled = False
                                highlight_year_bounds_enabled = False
                            elif apply_button_rect.collidepoint(pos):
                                _apply_settings_panel()
                            elif close_button_rect.collidepoint(pos):
                                _cancel_settings_panel()
                                matrix_status = "Settings canceled"
                                matrix_status_color = dark_gray
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                            continue

                        if template_panel_open:
                            if template_close_rect.collidepoint((x, y)):
                                template_panel_open = False
                                matrix_status = "Template panel closed"
                                matrix_status_color = dark_gray
                            else:
                                for i in range(5):
                                    template_filename = f"template-{i + 1}.json"
                                    if template_load_rects[i].collidepoint((x, y)):
                                        marked = load_marked_dates(template_filename)
                                        matrix_status = f"Loaded {template_filename}"
                                        matrix_status_color = green
                                        break
                                    if template_save_rects[i].collidepoint((x, y)):
                                        save_marked_dates(marked, year, template_filename)
                                        matrix_status = f"Saved {template_filename}"
                                        matrix_status_color = green
                                        break
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                            continue

                        if new_button_rect.collidepoint((x, y)):
                            marked.clear()
                            save_marked_dates(marked, year, applied_file)
                            matrix_status = "New matrix created"
                            matrix_status_color = green
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif random_button_rect.collidepoint((x, y)):
                            if not random_enabled:
                                matrix_status = "Random mode is off"
                                matrix_status_color = white
                            else:
                                try:
                                    marked = generate_random_marked_dates(applied_year, max_level=applied_max_level)
                                    save_marked_dates(marked, applied_year, applied_file)
                                    matrix_status = f"Random commits generated for {applied_year}"
                                    matrix_status_color = green
                                except Exception as exc:
                                    matrix_status = f"Random failed: {exc}"
                                    matrix_status_color = white
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif push_button_rect.collidepoint((x, y)):
                            try:
                                matrix_status = "Pushing..."
                                matrix_status_color = green
                                # Repaint status box before starting push.
                                _draw_matrix_status_box()
                                pygame.display.update(pygame.Rect(screen_width // 2 - 240, screen_height - 86, 480, 38))
                                pygame.event.pump()
                                safe_remote_url = push_workspace_repo()
                                matrix_status = f"Pushed to {safe_remote_url}"[:80]
                                matrix_status_color = green
                            except Exception as exc:
                                reason = _extract_push_reject_reason(exc)
                                matrix_status = f"Push failed: {reason}"
                                matrix_status_color = white
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif deploy_button_rect.collidepoint((x, y)):
                            matrix_status = "Committing..."
                            matrix_status_color = green
                            # Force the status box to repaint before the long deploy task starts.
                            _draw_matrix_status_box()
                            pygame.display.update(pygame.Rect(screen_width // 2 - 240, screen_height - 86, 480, 38))
                            pygame.event.pump()
                            try:
                                repo_path, commit_total = deploy_mock_repo(marked, year, applied_file)
                                matrix_status = f"Committed {repo_path.name} with {commit_total} commits"
                                matrix_status_color = green
                            except Exception as exc:
                                matrix_status = f"Commit failed: {exc}"
                                matrix_status_color = white
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif archive_button_rect.collidepoint((x, y)):
                            try:
                                matrix_status = "Archiving..."
                                matrix_status_color = green
                                # Repaint status box before starting archive.
                                _draw_matrix_status_box()
                                pygame.display.update(pygame.Rect(screen_width // 2 - 240, screen_height - 86, 480, 38))
                                pygame.event.pump()
                                archive_path = archive_workspace_repo()
                                matrix_status = f"Archived to {archive_path.name}"
                                matrix_status_color = green
                            except Exception as exc:
                                matrix_status = f"Archive failed: {exc}"
                                matrix_status_color = white
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif default_button_rect.collidepoint((x, y)):
                            marked = load_marked_dates("default-data.json")
                            matrix_status = "Loaded default-data.json"
                            matrix_status_color = green
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif exit_button_rect.collidepoint((x, y)):
                            save_marked_dates(marked, year, applied_file)
                            matrix_status = "Exiting..."
                            matrix_status_color = dark_gray
                            running = False
                        elif settings_button_rect.collidepoint((x, y)):
                            _open_settings_panel()
                        elif template_button_rect.collidepoint((x, y)):
                            template_panel_open = True
                            settings_panel_open = False
                            pygame.key.stop_text_input()
                            matrix_status = "Template panel opened"
                            matrix_status_color = green
                            drag_left_active = False
                            drag_right_active = False
                            drag_last_cell = None
                        elif grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                            week = (x - grid_x) // cell_size
                            day = (y - grid_y) // cell_size
                            if 0 <= week < matrix_columns and 0 <= day < 7 and date_from_year_grid_position(year, week, day) is not None:
                                pos = (week, day)
                                new_level = min(marked.get(pos, 0) + 1, applied_max_level)
                                marked[pos] = new_level
                                drag_left_active = True
                                drag_last_cell = pos
                    elif event.button == 3:
                        if settings_panel_open or template_panel_open:
                            continue
                        if grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                            week = (x - grid_x) // cell_size
                            day = (y - grid_y) // cell_size
                            if 0 <= week < matrix_columns and 0 <= day < 7 and date_from_year_grid_position(year, week, day) is not None:
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
                    if settings_panel_open:
                        continue
                    if event.y != 0:
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
                    if settings_panel_open or template_panel_open:
                        continue
                    if not (drag_left_active or drag_right_active):
                        continue
                    x, y = event.pos
                    if grid_x <= x < grid_x + grid_width and grid_y <= y < grid_y + grid_height:
                        week = (x - grid_x) // cell_size
                        day = (y - grid_y) // cell_size
                        if 0 <= week < matrix_columns and 0 <= day < 7 and date_from_year_grid_position(year, week, day) is not None:
                            pos = (week, day)
                            if pos != drag_last_cell:
                                if drag_left_active:
                                    marked[pos] = min(marked.get(pos, 0) + 1, applied_max_level)
                                elif drag_right_active:
                                    marked.pop(pos, None)
                                drag_last_cell = pos
                elif event.type == pygame.KEYDOWN:
                    if settings_panel_open:
                        if event.key == pygame.K_ESCAPE:
                            _cancel_settings_panel()
                            matrix_status = "Settings canceled"
                            matrix_status_color = dark_gray
                        elif event.key == pygame.K_TAB:
                            active_field = (active_field + 1) % 6 if active_field is not None else 0
                        elif event.key == pygame.K_RETURN:
                            _apply_settings_panel()
                        elif event.key == pygame.K_BACKSPACE and active_field is not None:
                            _set_active_field_value(_get_active_field_value()[:-1])
                        continue

                    if event.key == pygame.K_ESCAPE:
                        if template_panel_open:
                            template_panel_open = False
                            matrix_status = "Template panel closed"
                            matrix_status_color = dark_gray
                            continue
                        _open_settings_panel()
                elif event.type == pygame.TEXTINPUT and settings_panel_open and active_field is not None:
                    if event.text and event.text.isprintable():
                        _set_active_field_value(_get_active_field_value() + event.text)
        
        screen.fill(black)
        
        if state == STATE_SETTINGS:
            _draw_settings_form("Time Machine Settings", "CANCEL", screen_height - 12)
        
        elif state == STATE_MATRIX:
            # Draw matrix screen
            grid_width = matrix_columns * cell_size
            grid_height = 7 * cell_size
            matrix_width = label_width + grid_width
            matrix_height = label_height + grid_height
            matrix_x = max((screen_width - matrix_width) // 2, 0)
            matrix_y = max((screen_height - matrix_height) // 3, 0)
            matrix_center_x = matrix_x + matrix_width // 2
            grid_x = matrix_x + label_width
            grid_y = matrix_y + label_height
            
            # Draw cells
            highlight_positions: set[tuple[int, int]] = set()
            if highlight_year_bounds_enabled:
                jan_1 = date(year, 1, 1)
                dec_31 = date(year, 12, 31)
                for dt in (jan_1, dec_31):
                    week, day = year_grid_position(dt.year, dt.month, dt.day)
                    highlight_positions.add((week, day))

            for day in range(7):
                for week in range(matrix_columns):
                    cell_date = date_from_year_grid_position(year, week, day)
                    level = marked.get((week, day), 0)
                    visual_level = min(max(level, 0), 5)
                    color = level_colors[visual_level] if cell_date is not None else out_of_year_cell
                    rect = pygame.Rect(grid_x + week * cell_size, grid_y + day * cell_size, cell_size, cell_size)
                    pygame.draw.rect(screen, color, rect, border_radius=3)
                    if cell_date is not None and (week, day) in highlight_positions:
                        pygame.draw.rect(screen, (255, 220, 80), rect, 2, border_radius=3)
                    else:
                        pygame.draw.rect(screen, cell_border, rect, 1, border_radius=3)

            hover_date_text = ""
            hover_commits = ""
            hover_axis_text = ""
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if grid_x <= mouse_x < grid_x + grid_width and grid_y <= mouse_y < grid_y + grid_height:
                hover_week = (mouse_x - grid_x) // cell_size
                hover_day = (mouse_y - grid_y) // cell_size
                if 0 <= hover_week < matrix_columns and 0 <= hover_day < 7:
                    hover_date = date_from_year_grid_position(year, hover_week, hover_day)
                    if hover_date is not None:
                        hover_date_text = hover_date.strftime("%A, %d %b")
                        hover_commits = str(marked.get((hover_week, hover_day), 0))
                        hover_axis_text = f"[{hover_day + 1}:{hover_week + 1}]"
            
            # Draw labels
            day_labels = [(0, "Sun"), (3, "Wed"), (6, "Sat")]
            for row, day in day_labels:
                text = small_font.render(day, True, white)
                screen.blit(text, (matrix_x + 5, grid_y + row * cell_size + 2))
            
            month_labels: list[tuple[str, int]] = []
            for month in range(1, 13):
                month_date = date(year, month, 1)
                month_week, _ = year_grid_position(year, month, 1)
                month_labels.append((month_date.strftime("%b"), month_week))

            for month_text, month_week in month_labels:
                label_surface = small_font.render(month_text, True, white)
                label_x = grid_x + month_week * cell_size + 2
                screen.blit(label_surface, (label_x, matrix_y + 5))
            
            # Title and instructions
            title = title_font.render("Commit Graph Time Machine", True, green)
            title_rect = title.get_rect(center=(matrix_center_x, 15))
            screen.blit(title, title_rect)

            year_value = year_font.render(str(year), True, green)
            year_value_rect = year_value.get_rect(center=(matrix_center_x, 50))
            screen.blit(year_value, year_value_rect)
            year_scroll_rect = year_value_rect.inflate(16, 8)

            if hover_date_text:
                hover_date_surface = small_font.render(hover_date_text, True, tip_green)
                hover_date_rect = hover_date_surface.get_rect(center=(matrix_center_x, 74))
                screen.blit(hover_date_surface, hover_date_rect)
                
                hover_commit_count = int(hover_commits) if hover_commits.isdigit() else 0
                hover_commit_text = f"{hover_commit_count} commit(s)"
                hover_commits_surface = small_font.render(hover_commit_text, True, tip_green)
                hover_commits_rect = hover_commits_surface.get_rect(center=(matrix_center_x, 90))
                screen.blit(hover_commits_surface, hover_commits_rect)

                hover_axis_surface = small_font.render(hover_axis_text, True, tip_green)
                hover_axis_rect = hover_axis_surface.get_rect(center=(matrix_center_x, 106))
                screen.blit(hover_axis_surface, hover_axis_rect)

            new_button_color = green if new_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), new_button_rect, border_radius=6)
            pygame.draw.rect(screen, new_button_color, new_button_rect, 2, border_radius=6)
            new_text = small_font.render("NEW", True, new_button_color)
            new_text_rect = new_text.get_rect(center=new_button_rect.center)
            screen.blit(new_text, new_text_rect)

            random_button_color = green if random_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), random_button_rect, border_radius=6)
            pygame.draw.rect(screen, random_button_color, random_button_rect, 2, border_radius=6)
            random_text = small_font.render("RANDOM", True, random_button_color)
            random_text_rect = random_text.get_rect(center=random_button_rect.center)
            screen.blit(random_text, random_text_rect)

            deploy_button_color = green if deploy_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), deploy_button_rect, border_radius=6)
            pygame.draw.rect(screen, deploy_button_color, deploy_button_rect, 2, border_radius=6)
            deploy_text = small_font.render("COMMIT", True, deploy_button_color)
            deploy_text_rect = deploy_text.get_rect(center=deploy_button_rect.center)
            screen.blit(deploy_text, deploy_text_rect)

            push_button_color = green if push_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), push_button_rect, border_radius=6)
            pygame.draw.rect(screen, push_button_color, push_button_rect, 2, border_radius=6)
            push_text = small_font.render("PUSH", True, push_button_color)
            push_text_rect = push_text.get_rect(center=push_button_rect.center)
            screen.blit(push_text, push_text_rect)

            archive_button_color = green if archive_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), archive_button_rect, border_radius=6)
            pygame.draw.rect(screen, archive_button_color, archive_button_rect, 2, border_radius=6)
            archive_text = small_font.render("ARCHIVE", True, archive_button_color)
            archive_text_rect = archive_text.get_rect(center=archive_button_rect.center)
            screen.blit(archive_text, archive_text_rect)

            default_button_color = green if default_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), default_button_rect, border_radius=6)
            pygame.draw.rect(screen, default_button_color, default_button_rect, 2, border_radius=6)
            default_text = small_font.render("DEFAULT", True, default_button_color)
            default_text_rect = default_text.get_rect(center=default_button_rect.center)
            screen.blit(default_text, default_text_rect)

            settings_button_color = green if settings_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), settings_button_rect, border_radius=6)
            pygame.draw.rect(screen, settings_button_color, settings_button_rect, 2, border_radius=6)
            settings_text = small_font.render("SETTINGS", True, settings_button_color)
            settings_text_rect = settings_text.get_rect(center=settings_button_rect.center)
            screen.blit(settings_text, settings_text_rect)

            template_button_color = green if template_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), template_button_rect, border_radius=6)
            pygame.draw.rect(screen, template_button_color, template_button_rect, 2, border_radius=6)
            template_text = small_font.render("TEMPLATE", True, template_button_color)
            template_text_rect = template_text.get_rect(center=template_button_rect.center)
            screen.blit(template_text, template_text_rect)

            exit_button_color = green if exit_button_rect.collidepoint(pygame.mouse.get_pos()) else white
            pygame.draw.rect(screen, (14, 14, 14), exit_button_rect, border_radius=6)
            pygame.draw.rect(screen, exit_button_color, exit_button_rect, 2, border_radius=6)
            exit_text = small_font.render("EXIT", True, exit_button_color)
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            screen.blit(exit_text, exit_text_rect)

            if template_panel_open:
                template_shadow_rect = template_panel_rect.move(6, 6)
                pygame.draw.rect(screen, (6, 6, 6), template_shadow_rect, border_radius=10)
                pygame.draw.rect(screen, (12, 16, 14), template_panel_rect, border_radius=10)
                pygame.draw.rect(screen, green, template_panel_rect, 2, border_radius=10)
                panel_title = font.render("Templates", True, green)
                screen.blit(panel_title, (template_panel_rect.x + 18, template_panel_rect.y + 20))

                close_color = green if template_close_rect.collidepoint(pygame.mouse.get_pos()) else white
                pygame.draw.rect(screen, (14, 14, 14), template_close_rect, border_radius=6)
                pygame.draw.rect(screen, close_color, template_close_rect, 2, border_radius=6)
                close_text = small_font.render("CLOSE", True, close_color)
                close_text_rect = close_text.get_rect(center=template_close_rect.center)
                screen.blit(close_text, close_text_rect)

                for i in range(5):
                    slot_label = small_font.render(f"Template {i + 1}", True, white)
                    screen.blit(slot_label, (template_panel_rect.x + 24, template_panel_rect.y + 68 + i * 42))

                    load_color = green if template_load_rects[i].collidepoint(pygame.mouse.get_pos()) else white
                    pygame.draw.rect(screen, (14, 14, 14), template_load_rects[i], border_radius=6)
                    pygame.draw.rect(screen, load_color, template_load_rects[i], 2, border_radius=6)
                    load_text = small_font.render("LOAD", True, load_color)
                    load_text_rect = load_text.get_rect(center=template_load_rects[i].center)
                    screen.blit(load_text, load_text_rect)

                    save_color = green if template_save_rects[i].collidepoint(pygame.mouse.get_pos()) else white
                    pygame.draw.rect(screen, (14, 14, 14), template_save_rects[i], border_radius=6)
                    pygame.draw.rect(screen, save_color, template_save_rects[i], 2, border_radius=6)
                    save_text = small_font.render("SAVE", True, save_color)
                    save_text_rect = save_text.get_rect(center=template_save_rects[i].center)
                    screen.blit(save_text, save_text_rect)

                panel_hint = small_font.render("Save or load the current matrix using 5 template slots", True, tip_green)
                screen.blit(panel_hint, (template_panel_rect.x + 24, template_panel_rect.bottom - 26))

            if settings_panel_open:
                _draw_settings_form("Settings", "CLOSE", settings_panel_y + settings_panel_height - 12)

            if not settings_panel_open:
                _draw_matrix_status_box()
            
            instructions = small_font.render("Left click/drag to draw | Right click/drag to erase | Scroll to change year", True, tip_green)
            instructions_rect = instructions.get_rect(center=(screen_width // 2, screen_height - 12))
            screen.blit(instructions, instructions_rect)
        
        pygame.display.flip()
        clock.tick(30)
    
    # Save on exit
    if state == STATE_MATRIX and matrix is not None:
        save_marked_dates(marked, year, applied_file)
    
    pygame.quit()


