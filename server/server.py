# server/ricart_agrawala.py
import threading
import time
from collections import deque

class RicartAgrawala:
    """
    Server-side implementation of Ricart-Agrawala algorithm for mutual exclusion
    This is a centralized version managing the Time Warp token
    """
    def __init__(self, resource_name="time_warp"):
        self.resource_name = resource_name
        self.lock = threading.Lock()
        self.requesting_clients = {}  # {client_id: timestamp}
        self.deferred_replies = {}  # {client_id: [deferred_client_ids]}
        self.in_critical_section = None  # client currently in CS
        self.cs_timestamp = None  # timestamp of current CS holder
        self.cs_start_time = None  # when current holder entered CS
        self.cs_duration = 90  # Time Warp duration in seconds
        self.cooldowns = {}  # {client_id: expiry_time}
        self.cooldown_duration = 120  # cooldown duration in seconds
    
    def request_critical_section(self, client_id, timestamp):
        """
        Handle a client request for the critical section (Time Warp)
        Returns:
            (success, wait_reason, remaining_time)
            success: Boolean if granted
            wait_reason: None or reason why waiting
            remaining_time: Seconds remaining if waiting
        """
        with self.lock:
            # Check if client is in cooldown
            if client_id in self.cooldowns:
                cooldown_until = self.cooldowns[client_id]
                current_time = time.time()
                
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    return False, "cooldown", remaining
            
            # Check if critical section is already occupied
            if self.in_critical_section:
                # If current holder's time is expired, force release
                current_time = time.time()
                if self.cs_start_time and current_time - self.cs_start_time > self.cs_duration:
                    self._release_critical_section(self.in_critical_section)
                else:
                    # CS is occupied, defer the reply
                    if self.in_critical_section not in self.deferred_replies:
                        self.deferred_replies[self.in_critical_section] = []
                    
                    self.deferred_replies[self.in_critical_section].append(client_id)
                    remaining = int((self.cs_start_time + self.cs_duration) - current_time)
                    return False, "in_use", remaining
            
            # Grant the critical section
            self.in_critical_section = client_id
            self.cs_timestamp = timestamp
            self.cs_start_time = time.time()
            
            # Schedule automatic release
            threading.Timer(self.cs_duration, 
                            self._auto_release_critical_section, 
                            args=[client_id, timestamp]).start()
            
            return True, None, self.cs_duration
    
    def _auto_release_critical_section(self, client_id, timestamp):
        """Automatically release critical section after duration expires"""
        with self.lock:
            # Only release if it's still the same session (client and timestamp)
            if self.in_critical_section == client_id and self.cs_timestamp == timestamp:
                self._release_critical_section(client_id)
    
    def release_critical_section(self, client_id):
        """Explicitly release critical section"""
        with self.lock:
            if self.in_critical_section == client_id:
                self._release_critical_section(client_id)
                return True
            return False
    
    def _release_critical_section(self, client_id):
        """Internal method to release critical section and handle deferred replies"""
        # Apply cooldown
        current_time = time.time()
        self.cooldowns[client_id] = current_time + self.cooldown_duration
        
        # Release critical section
        self.in_critical_section = None
        self.cs_timestamp = None
        self.cs_start_time = None
        
        # Process deferred replies if any
        if client_id in self.deferred_replies:
            deferred = self.deferred_replies.pop(client_id)
            # For simplicity, we're not implementing the full RA algorithm
            # We just release the resource so it's available for the next request
    
    def is_in_critical_section(self, client_id):
        """Check if a client is currently in the critical section"""
        with self.lock:
            return self.in_critical_section == client_id
    
    def get_remaining_time(self, client_id):
        """Get remaining time in critical section or cooldown"""
        with self.lock:
            current_time = time.time()
            
            # Check if client is in critical section
            if self.in_critical_section == client_id and self.cs_start_time:
                elapsed = current_time - self.cs_start_time
                remaining = max(0, self.cs_duration - elapsed)
                return "active", int(remaining)
            
            # Check if client is in cooldown
            if client_id in self.cooldowns:
                cooldown_until = self.cooldowns[client_id]
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    return "cooldown", remaining
                else:
                    # Cooldown expired, remove from cooldowns
                    self.cooldowns.pop(client_id)
            
            return "available", 0
    
    def get_status(self):
        """Get current status of the Time Warp token"""
        with self.lock:
            if self.in_critical_section:
                remaining = 0
                if self.cs_start_time:
                    elapsed = time.time() - self.cs_start_time
                    remaining = max(0, self.cs_duration - elapsed)
                
                return {
                    "status": "in_use",
                    "holder": self.in_critical_section,
                    "remaining": int(remaining)
                }
            else:
                return {
                    "status": "available",
                    "holder": None,
                    "remaining": 0
                }