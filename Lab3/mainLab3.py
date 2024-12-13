import socket
import threading
import random
import time
from loguru import logger

ELECTION_TIMEOUT = (5, 10)
HEARTBEAT_INTERVAL = 2
PORTS = [5500, 5501, 5502, 5503, 5504]


class Node:
    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.state = "Follower"
        self.current_term = 0
        self.voted_for = None
        self.vote_count = 0
        self.lock = threading.Lock()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("localhost", self.port))
        self.running = True

    def send_message(self, message, target_port):
        self.socket.sendto(message.encode(), ("localhost", target_port))

    def broadcast_message(self, message):
        for p in PORTS:
            if p != self.port:
                self.send_message(message, p)

    def start(self):
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        threading.Thread(target=self.run_election_timer, daemon=True).start()

    def listen_for_messages(self):
        while self.running:
            try:
                data, _ = self.socket.recvfrom(1024)
                message = data.decode()
                self.handle_message(message)
            except Exception as e:
                logger.error(f"Error receiving message: {e}")

    def handle_message(self, message):
        logger.info(f"Node {self.node_id} received message: {message}")
        parts = message.split("|")
        msg_type = parts[0]
        term = int(parts[1])

        with self.lock:
            if term > self.current_term:
                self.current_term = term
                self.state = "Follower"
                self.voted_for = None

            if msg_type == "VoteRequest" and self.voted_for is None:
                self.voted_for = parts[2]
                self.send_message(f"VoteGranted|{self.current_term}|{self.node_id}", int(parts[3]))

            elif msg_type == "VoteGranted" and self.state == "Candidate":
                self.vote_count += 1
                if self.vote_count > len(PORTS) // 2:
                    self.state = "Leader"
                    logger.success(f"Node {self.node_id} is now the leader!")
                    threading.Thread(target=self.send_heartbeats, daemon=True).start()

            elif msg_type == "Heartbeat" and self.state != "Leader":
                self.state = "Follower"

    def run_election_timer(self):
        while self.running:
            timeout = random.uniform(*ELECTION_TIMEOUT)
            time.sleep(timeout)
            with self.lock:
                if self.state != "Leader":
                    self.state = "Candidate"
                    self.current_term += 1
                    self.vote_count = 1
                    self.broadcast_message(f"VoteRequest|{self.current_term}|{self.node_id}|{self.port}")
                    logger.info(f"Node {self.node_id} started an election for term {self.current_term}")

    def send_heartbeats(self):
        while self.state == "Leader" and self.running:
            self.broadcast_message(f"Heartbeat|{self.current_term}")
            time.sleep(HEARTBEAT_INTERVAL)

    def stop(self):
        self.running = False
        self.socket.close()


nodes = []
for i, port in enumerate(PORTS):
    node = Node(node_id=i, port=port)
    nodes.append(node)
    node.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    logger.info("Shutting down nodes...")
    for node in nodes:
        node.stop()
