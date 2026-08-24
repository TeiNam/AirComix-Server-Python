"""인증 미들웨어 테스트

패스워드 비교, 인증 제외 경로, 연속 실패 잠금 동작을 고정한다.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.auth import (
    LOCKOUT_SECONDS,
    MAX_FAILED_ATTEMPTS,
    MAX_TRACKED_CLIENTS,
    BasicAuthMiddleware,
    _passwords_match,
)


@pytest.fixture
def middleware():
    """미들웨어 인스턴스 (ASGI 앱 없이 내부 로직만 검증)"""
    return BasicAuthMiddleware(app=None)


def test_passwords_match_handles_non_ascii():
    """한글 패스워드도 예외 없이 비교한다

    secrets.compare_digest 는 non-ASCII 문자열을 거부하므로(TypeError)
    bytes 로 비교해야 한다.
    """
    assert _passwords_match("한글비밀번호", "한글비밀번호") is True
    assert _passwords_match("한글비밀번호", "다른비밀번호") is False
    assert _passwords_match("plain", "plain") is True
    assert _passwords_match("plain", "other") is False


def test_default_exclude_paths(middleware):
    """앱 초기 연결과 헬스체크에 필요한 경로만 인증에서 제외한다"""
    assert set(middleware.exclude_paths) == {"/", "/welcome.102", "/health"}

    # 만화 목록은 루트까지 인증 대상이다
    assert "/comix" not in middleware.exclude_paths
    assert "/comix/" not in middleware.exclude_paths


def test_lockout_after_consecutive_failures(middleware):
    """연속 실패가 상한에 도달하면 잠긴다"""
    client_ip = "192.0.2.10"

    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        middleware._record_failure(client_ip)
        assert middleware._lockout_remaining(client_ip) == 0

    middleware._record_failure(client_ip)

    remaining = middleware._lockout_remaining(client_ip)
    assert 0 < remaining <= LOCKOUT_SECONDS + 1


def test_success_clears_failures(middleware):
    """인증에 성공하면 실패 카운터를 지운다"""
    client_ip = "192.0.2.11"

    for _ in range(MAX_FAILED_ATTEMPTS):
        middleware._record_failure(client_ip)

    assert middleware._lockout_remaining(client_ip) > 0

    middleware._clear_failures(client_ip)

    assert middleware._lockout_remaining(client_ip) == 0


def test_tracked_clients_are_bounded(middleware):
    """실패 기록이 무한히 늘어나지 않는다"""
    for index in range(MAX_TRACKED_CLIENTS + 200):
        middleware._record_failure(f"10.{index // 65536}.{index // 256 % 256}.{index % 256}")

    assert len(middleware._failed_attempts) <= MAX_TRACKED_CLIENTS


def test_missing_credentials_do_not_count_as_failure(monkeypatch):
    """자격증명 없는 최초 요청은 실패로 세지 않는다

    AirComix 앱은 먼저 인증 없이 요청하고 401 을 받은 뒤 재시도한다.
    이 요청을 실패로 세면 정상 클라이언트가 잠긴다.
    """
    from app.middleware import auth as auth_module

    monkeypatch.setattr(auth_module.settings, "enable_auth", True)
    monkeypatch.setattr(auth_module.settings, "auth_password", "secret123")

    app = FastAPI()
    app.add_middleware(BasicAuthMiddleware)

    @app.get("/comix/{path:path}")
    async def listing(path: str):
        return "ok"

    client = TestClient(app)

    for _ in range(MAX_FAILED_ATTEMPTS + 3):
        response = client.get("/comix/")
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == 'Basic realm="AirComix"'

    # 잠기지 않았으므로 올바른 패스워드로 즉시 통과한다
    assert client.get("/comix/", auth=("any", "secret123")).status_code == 200
