import socket
import pickle
import numpy as np

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 1024
STATION_ID = int(input("Enter Station ID: "))
RECEIVE_ID = int(input("Enter ID to receive from: "))

def walsh_matrix(n):
    if n==1:
        return np.array([[1]])
    else:
        H = walsh_matrix(n//2)
        return np.block([[H, H], [H, -H]])


# Connect to server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))

    # Send one bit
    bit = int(input(f"Station {STATION_ID} enter bit (0/1): "))
    client_socket.sendall(pickle.dumps(bit))

    # Receive composite
    data = client_socket.recv(BUFFER_SIZE)
    composite = pickle.loads(data)

    # Decode
    WALSH_CODES = walsh_matrix(4)
    code = WALSH_CODES[RECEIVE_ID]
    val = np.dot(composite, code) / len(code)
    decoded_bit = 1 if val > 0 else 0

    print(f"Decoded at Station {STATION_ID} from Station {RECEIVE_ID}: {decoded_bit}")
