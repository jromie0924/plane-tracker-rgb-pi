import threading


class SingletonMeta(type):
  _lock = threading.RLock()
  
  def __call__(cls, *args, **kwargs):
    with cls._lock:
      if cls.__dict__.get('_instance') is None:
        cls._instance = super().__call__(*args, **kwargs)
      return cls._instance

class Singleton(metaclass=SingletonMeta):
  pass
