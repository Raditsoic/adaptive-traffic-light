import socket
import cv2
import struct
import pickle
import threading

# Server Configuration
HOST = 'localhost'  
PORT = 65433       
EXIT_FLAG = False  

# Frame Buffer
frame_lock = threading.Lock()
latest_frame = None

def exit_listener():
    global EXIT_FLAG
    input("Press Enter to stop the server...\n")
    EXIT_FLAG = True

def capture_frames():
    global latest_frame
    cap = cv2.VideoCapture(1)  # Use INT for webcam, or a file path for a video
    if not cap.isOpened():
        print("Error: Camera not accessible.")
        return

    while not EXIT_FLAG:
        ret, frame = cap.read()
        if ret:
            with frame_lock:
                latest_frame = frame

    cap.release()

def handle_client_connection(conn):
    global latest_frame
    while not EXIT_FLAG:
        try:
            request = conn.recv(8)
            if request == b"CAPTURE":
                with frame_lock:
                    if latest_frame is not None:
                        _, encoded_frame = cv2.imencode('.jpg', latest_frame)
                        data = pickle.dumps(encoded_frame, 0)
                        size = len(data)
                        conn.sendall(struct.pack(">L", size) + data)
                    else:
                        print("No frame captured yet.")
            else:
                print("Unknown request received")
        except Exception as e:
            print(f"Error handling client connection: {e}")
            break

    conn.close()

def main():
    global EXIT_FLAG
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f'Server is listening on {HOST}:{PORT}')

        threading.Thread(target=exit_listener, daemon=True).start()
        threading.Thread(target=capture_frames, daemon=True).start()

        while not EXIT_FLAG:
            try:
                conn, addr = server_socket.accept()
                print('Connected by', addr)
                threading.Thread(target=handle_client_connection, args=(conn,), daemon=True).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")

    print("Server has been stopped.")

if __name__ == "__main__":
    main()