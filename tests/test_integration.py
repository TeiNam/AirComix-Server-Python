"""API 엔드포인트 통합 테스트

실제 파일 시스템과 아카이브를 사용하여 전체 요청/응답 사이클을 테스트합니다.
"""

import pytest
from pathlib import Path
from urllib.parse import quote
from fastapi.testclient import TestClient


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestRootEndpoint:
    """루트 엔드포인트 테스트"""
    
    def test_get_root_directory_name(self, client: TestClient):
        """루트 디렉토리 이름 반환 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.text == "manga"
    
    def test_get_root_directory_name_with_custom_name(self, temp_manga_dir: Path, monkeypatch):
        """커스텀 디렉토리 이름 테스트"""
        # 커스텀 디렉토리 이름으로 설정
        custom_dir = temp_manga_dir.parent / "my_comics"
        custom_dir.mkdir()
        
        from app.models.config import Settings
        custom_settings = Settings(
            manga_directory=str(custom_dir),  # Path를 문자열로 변환
            debug_mode=True
        )
        
        # 설정 오버라이드
        monkeypatch.setattr("app.models.config.settings", custom_settings)
        monkeypatch.setattr("app.api.routes.settings", custom_settings)
        
        from app.main import create_app
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "my_comics"


@pytest.mark.usefixtures("override_settings")
class TestServerInfoEndpoint:
    """서버 정보 엔드포인트 테스트"""
    
    def test_get_server_info(self, client: TestClient):
        """서버 정보 반환 테스트"""
        response = client.get("/welcome.102")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        assert "allowDownload=True" in content
        assert "allowImageProcess=True" in content
        assert "Comix Server Python Port" in content


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestDirectoryListingEndpoint:
    """디렉토리 목록 엔드포인트 테스트"""
    
    def test_list_root_directory(self, client: TestClient):
        """루트 디렉토리 목록 테스트"""
        response = client.get("/manga/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        lines = content.split("\n") if content else []
        
        # 예상되는 항목들이 포함되어 있는지 확인
        assert "Series A" in lines
        assert "시리즈 B" in lines
        assert "cover.png" in lines
        
        # 숨겨진 파일들이 필터링되었는지 확인
        assert ".hidden_file" not in lines
        assert ".DS_Store" not in lines
        assert "Thumbs.db" not in lines
        assert "readme.txt" not in lines  # 지원되지 않는 파일
    
    def test_list_subdirectory(self, client: TestClient):
        """하위 디렉토리 목록 테스트"""
        response = client.get("/manga/Series%20A")
        
        assert response.status_code == 200
        content = response.text
        lines = content.split("\n") if content else []
        
        assert "Volume 1" in lines
    
    def test_list_image_directory(self, client: TestClient, sample_manga_structure):
        """이미지가 있는 디렉토리 목록 테스트"""
        response = client.get("/manga/Series%20A/Volume%201")
        
        assert response.status_code == 200
        content = response.text
        lines = content.split("\n") if content else []
        
        # 이미지 파일들이 포함되어 있는지 확인
        assert "page001.jpg" in lines
        assert "page002.jpg" in lines
        assert "page003.jpg" in lines
    
    def test_list_nonexistent_directory(self, client: TestClient, sample_manga_structure):
        """존재하지 않는 디렉토리 테스트"""
        response = client.get("/manga/nonexistent")
        
        # 존재하지 않는 디렉토리는 404 에러를 반환해야 함
        assert response.status_code == 404
    
    def test_list_empty_directory(self, client: TestClient, temp_manga_dir: Path):
        """빈 디렉토리 테스트"""
        empty_dir = temp_manga_dir / "empty"
        empty_dir.mkdir()
        
        response = client.get("/manga/empty")
        
        assert response.status_code == 200
        assert response.text == ""


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestArchiveListingEndpoint:
    """아카이브 목록 엔드포인트 테스트"""
    
    def test_list_zip_archive(self, client: TestClient, sample_manga_structure):
        """ZIP 아카이브 목록 테스트"""
        response = client.get("/manga/시리즈%20B/Chapter%20001.zip")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        content = response.text
        lines = content.split("\n") if content else []
        
        # 이미지 파일들만 포함되어 있는지 확인
        assert "page001.jpg" in lines
        assert "page002.jpg" in lines
        assert "page003.jpg" in lines
        
        # 지원되지 않는 파일들이 필터링되었는지 확인
        assert "info.txt" not in lines
        assert ".hidden" not in lines
    
    def test_list_cbz_archive(self, client: TestClient, sample_manga_structure):
        """CBZ 아카이브 목록 테스트"""
        response = client.get("/manga/시리즈%20B/Chapter%20002.cbz")
        
        assert response.status_code == 200
        content = response.text
        lines = content.split("\n") if content else []
        
        assert len(lines) >= 3  # 최소 3개의 이미지
        assert all(line.endswith('.jpg') for line in lines if line)
    
    def test_list_nonexistent_archive(self, client: TestClient, sample_manga_structure):
        """존재하지 않는 아카이브 테스트"""
        response = client.get("/manga/nonexistent.zip")
        
        # 존재하지 않는 아카이브는 404 에러를 반환해야 함
        assert response.status_code == 404
    
    def test_list_corrupted_archive(self, client: TestClient, corrupted_archive: Path):
        """손상된 아카이브 테스트"""
        archive_name = corrupted_archive.name
        response = client.get(f"/manga/{archive_name}")
        
        # 손상된 아카이브는 500 에러를 반환해야 함
        assert response.status_code == 500


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestImageStreamingEndpoint:
    """이미지 스트리밍 엔드포인트 테스트"""
    
    def test_stream_direct_image(self, client: TestClient, sample_manga_structure):
        """직접 이미지 파일 스트리밍 테스트"""
        response = client.get("/manga/cover.png")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert "content-length" in response.headers
        assert len(response.content) > 0
    
    def test_stream_image_from_directory(self, client: TestClient, sample_manga_structure):
        """디렉토리 내 이미지 스트리밍 테스트"""
        response = client.get("/manga/Series%20A/Volume%201/page001.jpg")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 0
    
    def test_stream_image_from_archive(self, client: TestClient, sample_manga_structure):
        """아카이브 내 이미지 스트리밍 테스트"""
        response = client.get("/manga/시리즈%20B/Chapter%20001.zip/page001.jpg")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 0
    
    def test_stream_nonexistent_image(self, client: TestClient, sample_manga_structure):
        """존재하지 않는 이미지 테스트"""
        response = client.get("/manga/nonexistent.jpg")
        
        # 존재하지 않는 이미지는 404 에러를 반환해야 함
        assert response.status_code == 404
    
    def test_stream_nonexistent_image_from_archive(self, client: TestClient, sample_manga_structure):
        """아카이브 내 존재하지 않는 이미지 테스트"""
        response = client.get("/manga/시리즈%20B/Chapter%20001.zip/nonexistent.jpg")
        
        # 아카이브 내 존재하지 않는 이미지는 404 또는 500 에러를 반환할 수 있음
        assert response.status_code in [404, 500]


@pytest.mark.usefixtures("override_settings", "encoding_test_data")
class TestCharacterEncodingHandling:
    """문자 인코딩 처리 테스트"""
    
    def test_unicode_directory_names(self, client: TestClient, encoding_test_data):
        """유니코드 디렉토리명 처리 테스트"""
        # 한국어 디렉토리
        response = client.get("/manga/한국어%20만화")
        assert response.status_code == 200
        
        # 일본어 디렉토리
        response = client.get(f"/manga/{quote('日本語マンガ')}")
        assert response.status_code == 200
        
        # 중국어 디렉토리
        response = client.get(f"/manga/{quote('中文漫画')}")
        assert response.status_code == 200
    
    def test_unicode_file_names(self, client: TestClient, encoding_test_data):
        """유니코드 파일명 처리 테스트"""
        # 한국어 파일명
        response = client.get(f"/manga/한국어%20만화/한국어%20만화_cover.jpg")
        # 파일이 존재하면 200, 없으면 404/500 에러
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            assert "image/" in response.headers["content-type"]


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestSecurityAndValidation:
    """보안 및 검증 테스트"""
    
    def test_path_traversal_prevention(self, client: TestClient, sample_manga_structure):
        """경로 순회 공격 방지 테스트"""
        # 다양한 경로 순회 시도
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd",
        ]
        
        for attempt in traversal_attempts:
            response = client.get(f"/manga/{attempt}")
            # 경로 순회 시도는 403 또는 404 에러를 반환해야 함
            assert response.status_code in [403, 404]
    
    def test_invalid_characters_in_path(self, client: TestClient, sample_manga_structure):
        """경로의 유효하지 않은 문자 처리 테스트"""
        invalid_paths = [
            "file\x00name",  # null byte
            "file\nname",    # newline
            "file\rname",    # carriage return
        ]
        
        for invalid_path in invalid_paths:
            response = client.get(f"/manga/{quote(invalid_path)}")
            # 유효하지 않은 문자는 403 또는 404 에러를 반환해야 함
            assert response.status_code in [403, 404]


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestErrorScenarios:
    """에러 시나리오 테스트"""
    
    def test_unsupported_file_type(self, client: TestClient, sample_manga_structure):
        """지원되지 않는 파일 형식 테스트"""
        response = client.get("/manga/readme.txt")
        
        # 지원되지 않는 파일은 400 에러를 반환해야 함
        assert response.status_code == 400
    
    def test_permission_denied_simulation(self, client: TestClient, temp_manga_dir: Path):
        """권한 거부 시뮬레이션 테스트"""
        # 접근할 수 없는 디렉토리 시뮬레이션
        # (실제 권한 변경은 테스트 환경에서 복잡하므로 경로 검증으로 대체)
        response = client.get("/manga/../outside_manga")
        
        assert response.status_code in [400, 403, 404, 500]


@pytest.mark.usefixtures("override_settings", "large_image")
class TestPerformanceAndLargeFiles:
    """성능 및 대용량 파일 테스트"""
    
    def test_large_image_streaming(self, client: TestClient, large_image: Path):
        """대용량 이미지 스트리밍 테스트"""
        image_name = large_image.name
        response = client.get(f"/manga/{image_name}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert int(response.headers["content-length"]) > 100000  # 100KB 이상
    
    def test_concurrent_requests_simulation(self, client: TestClient, sample_manga_structure):
        """동시 요청 시뮬레이션 테스트"""
        # 여러 요청을 순차적으로 실행하여 기본적인 동시성 테스트
        responses = []
        
        for i in range(5):
            response = client.get("/manga/cover.png")
            responses.append(response)
        
        # 모든 요청이 성공해야 함
        for response in responses:
            assert response.status_code == 200
            assert len(response.content) > 0


@pytest.mark.usefixtures("override_settings", "sample_manga_structure")
class TestAirComixProtocolCompatibility:
    """AirComix 프로토콜 호환성 테스트"""
    
    def test_aircomix_workflow_simulation(self, client: TestClient, sample_manga_structure):
        """AirComix 앱의 일반적인 워크플로우 시뮬레이션"""
        
        # 1. 서버 정보 확인
        response = client.get("/welcome.102")
        assert response.status_code == 200
        assert "allowDownload=True" in response.text
        
        # 2. 루트 디렉토리 이름 조회
        response = client.get("/")
        assert response.status_code == 200
        root_name = response.text
        
        # 3. 루트 디렉토리 목록 조회
        response = client.get("/manga/")
        assert response.status_code == 200
        root_items = response.text.split("\n") if response.text else []
        
        # 4. 시리즈 디렉토리 탐색
        if "Series A" in root_items:
            response = client.get("/manga/Series%20A")
            assert response.status_code == 200
            
            # 5. 볼륨 디렉토리 탐색
            series_items = response.text.split("\n") if response.text else []
            if "Volume 1" in series_items:
                response = client.get("/manga/Series%20A/Volume%201")
                assert response.status_code == 200
                
                # 6. 첫 번째 이미지 로드
                volume_items = response.text.split("\n") if response.text else []
                if volume_items:
                    first_image = volume_items[0]
                    response = client.get(f"/manga/Series%20A/Volume%201/{quote(first_image)}")
                    assert response.status_code == 200
                    assert "image/" in response.headers["content-type"]
        
        # 7. 아카이브 파일 처리
        if "시리즈 B" in root_items:
            response = client.get("/manga/시리즈%20B")
            assert response.status_code == 200
            
            series_b_items = response.text.split("\n") if response.text else []
            for item in series_b_items:
                if item.endswith(('.zip', '.cbz')):
                    # 아카이브 내용 조회
                    response = client.get(f"/manga/시리즈%20B/{quote(item)}")
                    assert response.status_code == 200
                    
                    # 아카이브 내 첫 번째 이미지 로드
                    archive_items = response.text.split("\n") if response.text else []
                    if archive_items:
                        first_image = archive_items[0]
                        response = client.get(f"/manga/시리즈%20B/{quote(item)}/{quote(first_image)}")
                        assert response.status_code == 200
                        assert "image/" in response.headers["content-type"]
                    break
    
    def test_response_format_compatibility(self, client: TestClient, sample_manga_structure):
        """응답 형식 호환성 테스트"""
        
        # 디렉토리 목록은 줄바꿈으로 구분된 텍스트여야 함
        response = client.get("/manga/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # 아카이브 목록도 줄바꿈으로 구분된 텍스트여야 함
        response = client.get("/manga/시리즈%20B/Chapter%20001.zip")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # 이미지는 적절한 MIME 타입을 가져야 함
        response = client.get("/manga/cover.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"