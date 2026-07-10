import socket
import time
import random
import threading
import os


P_PERSISTENCE = 0.5       
MAX_ATTEMPTS = 10          
SLOT_TIME = 0.05           
NUM_STATIONS = 4           
FRAME_SIZE = 64            
FRAMES_PER_STATION = 10    


def generate_random_frames(num_frames, frame_size=FRAME_SIZE):
    """Generate random binary data frames."""
    frames = [os.urandom(frame_size) for _ in range(num_frames)]
    return frames


def run_station(station_id, frames_to_send):
    """one CSMA/CD station """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(("localhost", 8080))
    except ConnectionRefusedError:
        print(f"Station {station_id}  :Connection failed. Is the server running?")
        return

    print(f"[Station {station_id}]  Started with p = {P_PERSISTENCE}")
    frames_sent_successfully = 0
    num_frames_to_send = len(frames_to_send)

    for i, frame_data in enumerate(frames_to_send):
        frame_num = i + 1
        current_attempts = 0

        print(f"\nStation {station_id}  Sending Frame {frame_num}/{num_frames_to_send} ")

        while current_attempts < MAX_ATTEMPTS:
            # 1. Carrier Sense
            client_socket.sendall("SENSE".encode())
            response = client_socket.recv(1024).decode()

            if response == "BUSY":
                print(f"[Station {station_id}] Medium BUSY. Waiting...")
                time.sleep(SLOT_TIME)
                continue

            # 2. Channel IDLE 
            if random.random() > P_PERSISTENCE:
                print(f"Station {station_id} p-check failed. Wait 1 slot.")
                time.sleep(SLOT_TIME)
                continue

            # 3. Transmit frame
            print(f"Station {station_id} Transmitting frame {frame_num}...")
            frame_start_time = time.time()
            client_socket.sendall(f"TRANSMIT|{frame_start_time}".encode())

            # 4. Wait for ACK or COLLISION
            result = client_socket.recv(1024).decode()

            if result == "SUCCESS":
                print(f"Station {station_id}:Frame {frame_num} sent successfully!")
                frames_sent_successfully += 1
                break
            elif result == "COLLISION":
                current_attempts += 1
                print(f"Station {station_id} :Collision detected (Attempt {current_attempts})")

                # Exponential Backoff
                backoff_limit = (2 ** current_attempts) - 1
                backoff_slots = random.randint(0, backoff_limit)
                wait_time = backoff_slots * SLOT_TIME
                print(f"Station {station_id}:Backing off for {backoff_slots} slots ({wait_time:.2f}s)")
                time.sleep(wait_time)

        if current_attempts >= MAX_ATTEMPTS:
            print(f"Station {station_id}: Dropped Frame {frame_num} after {MAX_ATTEMPTS} attempts.")

    print(f"\nStation {station_id}: Finished. Successful frames: {frames_sent_successfully}/{num_frames_to_send}")
    client_socket.close()


def main():
    #  for all stations
    all_stations_frames = [generate_random_frames(FRAMES_PER_STATION) for _ in range(NUM_STATIONS)]

    #  threads
    threads = []
    for i in range(NUM_STATIONS):
        t = threading.Thread(target=run_station, args=(i + 1, all_stations_frames[i]))
        t.start()
        threads.append(t)
        time.sleep(0.2)  # small delay so all clients

    # Wait for all to finish
    for t in threads:
        t.join()

    print("\Simulation completed for all stations.")


if __name__ == "__main__":
    main()
