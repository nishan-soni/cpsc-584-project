import socket
from picrawler import Picrawler 
from time import sleep
from vilib import Vilib
import subprocess
import os

# Initialize: PiCrawler
crawler = Picrawler()           

# --- START THE LIVE VIDEO FEED ---
Vilib.camera_start(vflip=False, hflip=False, size=(1280, 720))
Vilib.display(local=False, web=True)

# --- START CAMERA HUD EFFECTS ---
import cv2
original_putText = cv2.putText
def custom_putText(img, text, org, fontFace, fontScale, color, thickness=1, lineType=cv2.LINE_8, bottomLeftOrigin=False):
    if text == "red": text = "ENEMY"
    return original_putText(img, text, org, fontFace, fontScale, color, thickness, lineType, bottomLeftOrigin)
cv2.putText = custom_putText

Vilib.color_detect("red")  

# --- START THE PHOTO GALLERY SERVER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
PICS_DIR = os.path.join(MEDIA_DIR, 'Pictures')
VIDS_DIR = os.path.join(MEDIA_DIR, 'Videos')

os.makedirs(PICS_DIR, exist_ok=True)
os.makedirs(VIDS_DIR, exist_ok=True)

Vilib.rec_video_set["path"] = VIDS_DIR + "/"
Vilib.rec_video_set["framesize"] = (1280, 720)
Vilib.rec_video_set["fps"] = 10.0


# Start a simple HTTP server in the media folder on port 8000
http_server = subprocess.Popen(["python3", "-m", "http.server", "8000"], 
                               cwd=MEDIA_DIR, stderr=subprocess.DEVNULL)
print(f"Photo Gallery live at: http://172.17.10.193:8000")

# Define Server details
HOST = '0.0.0.0'
PORT = 65432

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    
    print(f"PiCrawler Server listening on port {PORT}...")
    print("Spy Camera Feed live at: http://172.17.10.193:9000/mjpg")

    server_socket.settimeout(1.0) # Allow interrupt to break the server wait loop

    try:
        while True:
            try:
                client, addr = server_socket.accept()
                print(f"Connected to Controller at {addr}")
            except socket.timeout:
                continue # Check for KeyboardInterrupt and try again
            
            client.settimeout(0.1)  
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
                        enemies_spotted = 0
                        
                        if 'color_n' in Vilib.detect_obj_parameter:
                            enemies_spotted += Vilib.detect_obj_parameter['color_n']
                            
                        if enemies_spotted > 0:
                            client.sendall(b"RUMBLE\n")
                            time.sleep(1.0) 
                        else:
                            time.sleep(0.1) 
                    except Exception:
                        break 

            import threading
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
                                
                                # Background conversion so the robot doesn't freeze while processing!
                                print(f"🔄 Converting {current_video_name}.avi into an MP4 so you can watch it in your browser...")
                                def convert_video(avi, mp4):
                                    import subprocess, os
                                    try:
                                        subprocess.run(['ffmpeg', '-y', '-i', avi, '-vcodec', 'libx264', '-crf', '28', mp4], 
                                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                        if os.path.exists(mp4):
                                            print(f"🎬 Conversion complete! You can now click on {current_video_name}.mp4 in your browser!")
                                            os.remove(avi)
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
                            crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-30], [50,50,-30]], current_speed)
                        elif command == 'look_down':
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
        print("Photo Gallery server stopped.")
        try:
            Vilib.camera_close()
        except:
            pass

if __name__ == "__main__":
    start_server()