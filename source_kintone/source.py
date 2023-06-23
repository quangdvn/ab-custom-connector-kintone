from abc import ABC
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Tuple)

import requests
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream

from source_kintone.api import Kintone
from source_kintone.auth import KintoneAuthenticator
from source_kintone.streams import AppDetail


# Source
class SourceKintone(AbstractSource):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  @staticmethod
  def _get_kintone_object(config: Mapping[str, Any]) -> Kintone:
    kintone = Kintone(**config)
    kintone.authentication()
    return kintone

  @staticmethod
  def _get_kintone_authenticator(config):
    username = config['auth_type']['username']
    password = config['auth_type']['password']
    if not username or not password:
      raise Exception(
          "username and passowrd are required properties")
    auth = KintoneAuthenticator(username=username, password=password)
    return auth

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
      return False, "System error"

  def streams(self, config: Mapping[str, Any]) -> List[Stream]:
    auth = self._get_kintone_authenticator(config)
    domain = config.get('domain')
    app_ids = config.get('app_ids')
    streams: List[Stream] = []
    for app_id in app_ids:
      streams.append(AppDetail(authenticator=auth,
                               domain=domain,
                               app_id=app_id))
    return streams
