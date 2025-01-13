from threading import Thread, Event
import time

class ThreadManager:
    def __init__(self):
        """Initialize a thread manager."""
        self.threads = []
        self.stop_event = Event()

    def add_thread(self, target, args=()):
        """Register a new thread."""
        thread = Thread(target=target, args=args)
        self.threads.append(thread)
        return thread

    def start_threads(self):
        """Start all registered threads."""
        for thread in self.threads:
            if not thread.is_alive():
                thread.start()

    def stop_threads(self):
        """Stop all threads by setting the stop event."""
        if not self.stop_event.is_set():
            self.stop_event.set()
            
            # Give threads time to shutdown gracefully
            timeout = 2.0  # seconds
            start_time = time.time()
            
            for thread in self.threads:
                if thread.is_alive():
                    remaining_time = timeout - (time.time() - start_time)
                    if remaining_time > 0:
                        thread.join(remaining_time)
                    if thread.is_alive():
                        print(f"Warning: Thread {thread.name} did not shutdown gracefully")
            
            self.threads.clear()
            self.stop_event.clear()

    def is_stopped(self):
        """Check if threads should stop."""
        return self.stop_event.is_set()
