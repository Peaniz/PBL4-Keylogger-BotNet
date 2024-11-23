import queue
import pygame
import socket
import zlib
import threading
import select


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


class ScreenReceiver:
    def __init__(self, host, port=5001):
        self.host = host
        self.port = port
        self.running = True
        self.screen = pygame.display.get_surface()
        self.frame_surface = pygame.Surface((600, 300))  # Khung cố định
        self.frame_surface.fill((0, 0, 0))  # Nền đen cho khung
        self.screen_panel_rect = self.frame_surface.get_rect(center=self.screen.get_rect().center)
        self.receive_thread = None
        self.buffer = None
        self.lock = threading.Lock()
        self.double_buffer = None

    def receive_frames(self):
        try:
            with socket.socket() as sock:
                sock.connect((self.host, self.port))
                sock.settimeout(1.0)  # Add timeout

                while self.running:

                    try:
                        size_len = sock.recv(1)
                        if not size_len:
                            print("Disconnected from server.")
                            break

                        size_len = int.from_bytes(size_len, byteorder='big')
                        if size_len != 4:
                            print(f"Invalid size length: {size_len}, expected 4")
                            continue

                        size_bytes = sock.recv(4)
                        if len(size_bytes) != 4:
                            print("Failed to receive size bytes")
                            continue

                        size = int.from_bytes(size_bytes, byteorder='big')
                        if size <= 0 or size > 1000000:
                            print(f"Invalid frame size: {size}")
                            continue

                        pixels = recvall(sock, size)
                        if not pixels:
                            print("Received incomplete frame data.")
                            continue

                        try:
                            pixels = zlib.decompress(pixels)
                            img = pygame.image.fromstring(pixels, (600, 300), 'RGB')

                            with self.lock:
                                self.buffer = img

                        except Exception as e:
                            print(f"Error processing frame: {e}")
                            continue


                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"Error receiving frame: {e}")
                        break

        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            self.running = False

    def start(self):
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_frames)
        self.receive_thread.daemon = True  # Make thread daemon so it exits when main program exits
        self.receive_thread.start()

    def stop(self):
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)  # Wait max 1 second for thread to finish

    def update_screen(self):
        frame_queue = queue.Queue(maxsize=1)

        while self.running:
            with self.lock:
                if self.buffer:
                    if not frame_queue.full():
                        frame_queue.put(self.buffer.copy())
                    self.buffer = None

            if not frame_queue.empty():
                self.double_buffer = frame_queue.get()

            if self.double_buffer:
                pygame.display.update([self.screen_panel_rect])


def screenreceiver(host, port=5001):
    receiver = ScreenReceiver(host, port)
    receiver.start()
    threading.Thread(target=receiver.update_screen, daemon=True).start()
    return receiver