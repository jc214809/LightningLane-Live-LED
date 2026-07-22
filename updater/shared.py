import threading

# Guards mutations of the shared parks_data structure by the WebSocket and REST
# threads. Held only for in-memory writes (microseconds) — never across HTTP
# calls. The display thread deliberately reads without locking: a torn read
# costs one frame of slightly inconsistent pixels, not corrupted state.
parks_data_lock = threading.Lock()
