import socket
import cv2
import struct
import pickle
import threading
import os
import time
import requests
from model import detect_vehicles_and_calculate_duration

# List of server configurations
SERVERS = [
    {'host': 'localhost', 'port': 65432, 'output_dir': 'out/camera-1'},
    {'host': 'localhost', 'port': 65433, 'output_dir': 'out/camera-2'},
    {'host': 'localhost', 'port': 65434, 'output_dir': 'out/camera-3'},
]

def send_green_light_to_arduino(seconds, traffic_light):
    array_str = f"{seconds},{traffic_light}"
    url = f'http://192.168.93.90/?array={array_str}'
    try:
        response = requests.get(url)
        print(response.text)
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

# Function to handle adaptive sleep intervals and round-robin requests
def adaptive_capture_requests(sockets, request_interval, lock, capture_event):
    server_index = 0
    while True:
        capture_event.wait()

        try:
            with lock:
                client_socket = sockets[server_index]
                if client_socket is None:
                    print(f"Socket for server {server_index} is not initialized.")
                    continue

                # Send capture request to the server/camera
                client_socket.sendall(b"CAPTURE")

                # Update the server index for round-robin
                server_index = (server_index + 1) % len(sockets)

                # Read the current interval
                current_interval = request_interval[0]

            # Wait for the green light duration
            capture_event.clear()
            time.sleep(current_interval)
        except Exception as e:
            print(f"Error sending capture request: {e}")
            break

def receive_frames(client_socket, output_dir, server_index, request_interval, lock, capture_event):
    data = b""
    payload_size = struct.calcsize(">L")
    image_count = 0

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    while True:
        while len(data) < payload_size:
            packet = client_socket.recv(4096)
            if not packet:
                return
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        # Save the received frame
        image_filename = os.path.join(output_dir, f'frame_{image_count + 1}.jpg')
        cv2.imwrite(image_filename, frame)
        print(f'Saved frame from server {server_index} as {image_filename}')

        # Process the frame
        processed_image, green_light_duration = detect_vehicles_and_calculate_duration(frame)

        processed_image_filename = os.path.join(output_dir, f'processed_{image_count + 1}.jpg')
        cv2.imwrite(processed_image_filename, processed_image)
        print(f'Saved processed frame from server {server_index} as {processed_image_filename}')

        # Update the request interval based on the green light duration
        with lock:
            request_interval[0] = max(green_light_duration + 1, 1)
            
        send_green_light_to_arduino(green_light_duration, server_index + 1)

        image_count += 1

        # Set the capture_event to trigger the next capture
        capture_event.set()

def handle_server_connection(server_config, server_index, sockets, request_interval, lock, capture_event):
    host = server_config['host']
    port = server_config['port']
    output_dir = server_config['output_dir']

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))

            # Add the client socket to the list
            with lock:
                sockets[server_index] = client_socket

            # Receiving and processing frames
            receive_frames(client_socket, output_dir, server_index, request_interval, lock, capture_event)

        except Exception as e:
            print(f"Error connecting to server {server_index}: {e}")

def main():
    sockets = [None] * len(SERVERS)
    request_interval = [5]  # Initial interval
    lock = threading.Lock()  # Lock for safe access to the request_interval and sockets
    capture_event = threading.Event()  # Event to trigger capture requests

    threads = []
    for index, server in enumerate(SERVERS):
        thread = threading.Thread(target=handle_server_connection, args=(server, index, sockets, request_interval, lock, capture_event))
        threads.append(thread)
        thread.start()

    capture_thread = threading.Thread(target=adaptive_capture_requests, args=(sockets, request_interval, lock, capture_event), daemon=True)
    capture_thread.start()

    capture_event.set()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
