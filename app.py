# app.py
from flask import Flask, render_template, Response
import sys
import threading
import time
from collections import deque


class LogBuffer:
    def __init__(self, maxlen=500):
        self.buffer = deque(maxlen=maxlen)
        self.lock = threading.Lock()

    def write(self, message):
        if message.strip():
            with self.lock:
                self.buffer.append(message.strip())

    def read_new(self, last_index):
        with self.lock:
            current_len = len(self.buffer)
            if last_index >= current_len:
                return [], current_len
            new_lines = list(self.buffer)[last_index:]
            return new_lines, current_len

    def flush(self):
        pass

log_buffer = LogBuffer()
sys.stdout = log_buffer


import func
import const
import serial_handler
from tcp_server import start_tcp_server

# === Flask app ===
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return render_template('video_feed.html', CAMERA_URL=const.CAMERA_URL, CAMERA_CMD=const.CAMERA_CMD)

@app.route('/vnc')
def vnc():
    return render_template('vnc.html')

@app.route('/workspace')
def table():
    return render_template('workspace.html')

@app.route('/submit', methods=['POST'])
def submit():
    return func.submit_connection()

@app.route('/submit_service', methods=['POST'])
def submit_service():
    return func.submit_connection_service()

@app.route('/connection')
def connection():
    return render_template('connection.html', local_ip="192.168.12.175", port_status={})

@app.route('/logs/stream')
def stream_logs():
    def generate():
        last_index = 0
        while True:
            lines, last_index = log_buffer.read_new(last_index)
            for line in lines:
                yield f"data: {line}\n\n"
            time.sleep(0.3)  
    return Response(generate(), mimetype='text/event-stream')

def i2c_keep_alive():
    from serial_handler import send_i2c
    import time
    while True:
        try:
            send_i2c("PING")
            print("PING\n")
        except Exception as e:
            print(f"[KEEP-ALIVE ERROR] {e}")
        time.sleep(3)
        
if __name__ == '__main__':

    print("=== START AUTODETECT MODULES ===")
    serial_handler.auto_detect_devices()

    print("=== START TCP SERVER ===")
    tcp_thread = threading.Thread(target=start_tcp_server, daemon=True)
    tcp_thread.start()
    
    print("=== START I2C BACKGROUND PING ===")
    keepalive_thread = threading.Thread(target=i2c_keep_alive, daemon=True)
    keepalive_thread.start()

    print(f"=== START FLASK APP {const.SERVER_PORT} ===")
    app.run(host='0.0.0.0', port=const.SERVER_PORT, debug=False, use_reloader=False)
    
    print("START!")
