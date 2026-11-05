"""HTTP / Socket.IO 存取防護（WSGI middleware，涵蓋 Flask 路由與 /socket.io/）。

背景：本系統可透過 POST /relay/<id>/<action>、/relay/control 與 Socket.IO 事件
直接切換實體電表繼電器（斷電/供電），原本完全沒有驗證，且 Socket.IO CORS 為 "*"。
同網段任何人，或任何「你在同網段瀏覽的惡意網頁」（CSRF / 跨站 WebSocket 劫持），都能斷電。

防護（不需修改前端）：
1. 跨站阻擋（一律開啟）：
   - 寫入請求（POST/PUT/PATCH/DELETE）與所有 /socket.io/ 請求，若帶 Origin 且不是本站
     （或不在 POWER_METER_ALLOWED_ORIGINS 清單）→ 403；Origin 為 "null" 也拒絕。
   - Sec-Fetch-Site: cross-site → 403。
   - 瀏覽器對跨站 POST 與 WebSocket 一定會送 Origin，因此能完整擋下 CSRF；
     curl / Python 腳本等非瀏覽器客戶端不送 Origin，不受影響。
2. 存取密碼（選用，強烈建議）：設定環境變數 POWER_METER_PASSWORD 後，
   所有頁面、API 與 Socket.IO 皆需 HTTP Basic 驗證（帳號任意，比對密碼）。
"""
from __future__ import annotations

import base64
import binascii
import hmac
import logging
import os
from typing import Callable, Iterable
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SOCKETIO_PREFIX = "/socket.io"


def _allowed_origins_from_env() -> set[str]:
    raw = os.environ.get("POWER_METER_ALLOWED_ORIGINS", "")
    return {o.strip().rstrip("/").lower() for o in raw.split(",") if o.strip()}


class SecurityMiddleware:
    def __init__(self, wsgi_app: Callable, password: str | None = None,
                 allowed_origins: Iterable[str] | None = None):
        self.wsgi_app = wsgi_app
        self.password = password or None
        self.allowed_origins = {o.rstrip("/").lower() for o in (allowed_origins or [])}

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _reply(start_response, status: str, body: str, extra_headers=None):
        data = body.encode("utf-8")
        headers = [("Content-Type", "application/json; charset=utf-8"),
                   ("Content-Length", str(len(data))),
                   ("Cache-Control", "no-store")]
        headers += list(extra_headers or [])
        start_response(status, headers)
        return [data]

    def _password_ok(self, environ) -> bool:
        header = environ.get("HTTP_AUTHORIZATION", "")
        if not header.lower().startswith("basic "):
            return False
        try:
            decoded = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return False
        _, _, supplied = decoded.partition(":")
        return hmac.compare_digest(supplied.encode("utf-8"), self.password.encode("utf-8"))

    def _origin_ok(self, environ) -> bool:
        if environ.get("HTTP_SEC_FETCH_SITE", "").lower() == "cross-site":
            return False
        origin = environ.get("HTTP_ORIGIN")
        if origin is None:
            return True                      # 非瀏覽器客戶端或同源導覽
        origin = origin.strip()
        if origin.lower() == "null":
            return False
        if origin.rstrip("/").lower() in self.allowed_origins:
            return True
        try:
            netloc = urlsplit(origin).netloc.lower()
        except ValueError:
            return False
        host = (environ.get("HTTP_HOST") or "").lower()
        return bool(netloc) and netloc == host

    # -- WSGI ----------------------------------------------------------------
    def __call__(self, environ, start_response):
        if self.password and not self._password_ok(environ):
            return self._reply(start_response, "401 Unauthorized",
                               '{"success": false, "error": "authentication required"}',
                               [("WWW-Authenticate", 'Basic realm="Power Meter", charset="UTF-8"')])

        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "")
        if (method in UNSAFE_METHODS or path.startswith(SOCKETIO_PREFIX)) and not self._origin_ok(environ):
            log.warning("blocked cross-origin %s %s from Origin=%r", method, path, environ.get("HTTP_ORIGIN"))
            return self._reply(start_response, "403 Forbidden",
                               '{"success": false, "error": "cross-origin request rejected"}')
        return self.wsgi_app(environ, start_response)


def install_security(app) -> None:
    """在 SocketIO(app) 之後呼叫，讓 middleware 包住 Socket.IO 與 Flask。"""
    password = os.environ.get("POWER_METER_PASSWORD", "").strip() or None
    app.wsgi_app = SecurityMiddleware(app.wsgi_app, password, _allowed_origins_from_env())
    if not password:
        log.warning("POWER_METER_PASSWORD 未設定：同網段任何人都能操作繼電器（斷電/供電）。"
                    "已啟用跨站阻擋，但仍強烈建議設定密碼。")


def socketio_allowed_origins():
    """Socket.IO 的 cors_allowed_origins。

    - 未設定 POWER_METER_ALLOWED_ORIGINS：None → engine.io 只接受同源（雙重防護）。
    - 有設定：engine.io 的清單模式會連同源都拒絕（它不知道本機 host），因此交給
      SecurityMiddleware 判斷（同源 + 清單），engine.io 端放行 "*"。
    """
    return "*" if _allowed_origins_from_env() else None
