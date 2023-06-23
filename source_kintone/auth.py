
from typing import Any, Mapping

from airbyte_cdk.sources.streams.http.requests_native_auth.abstract_token import \
    AbstractHeaderAuthenticator

from source_kintone.utils import encode_to_base64


class KintoneAuthenticator(AbstractHeaderAuthenticator):
  @property
  def auth_header(self) -> str:
    return self._auth_header

  @property
  def token(self) -> str:
    return f"{self._token}"

  def __init__(self, username: str, password: str = "", auth_method: str = "Basic", auth_header: str = "X-Cybozu-Authorization"):
    # auth_string = f"{username}:{password}".encode("utf8")
    # b64_encoded = base64.b64encode(auth_string).decode("utf8")
    self._auth_header = auth_header
    self._auth_method = auth_method
    self._token = encode_to_base64(f"{username}:{password}")
