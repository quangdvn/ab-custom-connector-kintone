from abc import ABC
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Tuple)

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator

from source_kintone.api import Kintone


# Source
class SourceKintone(AbstractSource):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  @staticmethod
  def _get_kintone_object(config: Mapping[str, Any]) -> Kintone:
    kintone = Kintone(**config)
    kintone.authentication()
    return kintone

  def check_connection(self, logger, config) -> Tuple[bool, any]:
    try:
      kintone_object = self._get_kintone_object(config)
      if kintone_object.authentication_error is not None:
        logger.info('Authentication failed')
        return False, kintone_object.authentication_error
      return True, None
    except requests.exceptions.HTTPError as error:
      error_data = error.response.json()[0]
      error_code = error_data.get("errorCode")
      if error.response.status_code == requests.codes.FORBIDDEN and error_code == "REQUEST_LIMIT_EXCEEDED":
        logger.warn(
            f"API Call limit is exceeded. Error message: '{error_data.get('message')}'")
        return False, "API Call limit is exceeded"

  def streams(self, config: Mapping[str, Any]) -> List[Stream]:
    """
    TODO: Replace the streams below with your own streams.

    :param config: A Mapping of the user input configuration as defined in the connector spec.
    """
    # TODO remove the authenticator if not required.
    # Oauth2Authenticator is also available if you need oauth support
    auth = TokenAuthenticator(token="api_key")
    return []
