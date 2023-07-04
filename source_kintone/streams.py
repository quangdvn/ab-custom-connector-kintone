from abc import ABC
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Tuple)

import requests
from airbyte_cdk.sources.streams.http import HttpStream

from source_kintone.auth import KintoneAuthenticator
from source_kintone.mapping import KINTONE_TO_AIRBYTE_MAPPING
from source_kintone.utils import generate_mapping_result


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

  def __init__(self, domain: str, app_id: str, include_label: bool, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain
    self.app_id = app_id
    self.include_label = include_label

  def path(self, **kwargs) -> str:
    return f"{self.domain}/k/v1/app/form/fields.json?app={self.app_id}&lang=ja"

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    app_schema: dict = response.json()['properties']
    # Remove unused properties from API response
    filter_app_schema = {
        key: value for key, value in app_schema.items() if "enabled" not in value or value.get("enabled") == True
    }

    for key, value in filter_app_schema.items():
      try:
        field_name = value['label'] if self.include_label else key
        field_type = value['type']
        field_schema = {
            field_name: {
                **KINTONE_TO_AIRBYTE_MAPPING[field_type], "data_label": key}
        }
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
  page_size = 500
  current_offset = 0

  def __init__(self, domain: str, app_id: str, include_label: bool, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain
    self.app_id = app_id
    self.include_label = include_label

  @property
  def name(self) -> str:
    return f"APP_{self.app_id}"

  def path(self, **kwargs) -> str:
    return f"{self.domain}/k/v1/records.json?app={self.app_id}&totalCount=true"

  def next_page_token(self, response: requests.Response) -> Mapping[str, Any]:
    offset = 0
    total_records = int(response.json()['totalCount'])

    # Assign offset value on every stream read
    if total_records - AppDetail.current_offset > AppDetail.page_size:
      offset = AppDetail.current_offset + AppDetail.page_size
      AppDetail.current_offset += AppDetail.page_size
      return {"query": f"limit {AppDetail.page_size} offset {offset}"}

    # Last stream read
    elif total_records - AppDetail.current_offset < AppDetail.page_size:
      return {}

  def request_params(
      self,
      stream_state: Mapping[str, Any],
      stream_slice: Mapping[str, Any] = None,
      next_page_token: Mapping[str, Any] = None,
  ) -> MutableMapping[str, Any]:
    params = {}

    # Handle pagination by inserting the next page's token in the request parameters
    # First stream read
    if AppDetail.current_offset == 0:
      params.update({"query": f"limit {AppDetail.page_size} offset 0"})
    else:
      if next_page_token:
        params.update(next_page_token)
      # Final stream read, next_page_token is None
      params.update(
          {"query": f"limit {AppDetail.page_size} offset {AppDetail.current_offset}"})
    return params

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    mapping_dict = {}
    app_records = response.json()['records']

    if not self.include_label:
      app_records_generator = generate_mapping_result(
          raw_data=app_records)
    else:
      app_schema_stream = AppSchema(
          authenticator=self.authenticator,
          domain=self.domain,
          app_id=self.app_id,
          include_label=self.include_label)
      app_schema_records = app_schema_stream.read_records(
          sync_mode="full_refresh")
      default_schema = {
          "$id": {"type": ["null", "string"], "data_label": "$id"},
          "$revision": {"type": ["null", "string"], "data_label": "$revision"},
      }
      for schema_property in app_schema_records:
        default_schema.update(schema_property)
      for key, value in default_schema.items():
        # Eg: mapping_dict = {
        #   "SalesCategoryDetails": "売上区分詳細"
        # }
        mapping_dict[value["data_label"]] = key
      app_records_generator = generate_mapping_result(
          raw_data=app_records,
          mapping_dict=mapping_dict,
          include_label=True)

    # Finally, convert the generator to a list
    records_response = list(app_records_generator)
    yield from records_response

  def get_json_schema(self) -> Mapping[str, Any]:
    app_schema_stream = AppSchema(
        authenticator=self.authenticator,
        domain=self.domain,
        app_id=self.app_id,
        include_label=self.include_label
    )
    app_schema_records = app_schema_stream.read_records(
        sync_mode="full_refresh")

    # Each record corresponds to a property in the JSON Schema
    # Loop over each of these properties and add it to the JSON Schema
    default_schema = {
        "$id": {"type": ["null", "string"], "data_label": "$id"},
        "$revision": {"type": ["null", "string"], "data_label": "$revision"},
    }
    for schema_property in app_schema_records:
      default_schema.update(schema_property)
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "additionalProperties": True,
        "type": "object",
        "properties": default_schema,
    }
