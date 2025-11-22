# a2a_bus.py
# Simple in-process A2A message bus for agents.
from typing import Callable, Dict, Any
from collections import defaultdict
from threading import Lock

class A2ABus:
    def __init__(self):
        self._subs = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, topic: str, handler: Callable[[Dict[str,Any]], None]):
        with self._lock:
            self._subs[topic].append(handler)

    def publish(self, topic: str, message: Dict[str,Any]):
        handlers = list(self._subs.get(topic, []))
        for h in handlers:
            try:
                h(message)
            except Exception as e:
                # handlers should handle their own exceptions
                print(f"A2A handler error: {e}")
