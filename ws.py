from flask import Response, Flask, render_template, jsonify
import threading
import argparse
import time
import cv2
from pyimagesearch.motion_detection.orange_detection import OrangeCircleDetector, draw_shapes
from app.pixhawk_reader import PixhawkReader

# Initialize global variables
outputFrame = None
outputMask = None
lock = threading.Lock()

# Initialize Flask application
app = Flask(__name__)

# Initialize video capture
vs = cv2.VideoCapture(0)
time.sleep(2.0)

# Initialize PixhawkReader
pixhawk_reader = PixhawkReader()

@app.route("/")
def index():
    return render_template("index.html")

def detect_motion(frameCount):
    global vs, outputFrame, outputMask, lock
    detector = OrangeCircleDetector()
    while True:
        ret, frame = vs.read()
        if not ret:
            continue
        frame = cv2.resize(frame, (400, 300))
        mask, shapes = detector.detect(frame)
        draw_shapes(frame, shapes)
        with lock:
            outputFrame = frame.copy()
            outputMask = mask.copy()

def generate_frames():
    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not flag:
                continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

def generate_mask():
    global outputMask, lock
    while True:
        with lock:
            if outputMask is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputMask)
            if not flag:
                continue
        yield (b'--mask\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/mask_feed")
def mask_feed():
    return Response(generate_mask(), mimetype="multipart/x-mixed-replace; boundary=mask")

@app.route("/pixhawk_data")
def pixhawk_data():
    data = pixhawk_reader.get_data()
    return jsonify(data)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--ip", type=str, required=True, help="IP address of the device")
    ap.add_argument("-o", "--port", type=int, required=True, help="Ephemeral port number of the server (1024 to 65535)")
    ap.add_argument("-f", "--frame-count", type=int, default=32, help="# of frames used to construct the background model")
    args = vars(ap.parse_args())

    t = threading.Thread(target=detect_motion, args=(args["frame_count"],))
    t.daemon = True
    t.start()

    app.run(host=args["ip"], port=args["port"], debug=True, threaded=True, use_reloader=False)

vs.release()
