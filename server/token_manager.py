# server/token_manager.py
import threading
import time
from collections import deque

class TokenManager:
    """
    Manages tokens for resources like hint and skip
    Each token can be held by at most one client at a time
    """
    def __init__(self, resource_name, cooldown_duration=30):
        self.resource_name = resource_name
        self.token_holder = None  # Client currently holding the token
        self.request_queue = deque()  # Queue of waiting clients
        self.lock = threading.Lock()
        self.token_acquired_time = None  # When the token was acquired
        self.cooldowns = {}  # {client_id: expiry_time}
        self.cooldown_duration = cooldown_duration  # Cooldown duration in seconds
        self.pending_requests = set()  # Set of clients who have pending requests
    
    def request_token(self, client_id):
        """
        Handle a client request for the token
        Returns:
            (granted, position, wait_time)
            granted: Boolean if token was granted
            position: Position in queue (0 = granted)
            wait_time: Estimated time to wait or cooldown time
        """
        with self.lock:
            current_time = time.time()
            
            # Check if client is in cooldown
            if client_id in self.cooldowns:
                cooldown_until = self.cooldowns[client_id]
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    return False, -1, remaining
                else:
                    # Cooldown expired, remove from cooldowns
                    self.cooldowns.pop(client_id)
            
            # Client already has a pending request
            if client_id in self.pending_requests:
                # Find position in queue
                position = None
                for i, queued_id in enumerate(self.request_queue):
                    if queued_id == client_id:
                        position = i
                        break
                
                if position is not None:
                    return False, position, position * 5  # Estimate 5 seconds per client
                else:
                    # Client already has the token
                    if self.token_holder == client_id:
                        return True, 0, 0
            
            # Check if token is free
            if self.token_holder is None and not self.request_queue:
                # Grant token immediately
                self.token_holder = client_id
                self.token_acquired_time = current_time
                self.pending_requests.add(client_id)
                return True, 0, 0
            else:
                # Add to queue
                self.request_queue.append(client_id)
                self.pending_requests.add(client_id)
                position = len(self.request_queue) - 1
                return False, position, position * 5  # Estimate 5 seconds per client
    
    def release_token(self, client_id):
        """
        Release token held by client_id
        Returns:
            (success, next_holder)
            success: Boolean if release was successful
            next_holder: ID of client who gets the token next, or None
        """
        with self.lock:
            if self.token_holder != client_id:
                return False, None
            
            # Apply cooldown for the client
            current_time = time.time()
            self.cooldowns[client_id] = current_time + self.cooldown_duration
            
            # Remove from pending requests
            if client_id in self.pending_requests:
                self.pending_requests.remove(client_id)
            
            # Grant token to next in queue if any
            next_holder = None
            while self.request_queue and not next_holder:
                next_client = self.request_queue.popleft()
                
                # Skip clients in cooldown
                if next_client in self.cooldowns:
                    cooldown_until = self.cooldowns[next_client]
                    if current_time < cooldown_until:
                        # Still in cooldown, remove from pending
                        if next_client in self.pending_requests:
                            self.pending_requests.remove(next_client)
                        continue
                    else:
                        # Cooldown expired
                        self.cooldowns.pop(next_client)
                
                next_holder = next_client
            
            if next_holder:
                self.token_holder = next_holder
                self.token_acquired_time = current_time
            else:
                self.token_holder = None
                self.token_acquired_time = None
            
            return True, next_holder
    
    def force_release_token(self):
        """
        Force release of token (used for deadlock resolution)
        Returns:
            (previous_holder, next_holder)
        """
        with self.lock:
            previous_holder = self.token_holder
            
            if previous_holder:
                # Don't apply cooldown for forced releases
                if previous_holder in self.pending_requests:
                    self.pending_requests.remove(previous_holder)
            
            # Grant token to next in queue if any
            next_holder = None
            if self.request_queue:
                next_holder = self.request_queue.popleft()
                self.token_holder = next_holder
                self.token_acquired_time = time.time()
            else:
                self.token_holder = None
                self.token_acquired_time = None
            
            return previous_holder, next_holder
    
    def get_status(self):
        """
        Get current status of the token
        Returns a dictionary with token status info
        """
        with self.lock:
            queue_list = list(self.request_queue)
            return {
                "resource": self.resource_name,
                "holder": self.token_holder,
                "queue": queue_list,
                "queue_length": len(queue_list)
            }
    
    def is_token_held(self, client_id=None):
        """Check if token is held, optionally by a specific client"""
        with self.lock:
            if client_id is not None:
                return self.token_holder == client_id
            else:
                return self.token_holder is not None
    
    def is_in_cooldown(self, client_id):
        """Check if a client is in cooldown period"""
        with self.lock:
            if client_id in self.cooldowns:
                current_time = time.time()
                cooldown_until = self.cooldowns[client_id]
                
                if current_time < cooldown_until:
                    return True, int(cooldown_until - current_time)
                else:
                    # Cooldown expired, remove from cooldowns
                    self.cooldowns.pop(client_id)
            
            return False, 0