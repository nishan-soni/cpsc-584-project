from pydualsense import pydualsense
import socket
from time import sleep

# Set up the client socket
HOST = '192.168.1.75' # Your PiCrawler's IP
PORT = 65432

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"Connecting to PiCrawler at {HOST}:{PORT}...")
    client_socket.connect((HOST, PORT))
    print("Connected successfully!")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()

def send_command(cmd):
    try:
        # Appending \n ensures the server processes each command cleanly
        client_socket.sendall((cmd + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Connection lost: {e}")

def main():
    ds = pydualsense()
    ds.init()
    
    # 1. THE STARTUP FIX: 
    # Give the controller a second to read its true centered values (128)
    # so it doesn't default to 0 and trigger a ghost movement.
    sleep(1)

    # --- THE SPY POSTURES (Face Buttons) ---
    ds.triangle_pressed += lambda state: send_command("high_posture") if state else send_command("stand")
    ds.cross_pressed += lambda state: send_command("stealth_mode") if state else send_command("stand")
    ds.square_pressed += lambda state: send_command("peek_left") if state else send_command("stand")
    ds.circle_pressed += lambda state: send_command("peek_right") if state else send_command("stand")

    # 2. THE "NEVER STOP" FIX:
    # State trackers to remember what the robot is currently doing
    current_move = "stop"
    current_cam = "cam_stop"

    print("Listening for PS5 controller input. Press Ctrl+C to exit.")
    
    try:
        while True:
            # --- LEFT JOYSTICK (Movement) ---
            ly = ds.state.LY
            lx = ds.state.LX
            
            new_move = "stop"
            if ly < 100: new_move = "forward"
            elif ly > 155: new_move = "back"
            elif lx < 100: new_move = "left"
            elif lx > 155: new_move = "right"

            # Only send a command if the joystick changed positions
            if new_move != current_move:
                send_command(new_move)
                current_move = new_move
            
            # --- RIGHT JOYSTICK (Camera Pan/Tilt) ---
            ry = ds.state.RY
            rx = ds.state.RX
            
            new_cam = "cam_stop"
            if ry < 100: new_cam = "cam_up"
            elif ry > 155: new_cam = "cam_down"
            elif rx < 100: new_cam = "cam_left"
            elif rx > 155: new_cam = "cam_right"

            # Only send a camera command if the joystick changed positions
            if new_cam != current_cam:
                send_command(new_cam)
                current_cam = new_cam
            
            # Faster polling now that we aren't spamming the network
            sleep(0.05) 

    except KeyboardInterrupt:
        print("\nClosing connection.")
    finally:
        ds.close()
        client_socket.close()

if __name__ == "__main__":
    main()