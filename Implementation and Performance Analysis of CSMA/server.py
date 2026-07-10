import socket
import threading
import time

PORT = 8080
HOST = "localhost"
SLOT_TIME = 0.05

lock = threading.Lock()
medium_busy = False

current_station = None

def release_medium(station_id, frame_num):
    """Release the medium after transmission duration."""
    global medium_busy, current_station
    time.sleep(SLOT_TIME)  # simulate transmission duration
    with lock:
        medium_busy = False
        print(f"Medium released by Station  after Frame {frame_num}")
        current_station = None

def handle_client(conn, addr):
    global medium_busy, current_station
    print(f" Connected with {addr}")

    station_id = None  # will be set on first TRANSMIT
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode().strip()

            # Carrier sense
            if msg == "SENSE":
                with lock:
                    if medium_busy:
                        conn.sendall(b"BUSY")
                    else:
                        conn.sendall(b"IDLE")

            # Transmission request
            elif msg.startswith("TRANSMIT"):
                
                parts = msg.split("|")
                frame_num = parts[1] if len(parts) > 1 else "?"
                
                with lock:
                    if medium_busy:
                        
                        conn.sendall(b"COLLISION")
                        print(f"Collision detected! Station {station_id} tried to send Frame {frame_num}")
                    else:
                        
                        medium_busy = True
                        current_station = station_id
                        conn.sendall(b"SUCCESS")
                        print(f" Station {station_id} is transmitting Frame {frame_num}")
                        threading.Thread(target=release_medium, args=(station_id, frame_num), daemon=True).start()
            
            
            if station_id is None and msg.startswith("TRANSMIT"):
            
                station_id = addr[1]  # use client port as a temporary ID

    except ConnectionResetError:
        print(f" Connection forcibly closed by {addr}")
    finally:
        conn.close()
        print(f" Disconnected {addr}")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    print(f"Running on port {PORT}")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
