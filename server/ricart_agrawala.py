class RicartAgrawala:
    def __init__(self):
        self.in_critical_section = False
        self.current_holder = None
        self.start_time = 0
        self.duration = 30  # Time warp lasts 30 seconds

    def request_critical_section(self, player_id, timestamp):
        """Request access to critical section"""
        current_time = time.time()

        # If in use, return busy
        if self.in_critical_section:
            remaining = (self.start_time + self.duration) - current_time
            if remaining <= 0:
                # Time's up, force release
                self.release_critical_section(self.current_holder)
            else:
                return False, self.current_holder, remaining

        # Grant critical section
        self.in_critical_section = True
        self.current_holder = player_id
        self.start_time = current_time

        # Schedule automatic release after duration
        return True, None, self.duration

    def release_critical_section(self, player_id):
        """Release the critical section"""
        if not self.in_critical_section or self.current_holder != player_id:
            return False, "Not in critical section"

        self.in_critical_section = False
        self.current_holder = None
        return True, "Released critical section"

    def get_status(self):
        """Get critical section status"""
        current_time = time.time()
        remaining = 0

        if self.in_critical_section:
            remaining = max(0, (self.start_time + self.duration) - current_time)

        return {
            "in_use": self.in_critical_section,
            "current_holder": self.current_holder,
            "remaining": remaining
        }