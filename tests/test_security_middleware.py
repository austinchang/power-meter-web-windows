"""backend.security.SecurityMiddleware 回歸測試（只需 Flask，不需硬體）。

執行：pip install pytest flask && python -m pytest -q tests/test_security_middleware.py
"""
import base64
import importlib.util
import sys
from pathlib import Path

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pm_security", ROOT / "backend" / "security.py")
security = importlib.util.module_from_spec(spec)
sys.modules["pm_security"] = security
spec.loader.exec_module(security)


def make_client(password=None, allowed=None):
    app = Flask(__name__)
    calls = []

    @app.route("/relay/<int:meter_id>/<action>", methods=["POST"])
    def relay(meter_id, action):
        calls.append((meter_id, action))
        return {"success": True}

    @app.route("/socket.io/", methods=["GET", "POST"])
    def sio():
        return "ok"

    @app.route("/")
    def index():
        return "home"

    app.wsgi_app = security.SecurityMiddleware(app.wsgi_app, password, allowed)
    return app.test_client(), calls


def basic(pw):
    return {"Authorization": "Basic " + base64.b64encode(f"u:{pw}".encode()).decode()}


def test_cross_site_relay_post_blocked():
    c, calls = make_client()
    r = c.post("/relay/3/off", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and calls == []
    r = c.post("/relay/3/off", headers={"Origin": "null"})
    assert r.status_code == 403 and calls == []
    r = c.post("/relay/3/off", headers={"Sec-Fetch-Site": "cross-site"})
    assert r.status_code == 403 and calls == []


def test_same_origin_and_non_browser_allowed():
    c, calls = make_client()
    assert c.post("/relay/1/on", headers={"Origin": "http://localhost"}).status_code == 200
    assert c.post("/relay/2/on").status_code == 200           # curl / script: no Origin
    assert calls == [(1, "on"), (2, "on")]


def test_cross_site_websocket_handshake_blocked():
    c, _ = make_client()
    assert c.get("/socket.io/", headers={"Origin": "https://evil.example"}).status_code == 403
    assert c.get("/socket.io/", headers={"Origin": "http://localhost"}).status_code == 200


def test_allowlisted_origin():
    c, calls = make_client(allowed=["http://scada.lan:8080"])
    assert c.post("/relay/1/off", headers={"Origin": "http://scada.lan:8080/"}).status_code == 200
    assert calls == [(1, "off")]


def test_password_required_everywhere():
    c, calls = make_client(password="pw-123456")
    assert c.get("/").status_code == 401
    assert c.post("/relay/1/off").status_code == 401
    assert c.get("/socket.io/").status_code == 401
    assert c.post("/relay/1/off", headers=basic("wrong")).status_code == 401
    assert c.post("/relay/1/off", headers=basic("pw-123456")).status_code == 200
    assert calls == [(1, "off")]
    assert c.get("/", headers={"Authorization": "Basic !!!"}).status_code == 401
