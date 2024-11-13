import pygame
import socket
import zlib
import threading

def recvall(sock, size):
    """Nhận chính xác 'size' byte từ socket."""
    buf = b''
    try:
        sock.settimeout(1.0)  # Add timeout to prevent hanging
        while len(buf) < size:
            data = sock.recv(min(size - len(buf), 8192))  # Read in chunks
            if not data:
                return None
            buf += data
        return buf
    except socket.timeout:
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
        self.screen_panel_rect = pygame.Rect(100, 70, 600, 300)
        self.receive_thread = None

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
                            
                            # Use a lock or event to synchronize screen updates
                            if pygame.display.get_init():
                                self.screen.blit(img, self.screen_panel_rect.topleft)
                                pygame.display.update([self.screen_panel_rect])
                            
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

def screenreceiver(host, port=5001):
    receiver = ScreenReceiver(host, port)
    receiver.start()
    return receiver 