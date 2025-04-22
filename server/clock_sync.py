# server/clock_sync.py
import time
import threading

class LogicalClock:
    """
    Lamport logical clock implementation for maintaining event ordering
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


class NetworkTimeProtocol:
    """
    Network Time Protocol implementation for clock synchronization
    between the server and clients
    """
    def __init__(self):
        self.offset = 0  # Time offset from server
        self.reference_timestamp = time.time()
        self._lock = threading.Lock()
    
    def synchronize(self, t1, t2, t3, t4):
        """
        Synchronize using NTP algorithm
        t1: client request time
        t2: server receive time
        t3: server reply time
        t4: client receive time
        """
        with self._lock:
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