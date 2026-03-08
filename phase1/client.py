from pydualsense import pydualsense
import socket
from time import sleep

HOST = '192.168.1.76' 
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
        client_socket.sendall((cmd + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Connection lost: {e}")

def main():
    ds = pydualsense()
    ds.init()
    sleep(1) # Let the controller find its center

    robot_state = {"move": "stop", "cam": "cam_stop", "speed": "speed_normal"}

    def handle_button_release():
        # Only stand if we're not supposed to be moving
        if robot_state["move"] == "stop":
            send_command("stand")

    # --- THE SPY POSTURES (Face Buttons) ---
    ds.triangle_pressed += lambda state: send_command("high_posture") if state else handle_button_release()
    ds.cross_pressed += lambda state: send_command("stealth_mode") if state else handle_button_release()
    ds.square_pressed += lambda state: send_command("strafe_left") if state else handle_button_release()
    ds.circle_pressed += lambda state: send_command("strafe_right") if state else handle_button_release()

    print("Listening for PS5 controller input. Press Ctrl+C to exit.")
    
    try:
        while True:
            # --- LEFT JOYSTICK (Movement) ---
            # DualSense axes range from -128 to 127. 0 is center.
            ly = ds.state.LY
            lx = ds.state.LX
            
            new_move = "stop"
            if ly < -50: new_move = "forward"
            elif ly > 50: new_move = "back"
            elif lx < -50: new_move = "left"
            elif lx > 50: new_move = "right"

            if new_move != robot_state["move"]:
                send_command(new_move)
                robot_state["move"] = new_move
            
            # --- RIGHT JOYSTICK (Body Lean / Camera Tilt) ---
            ry = ds.state.RY
            rx = ds.state.RX
            
            new_cam = "cam_stop"
            if ry < -50: new_cam = "look_up"
            elif ry > 50: new_cam = "look_down"
            elif rx < -50: new_cam = "lean_left"
            elif rx > 50: new_cam = "lean_right"

            if new_cam != robot_state["cam"]:
                send_command(new_cam)
                robot_state["cam"] = new_cam
                
            # --- TRIGGERS (Speed Controls) ---
            l2 = ds.state.L2
            r2 = ds.state.R2
            
            new_speed = "speed_normal"
            if r2 > 10: 
                new_speed = "speed_sprint"
            elif l2 > 10: 
                new_speed = "speed_ghost"
                
            if new_speed != robot_state["speed"]:
                send_command(new_speed)
                robot_state["speed"] = new_speed
            
            sleep(0.05) 

    except KeyboardInterrupt:
        print("\nClosing connection.")
    finally:
        ds.close()
        client_socket.close()

if __name__ == "__main__":
    main()