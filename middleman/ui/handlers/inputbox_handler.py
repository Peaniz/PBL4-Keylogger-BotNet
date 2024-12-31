from database.connect.connect import get_all_victims_ip, add_victim, connect_to_database



def connect_to_db():
    return connect_to_database()

def get_ip_all_victims():
    return get_all_victims_ip()

def insert_new_victim(ip):
    conn=connect_to_database()
    add_victim(conn,ip)
import re

def is_valid_ip(ip):
    """
    Kiểm tra tính hợp lệ của địa chỉ IP.
    """
    pattern = r"^\d{1,3}(\.\d{1,3}){3}$"
    if re.match(pattern, ip):
        return all(0 <= int(octet) <= 255 for octet in ip.split('.'))
    return False
