"""
Leaderboard Token Manager implementing Raymond's algorithm (simplified).
"""
import time


class LeaderboardToken:
    def __init__(self):
        self.has_token = True
        self.queue = []
        self.current_holder = None
        self.last_used = {}  # player_id -> timestamp
        self.cooldown_period = 30  # 30 seconds cooldown

    def request_token(self, player_id):
        """Handle a token request"""
        current_time = time.time()

        # Check cooldown
        if player_id in self.last_used and current_time - self.last_used[player_id] < self.cooldown_period:
            remaining = self.cooldown_period - (current_time - self.last_used[player_id])
            return False, f"Cooldown: {remaining:.1f}s remaining"

        # If we have the token and it's free, grant it
        if self.has_token and self.current_holder is None:
            self.current_holder = player_id
            return True, "Leaderboard token granted"

        # Otherwise, add to queue
        if player_id not in self.queue:
            self.queue.append(player_id)
        return False, f"Added to leaderboard queue. Position: {self.queue.index(player_id) + 1}"

    def release_token(self, player_id):
        """Handle token release"""
        if self.current_holder != player_id:
            return False, "You don't hold the leaderboard token"

        # Record last usage time
        self.last_used[player_id] = time.time()

        # If queue is not empty, pass token to next in queue
        if self.queue:
            self.current_holder = self.queue.pop(0)
            return True, f"Leaderboard token passed to {self.current_holder}"
        else:
            self.current_holder = None
            return True, "Leaderboard token released"

    def get_status(self):
        """Get the current token status"""
        return {
            "has_token": self.has_token,
            "current_holder": self.current_holder,
            "queue": self.queue
        }
