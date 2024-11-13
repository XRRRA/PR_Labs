import socket
import threading
import json
import random
import time
import os

FILE_PATH = "shared_data.json"

if not os.path.exists(FILE_PATH):
    with open(FILE_PATH, "w") as f:
        json.dump({"data": []}, f)

file_lock = threading.Lock()
read_write_condition = threading.Condition(file_lock)
active_writes = 0


def handle_client(client_socket):
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"Received message: {message}")

            command = message.strip().lower()
            if command == "write":
                handle_write(client_socket)
            elif command == "read":
                handle_read(client_socket)
            else:
                client_socket.send("Unknown command. Use 'write' or 'read'.\n".encode('utf-8'))
    finally:
        client_socket.close()


def handle_write(client_socket):
    global active_writes
    time.sleep(random.randint(1, 7))

    data = {"timestamp": time.time(), "message": "Data written"}

    with read_write_condition:
        active_writes += 1

    with file_lock:
        with open(FILE_PATH, "r+") as f:
            file_data = json.load(f)
            file_data["data"].append(data)
            f.seek(0)
            json.dump(file_data, f)
            f.truncate()
    print("Data written to file.")

    with read_write_condition:
        active_writes -= 1
        if active_writes == 0:
            read_write_condition.notify_all()

    client_socket.send("Write operation completed.\n".encode('utf-8'))


def handle_read(client_socket):
    time.sleep(random.randint(1, 7))

    with read_write_condition:
        while active_writes > 0:
            read_write_condition.wait()

    with file_lock:
        with open(FILE_PATH, "r") as f:
            file_data = json.load(f)

    client_socket.send(f"Read data: {file_data}\n".encode('utf-8'))
    print("Data read from file.")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 50001))
    server.listen(5)
    print("TCP server started on port 50001.")

    try:
        while True:
            client_socket, addr = server.accept()
            print(f"Accepted connection from {addr}")

            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.start()
    finally:
        server.close()


if __name__ == "__main__":
    start_server()
