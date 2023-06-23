from abc import ABC
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Tuple)

import requests
from airbyte_cdk.sources.streams.http import HttpStream

from source_kintone.auth import KintoneAuthenticator
from source_kintone.mapping import KINTONE_TO_AIRBYTE_MAPPING


# Basic full refresh stream
class KintoneStream(HttpStream, ABC):
  url_base = ""

  @property
  def authenticator(self) -> KintoneAuthenticator:
    return self._session.auth

  def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
    """kintone API does not return any information to support pagination"""
    return None

  def request_params(
      self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
  ) -> MutableMapping[str, Any]:
    return {}

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    yield {}


class AppSchema(KintoneStream):
  primary_key = None

  def __init__(self, domain: str, app_id: str, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain
    self.app_id = app_id

  def path(self, **kwargs) -> str:
    return f"https://{self.domain}.cybozu.com/k/v1/app/form/fields.json?app={self.app_id}&lang=ja"

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    app_schema = response.json()['properties']
    for key, value in app_schema.items():
      try:
        field_name = key
        field_type = value['type']
        field_schema = {
            field_name: KINTONE_TO_AIRBYTE_MAPPING[field_type]}
        yield field_schema
      except Exception as error:
        msg = f"""Encountered an exception parsing schema for kintone type: {field_type}\n
                  Is "{field_type}" defined in the mapping between kintone and JSON Schema? """
        self.logger.exception(msg)
        # Don't eat the exception, raise it again as this needs to be fixed
        raise error


class AppDetail(KintoneStream):
  http_method = "GET"
  primary_key = None

  def __init__(self, domain: str, app_id: str, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain
    self.app_id = app_id

  @property
  def name(self) -> str:
    return f"APP_{self.app_id}"

  def path(self, **kwargs) -> str:
    return f"https://{self.domain}.cybozu.com/k/v1/apps.json"

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    response_json = response.json()
    yield from response_json

  def get_json_schema(self) -> Mapping[str, Any]:
    app_schema_stream = AppSchema(
        authenticator=self.authenticator, domain=self.domain, app_id=self.app_id)
    app_schema_records = app_schema_stream.read_records(
        sync_mode="full_refresh")

    # Each record corresponds to a property in the JSON Schema
    # Loop over each of these properties and add it to the JSON Schema
    json_schema = {}
    for schema_property in app_schema_records:
      json_schema.update(schema_property)

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "additionalProperties": True,
        "type": "object",
        "properties": json_schema,
    }
