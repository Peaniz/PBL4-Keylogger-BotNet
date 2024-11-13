import pygame
from  ui.components.colors import DARK_GRAY, BLACK

class Button:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.font = pygame.font.Font(None, 36)

    def draw(self, surface, offset_y=0):
        adjusted_rect = self.rect.move(0, -offset_y)
        pygame.draw.rect(surface, self.color, adjusted_rect)
        pygame.draw.rect(surface, DARK_GRAY, adjusted_rect, 2)
        
        if self.text:  # Only render text if it exists
            text_surface = self.font.render(self.text, True, BLACK)
            text_rect = text_surface.get_rect(center=adjusted_rect.center)
            surface.blit(text_surface, text_rect) 