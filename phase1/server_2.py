import socket
from picrawler import Picrawler
from time import sleep
from vilib import Vilib
import subprocess
import os
import cv2
import numpy as np
import threading
import time
from flask import Flask, Response

# Initialize PiCrawler
crawler = Picrawler()

# --- START CAMERA (no web display — we serve our own annotated stream) ---
Vilib.camera_start(vflip=False, hflip=False, size=(1280, 720))
# NOTE: Do NOT call Vilib.display() — we run our own MJPEG server below

# -----------------------------------------------------------------------
# MULTI-COLOR DETECTION + ANNOTATED MJPEG STREAM
# We grab Vilib.img, draw boxes for red and green, then serve that
# annotated frame ourselves on port 9000 at /mjpg — same URL as before.
# -----------------------------------------------------------------------

color_detections = {
    "red":   {"n": 0, "x": 0, "y": 0, "w": 0, "h": 0},
    "green": {"n": 0, "x": 0, "y": 0, "w": 0, "h": 0},
}

# Shared annotated frame (JPEG bytes) for the MJPEG stream
latest_jpeg = None
jpeg_lock = threading.Lock()

def multi_color_detect_loop():
    global latest_jpeg
    kernel = np.ones((5, 5), np.uint8)

    while True:
        try:
            frame = Vilib.img
            if frame is None:
                time.sleep(0.05)
                continue

            # Convert to numpy array if it isn't one already
            # (Picamera2 can return various formats)
            if not isinstance(frame, np.ndarray):
                frame = np.array(frame)

            if frame.size == 0:
                time.sleep(0.05)
                continue

            # Vilib/Picamera2 gives RGB, OpenCV needs BGR
            if frame.shape[2] == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # Work on a copy so we don't interfere with Vilib internals
            annotated = frame.copy()
            hsv = cv2.cvtColor(annotated, cv2.COLOR_BGR2HSV)

            # Red needs two HSV ranges because it wraps around 180
            red_mask1 = cv2.inRange(hsv, np.array([0,   120, 80]),  np.array([10,  255, 255]))
            red_mask2 = cv2.inRange(hsv, np.array([160, 120, 80]),  np.array([180, 255, 255]))
            red_mask  = cv2.dilate(red_mask1 | red_mask2, kernel)

            # Green
            green_mask = cv2.dilate(
                cv2.inRange(hsv, np.array([40, 70, 70]), np.array([80, 255, 255])),
                kernel
            )

            for color_name, mask, box_color, label in [
                ("red",   red_mask,   (0, 0, 255), "ENEMY"),
                ("green", green_mask, (0, 255, 0), "TARGET"),
            ]:
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                valid = [c for c in contours if cv2.contourArea(c) > 800]

                if valid:
                    largest = max(valid, key=cv2.contourArea)
                    bx, by, bw, bh = cv2.boundingRect(largest)
                    cx = bx + bw // 2
                    cy = by + bh // 2

                    cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), box_color, 3)
                    cv2.putText(annotated, label, (bx, max(by - 10, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2)

                    color_detections[color_name] = {"n": len(valid), "x": cx, "y": cy, "w": bw, "h": bh}
                else:
                    color_detections[color_name] = {"n": 0, "x": 0, "y": 0, "w": 0, "h": 0}

            # Encode annotated frame as JPEG for streaming
            ok, jpg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                with jpeg_lock:
                    latest_jpeg = jpg.tobytes()

        except Exception as e:
            print(f"[color detect] {e}")

        time.sleep(0.033)  # ~30 fps


def generate_mjpeg():
    while True:
        with jpeg_lock:
            frame = latest_jpeg
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)


# Start detection thread
threading.Thread(target=multi_color_detect_loop, daemon=True).start()

# Start our own annotated MJPEG Flask server on port 9000
stream_app = Flask(__name__)

@stream_app.route('/mjpg')
def mjpg():
    return Response(generate_mjpeg(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

threading.Thread(target=lambda: stream_app.run(host='0.0.0.0', port=9000, threaded=True, use_reloader=False, debug=False), daemon=True).start()
print("Annotated spy camera feed live at: http://172.17.10.193:9000/mjpg")

# -----------------------------------------------------------------------

# --- PHOTO GALLERY SERVER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
PICS_DIR = os.path.join(MEDIA_DIR, 'Pictures')
VIDS_DIR = os.path.join(MEDIA_DIR, 'Videos')

os.makedirs(PICS_DIR, exist_ok=True)
os.makedirs(VIDS_DIR, exist_ok=True)

Vilib.rec_video_set["path"] = VIDS_DIR + "/"
Vilib.rec_video_set["framesize"] = (1280, 720)
Vilib.rec_video_set["fps"] = 10.0

http_server = subprocess.Popen(["python3", "-m", "http.server", "8000"],
                               cwd=MEDIA_DIR, stderr=subprocess.DEVNULL)
print(f"Photo Gallery live at: http://172.17.10.193:8000")

HOST = '0.0.0.0'
PORT = 65432

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)

    print(f"PiCrawler Server listening on port {PORT}...")
    server_socket.settimeout(1.0)

    try:
        while True:
            try:
                client, addr = server_socket.accept()
                print(f"Connected to Controller at {addr}")
            except socket.timeout:
                continue

            client.settimeout(0.1)
            buffer = ""
            current_move = 'stop'
            current_speed = 60
            is_recording = False
            current_video_name = None

            def rumble_monitor():
                while True:
                    try:
                        total_spotted = (
                            color_detections["red"]["n"] +
                            color_detections["green"]["n"]
                        )
                        if total_spotted > 0:
                            client.sendall(b"RUMBLE\n")
                            time.sleep(1.0)
                        else:
                            time.sleep(0.1)
                    except Exception as e:
                        print(e)
                        break

            threading.Thread(target=rumble_monitor, daemon=True).start()

            while True:
                try:
                    if current_move == 'stop':
                        client.settimeout(0.1)
                    else:
                        client.settimeout(0.001)

                    data = client.recv(1024)
                    if not data:
                        break

                    buffer += data.decode('utf-8')

                    while '\n' in buffer:
                        command, buffer = buffer.split('\n', 1)
                        command = command.strip()

                        if not command:
                            continue

                        if command in ['forward', 'back', 'left', 'right', 'stop']:
                            current_move = command
                        elif command == 'speed_sprint':
                            current_speed = 100
                            print(f"🏎️ SPRINT MODE ENGAGED (Speed: {current_speed})")
                        elif command == 'speed_ghost':
                            current_speed = 20
                            print(f"👻 GHOST MODE ENGAGED (Speed: {current_speed})")
                        elif command == 'speed_normal':
                            current_speed = 60
                            print(f"🚶 NORMAL SPEED (Speed: {current_speed})")

                        elif command == 'take_photo':
                            timestamp = int(time.time())
                            file_name = f'spy_photo_{timestamp}'
                            Vilib.take_photo(file_name, PICS_DIR)
                            print(f"📸 Photo taken! Saved to {PICS_DIR}/{file_name}.jpg")

                        elif command == 'toggle_record':
                            if is_recording:
                                Vilib.rec_video_stop()
                                is_recording = False
                                avi_path = f"{Vilib.rec_video_set['path']}{current_video_name}.avi"
                                mp4_path = f"{Vilib.rec_video_set['path']}{current_video_name}.mp4"
                                print(f"🛑 Video recording STOPPED.")

                                def convert_video(avi, mp4):
                                    try:
                                        subprocess.run(['ffmpeg', '-y', '-i', avi, '-vcodec', 'libx264', '-crf', '28', mp4],
                                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        if os.path.exists(mp4):
                                            print(f"🎬 Conversion complete: {mp4}")
                                            os.remove(avi)
                                    except FileNotFoundError:
                                        print("⚠️ FFmpeg not found — video stays as .avi")

                                threading.Thread(target=convert_video, args=(avi_path, mp4_path), daemon=True).start()

                            else:
                                from time import strftime, localtime
                                current_video_name = strftime("%Y-%m-%d-%H.%M.%S", localtime())
                                Vilib.rec_video_set["name"] = current_video_name
                                Vilib.rec_video_run()
                                Vilib.rec_video_start()
                                is_recording = True
                                print(f"🎥 Recording started: {current_video_name}.avi")

                        elif command == 'look_up':
                            crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-30], [50,50,-30]], current_speed)
                        elif command == 'look_down':
                            crawler.do_step([[50,50,-30], [50,50,-30], [50,50,-90], [50,50,-90]], current_speed)
                        elif command == 'lean_left':
                            crawler.do_step([[50,50,-90], [50,50,-30], [50,50,-30], [50,50,-90]], current_speed)
                        elif command == 'lean_right':
                            crawler.do_step([[50,50,-30], [50,50,-90], [50,50,-90], [50,50,-30]], current_speed)
                        elif command == 'cam_stop':
                            crawler.do_action('stand', 1, current_speed)

                        elif command == 'high_posture':
                            crawler.do_step([[50,50,-110], [50,50,-110], [50,50,-110], [50,50,-110]], current_speed)
                        elif command == 'stealth_mode':
                            crawler.do_step([[0,0,0], [0,0,0], [0,0,0], [0,0,0]], current_speed)
                        elif command == 'stand':
                            crawler.do_action('stand', 1, current_speed)

                except socket.timeout:
                    pass
                except ConnectionResetError:
                    print("Connection lost unexpectedly.")
                    break

                if current_move == 'forward':
                    crawler.do_action('forward', 1, current_speed)
                elif current_move == 'back':
                    crawler.do_action('backward', 1, current_speed)
                elif current_move == 'right':
                    crawler.do_action('turn right', 1, 85)
                elif current_move == 'left':
                    crawler.do_action('turn left', 1, 85)

    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()
        http_server.terminate()
        print("Photo Gallery server stopped.")
        try:
            Vilib.camera_close()
        except:
            pass

if __name__ == "__main__":
    start_server()