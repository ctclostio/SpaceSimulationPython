import threading
from collections import deque
from time import perf_counter
from ursina import Vec3

class PositionBuffer:
    def __init__(self, max_history=5):
        self.buffers = [deque(maxlen=max_history), deque(maxlen=max_history)]
        self.buffer_index = 0
        self.lock = threading.Lock()
        self.swap_lock = threading.Lock()
        self.swap_in_progress = threading.Event()
        self.last_swap = perf_counter()

    def write_position(self, entity_id, position):
        """Thread-safe position write to active buffer"""
        with self.lock:
            current_buffer = self.buffers[self.buffer_index]
            current_buffer.append({
                'id': entity_id,
                'pos': Vec3(position),
                'timestamp': perf_counter()
            })

    def read_position(self, entity_id, interpolate=True):
        """Get position with optional interpolation from inactive buffer"""
        # Check both buffers if inactive is empty
        inactive_buffer = self.buffers[not self.buffer_index]
        active_buffer = self.buffers[self.buffer_index]
        
        # Combine entries from both buffers, prioritizing inactive buffer
        combined_entries = list(inactive_buffer) + list(active_buffer)
        
        # Find matching entity entries sorted by recency
        entries = [e for e in combined_entries if e['id'] == entity_id]
        entries.sort(key=lambda x: x['timestamp'], reverse=True)
        
        if not entries:
            return None
            
        if not interpolate or len(entries) < 2:
            return entries[0]['pos']
            
        # Interpolate between two most recent positions
        current_time = perf_counter()
        newer = entries[0]
        older = entries[1]
        time_delta = newer['timestamp'] - older['timestamp']
        
        if time_delta <= 0:
            return newer['pos']
            
        blend_factor = (current_time - newer['timestamp']) / time_delta
        return newer['pos'].lerp(older['pos'], blend_factor)

    def swap_buffers(self):
        """Atomic buffer swap with consistency checks"""
        with self.swap_lock:
            if self.swap_in_progress.is_set():
                return False
            self.swap_in_progress.set()
        
        try:
            self.buffer_index = not self.buffer_index
            self.buffers[self.buffer_index].clear()
            self.last_swap = perf_counter()
            return True
        finally:
            self.swap_in_progress.clear()

    def get_buffer_metrics(self):
        """Return performance counters and buffer stats"""
        with self.lock:
            return {
                'buffer_depth': [len(b) for b in self.buffers],
                'last_swap': self.last_swap,
                'swap_count': self.buffer_index
            }

class BufferManager:
    def __init__(self):
        self.entity_buffers = {}
        self.global_lock = threading.RLock()

    def register_entity(self, entity_id):
        with self.global_lock:
            if entity_id not in self.entity_buffers:
                self.entity_buffers[entity_id] = PositionBuffer()

    def update_position(self, entity_id, position):
        with self.global_lock:
            buf = self.entity_buffers.get(entity_id)
            if buf:
                buf.write_position(entity_id, position)

    def get_position(self, entity_id):
        with self.global_lock:
            buf = self.entity_buffers.get(entity_id)
            return buf.read_position(entity_id) if buf else None

    def perform_global_swap(self):
        with self.global_lock:
            results = {}
            for eid, buf in self.entity_buffers.items():
                results[eid] = buf.swap_buffers()
            return results