import time

class TimeUtils:
  def __init__(self):
    pass
  
  
  @staticmethod
  def current_time_milli():
    return time.time() * 1000