import config
import logging

from models.runtimeModel import RuntimeModel
from services.singleton import Singleton

class RuntimeService(Singleton):
  def __init__(self):
    if hasattr(self, '_initialized'):
      return
    self._initialized = True
    
    self.logger = logging.getLogger(config.APP_NAME)
    self.logger.info(f'{self.__class__.__name__} successfully initialized.')
    
  def set_runtime_vars(self, runtime_vars: RuntimeModel):
    self._runtime_vars = runtime_vars
  
  @property
  def aws_access_key_id(self):
    return self._runtime_vars._aws_access_key_id
  
  @property
  def aws_secret_access_key(self):
    return self._runtime_vars._aws_secret_access_key
    
  