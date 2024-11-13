import socket

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
        return results.strip()
    except Exception as e:
        return f"Error when sending command: {e}" 