# client/clock_sync.py
import time
import threading


class LogicalClock:
    """
    Client-side Lamport logical clock implementation
    """

    def __init__(self):
        self.timestamp = 0
        self._lock = threading.Lock()

    def increment(self):
        """Increment the logical clock by 1"""
        with self._lock:
            self.timestamp += 1
            return self.timestamp

    def sync(self, received_time):
        """
        Synchronize with received timestamp
        Updates local clock to max(local, received) + 1
        """
        with self._lock:
            self.timestamp = max(self.timestamp, received_time) + 1
            return self.timestamp

    def get_time(self):
        """Get current timestamp"""
        with self._lock:
            return self.timestamp


class NetworkTimeClient:
    """
    NTP client implementation for clock synchronization with the server
    """

    def __init__(self):
        self.offset = 0  # Time offset from server
        self.reference_timestamp = time.time()
        self._lock = threading.Lock()
        self.last_sync_time = 0

    def request_sync(self):
        """
        Return client timestamp for sync request
        """
        with self._lock:
            self.last_sync_time = time.time()
            return self.last_sync_time

    def process_sync_response(self, t2, t3):
        """
        Process server response and calculate offset
        t2: server receive time
        t3: server reply time
        """
        with self._lock:
            t1 = self.last_sync_time
            t4 = time.time()

            # Calculate round-trip delay
            delay = (t4 - t1) - (t3 - t2)

            # Calculate offset
            offset = ((t2 - t1) + (t3 - t4)) / 2

            # Update offset if delay is reasonable (not too large)
            if delay > 0 and delay < 5.0:  # 5 seconds is an arbitrary threshold
                self.offset = offset
                self.reference_timestamp = time.time()

            return self.offset

    def get_adjusted_time(self):
        """Get time adjusted by the calculated offset"""
        with self._lock:
            return time.time() + self.offset