# server/raymond_server.py
import threading
import time
from collections import deque


class RaymondServer:
    """
    Centralized implementation of Raymond's algorithm for the leaderboard token
    """

    def __init__(self, resource_name="leaderboard", cooldown_duration=30):
        self.resource_name = resource_name
        self.has_token = True  # Server initially holds the token
        self.current_holder = None  # No client holds the token initially
        self.queue = deque()  # Queue of clients waiting for the token
        self.lock = threading.Lock()
        self.cooldowns = {}  # {client_id: expiry_time}
        self.cooldown_duration = cooldown_duration  # seconds

    def request_token(self, client_id, timestamp):
        """
        Handle a request for the leaderboard token
        Returns:
            (granted, position, message)
        """
        with self.lock:
            # Check if client is in cooldown
            if client_id in self.cooldowns:
                cooldown_until = self.cooldowns[client_id]
                current_time = time.time()

                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    return False, -1, f"In cooldown for {remaining}s"
                else:
                    # Cooldown expired, remove from cooldowns
                    self.cooldowns.pop(client_id)

            # Check if client already has the token
            if self.current_holder == client_id:
                return True, 0, "Token already held"

            # Check if client is already in queue
            if client_id in self.queue:
                position = 0
                for qid in self.queue:
                    if qid == client_id:
                        break
                    position += 1
                return False, position, f"Already in queue at position {position}"

            # Check if token is available
            if self.has_token and self.current_holder is None:
                # Grant token immediately
                self.has_token = False
                self.current_holder = client_id
                return True, 0, "Token granted"
            else:
                # Add to queue
                self.queue.append(client_id)

                # If we have more than one client requesting leaderboard
                if len(self.queue) > 1 or self.current_holder is not None:
                    return False, len(self.queue) - 1, "Leaderboard requested by multiple players"

                return False, len(self.queue) - 1, "In queue"

    def release_token(self, client_id):
        """
        Release token held by client_id
        Returns:
            (success, next_holder)
        """
        with self.lock:
            # Only the current holder can release the token
            if self.current_holder != client_id:
                return False, None

            # Apply cooldown
            current_time = time.time()
            self.cooldowns[client_id] = current_time + self.cooldown_duration

            # Grant token to next in queue if any
            next_holder = None
            while self.queue and not next_holder:
                next_client = self.queue.popleft()

                # Skip clients in cooldown
                if next_client in self.cooldowns:
                    cooldown_until = self.cooldowns[next_client]
                    if current_time < cooldown_until:
                        continue
                    else:
                        # Cooldown expired
                        self.cooldowns.pop(next_client)

                next_holder = next_client

            if next_holder:
                self.current_holder = next_holder
                # Token is passed to next holder
                self.has_token = False
            else:
                self.current_holder = None
                # Token returns to server
                self.has_token = True

            return True, next_holder

    def get_status(self):
        """Get status of the leaderboard token"""
        with self.lock:
            queue_list = list(self.queue)
            return {
                "resource": self.resource_name,
                "holder": self.current_holder,
                "queue": queue_list,
                "queue_length": len(queue_list)
            }