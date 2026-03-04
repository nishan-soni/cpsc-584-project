from pydualsense import pydualsense
import socket
from time import sleep

# Set up the client socket with the correct IP and Port
HOST = '192.168.1.75' # Your PiCrawler's IP
PORT = 65432           # Matching the server port

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    print(f"Connecting to PiCrawler at {HOST}:{PORT}...")
    client_socket.connect((HOST, PORT))
    print("Connected successfully!")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()

def button_pressed(cmd):
    client_socket.sendall(cmd.encode('utf-8'))

def button_released(cmd):
    client_socket.sendall(cmd.encode('utf-8'))

def main():
    # Initialize the DualSense controller
    ds = pydualsense()
    ds.init()

    # Set up event handlers for buttons
    ds.cross_pressed += lambda state: button_pressed("back") if state else button_released("stop")
    ds.circle_pressed += lambda state: button_pressed("right") if state else button_released("stop")
    ds.square_pressed += lambda state: button_pressed("left") if state else button_released("stop")
    ds.triangle_pressed += lambda state: button_pressed("forward") if state else button_released("stop")

    try:
        print("Listening for PS5 controller input. Press Ctrl+C to exit.")
        while True:
            pass  # Keep the script running to listen for events
    except KeyboardInterrupt:
        print("\nClosing connection.")
    finally:
        ds.close()
        client_socket.close()

if __name__ == "__main__":
    main()