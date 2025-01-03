import pygame
import textwrap
from ui.components.colors import BLACK, WHITE, GREEN, GRAY
from ui.utils.network import R_tcp

class InputBox:
    def __init__(self, x, y, width, height, host):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.text = ''
        self.prompt = 'Enter command: '
        self.active = False
        
     
        self.font = pygame.font.Font(None, 25)
        self.history = []  
        self.scroll_offset = 0 
        self.cursor_visible = True  
        self.cursor_counter = 0 
        self.host = host

    def handle_event(self, event, port):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = GREEN if self.active else GRAY

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                command = self.text.strip()
                result = R_tcp(self.host, command, port)
                self.history.append(f"$ {command}")
                self.history.append(result)
                self.text = ''

                total_lines = sum(len(textwrap.wrap(line, width=70)) for line in self.history)
                visible_lines = (self.rect.height - 20) // 30  
                if total_lines > visible_lines:
                    self.scroll_offset = (total_lines - visible_lines) * 30
                else:
                    self.scroll_offset = 0

            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 30)
            elif event.button == 5:  # Scroll down
                total_lines = sum(len(textwrap.wrap(line, width=50)) for line in self.history)
                visible_lines = (self.rect.height - 20) // 30
                max_scroll = max(0, (total_lines - visible_lines) * 30)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 30)

    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect)
        y_offset = self.rect.y - self.scroll_offset
        for line in self.history:
            wrapped_lines = line.splitlines() 
            for wrapped_line in wrapped_lines:
           
             
                txt_surface = self.font.render(wrapped_line, True, WHITE)
                surface.blit(txt_surface, (self.rect.x + 5, y_offset))
                y_offset += txt_surface.get_height()

  
        dollar_surface = self.font.render('$ ', True, WHITE)
        surface.blit(dollar_surface, (self.rect.x + 5, y_offset))

        input_surface = self.font.render(self.text, True, WHITE)
        surface.blit(input_surface, (self.rect.x + 20, y_offset))

    
        if self.active and self.cursor_visible:
            cursor_x = 20 + input_surface.get_width()
            pygame.draw.rect(surface, WHITE, 
                           (self.rect.x + cursor_x, y_offset, 2, input_surface.get_height()))

     
        self.cursor_counter += 1
        if self.cursor_counter % 60 < 30:
            self.cursor_visible = True
        else:
            self.cursor_visible = False

    def wrap_line(self, line, width):
        """Helper function to wrap long lines of text without cutting off words too early."""
        return textwrap.fill(line, width=width)