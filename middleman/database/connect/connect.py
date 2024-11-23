import mysql.connector

def connect_to_database(host="localhost", user="root", password="", database="database_pbl4", port=3307):
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
        conn.commit()
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