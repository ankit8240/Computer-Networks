import socket
import sys
import checkSum as cs
import crc as cr
import injectError
import random

SERVER_IP = '127.0.0.1'
SERVER_PORT = 3000

def main():
    if len(sys.argv) < 3:
        print("Usage: python sender.py <input_file> <technique> [crc_poly]")
        return

    file_name = sys.argv[1]
    technique = sys.argv[2].lower()

    block_len = 16   # number of chars to read at once
    crc_poly = ""

    if technique == "crc":
        if len(sys.argv) < 4:
            print("Usage: python sender.py <input_file> crc <crc_poly>")
            return
        crc_poly = sys.argv[3]

    try:
        with open(file_name, "r") as infile, socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((SERVER_IP, SERVER_PORT))
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

            while True:
                chunk = infile.read(block_len)
                if not chunk:
                    break

                if technique == "checksum":
                    code = cs.gen_checksum(chunk)
                elif technique == "crc":
                    code = cr.gen_crc(chunk, crc_poly)
                else:
                    print(f"Invalid method: {technique}")
                    return

                
                err_flag = 0
                if random.random() < 0.5:
                    # pick a random error type
                    modes = ["single", "multiple", "burst", "drop", "dup", "swap"]
                    mode = random.choice(modes)
                    mode = ""
                    
                    if mode == "multiple":
                        code = injectError.injecterror(code, mode=mode, flips=3)   # flip 3 bits
                    elif mode == "burst":
                        code = injectError.injecterror(code, mode=mode, flips=4)   # burst of 4 bits
                    else:
                        code = injectError.injecterror(code, mode=mode)

                    print(f"Injected error mode={mode}")  # debug print
                    err_flag = 1

                if technique == "crc":
                    payload = f"{technique}:{crc_poly}:{err_flag}:{code}\n"
                else:
                    payload = f"{technique}:-:{err_flag}:{code}\n"


                sock.sendall(payload.encode("utf-8"))
                print(f"Sent block: {code} (error={err_flag})")

        print("Finished sending file.")

    except FileNotFoundError:
        print(f"File not found: {file_name}")
    except ConnectionRefusedError:
        print("Server not running or refused connection.")

if __name__ == "__main__":
    main()
