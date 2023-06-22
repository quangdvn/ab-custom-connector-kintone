from abc import ABC
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Tuple)

import requests
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator


# Basic full refresh stream
class KintoneStream(HttpStream, ABC):
  url_base = "https://"

  def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
    return None

  def request_params(
      self, stream_state: Mapping[str, Any], stream_slice: Mapping[str, any] = None, next_page_token: Mapping[str, Any] = None
  ) -> MutableMapping[str, Any]:
    return {}

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    yield {}

# Get all apps


class AppList(KintoneStream):
  def __init__(self, domain: str, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain

  def path(self, **kwargs) -> str:
    return f"{self.domain}/.cybozu.com/k/v1/apps.json"

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    # Use the generator function to iterate over the rows of data
    response_json = response.json()
    yield from response_json

# Get all space apps


class AppDetail(KintoneStream):
  http_method = "GET"
  #  primary_key is not used as we don't do incremental syncs - https://docs.airbyte.com/understanding-airbyte/connections/
  primary_key = None

  def __init__(self, domain: str, app_ids: list[str], guest_space_id=None, ** kwargs):
    super().__init__(**kwargs)
    self.domain = domain
    self.app_ids = app_ids

  @property
  def name(self) -> str:
    if self.guest_space_id:
      return f"GUEST_SPACE_{self.guest_space_id}_APP_{self.app_id}"
    return f"PUBLIC_SPACE_APP_{self.app_id}"

  def path(self, **kwargs) -> str:
    return f"{self.domain}.cybozu.com/k/v1/apps.json"

  def parse_response(self, response: requests.Response, **kwargs) -> Iterable[Mapping]:
    # Use the generator function to iterate over the rows of data
    response_json = response.json()
    yield from response_json


class Customers(KintoneStream):
  """
  TODO: Change class name to match the table/data source this stream corresponds to.
  """

  # TODO: Fill in the primary key. Required. This is usually a unique field in the stream, like an ID or a timestamp.
  primary_key = "customer_id"

  def path(
      self, stream_state: Mapping[str, Any] = None, stream_slice: Mapping[str, Any] = None, next_page_token: Mapping[str, Any] = None
  ) -> str:
    """
    TODO: Override this method to define the path this stream corresponds to. E.g. if the url is https://example-api.com/v1/customers then this
    should return "customers". Required.
    """
    return "customers"


# Basic incremental stream
class IncrementalKintoneStream(KintoneStream, ABC):
  """
  TODO fill in details of this class to implement functionality related to incremental syncs for your connector.
       if you do not need to implement incremental sync for any streams, remove this class.
  """

  # TODO: Fill in to checkpoint stream reads after N records. This prevents re-reading of data if the stream fails for any reason.
  state_checkpoint_interval = None

  @property
  def cursor_field(self) -> str:
    """
    TODO
    Override to return the cursor field used by this stream e.g: an API entity might always use created_at as the cursor field. This is
    usually id or date based. This field's presence tells the framework this in an incremental stream. Required for incremental.

    :return str: The name of the cursor field.
    """
    return []

  def get_updated_state(self, current_stream_state: MutableMapping[str, Any], latest_record: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Override to determine the latest state after reading the latest record. This typically compared the cursor_field from the latest record and
    the current state and picks the 'most' recent cursor. This is how a stream's state is determined. Required for incremental.
    """
    return {}


class Employees(IncrementalKintoneStream):
  """
  TODO: Change class name to match the table/data source this stream corresponds to.
  """

  # TODO: Fill in the cursor_field. Required.
  cursor_field = "start_date"

  # TODO: Fill in the primary key. Required. This is usually a unique field in the stream, like an ID or a timestamp.
  primary_key = "employee_id"

  def path(self, **kwargs) -> str:
    """
    TODO: Override this method to define the path this stream corresponds to. E.g. if the url is https://example-api.com/v1/employees then this should
    return "single". Required.
    """
    return "employees"

  def stream_slices(self, stream_state: Mapping[str, Any] = None, **kwargs) -> Iterable[Optional[Mapping[str, any]]]:
    """
    TODO: Optionally override this method to define this stream's slices. If slicing is not needed, delete this method.

    Slices control when state is saved. Specifically, state is saved after a slice has been fully read.
    This is useful if the API offers reads by groups or filters, and can be paired with the state object to make reads efficient. See the "concepts"
    section of the docs for more information.

    The function is called before reading any records in a stream. It returns an Iterable of dicts, each containing the
    necessary data to craft a request for a slice. The stream state is usually referenced to determine what slices need to be created.
    This means that data in a slice is usually closely related to a stream's cursor_field and stream_state.

    An HTTP request is made for each returned slice. The same slice can be accessed in the path, request_params and request_header functions to help
    craft that specific request.

    For example, if https://example-api.com/v1/employees offers a date query params that returns data for that particular day, one way to implement
    this would be to consult the stream state object for the last synced date, then return a slice containing each date from the last synced date
    till now. The request_params function would then grab the date from the stream_slice and make it part of the request by injecting it into
    the date query param.
    """
    raise NotImplementedError("Implement stream slices or delete this method!")
