import traceback
import socket
from typing import Any
import sys
import ssl
from dotenv import load_dotenv
import os
import time

def write_to_error_log(log="error.log"):
    print("[MESSAGE] Writing to error.log\t")
    with open(log, "a") as f:
        f.write("[MESSAGE] Writing to error.log\n\t")
        traceback.print_exc(file=f)

class Socket():
    def __init__(self, ports=(8600, 8610), host="localhost"):
        self.host = host
        self.range = range(ports[0], ports[1])

    def __enter__(self):
        while True:

            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssock = context.wrap_socket(self.socket, server_hostname=self.host)

            print("[HOST]", self.host)
            print("[RANGE]", self.range)
            
            for port in self.range:
                try:
                    HOST = self.host
                    PORT = port                
                    ssock.connect((HOST, PORT)) 
                    
                    print(f"[STATUS] Connected to {self.host} on port", port)               
                    return ssock           
                
                except Exception as e:
                    print(f"[ERROR] Failed to connect to {self.host} on port", port)
                    continue 
            
            print("Retrying...")
            time.sleep(5)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        print("[STATUS] Closing socket")
        self.socket.close()
    
    def receive(self, size=2048):
        print("[HOOK] Receiving data")
        data = self.socket.recv(size)
        print("[SOCKET][RECEIVED]", data)
        return data
    
    def generate_ports(self):
        print("[HOOK] Finding port")
        for port in range(8600, 8699):
            yield port

class Server():
    def __init__(self, host="localhost", ports=(8600, 8610)):
        load_dotenv()

        self.sslpass = os.getenv("SSLPASS")
        self.host = host
        self.range = range(ports[0], ports[1])
        self.socket = None

    def __enter__(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="./.ssl/cert.pem", keyfile="./.ssl/key.pem", password=self.sslpass)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        ssock = context.wrap_socket(sock, server_side=True)
        
        print("[HOST]", self.host)
        print("[RANGE]", self.range)

        self.socket = ssock
        for port in self.range:
            try:
                HOST = self.host
                PORT = port
                self.socket.bind((HOST, PORT))
                self.socket.listen(5)

                print("[STATUS] Socket bound to port", port)
                return self.socket
            
            except Exception as e:
                print(f"[ERROR] Not able to bind host {HOST} and port {PORT}")

    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        print("[STATUS] Closing socket")
        if self.socket is not None:
            self.socket.close()
        
    def accept(self):
        print("[HOOK] Accepting connection")
        conn, addr = self.socket.accept()
        print("[MONITORING] incoming connection from", addr)
        return conn, addr
    
    def allocate_port(self):
        print("[HOOK] Allocating port")
        for port in range(8600, 8699):
            yield port

    def write_to_error_log(self, log="error.log"):
        print("[ACTION] Writing to error.log")
        write_to_error_log(log)

if __name__ == "__main__":
    sys.stdout = open("sock.log", "w")
    
    with Socket() as sock:
        sock.generate_ports()
        sock.receive()