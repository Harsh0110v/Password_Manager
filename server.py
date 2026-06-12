import socket

HOST = "127.0.0.1"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print(f"Server listening on {HOST}:{PORT}")

conn, addr = server.accept()
print(f"Connected by {addr}")

while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    print(f"Received: {data}")
    conn.send(f"Echo: {data}".encode())

conn.close()