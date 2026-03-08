import socket
from picrawler import Picrawler 
from time import sleep
from vilib import Vilib

# Initialize your PiCrawler
crawler = Picrawler()           

# --- START THE LIVE VIDEO FEED ---
Vilib.camera_start(vflip=False, hflip=False)
Vilib.display(local=False, web=True)

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
                        if command in ['forward', 'back', 'left', 'right', 'stop', 'strafe_left', 'strafe_right']:
                            current_move = command
                        # --- RIGHT JOYSTICK (Body Lean / Camera Tilt) ---
                        elif command == 'look_up':
                            # Front legs straight (-90), back legs crouched (-30)
                            crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-30], [50,50,-30]], 80)
                        elif command == 'look_down':
                            # Front legs crouched (-30), back legs straight (-90)
                            crawler.do_step([[50,50,-30], [50,50,-30], [50,50,-90], [50,50,-90]], 80)
                        elif command == 'lean_left':
                            crawler.do_step([[50,50,-90], [50,50,-30], [50,50,-30], [50,50,-90]], 80)
                        elif command == 'lean_right':
                            crawler.do_step([[50,50,-30], [50,50,-90], [50,50,-90], [50,50,-30]], 80)
                        elif command == 'cam_stop':
                            crawler.do_action('stand', 1, 80)
                            
                        # --- THE SPY POSTURES (Face Buttons) ---
                        elif command == 'high_posture':
                            crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-90], [50,50,-90]], 80)
                        elif command == 'stealth_mode':
                            crawler.do_step([[50,50,-30], [50,50,-30], [50,50,-30], [50,50,-30]], 80)
                        elif command == 'stand':
                            current_move = 'stop'
                            crawler.do_action('stand', 1, 80)
                            
                except socket.timeout:
                    # Timeout reached, meaning we haven't received a new command, 
                    # keep repeating the continuous movement
                    pass
                except ConnectionResetError:
                    print("Connection lost unexpectedly.")
                    break
                
                # Execute continuous movement
                if current_move == 'forward':
                    crawler.do_action('forward', 1, 80)
                elif current_move == 'back':
                    crawler.do_action('backward', 1, 80)
                elif current_move == 'right':
                    crawler.do_action('turn right', 1, 80)
                elif current_move == 'left':
                    crawler.do_action('turn left', 1, 80)
                elif current_move == 'strafe_left':
                    # Phase 1: Lift RF & LR, move left. Body shifts left over grounded LF & RR.
                    crawler.do_step([[50, 10, -30], [50, 10, -60], [50, 90, -30], [50, 90, -60]], 80)
                    crawler.do_step([[50, 10, -60], [50, 10, -60], [50, 90, -60], [50, 90, -60]], 80)
                    # Phase 3: Lift LF & RR, move left. Body shifts left over grounded RF & LR.
                    crawler.do_step([[50, 90, -60], [50, 90, -30], [50, 10, -60], [50, 10, -30]], 80)
                    crawler.do_step([[50, 90, -60], [50, 90, -60], [50, 10, -60], [50, 10, -60]], 80)
                elif current_move == 'strafe_right':
                    # Phase 1: Lift RF & LR, move right. Body shifts right over grounded LF & RR.
                    crawler.do_step([[50, 90, -30], [50, 90, -60], [50, 10, -30], [50, 10, -60]], 80)
                    crawler.do_step([[50, 90, -60], [50, 90, -60], [50, 10, -60], [50, 10, -60]], 80)
                    # Phase 3: Lift LF & RR, move right. Body shifts right over grounded RF & LR.
                    crawler.do_step([[50, 10, -60], [50, 10, -30], [50, 90, -60], [50, 90, -30]], 80)
                    crawler.do_step([[50, 10, -60], [50, 10, -60], [50, 90, -60], [50, 90, -60]], 80)

    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()