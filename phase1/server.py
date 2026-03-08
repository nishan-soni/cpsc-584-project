import socket
from picrawler import Picrawler 
from time import sleep
from vilib import Vilib
import subprocess
import os

# Initialize your PiCrawler
crawler = Picrawler()           

# --- START THE LIVE VIDEO FEED ---
# Increased resolution to 720p HD (1280x720) to fill more of the screen!
Vilib.camera_start(vflip=False, hflip=False, size=(1280, 720))
Vilib.display(local=False, web=True)

# --- START CAMERA HUD EFFECTS ---
import cv2
original_putText = cv2.putText
def custom_putText(img, text, org, fontFace, fontScale, color, thickness=1, lineType=cv2.LINE_8, bottomLeftOrigin=False):
    if text == "red": text = "ENEMY"
    return original_putText(img, text, org, fontFace, fontScale, color, thickness, lineType, bottomLeftOrigin)
cv2.putText = custom_putText

Vilib.color_detect("red")        # Draw bounding boxes around red objects

# --- START THE PHOTO GALLERY SERVER ---
# Ensure the media folders exist inside the project directory using absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
PICS_DIR = os.path.join(MEDIA_DIR, 'Pictures')
VIDS_DIR = os.path.join(MEDIA_DIR, 'Videos')

os.makedirs(PICS_DIR, exist_ok=True)
os.makedirs(VIDS_DIR, exist_ok=True)

# Important for Vilib: set the path exactly like the example script
Vilib.rec_video_set["path"] = VIDS_DIR + "/"

# Start a simple HTTP server in the media folder on port 8000
http_server = subprocess.Popen(["python3", "-m", "http.server", "8000"], cwd=MEDIA_DIR)
print(f"Photo Gallery live at: http://192.168.1.76:8000")

# Define Server details
HOST = '0.0.0.0'
PORT = 65432

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    
    print(f"PiCrawler Server listening on port {PORT}...")
    print("Spy Camera Feed live at: http://192.168.1.76:9000/mjpg")

    try:
        while True:
            client, addr = server_socket.accept()
            print(f"Connected to Controller at {addr}")
            
            client.settimeout(0.1)  # Allow socket to timeout so robot can keep moving
            buffer = ""
            current_move = 'stop'
            current_speed = 60
            is_recording = False
            current_video_name = None
            
            # --- START ENEMY DETECTION RUMBLE THREAD ---
            def rumble_monitor():
                import time
                while True:
                    try:
                        # Check if Vilib sees any red objects
                        enemies_spotted = 0
                        
                        if 'color_n' in Vilib.detect_obj_parameter:
                            enemies_spotted += Vilib.detect_obj_parameter['color_n']
                            
                        if enemies_spotted > 0:
                            client.sendall(b"RUMBLE\n")
                            time.sleep(1.0) # Wait 1 second before rumbling again
                        else:
                            time.sleep(0.1) # Check again shortly
                    except Exception:
                        break # Exit thread if client disconnects or socket fails
                        
            import threading
            threading.Thread(target=rumble_monitor, daemon=True).start()
            
            while True:
                try:
                    # If we are supposed to be moving, minimize the timeout to avoid movement stutter
                    # Otherwise, block briefly to avoid high CPU usage
                    if current_move == 'stop':
                        client.settimeout(0.1)
                    else:
                        client.settimeout(0.001)

                    data = client.recv(1024)
                    if not data:
                        break # Client disconnected
                    
                    buffer += data.decode('utf-8')
                    
                    while '\n' in buffer:
                        command, buffer = buffer.split('\n', 1)
                        command = command.strip()
                        
                        if not command:
                            continue
                            
                        # Update current movement state
                        if command in ['forward', 'back', 'left', 'right', 'stop']:
                            current_move = command
                        # --- SPEED CONTROLS (Triggers) ---
                        elif command == 'speed_sprint':
                            current_speed = 100
                            print(f"🏎️ SPRINT MODE ENGAGED (Speed: {current_speed})")
                        elif command == 'speed_ghost':
                            current_speed = 20
                            print(f"👻 GHOST MODE ENGAGED (Speed: {current_speed})")
                        elif command == 'speed_normal':
                            current_speed = 60
                            print(f"🚶 NORMAL SPEED (Speed: {current_speed})")
                            
                        # --- CAMERA CONTROLS (Face Buttons) ---
                        elif command == 'take_photo':
                            import time
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
                                print(f"🛑 Video recording STOPPED. Saved to {avi_path}")
                                
                                # Launch a background conversion so the robot doesn't freeze while processing!
                                print(f"🔄 Converting {current_video_name}.avi into an MP4 so you can watch it in your browser...")
                                def convert_video(avi, mp4):
                                    import subprocess, os
                                    try:
                                        # Use ffmpeg to convert to H.264 mp4 which is universally supported by web browsers
                                        subprocess.run(['ffmpeg', '-y', '-i', avi, '-vcodec', 'libx264', '-crf', '28', mp4], 
                                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        if os.path.exists(mp4):
                                            print(f"🎬 Conversion complete! You can now click on {current_video_name}.mp4 in your browser!")
                                            os.remove(avi) # Delete original to save SD card space
                                    except FileNotFoundError:
                                        print("⚠️ FFmpeg is not installed on the Raspberry Pi! Video will remain as .avi")
                                        
                                import threading
                                threading.Thread(target=convert_video, args=(avi_path, mp4_path), daemon=True).start()
                                
                            else:
                                from time import strftime, localtime
                                current_video_name = strftime("%Y-%m-%d-%H.%M.%S", localtime())
                                Vilib.rec_video_set["name"] = current_video_name
                                Vilib.rec_video_run()
                                Vilib.rec_video_start()
                                is_recording = True
                                print(f"🎥 Video recording STARTED! Saving as {current_video_name}.avi in {VIDS_DIR}")
                            
                        # --- RIGHT JOYSTICK (Body Lean / Camera Tilt) ---
                        elif command == 'look_up':
                            # Front legs straight (-90), back legs crouched (-30)
                            crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-30], [50,50,-30]], current_speed)
                        elif command == 'look_down':
                            # Front legs crouched (-30), back legs straight (-90)
                            crawler.do_step([[50,50,-30], [50,50,-30], [50,50,-90], [50,50,-90]], current_speed)
                        elif command == 'lean_left':
                            crawler.do_step([[50,50,-90], [50,50,-30], [50,50,-30], [50,50,-90]], current_speed)
                        elif command == 'lean_right':
                            crawler.do_step([[50,50,-30], [50,50,-90], [50,50,-90], [50,50,-30]], current_speed)
                        elif command == 'cam_stop':
                            crawler.do_action('stand', 1, current_speed)
                            
                        # --- THE SPY POSTURES (Face Buttons) ---
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
                
                # Execute continuous movement
                if current_move == 'forward':
                    crawler.do_action('forward', 1, current_speed)
                elif current_move == 'back':
                    crawler.do_action('backward', 1, current_speed)
                elif current_move == 'right':
                    crawler.do_action('turn right', 1, current_speed)
                elif current_move == 'left':
                    crawler.do_action('turn left', 1, current_speed)

    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()
        http_server.terminate()
        Vilib.camera_close()
        print("Photo Gallery server stopped.")

if __name__ == "__main__":
    start_server()