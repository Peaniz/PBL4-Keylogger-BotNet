import queue
import zlib

import pygame
import socket
import threading
import select
import numpy as np
import cv2


def recvall(sock, size):
    buf = b''
    try:
        while len(buf) < size:
            ready, _, _ = select.select([sock], [], [], 1.0)  # Chờ tối đa 1 giây
            if ready:
                data = sock.recv(size - len(buf))
                if not data:
                    return None
                buf += data
            else:
                break  # Thoát nếu không có dữ liệu
        return buf if len(buf) == size else None
    except Exception as e:
        print(f"Error in recvall: {e}")
        return None


class CameraReceiver:
    def __init__(self, host, port=5002):
        self.host = host
        self.port = port
        self.running = True
        self.screen = pygame.display.get_surface()
        self.frame_surface = pygame.Surface((800, 450))
        self.frame_surface.fill((0, 0, 0))
        self.screen_panel_rect = pygame.Rect(
            (self.screen.get_width() - 800) // 2,
            (self.screen.get_height() - 450) // 2,
            600, 300
        )
        self.receive_thread = None
        self.buffer = None
        self.double_buffer = None
        self.lock = threading.Lock()
        self.update_thread = None
        self.frame_ready = threading.Event()  # Add event for frame synchronization
        self.error_surface = None
        self.connection_error = False

    def create_error_surface(self, message):
        """Create an error message surface"""
        surface = pygame.Surface((800, 450))
        surface.fill((0, 0, 0))
        text = pygame.font.Font(None, 36).render(message, True, (255, 255, 255))
        text_rect = text.get_rect(center=(400, 225))
        surface.blit(text, text_rect)
        return surface

    def update_screen(self):
        while self.running:
            if self.connection_error and self.error_surface:
                with self.lock:
                    self.double_buffer = self.error_surface
            else:
                if self.frame_ready.wait(timeout=0.1):
                    self.frame_ready.clear()
                    with self.lock:
                        if self.buffer:
                            self.double_buffer = self.buffer
                            self.buffer = None
            pygame.time.wait(16)

    def receive_frames(self):
        try:
            with socket.socket() as sock:
                try:
                    sock.connect((self.host, self.port))
                except ConnectionRefusedError:
                    print("Could not connect to camera")
                    self.error_surface = self.create_error_surface("Camera Not Connected")
                    self.connection_error = True
                    return
                except Exception as e:
                    print(f"Connection error: {e}")
                    self.error_surface = self.create_error_surface("Connection Error")
                    self.connection_error = True
                    return

                sock.settimeout(1.0)
                while self.running:
                    try:
                        # Get size length
                        size_len = sock.recv(1)
                        if not size_len:
                            print("Disconnected from server.")
                            break

                        size_len = int.from_bytes(size_len, byteorder='big')
                        if size_len != 4:
                            print(f"Invalid size length: {size_len}, expected 4")
                            continue

                        # Get frame size
                        size_bytes = sock.recv(4)
                        if len(size_bytes) != 4:
                            print("Failed to receive size bytes")
                            continue

                        size = int.from_bytes(size_bytes, byteorder='big')
                        if size <= 0 or size > 1000000:  # 1MB max
                            print(f"Invalid frame size: {size}")
                            continue

                        # Get frame data
                        pixels = recvall(sock, size)
                        if not pixels:
                            print("Received incomplete frame data.")
                            continue

                        try:
                            # Decompress and process frame
                            pixels = zlib.decompress(pixels)
                            img = cv2.imdecode(np.frombuffer(pixels, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if img is not None:
                                # Convert and resize frame
                                img = cv2.resize(img, (800, 450))
                                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                img = pygame.surfarray.make_surface(img.swapaxes(0, 1))
                                
                                with self.lock:
                                    self.buffer = img
                                self.frame_ready.set()  # Signal new frame is ready

                        except Exception as e:
                            print(f"Error processing frame: {e}")
                            continue

                        # After processing the frame successfully
                        self.connection_error = False
                        self.error_surface = None

                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error receiving frame: {e}")
                        self.error_surface = self.create_error_surface("Connection Lost")
                        self.connection_error = True
                        break

        except Exception as e:
            print(f"Connection error: {e}")
            self.error_surface = self.create_error_surface("Connection Error")
            self.connection_error = True
        finally:
            self.running = False
            self.frame_ready.set()

    def start(self):
        self.running = True
        self.frame_ready.clear()
        
        self.receive_thread = threading.Thread(target=self.receive_frames)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        self.update_thread = threading.Thread(target=self.update_screen)
        self.update_thread.daemon = True
        self.update_thread.start()

    def stop(self):
        self.running = False
        self.frame_ready.set()  # Signal threads to exit
        
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)


def camerareceiver(host, port=5002):
    receiver = CameraReceiver(host, port)
    receiver.start()
    return receiver