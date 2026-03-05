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
    print("Spy Camera Feed live at: http://192.168.1.75:9000/mjpg")

    try:
        while True:
            client, addr = server_socket.accept()
            print(f"Connected to Controller at {addr}")
            
            while True:
                data = client.recv(1024)
                if not data:
                    break # Client disconnected
                
                commands = data.decode('utf-8').strip().split('\n')
                
                for command in commands:
                    if not command:
                        continue
                        
                    # --- LEFT JOYSTICK (Movement) ---
                    if command == 'forward':
                        crawler.do_action('forward', 1, 80)
                    elif command == 'back':
                        crawler.do_action('backward', 1, 80)
                    elif command == 'right':
                        crawler.do_action('turn right', 1, 80)
                    elif command == 'left':
                        crawler.do_action('turn left', 1, 80)
                    elif command == 'stop':
                        crawler.do_action('stand', 1, 80)
                        
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
                    elif command == 'strafe_left':
                        # Right legs push OUT (Y=90), Left legs pull IN (Y=10) -> Body shifts strictly left
                        crawler.do_step([[50,90,-60], [50,10,-60], [50,10,-60], [50,90,-60]], 80)
                    elif command == 'strafe_right':
                        # Right legs pull IN (Y=10), Left legs push OUT (Y=90) -> Body shifts strictly right
                        crawler.do_step([[50,10,-60], [50,90,-60], [50,90,-60], [50,10,-60]], 80)
                    elif command == 'stand':
                        crawler.do_action('stand', 1, 80)
                        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()