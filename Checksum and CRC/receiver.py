import socket
import checkSum
import crc

IP = '127.0.0.1'
PORT = 3000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
    server_sock.bind((IP, PORT))
    server_sock.listen()
    print(f"Server is running at {IP}:{PORT}")

    conn, client_addr = server_sock.accept()
    with conn:
        print(f"Connection established with {client_addr}")
        data_buffer = ""
        total_msgs = 0
        correct_hits = 0

        while True:
            packet = conn.recv(1024)
            if not packet:
                print("No more data. Transfer finished.")
                break

            data_buffer += packet.decode("utf-8")

            # handle multiple messages
            while "\n" in data_buffer:
                raw_msg, data_buffer = data_buffer.split("\n", 1)
                if not raw_msg.strip():
                    continue

                try:
                    scheme, poly, has_error, received_code = raw_msg.split(":", 3)
                    total_msgs += 1
                except ValueError:
                    print(f"Badly formatted message: {raw_msg}")
                    continue

                valid = False
                scheme = scheme.strip().lower()
                if scheme == "checksum":
                    valid = checkSum.verify_checksum(received_code)
                elif scheme == "crc":
                    valid = crc.verify_crc(received_code, poly)
                else:
                    print(f"Unknown scheme: {scheme}")
                    continue

                # convert error string to boolean
                error_flag = has_error.strip() == "1"

                if valid != error_flag:
                    correct_hits += 1

        print(f"Detection accuracy: {correct_hits}/{total_msgs}")
