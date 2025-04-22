# common/utils.py
import json
import socket
import time
from datetime import datetime


def send_message(sock, message_type, payload):
    """
    Format and send a message over a socket

    Args:
        sock: Socket object
        message_type: Type of message from message_types.py
        payload: Data to send (will be JSON serialized)
    """
    message = {
        "type": message_type,
        "timestamp": time.time(),
        "payload": payload
    }

    data = json.dumps(message).encode('utf-8')
    try:
        sock.sendall(data + b'\n')
        return True
    except (socket.error, BrokenPipeError) as e:
        print(f"Error sending message: {e}")
        return False


def receive_message(sock, buffer_size=4096):
    """
    Receive and parse a message from a socket

    Args:
        sock: Socket object
        buffer_size: Maximum message size to receive

    Returns:
        Parsed message dict or None if error
    """
    try:
        data = sock.recv(buffer_size)
        if not data:
            return None

        # Handle newline-separated messages
        messages = data.decode('utf-8').strip().split('\n')
        parsed_messages = []

        for message in messages:
            if message:
                try:
                    parsed_messages.append(json.loads(message))
                except json.JSONDecodeError:
                    print(f"Error decoding message: {message}")

        return parsed_messages[0] if parsed_messages else None
    except socket.error as e:
        print(f"Error receiving message: {e}")
        return None


def format_time(seconds):
    """Format seconds into mm:ss format"""
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def log_event(message, level="INFO"):
    """Log an event with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] [{timestamp}] {message}")