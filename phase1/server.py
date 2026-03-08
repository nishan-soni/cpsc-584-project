import socket
from picrawler import Picrawler 
from time import sleep
from vilib import Vilib
import subprocess
import os

# Initialize your PiCrawler
crawler = Picrawler()           

# --- START THE LIVE VIDEO FEED ---
Vilib.camera_start(vflip=False, hflip=False)
Vilib.display(local=False, web=True)

# --- START THE PHOTO GALLERY SERVER ---
# Ensure the Pictures folder exists
os.makedirs('/home/pi/Pictures', exist_ok=True)
os.makedirs('/home/pi/Videos', exist_ok=True)
# Start a simple HTTP server in the Pictures folder on port 8000
http_server = subprocess.Popen(["python3", "-m", "http.server", "8000"], cwd="/home/pi/Pictures")
print("Photo Gallery live at: http://192.168.1.76:8000")

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
                            Vilib.take_photo('spy_photo', '/home/pi/Pictures')
                            print("📸 Photo taken! Saved to /home/pi/Pictures")
                        elif command == 'toggle_record':
                            if is_recording:
                                Vilib.video_record_stop()
                                is_recording = False
                                print("🛑 Video recording STOPPED.")
                            else:
                                Vilib.video_record_start('spy_video', '/home/pi/Videos')
                                is_recording = True
                                print("🎥 Video recording STARTED! Saving to /home/pi/Videos")
                            
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
                            crawler.do_step([[80,80,-30], [80,80,-30], [80,80,-30], [80,80,-30]], current_speed)
                        elif command == 'strafe_left':
                            crawler.do_step([[50,90,-60], [50,10,-60], [50,10,-60], [50,90,-60]], current_speed)
                        elif command == 'strafe_right':
                            crawler.do_step([[50,10,-60], [50,90,-60], [50,90,-60], [50,10,-60]], current_speed)
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

if __name__ == "__main__":
    start_server()