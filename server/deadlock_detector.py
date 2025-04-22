# server/deadlock_detector.py
import threading
import time

class DeadlockDetector:
    """
    Detects and resolves deadlocks between tokens
    Specifically looking for circular waits between hint and skip tokens
    """
    def __init__(self, hint_token_manager, skip_token_manager, check_interval=5):
        self.hint_token_manager = hint_token_manager
        self.skip_token_manager = skip_token_manager
        self.check_interval = check_interval  # seconds between checks
        self.stop_event = threading.Event()
        self.deadlock_thread = None
    
    def start(self):
        """Start periodic deadlock detection"""
        self.stop_event.clear()
        self.deadlock_thread = threading.Thread(target=self._detection_loop)
        self.deadlock_thread.daemon = True
        self.deadlock_thread.start()
    
    def stop(self):
        """Stop deadlock detection"""
        if self.deadlock_thread:
            self.stop_event.set()
            self.deadlock_thread.join(timeout=2)
            self.deadlock_thread = None
    
    def _detection_loop(self):
        """Main detection loop that runs in background thread"""
        while not self.stop_event.is_set():
            self.check_for_deadlocks()
            # Sleep until next check interval
            self.stop_event.wait(self.check_interval)
    
    def check_for_deadlocks(self):
        """
        Check for deadlocks between hint and skip tokens
        Returns True if deadlock found and resolved, False otherwise
        """
        hint_status = self.hint_token_manager.get_status()
        skip_status = self.skip_token_manager.get_status()
        
        # Simple deadlock case: client A has hint token and waits for skip token
        # while client B has skip token and waits for hint token
        hint_holder = hint_status["holder"]
        skip_holder = skip_status["holder"]
        
        # No deadlock possible if either token is free
        if hint_holder is None or skip_holder is None:
            return False
        
        hint_queue = hint_status["queue"]
        skip_queue = skip_status["queue"]
        
        # Check if hint holder is waiting for skip
        if hint_holder in skip_queue and skip_holder in hint_queue:
            # Deadlock detected - resolve by releasing hint token
            print(f"Deadlock detected between {hint_holder} and {skip_holder}")
            self._resolve_deadlock()
            return True
        
        return False
    
    def _resolve_deadlock(self):
        """
        Resolve deadlock by forcing release of one token
        Strategy: Always release hint token in case of deadlock
        """
        previous_holder, next_holder = self.hint_token_manager.force_release_token()
        return previous_holder, next_holder