import socket
from picrawler import PiCrawler
from time import sleep

# Initialize your PiCrawler
crawler = PiCrawler()

# Define Server details
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 65432      # Unprivileged port to avoid permission issues

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow the port to be reused immediately after restart
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    
    print(f"PiCrawler Server listening on port {PORT}...")

    try:
        while True:
            client, addr = server_socket.accept()
            print(f"Connected to Controller at {addr}")
            
            while True:
                data = client.recv(1024)
                if not data:
                    break # Client disconnected
                
                command = data.decode('utf-8')
                print(f"Command received: {command}")
                
                # Execute PiCrawler movements
                # Note: Adjust the action names/parameters to match your specific PiCrawler version if needed
                if command == 'forward':
                    crawler.do_action('forward', 1, 50)
                elif command == 'back':
                    crawler.do_action('backward', 1, 50)
                elif command == 'right':
                    crawler.do_action('turn right', 1, 50)
                elif command == 'left':
                    crawler.do_action('turn left', 1, 50)
                elif command == 'stop':
                    # Command to return crawler to a neutral standing position
                    crawler.do_action('stand', 1, 50) 
                    
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()