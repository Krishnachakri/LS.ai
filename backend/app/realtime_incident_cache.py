from collections import deque
from typing import Deque

# Realtime In-Memory Incident Cache to store the last 20 incident dictionaries.
# Stored as serialized dictionaries matching the Incident Schema v1.
incidents_cache: Deque[dict] = deque(maxlen=20)
