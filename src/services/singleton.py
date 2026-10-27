import threading


class Singleton:
  _lock = threading.Lock()

  def __new__(cls, *args, **kwargs):
    with cls._lock:
      if cls.__dict__.get('_instance') is None:
        cls._instance = super().__new__(cls)
      return cls._instance
