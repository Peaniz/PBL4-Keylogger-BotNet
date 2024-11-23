import os
import socket
import threading

class FileReceiver:
    def __init__(self, host, port=5003, on_complete=None):
        self.host = host
        self.port = port
        self.running = True
        self.receive_thread = None
        self.on_complete = on_complete
    
    def receive_file(self, host, port, save_directory='received_files'):
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host,port))
                sock.listen()
                print(f"Listening for files on {host}:{port}")
                conn, addr = sock.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while self.running:
                        try:
                            file_info = conn.recv(1024).strip().decode('utf-8')
                            if not file_info:
                                print("No more file info received.")
                                if self.on_complete:
                                    self.on_complete()
                                return False

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
                            if self.on_complete:
                                self.on_complete()
                            break
        except Exception as e:
            print(f"Connection error: {e}")
            if self.on_complete:
                self.on_complete()
        finally:
            self.running = False
            if self.on_complete:
                self.on_complete()
    
    def start(self):
        self.running = True
        self.receive_thread = threading.Thread(target=lambda: self.receive_file(self.host, self.port))
        self.receive_thread.daemon = True
        self.receive_thread.start()

    def stop(self):
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
def filereceiver(host, port=5003, on_complete=None):
    receiver = FileReceiver(host, port, on_complete)
    receiver.start()
    return receiver
