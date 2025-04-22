# server/time_warp_manager.py
import threading
import time

class TimeWarpManager:
    """
    Manager for the Time Warp token
    Uses Ricart-Agrawala for mutual exclusion
    """
    def __init__(self, duration=90, cooldown=120):
        self.duration = duration  # Time Warp active time in seconds
        self.cooldown = cooldown  # Cooldown period in seconds
        self.active_warps = {}  # {client_id: (start_time, end_time)}
        self.cooldowns = {}  # {client_id: end_time}
        self.lock = threading.Lock()

    def activate_time_warp(self, client_id):
        """
        Activate Time Warp for a client
        Returns:
            (success, remaining, message)
        """
        with self.lock:
            # Check if client is in cooldown
            current_time = time.time()
            if client_id in self.cooldowns:
                cooldown_until = self.cooldowns[client_id]
                if current_time < cooldown_until:
                    remaining = int(cooldown_until - current_time)
                    return False, remaining, f"In cooldown for {remaining}s"

            # Check if client already has active time warp
            if client_id in self.active_warps:
                _, end_time = self.active_warps[client_id]
                if current_time < end_time:
                    remaining = int(end_time - current_time)
                    return True, remaining, f"Already active for {remaining}s"

            # Activate new time warp
            start_time = current_time
            end_time = start_time + self.duration
            self.active_warps[client_id] = (start_time, end_time)

            # Schedule automatic deactivation
            threading.Timer(
                self.duration,
                self._auto_deactivate_time_warp,
                args=[client_id, end_time]
            ).start()

            return True, self.duration, "Time Warp activated"

    def _auto_deactivate_time_warp(self, client_id, expected_end_time):
        """Automatically deactivate time warp when duration expires"""
        with self.lock:
            # Only deactivate if it's the same session
            if client_id in self.active_warps:
                _, end_time = self.active_warps[client_id]
                if end_time == expected_end_time:
                    self.deactivate_time_warp(client_id)

    def deactivate_time_warp(self, client_id):
        """
        Deactivate Time Warp for a client
        Returns:
            success: Boolean indicating if deactivation was successful
        """
        with self.lock:
            if client_id not in self.active_warps:
                return False

            # Remove active time warp
            self.active_warps.pop(client_id)

            # Apply cooldown
            current_time = time.time()
            self.cooldowns[client_id] = current_time + self.cooldown

            return True

    def is_time_warp_active(self, client_id):
        """
        Check if Time Warp is active for a client
        Returns:
            (active, remaining)
        """
        with self.lock:
            current_time = time.time()

            # Check if time warp is active
            if client_id in self.active_warps:
                _, end_time = self.active_warps[client_id]
                if current_time < end_time:
                    remaining = int(end_time - current_time)
                    return True, remaining
                else:
                    # Time warp expired, clean up
                    self.deactivate_time_warp(client_id)

            return False, 0

    def get_score_multiplier(self, client_id):
        """
        Get the score multiplier for a client
        Returns:
            multiplier: 2 if time warp is active, 1 otherwise
        """
        active, _ = self.is_time_warp_active(client_id)
        return 2 if active else 1

    def get_status(self, client_id=None):
        """
        Get status of Time Warp for a specific client or all clients
        """
        with self.lock:
            current_time = time.time()

            if client_id is not None:
                # Status for specific client
                status = {
                    "active": False,
                    "remaining": 0,
                    "cooldown": 0,
                    "multiplier": 1
                }

                # Check if time warp is active
                if client_id in self.active_warps:
                    _, end_time = self.active_warps[client_id]
                    if current_time < end_time:
                        status["active"] = True
                        status["remaining"] = int(end_time - current_time)
                        status["multiplier"] = 2

                # Check if client is in cooldown
                if client_id in self.cooldowns:
                    cooldown_until = self.cooldowns[client_id]
                    if current_time < cooldown_until:
                        status["cooldown"] = int(cooldown_until - current_time)

                return status
            else:
                # Status for all clients
                active_warps = {}
                for cid, (start, end) in self.active_warps.items():
                    if current_time < end:
                        active_warps[cid] = int(end - current_time)

                cooldowns = {}
                for cid, end in self.cooldowns.items():
                    if current_time < end:
                        cooldowns[cid] = int(end - current_time)

                return {
                    "active_warps": active_warps,
                    "cooldowns": cooldowns
                }