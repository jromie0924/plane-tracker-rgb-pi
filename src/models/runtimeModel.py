
class RuntimeModel:
  def __init__(self, aws_access_key_id: str, aws_secret_access_key: str):
    self._aws_access_key_id: str = aws_access_key_id
    self._aws_secret_access_key: str = aws_secret_access_key