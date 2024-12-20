import socket


def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("localhost", 50001))
        sock.sendall(command.encode('utf-8'))
        response = sock.recv(1024).decode('utf-8')
        print("Received:", response)


if __name__ == "__main__":
    send_command("read")
