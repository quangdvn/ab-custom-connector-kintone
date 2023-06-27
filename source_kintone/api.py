# import concurrent.futures
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Optional, Tuple

import requests  # type: ignore[import]
from airbyte_cdk.models import ConfiguredAirbyteCatalog
from requests import adapters as request_adapters
# type: ignore[import]
from requests.exceptions import HTTPError, RequestException

from source_kintone.utils import encode_to_base64

from .exceptions import KintoneException
from .rate_limiting import default_backoff_handler

KINTONE_ERROR = [
    {"code": "CB_AU01", "message": "ログインしてください。"},
    {"code": "CB_NO02", "message": "権限がありません。"},
    {"code": "CB_IJ01", "message": "不正なJSON文字列です。"},
    {"code": "CB_IL02", "message": "謎のエラー"},
    {"code": "CB_TW02", "message": "2要素認証を有効にしているため、認証できません。REST APIでは2要素認証はサポートされていません。"},
    {"code": "CB_VA01", "message": "クエリ記法が間違っています。"},
    {"code": "GAIA_FU01", "message": "フィールド「XXXXX」の編集権限がありません。"},
    {"code": "GAIA_IL23",
     "message": "ゲストスペース内のアプリを操作する場合は、ゲストスペースのID を追加してください。"},
    {"code": "GAIA_IL26", "message": "指定したユーザー(code:XXXXXX)が見つかりません。"},
    {"code": "GAIA_IL28", "message": "指定した組織(code:XXXXXX)が見つかりません。"},
    {"code": "GAIA_IL42", "message": "レコードの絞り込み条件に指定したユーザー、グループ、または組織が存在しません。削除された可能性があります。"},
    {"code": "GAIA_IQ03", "message": "作業者フィールドのフィールドタイプには演算子=を使用できません。"},
    {"code": "GAIA_IQ07",
     "message": "レコードを読み込めません。テーブルに設定している場合、数値フィールドのフィールドタイプには、演算子=を使用できません。"},
    {"code": "GAIA_IQ11", "message": "指定されたフィールド(XXXX)が見つかりません。"},
    {"code": "GAIA_IR02",
     "message": "フィールド「xxxxx」に指定したクエリが正しくありません。指定したクエリは、関連レコード一覧フィールドでのみ使用できます。"},
    {"code": "GAIA_LO03",
     "message": "ルックアップの参照先から値をコピーできません。「コピー元のフィールド」に指定したフィールドの設定で「値の重複を禁止する」を選択しておく必要があります。"},
    {"code": "GAIA_LT01",
     "message": "データベースがロックされているため、操作に失敗しました。時間をおいて再度お試しください。"},
    {"code": "GAIA_DA02",
     "message": "データベースがロックされているため、操作に失敗しました。時間をおいて再度お試しください。"},
    {"code": "GAIA_NT01", "message": "作業者のみがステータスを変更できます"},
    {"code": "GAIA_NO01", "message": "このAPIトークンでは、指定したAPIを実行できません。"},
    {"code": "GAIA_TM12",
     "message": "作成できるカーソルの上限に達しているため、カーソルを作成できません。不要なカーソルを削除するか、しばらく経ってから再実行してください。"},
    {"code": "GAIA_UN03", "message": "レコードを再読み込みしてください。編集中に、ほかのユーザーがレコードを更新しました"},
]

SUCCESS_CODE = 200
API_KEY_AUTHENTICATION = 'api_key'
USERNAME_PASSWORD_AUTHENTICATION = 'username_password'


class Kintone:
  logger = logging.getLogger("airbyte")
  parallel_tasks_size = 100

  def __init__(
      self,
      domain: str = None,
      app_ids: list[str] = None,
      auth_type: dict[str, str] = None,
      query: str = None,
      **kwargs: Any,
  ) -> None:
    self.domain = domain
    self.app_ids = app_ids
    self.auth_option = auth_type.get('option', None)
    self.username = auth_type.get('username', None)
    self.password = auth_type.get('password', None)

    self.authentication_error = None
    self.session = requests.Session()

    # Change the connection pool size. Default value is not enough for parallel tasks
    adapter = request_adapters.HTTPAdapter(
        pool_connections=self.parallel_tasks_size, pool_maxsize=self.parallel_tasks_size)
    self.session.mount("https://", adapter)

  def authentication(self):
    # Get all apps of this account
    get_apps_url = f"{self.domain}/k/v1/apps.json"

    # Authentication request does not need retry handler
    app_list_res = self.session.get(
        url=get_apps_url,
        headers=self._get_standard_headers()
    )
    app_list = app_list_res.json().get('apps', [])
    if len(app_list) == 0:
      self.authentication_error = 'このアカウントでアプリがありません。'
      return

    filtered_app_list = [{"appId": obj["appId"], "spaceId": obj["spaceId"]}
                         for obj in app_list]
    for item in self.app_ids:
      matching_app = next(
          (app for app in filtered_app_list if app['appId'] == item), None)
      if matching_app is None:
        self.authentication_error = '存在していないアプリのアプリIDがあります。'
        break
      if matching_app['spaceId'] is None:
        # This app belongs to the current Organization
        continue
      # Check if this app is in Public Space
      get_space_detail_url = f"{self.domain}/k/v1/space.json"
      params = {"id": matching_app['spaceId']}

      space_detail_res = self.session.get(
          url=get_space_detail_url,
          params=params,
          headers=self._get_standard_headers()
      )
      if space_detail_res.status_code is not SUCCESS_CODE:
        self.authentication_error = 'ゲストスペース内のアプリがあります。'
        break

  @default_backoff_handler(max_tries=5, factor=5)
  def _make_request(
      self,
      http_method: str,
      url: str,
      headers: dict = None,
      body: dict = None,
      stream: bool = False,
      params: dict = None
  ) -> requests.models.Response:
    try:
      if http_method == "GET":
        resp = self.session.get(
            url, headers=headers, stream=stream, params=params)
      elif http_method == "POST":
        resp = self.session.post(url, headers=headers, data=body)
      resp.raise_for_status()
    except HTTPError as err:
      self.logger.warn(f"http error body: {err.response.text}")
      raise
    return resp

  def _get_standard_headers(self) -> Mapping[str, str]:
    return {
        "X-Cybozu-Authorization": self._get_authorization_key()
    }

  def _get_error_message(self, error_code: str) -> str:
    for error in KINTONE_ERROR:
      if error_code == error['code']:
        return error['message']
    return "不明なシステムエラーが発生しました。"

  def _get_authorization_key(self) -> str:
    if self.auth_option == USERNAME_PASSWORD_AUTHENTICATION:
      return encode_to_base64(f"{self.username}:{self.password}")
