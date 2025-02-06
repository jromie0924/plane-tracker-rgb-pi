import threading
import config
import logging

from models.runtimeModel import RuntimeModel

class RuntimeService:
  _instance = None
  _lock = threading.Lock()
  
  def __new__(cls):
    with cls._lock:
      if not cls._instance:
        cls._instance = super(RuntimeService, cls).__new__(cls)
        cls._instance.__init__()
      return cls._instance
  
  def __init__(self):
    self.logger = logging.getLogger(config.APP_NAME)
    
  def set_runtime_vars(self, runtime_vars: RuntimeModel):
    self._runtime_vars = runtime_vars
  
  @property
  def aws_access_key_id(self):
    return self._runtime_vars._aws_access_key_id
  
  @property
  def aws_secret_access_key(self):
    return self._runtime_vars._aws_secret_access_key
    
  