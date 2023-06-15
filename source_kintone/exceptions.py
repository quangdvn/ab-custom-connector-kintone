from airbyte_cdk.logger import AirbyteLogger


class Error(Exception):
  """Base Error class for other exceptions"""

  # Define the instance of the Native Airbyte Logger
  logger = AirbyteLogger()


class KintoneException(Exception):
  """
  Default Kintone exception.
  """


class TypeKintoneException(KintoneException):
  """
  We use this exception for unknown input data types for Yahoo Ads.
  """


class TmpFileIOError(Error):
  def __init__(self, msg: str, err: str = None):
    self.logger.fatal(f"{msg}. Error: {err}")
