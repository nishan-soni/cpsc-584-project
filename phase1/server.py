import socket
from picrawler import Picrawler 
from robot_hat import Servo, PWM
from time import sleep
from vilib import Vilib

# Initialize your PiCrawler
crawler = Picrawler()           

# --- START THE LIVE VIDEO FEED ---
# Broadcasts the camera feed to http://192.168.1.75:9000/mjpg
Vilib.camera_start(vflip=False, hflip=False)
Vilib.display(local=False, web=True)

# --- INITIALIZE CAMERA SERVOS ---
try:
    pan_servo = Servo(PWM("P1"))
    tilt_servo = Servo(PWM("P0"))
    pan_angle = 0
    tilt_angle = 0
    pan_servo.angle(pan_angle)
    tilt_servo.angle(tilt_angle)
except Exception as e:
    print(f"Warning: Camera servos not detected on P0/P1. {e}")

# Define Server details
HOST = '0.0.0.0'
PORT = 65432

def start_server():
    global pan_angle, tilt_angle
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
                
                # Split commands by newline to handle fast controller inputs smoothly
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
                        
                    # --- RIGHT JOYSTICK (Camera Pan/Tilt) ---
                    elif command == 'cam_up':
                        tilt_angle = max(-90, tilt_angle - 5)
                        tilt_servo.angle(tilt_angle)
                    elif command == 'cam_down':
                        tilt_angle = min(90, tilt_angle + 5)
                        tilt_servo.angle(tilt_angle)
                    elif command == 'cam_left':
                        pan_angle = max(-90, pan_angle - 5)
                        pan_servo.angle(pan_angle)
                    elif command == 'cam_right':
                        pan_angle = min(90, pan_angle + 5)
                        pan_servo.angle(pan_angle)
                        
                    # --- THE SPY POSTURES (Face Buttons) ---
                    elif command == 'high_posture':
                        # Stand tall (A highly negative Z value pushes the body up)
                        crawler.do_step([[50,50,-90], [50,50,-90], [50,50,-90], [50,50,-90]], 80)
                    elif command == 'stealth_mode':
                        # Crawl extremely low to the ground
                        crawler.do_step([[50,50,-30], [50,50,-30], [50,50,-30], [50,50,-30]], 80)
                    elif command == 'peek_left':
                        # Right legs extend fully, left legs compress (Robot leans left)
                        crawler.do_step([[50,50,-90], [50,50,-30], [50,50,-30], [50,50,-90]], 80)
                    elif command == 'peek_right':
                        # Left legs extend fully, right legs compress (Robot leans right)
                        crawler.do_step([[50,50,-30], [50,50,-90], [50,50,-90], [50,50,-30]], 80)
                    elif command == 'stand':
                        # Return to neutral resting position when face buttons are released
                        crawler.do_action('stand', 1, 80)
                        
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()