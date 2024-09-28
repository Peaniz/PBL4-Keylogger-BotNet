import pygame
import sys

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Remote Desktop Menu")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Font
font = pygame.font.Font(None, 36)

class Victim:
    def __init__(self, name, num_displays):
        self.name = name
        self.num_displays = num_displays
        self.screen = None
        self.camera = None


class Display:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text

    def draw(self, surface, offset_y):
        adjusted_rect = self.rect.copy()
        adjusted_rect.y -= offset_y
        if 0 <= adjusted_rect.y < HEIGHT and adjusted_rect.bottom > 0:
            pygame.draw.rect(surface, GRAY, adjusted_rect)
            pygame.draw.rect(surface, DARK_GRAY, adjusted_rect, 2)
            text_surface = font.render(self.text, True, BLACK)
            text_rect = text_surface.get_rect(center=adjusted_rect.center)
            surface.blit(text_surface, text_rect)

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, DARK_GRAY, self.rect, 2)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

# Create initial displays
displays = [
    Display(50, 50, 200, 150, "Display 1"),
    Display(300, 50, 200, 150, "Display 2"),
    Display(550, 50, 200, 150, "Display 3"),
]

# Create "+" button
add_button = Display(WIDTH - 100, HEIGHT - 100, 80, 80, "+")

# Create "Back" button
back_button = Display(10, 10, 100, 50, "Back")

def create_new_display():
    num_displays = len(displays)
    row = num_displays // 3
    col = num_displays % 3
    x = 50 + col * 250
    y = 50 + row * 200
    return Display(x, y, 200, 150, f"Display {num_displays + 1}")

def show_full_screen(display):
    full_screen = True
    camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 200, 200, 50, "Display Camera", GREEN)
    screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 200, 200, 50, "Display Screen", BLUE)
    
    while full_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if back_button.rect.collidepoint(event.pos):
                        full_screen = False
                    elif camera_button.rect.collidepoint(event.pos):
                        print(f"Display Camera for {display.text}")
                    elif screen_button.rect.collidepoint(event.pos):
                        print(f"Display Screen for {display.text}")

        screen.fill(WHITE)
        text_surface = font.render(f"Full Screen: {display.text}", True, BLACK)
        text_rect = text_surface.get_rect(center=(WIDTH//2, HEIGHT//4))
        screen.blit(text_surface, text_rect)
        
        back_button.draw(screen, 0)
        camera_button.draw(screen)
        screen_button.draw(screen)
        
        pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    scroll_y = 0
    max_scroll_y = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    for display in displays:
                        if display.rect.collidepoint(event.pos[0], event.pos[1] + scroll_y):
                            print(f"Clicked on {display.text}")
                            show_full_screen(display)
                    if add_button.rect.collidepoint(event.pos):
                        new_display = create_new_display()
                        displays.append(new_display)
                        max_scroll_y = max(0, (len(displays) // 3) * 200 + 50 - HEIGHT)
                elif event.button == 4:  # Scroll up
                    scroll_y = max(0, scroll_y - 20)
                elif event.button == 5:  # Scroll down
                    scroll_y = min(max_scroll_y, scroll_y + 20)

        screen.fill(WHITE)

        for display in displays:
            display.draw(screen, scroll_y)

        add_button.draw(screen, 0)  # The add button doesn't scroll

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
