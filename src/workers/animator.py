from time import sleep

DELAY_DEFAULT = 0.1


class Animator(object):
  class KeyFrame(object):
    @staticmethod
    def add(divisor, offset=0, scene_name='unknown'):
      def wrapper(func):
        func.properties = {"divisor": divisor, "offset": offset, "count": 0, "scene_name": scene_name}
        return func

      return wrapper

  def __init__(self):
    self.keyframes = []
    self.frame = 0
    self._delay = DELAY_DEFAULT
    self._reset_scene = True

    self._register_keyframes()

    super().__init__()

  def _register_keyframes(self):
    # Some introspection to setup keyframes
    for methodname in dir(self):
      method = getattr(self, methodname)
      if hasattr(method, "properties"):
        self.keyframes.append(method)

  def reset_scene(self):
    for keyframe in self.keyframes:
      if keyframe.properties["divisor"] == 0:
        keyframe()

  def play(self):
    while True:
      for keyframe in self.keyframes:
        # If divisor == 0 then only run once on first loop
        if self.frame == 0:
          if keyframe.properties["divisor"] == 0:
            keyframe()

        # Otherwise perform normal operation
        elif keyframe.properties["divisor"] and not ((self.frame - keyframe.properties["offset"]) % keyframe.properties["divisor"]):
          if keyframe(keyframe.properties["count"]):
            keyframe.properties["count"] = 0
          else:
            keyframe.properties["count"] += 1

      self._reset_scene = False
      self.frame += 1
      sleep(self._delay)

  @property
  def delay(self):
    return self._delay

  @delay.setter
  def delay(self, value):
    self._delay = value
