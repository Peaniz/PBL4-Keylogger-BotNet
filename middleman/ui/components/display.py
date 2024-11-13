import pygame
from ui.components.colors import *

class Display:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.status = "Not reachable"
        self.font = font

    def draw(self, surface, offset_y, HEIGHT):
        adjusted_rect = self.rect.copy()
        adjusted_rect.y -= offset_y
        if 0 <= adjusted_rect.y < HEIGHT and adjusted_rect.bottom > 0:
            pygame.draw.rect(surface, GRAY, adjusted_rect)
            pygame.draw.rect(surface, DARK_GRAY, adjusted_rect, 2)
            text_surface = self.font.render(self.text, True, BLACK)
            text_rect = text_surface.get_rect(center=adjusted_rect.center)
            surface.blit(text_surface, text_rect)

    def update_status(self, status):
        self.status = status 