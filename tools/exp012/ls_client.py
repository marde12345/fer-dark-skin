"""EXP-012: build a Label Studio SDK client from either a legacy API token or a
Personal Access Token (PAT).

Label Studio 1.23 PATs are refresh tokens: they are exchanged at
/api/token/refresh for a short-lived access token sent as "Bearer". The legacy
SDK Client sends "Token <key>" and does not pass extra headers to the Project
objects it creates, but every object shares the client's HTTP session, so for a
PAT the session itself sets the Bearer header on each request. The key is never
printed or written anywhere.
"""

from __future__ import annotations

import requests
from label_studio_sdk import Client


class _BearerSession(requests.Session):
    def __init__(self, access_token: str):
        super().__init__()
        self._auth = f"Bearer {access_token}"

    def request(self, method, url, *args, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers["Authorization"] = self._auth
        return super().request(method, url, *args, headers=headers, **kwargs)


def make_client(url: str, api_key: str) -> Client:
    refresh = requests.post(f"{url}/api/token/refresh", json={"refresh": api_key}, timeout=30)
    if refresh.ok and "access" in refresh.json():
        return Client(url=url, api_key=api_key, session=_BearerSession(refresh.json()["access"]))
    return Client(url=url, api_key=api_key)  # legacy token
