
"""Pygame-based UI for the 8-bit commit matrix editor."""

from .module.data_persistence import load_marked_dates, save_marked_dates
from .module.matrix_logic import generate_commit_matrix
from .module.visualization import plot_matrix

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

