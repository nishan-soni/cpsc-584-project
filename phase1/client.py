from pydualsense import pydualsense
import socket
from time import sleep

import asyncio
import websockets


ui_socket = None

async def ui_websocket_handler(web_socket):
    global ui_socket
    ui_socket = web_socket
    await web_socket.wait_closed()

HOST = '172.17.10.193' 
PORT = 65432

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# ======================Uncomment this soon=============================================
# try:
#     print(f"Connecting to PiCrawler at {HOST}:{PORT}...")
#     client_socket.connect((HOST, PORT))
#     print("Connected successfully!")
# except Exception as e:
#     print(f"Failed to connect: {e}")
#     exit()

async def send_command(cmd):
    try:
        await ui_socket.send(cmd)
        print("command sent to the ui")
        client_socket.sendall((cmd + '\n').encode('utf-8'))
    except Exception as e:
        print(f"Connection lost: {e}")

async def start():
    ds = pydualsense()
    ds.init()
    await asyncio.sleep(1)
    loop = asyncio.get_running_loop()

    # --- START RUMBLE LISTENER THREAD ---
    def listen_for_rumble():
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                if "RUMBLE" in data:
                    print("🚨 ENEMY SPOTTED! RUMBLING THE CONTROLLER! 🚨")
                    ds.setLeftMotor(255)  
                    ds.setRightMotor(255) 
                    sleep(0.5)  
                    ds.setLeftMotor(0)
                    ds.setRightMotor(0)
            except Exception:
                break
                
    import threading
    threading.Thread(target=listen_for_rumble, daemon=True).start()

    robot_state = {"move": "stop", "cam": "cam_stop", "speed": "speed_normal"}


    def schedule(coro):
        asyncio.run_coroutine_threadsafe(coro, loop)

    async def handle_button_release():
        if robot_state["move"] == "stop":
            await send_command("stand")

    # --- THE SPY POSTURES & CAMERA (Face Buttons) ---
    ds.triangle_pressed += lambda state: schedule(send_command("high_posture")) if state else schedule(handle_button_release())
    ds.cross_pressed += lambda state: schedule(send_command("stealth_mode")) if state else schedule(handle_button_release())
    
    # Send camera commands ONLY when the button is pressed down (state == True)
    ds.square_pressed += lambda state: schedule(send_command("take_photo")) if state else None
    ds.circle_pressed += lambda state: schedule(send_command("toggle_record")) if state else None

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
                await send_command(new_move)
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
                await send_command(new_cam)
                robot_state["cam"] = new_cam
                
            # --- TRIGGERS (Speed Controls using Polling) ---
            # In pydualsense L2 and R2 go from 0 to 255.
            try:
                l2 = getattr(ds.state, 'L2', 0)
                r2 = getattr(ds.state, 'R2', 0)
            except Exception:
                l2 = 0
                r2 = 0
            
            new_speed = "speed_normal"
            if r2 > 0: 
                new_speed = "speed_sprint"
            elif l2 > 0: 
                new_speed = "speed_ghost"
                
            if new_speed != robot_state["speed"]:
                print(f"\n🎮 Trigger changed! L2: {l2}, R2: {r2} -> Sending: {new_speed}")
                await send_command(new_speed)
                robot_state["speed"] = new_speed
                
            # Real-time debug print of all axes
            print(f"DEBUG | LX:{lx:^4} LY:{ly:^4} | RX:{rx:^4} RY:{ry:^4} | L2:{l2:^3} R2:{r2:^3}   ", end="\r")
            
            await asyncio.sleep(0.05)

    except KeyboardInterrupt:
        print("\nClosing connection.")
    finally:
        ds.close()
        client_socket.close()

async def main():
    async with websockets.serve(ui_websocket_handler, "localhost", 8765):
        print("WebSocket server running on ws://localhost:8765")
        await start()


asyncio.run(main())