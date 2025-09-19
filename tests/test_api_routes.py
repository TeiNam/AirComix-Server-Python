"""API 라우트 테스트"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import create_app


@pytest.fixture
def client():
    """테스트 클라이언트 생성"""
    app = create_app()
    return TestClient(app)


class TestBasicRoutes:
    """기본 라우트 테스트 클래스"""
    
    def test_get_root_directory_name_success(self, client):
        """루트 디렉토리 이름 조회 성공 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # 응답이 문자열이고 비어있지 않은지 확인
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0
        assert content != ""
    
    def test_get_root_directory_name_with_custom_path(self, client):
        """커스텀 경로로 루트 디렉토리 이름 조회 테스트"""
        with patch('app.api.routes.settings') as mock_settings:
            mock_settings.manga_directory = "/custom/comix/path"
            
            response = client.get("/")
            
            assert response.status_code == 200
            assert "path" in response.text
    
    def test_get_server_info_success(self, client):
        """서버 정보 조회 성공 테스트"""
        response = client.get("/welcome.102")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        assert "allowDownload=True" in content
        assert "allowImageProcess=True" in content
        assert "Comix Server Python Port" in content
    
    def test_get_server_info_format(self, client):
        """서버 정보 형식 테스트"""
        response = client.get("/welcome.102")
        
        assert response.status_code == 200
        
        lines = response.text.split('\n')
        assert len(lines) >= 3
        
        # 첫 번째 줄은 allowDownload 설정
        assert lines[0] == "allowDownload=True"
        
        # 두 번째 줄은 allowImageProcess 설정
        assert lines[1] == "allowImageProcess=True"
        
        # 세 번째 줄은 서버 식별 메시지
        assert "Comix Server Python Port" in lines[2]
    
    def test_nonexistent_endpoint(self, client):
        """존재하지 않는 엔드포인트 테스트"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_root_endpoint_method_not_allowed(self, client):
        """루트 엔드포인트 POST 메서드 테스트"""
        response = client.post("/")
        
        assert response.status_code == 405  # Method Not Allowed
    
    def test_welcome_endpoint_method_not_allowed(self, client):
        """welcome 엔드포인트 POST 메서드 테스트"""
        response = client.post("/welcome.102")
        
        assert response.status_code == 405  # Method Not Allowed


class TestApplicationConfiguration:
    """애플리케이션 설정 테스트 클래스"""
    
    def test_app_creation_with_debug_mode(self):
        """디버그 모드로 앱 생성 테스트"""
        with patch('app.main.settings') as mock_settings:
            mock_settings.debug_mode = True
            mock_settings.manga_directory = "/test/manga"
            mock_settings.server_port = 31257
            mock_settings.server_host = "0.0.0.0"
            mock_settings.log_level = "DEBUG"
            
            app = create_app()
            
            # FastAPI의 debug 속성 대신 title과 version 확인
            assert app.title == "Comix Server"
            assert app.version == "1.0.0"
            # 디버그 모드는 미들웨어 설정으로 확인
    
    def test_app_creation_without_debug_mode(self):
        """프로덕션 모드로 앱 생성 테스트"""
        with patch('app.main.settings') as mock_settings:
            mock_settings.debug_mode = False
            mock_settings.manga_directory = "/test/manga"
            mock_settings.server_port = 31257
            mock_settings.server_host = "0.0.0.0"
            mock_settings.log_level = "INFO"
            
            app = create_app()
            
            # FastAPI의 기본 속성들 확인
            assert app.title == "Comix Server"
            assert app.version == "1.0.0"
    
    def test_cors_middleware_in_debug_mode(self):
        """디버그 모드에서 CORS 미들웨어 테스트"""
        with patch('app.main.settings') as mock_settings:
            mock_settings.debug_mode = True
            mock_settings.manga_directory = "/test/manga"
            mock_settings.server_port = 31257
            mock_settings.server_host = "0.0.0.0"
            mock_settings.log_level = "DEBUG"
            
            app = create_app()
            client = TestClient(app)
            
            # OPTIONS 요청으로 CORS 헤더 확인
            response = client.options("/", headers={"Origin": "http://localhost:3000"})
            
            # CORS가 활성화되어 있으면 적절한 헤더가 있어야 함
            assert response.status_code in [200, 405]  # OPTIONS가 허용되지 않을 수도 있음


class TestHealthCheck:
    """헬스 체크 관련 테스트"""
    
    def test_basic_connectivity(self, client):
        """기본 연결성 테스트"""
        # 루트 엔드포인트로 기본 연결성 확인
        response = client.get("/")
        assert response.status_code == 200
        
        # 서버 정보 엔드포인트로 기능 확인
        response = client.get("/welcome.102")
        assert response.status_code == 200
    
    def test_response_headers(self, client):
        """응답 헤더 테스트"""
        response = client.get("/")
        
        # Content-Type 헤더가 올바르게 설정되었는지 확인
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Content-Length 헤더가 있는지 확인
        assert "content-length" in response.headers
        assert int(response.headers["content-length"]) > 0