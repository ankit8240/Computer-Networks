# server.py (Corrected)
import socket
import threading
import pickle
import numpy as np

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024

NO_OF_CLIENTS = 4
CLIENTS = []
THREADS = []
DATA_FROM_CLIENTS = {}

lock = threading.Lock()


# --- Walsh code generation ---
def walsh_matrix(n):
    if n==1:
        return np.array([[1]])
    else:
        H = walsh_matrix(n//2)
        return np.block([[H, H], [H, -H]])


WALSH_CODES = walsh_matrix(NO_OF_CLIENTS)


def handle_client(conn, station_id):
    """Receive one bit from client"""
    global DATA_FROM_CLIENTS
    try:
        data = conn.recv(BUFFER_SIZE)
        if not data:
            return
        decoded_data = pickle.loads(data)
        with lock:
            DATA_FROM_CLIENTS[station_id] = decoded_data
        print(f"Received from Station {station_id}: {decoded_data}")
    except Exception as e:
        print(f"Error handling client {station_id}: {e}")


# --- Main server loop ---
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")
    print(f"Waiting for {NO_OF_CLIENTS} clients to connect...")

    station_id = 0
    while station_id < NO_OF_CLIENTS:
        conn, addr = server_socket.accept()
        CLIENTS.append((conn, addr))
        DATA_FROM_CLIENTS[station_id] = None
        
        thread = threading.Thread(target=handle_client, args=(conn, station_id))
        thread.start()
        THREADS.append(thread)

        print(f"Connected by {addr} as Station {station_id}")
        station_id += 1

    # --- REVISED: Wait for all threads to complete ---
    print("Waiting for all clients to send their bits...")
    for thread in THREADS:
        thread.join()

    # Encode and build composite
    signals = []
    for i in range(NO_OF_CLIENTS):
        bit = DATA_FROM_CLIENTS[i]
        val = 1 if bit == 1 else -1
        signals.append(val * WALSH_CODES[i])

    composite = np.sum(signals, axis=0)
    print(f"\nComposite Signal: {composite}")

    # Send composite to all clients
    print("Sending composite signal to all clients...")
    for conn, addr in CLIENTS:
        try:
            conn.sendall(pickle.dumps(composite))
        except Exception as e:
            print(f"Could not send to {addr}: {e}")

    # --- Close all connections at the end ---
    print("Closing all connections.")
    for conn, addr in CLIENTS:
        conn.close()