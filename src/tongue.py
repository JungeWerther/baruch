import socket
import subprocess
from sock import Server

with Server("baruch.local", (8765, 8766)) as server:
    server.listen()
    while True:
        
        # wait for a new connection
        print("Waiting for connection...")
        conn, addr = server.accept()
        print(f"Connected to {addr}")

        # write transmission to file
        with open("input_stream.wav", "wb") as file:
            while True:
                data = conn.recv(1024)
                if not data: break

                match data:
                    case b'[START]':
                        print("[START]")
                        continue
                    case b'[STOP]':
                        print("[STOP]")
                        break
                    case bytes():
                        file.write(data)

        
        print("[STATUS] Playing audio...")
        subprocess.run(["aplay", "input_stream.wav"])

        print("[STATUS] Closing connection...")
        conn.close()

        # close after playing (or should we close before? at least we'll play one thing at a time)
        # print(f"Connection closed.")
        # comm_socket.close()