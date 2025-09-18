"""예외 핸들러 테스트"""

import pytest
from unittest.mock import patch, Mock
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.exceptions import ComixServerException, FileNotFoundError
from app.exception_handlers import (
    comix_server_exception_handler,
    http_exception_handler,
    general_exception_handler,
    register_exception_handlers
)


@pytest.fixture
def mock_request():
    """모의 요청 객체"""
    request = Mock(spec=Request)
    request.method = "GET"
    request.url.path = "/test/path"
    request.url = Mock()
    request.url.__str__ = Mock(return_value="http://test.com/test/path")
    return request


class TestComixServerExceptionHandler:
    """ComixServerException 핸들러 테스트"""
    
    @pytest.mark.asyncio
    async def test_debug_mode_response(self, mock_request):
        """디버그 모드에서의 응답 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = True
            
            exc = FileNotFoundError("/test/file")
            response = await comix_server_exception_handler(mock_request, exc)
            
            assert response.status_code == 404
            # JSON 응답인지 확인
            content = response.body.decode()
            assert "error" in content
            assert "detail" in content
    
    @pytest.mark.asyncio
    async def test_production_mode_response(self, mock_request):
        """프로덕션 모드에서의 응답 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = False
            
            exc = FileNotFoundError("/test/file")
            response = await comix_server_exception_handler(mock_request, exc)
            
            assert response.status_code == 404
            # 텍스트 응답인지 확인
            content = response.body.decode()
            assert "파일 또는 디렉토리를 찾을 수 없습니다" in content


class TestHttpExceptionHandler:
    """HTTPException 핸들러 테스트"""
    
    @pytest.mark.asyncio
    async def test_http_exception_debug_mode(self, mock_request):
        """디버그 모드에서의 HTTPException 처리 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = True
            
            exc = HTTPException(status_code=400, detail="Bad Request")
            response = await http_exception_handler(mock_request, exc)
            
            assert response.status_code == 400
            content = response.body.decode()
            assert "Bad Request" in content
    
    @pytest.mark.asyncio
    async def test_http_exception_production_mode(self, mock_request):
        """프로덕션 모드에서의 HTTPException 처리 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = False
            
            exc = HTTPException(status_code=400, detail="Bad Request")
            response = await http_exception_handler(mock_request, exc)
            
            assert response.status_code == 400
            content = response.body.decode()
            assert "Bad Request" in content


class TestGeneralExceptionHandler:
    """일반 예외 핸들러 테스트"""
    
    @pytest.mark.asyncio
    async def test_general_exception_debug_mode(self, mock_request):
        """디버그 모드에서의 일반 예외 처리 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = True
            
            exc = ValueError("테스트 오류")
            response = await general_exception_handler(mock_request, exc)
            
            assert response.status_code == 500
            content = response.body.decode()
            assert "테스트 오류" in content
    
    @pytest.mark.asyncio
    async def test_general_exception_production_mode(self, mock_request):
        """프로덕션 모드에서의 일반 예외 처리 테스트"""
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = False
            
            exc = ValueError("테스트 오류")
            response = await general_exception_handler(mock_request, exc)
            
            assert response.status_code == 500
            content = response.body.decode()
            assert "서버 내부 오류가 발생했습니다" in content


class TestExceptionHandlerRegistration:
    """예외 핸들러 등록 테스트"""
    
    def test_register_exception_handlers(self):
        """예외 핸들러 등록 테스트"""
        app = FastAPI()
        
        # 핸들러 등록 전 기본 핸들러 개수 확인
        initial_handlers = len(app.exception_handlers)
        
        # 핸들러 등록
        register_exception_handlers(app)
        
        # 핸들러가 등록되었는지 확인
        assert len(app.exception_handlers) > 0
        assert ComixServerException in app.exception_handlers
        assert HTTPException in app.exception_handlers
        assert Exception in app.exception_handlers


class TestIntegratedExceptionHandling:
    """통합 예외 처리 테스트"""
    
    def test_custom_exception_in_fastapi_app(self):
        """FastAPI 앱에서 커스텀 예외 처리 테스트"""
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/test-error")
        async def test_error():
            raise FileNotFoundError("/test/file")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = False
            
            response = client.get("/test-error")
            assert response.status_code == 404
            assert "파일 또는 디렉토리를 찾을 수 없습니다" in response.text
    
    def test_general_exception_in_fastapi_app(self):
        """FastAPI 앱에서 일반 예외 처리 테스트"""
        app = FastAPI()
        register_exception_handlers(app)
        
        @app.get("/test-general-error")
        async def test_general_error():
            raise ValueError("예상하지 못한 오류")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        with patch('app.models.config.settings') as mock_settings:
            mock_settings.debug_mode = False
            
            response = client.get("/test-general-error")
            assert response.status_code == 500
            assert "서버 내부 오류가 발생했습니다" in response.text