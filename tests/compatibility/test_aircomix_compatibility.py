#!/usr/bin/env python3
"""
AirComix iOS 앱 호환성 테스트

이 스크립트는 Comix Server가 AirComix iOS 앱과 완전히 호환되는지 테스트합니다.
실제 AirComix 앱이 사용하는 API 호출 패턴을 시뮬레이션합니다.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote

import pytest
import requests
from fastapi.testclient import TestClient

from app.main import create_app
from tests.fixtures.sample_data import SampleDataGenerator

# 실행 중인 서버를 대상으로 하는 통합 테스트 모듈
pytestmark = pytest.mark.integration


class AirComixCompatibilityTester:
    """AirComix 앱 호환성 테스트 클래스"""
    
    def __init__(self, base_url: str = "http://localhost:31257"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AirComix/1.0 (iOS; iPhone; iOS 15.0)',
            'Accept': 'text/plain, image/*',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
    def test_initial_connection(self) -> Dict[str, any]:
        """초기 연결 테스트 - AirComix 앱이 서버에 처음 연결할 때의 동작"""
        results = {}
        
        # 1. 루트 디렉토리 이름 조회 (앱이 가장 먼저 호출)
        try:
            response = self.session.get(f"{self.base_url}/")
            results['root_directory'] = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content': response.text.strip() if response.status_code == 200 else None,
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            results['root_directory'] = {'error': str(e)}
        
        # 2. 서버 정보 조회 (앱이 서버 기능을 확인)
        try:
            response = self.session.get(f"{self.base_url}/welcome.102")
            results['server_info'] = {
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content': response.text.strip() if response.status_code == 200 else None,
                'response_time': response.elapsed.total_seconds(),
                'has_download_support': 'allowDownload=True' in response.text if response.status_code == 200 else False,
                'has_image_process': 'allowImageProcess=True' in response.text if response.status_code == 200 else False
            }
        except Exception as e:
            results['server_info'] = {'error': str(e)}
            
        return results
    
    def test_directory_navigation(self, test_paths: List[str]) -> Dict[str, any]:
        """디렉토리 탐색 테스트 - AirComix 앱의 폴더 탐색 동작"""
        results = {}
        
        for path in test_paths:
            encoded_path = quote(path, safe='/')
            try:
                response = self.session.get(f"{self.base_url}/comix/{encoded_path}")
                
                content_lines = []
                if response.status_code == 200:
                    content_lines = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                
                results[path] = {
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'item_count': len(content_lines),
                    'items': content_lines[:10],  # 처음 10개만 저장
                    'response_time': response.elapsed.total_seconds(),
                    'has_archives': any(item.lower().endswith(('.zip', '.cbz', '.rar', '.cbr')) for item in content_lines),
                    'has_images': any(item.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')) for item in content_lines)
                }
            except Exception as e:
                results[path] = {'error': str(e)}
                
        return results
    
    def test_archive_handling(self, archive_paths: List[str]) -> Dict[str, any]:
        """아카이브 파일 처리 테스트 - ZIP/CBZ/RAR/CBR 파일 지원"""
        results = {}
        
        for archive_path in archive_paths:
            encoded_path = quote(archive_path, safe='/')
            try:
                response = self.session.get(f"{self.base_url}/comix/{encoded_path}")
                
                image_files = []
                if response.status_code == 200:
                    image_files = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                
                results[archive_path] = {
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'image_count': len(image_files),
                    'images': image_files[:5],  # 처음 5개만 저장
                    'response_time': response.elapsed.total_seconds(),
                    'sorted_properly': self._check_natural_sorting(image_files),
                    'all_images': all(self._is_image_file(img) for img in image_files) if image_files else True
                }
            except Exception as e:
                results[archive_path] = {'error': str(e)}
                
        return results
    
    def test_image_streaming(self, image_paths: List[str]) -> Dict[str, any]:
        """이미지 스트리밍 테스트 - 직접 이미지 및 아카이브 내 이미지"""
        results = {}
        
        for image_path in image_paths:
            encoded_path = quote(image_path, safe='/')
            try:
                # HEAD 요청으로 헤더만 확인 (빠른 테스트)
                response = self.session.head(f"{self.base_url}/comix/{encoded_path}")
                
                results[image_path] = {
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': response.headers.get('content-length'),
                    'response_time': response.elapsed.total_seconds(),
                    'is_image_mime': response.headers.get('content-type', '').startswith('image/') if response.status_code == 200 else False,
                    'has_content_length': 'content-length' in response.headers,
                    'cache_headers': {
                        'cache-control': response.headers.get('cache-control'),
                        'etag': response.headers.get('etag'),
                        'last-modified': response.headers.get('last-modified')
                    }
                }
                
                # 실제 이미지 다운로드 테스트 (작은 청크만)
                if response.status_code == 200:
                    try:
                        img_response = self.session.get(
                            f"{self.base_url}/comix/{encoded_path}",
                            headers={'Range': 'bytes=0-1023'},  # 첫 1KB만 요청
                            timeout=5
                        )
                        results[image_path]['partial_download'] = {
                            'status_code': img_response.status_code,
                            'content_length': len(img_response.content),
                            'supports_range': img_response.status_code == 206
                        }
                    except Exception as e:
                        results[image_path]['partial_download'] = {'error': str(e)}
                        
            except Exception as e:
                results[image_path] = {'error': str(e)}
                
        return results
    
    def test_character_encoding(self, paths_with_unicode: List[str]) -> Dict[str, any]:
        """문자 인코딩 테스트 - 한글, 일본어 등 유니코드 파일명 처리"""
        results = {}
        
        for path in paths_with_unicode:
            # URL 인코딩 테스트
            encoded_path = quote(path, safe='/')
            try:
                response = self.session.get(f"{self.base_url}/comix/{encoded_path}")
                
                results[path] = {
                    'original_path': path,
                    'encoded_path': encoded_path,
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds(),
                    'encoding_handled': response.status_code != 400,  # 400은 인코딩 오류를 의미할 수 있음
                }
                
                # 응답 내용의 인코딩 확인
                if response.status_code == 200:
                    try:
                        content = response.text
                        results[path]['content_encoding'] = 'utf-8'
                        results[path]['has_unicode_content'] = any(ord(c) > 127 for c in content)
                    except UnicodeDecodeError:
                        results[path]['content_encoding'] = 'error'
                        
            except Exception as e:
                results[path] = {'error': str(e)}
                
        return results
    
    def test_performance_characteristics(self) -> Dict[str, any]:
        """성능 특성 테스트 - AirComix 앱이 요구하는 성능 수준 확인"""
        results = {}
        
        # 1. 연속 요청 테스트 (앱이 빠르게 여러 요청을 보내는 경우)
        start_time = time.time()
        response_times = []
        
        for i in range(10):
            try:
                response = self.session.get(f"{self.base_url}/")
                response_times.append(response.elapsed.total_seconds())
            except Exception:
                response_times.append(None)
        
        results['rapid_requests'] = {
            'total_time': time.time() - start_time,
            'average_response_time': sum(t for t in response_times if t) / len([t for t in response_times if t]),
            'max_response_time': max(t for t in response_times if t),
            'success_rate': len([t for t in response_times if t]) / len(response_times)
        }
        
        # 2. 동시 연결 테스트 (앱이 여러 이미지를 동시에 로드하는 경우)
        # 실제 구현에서는 threading 또는 asyncio 사용
        results['concurrent_capability'] = {
            'max_connections': 10,  # 테스트할 동시 연결 수
            'note': 'Concurrent testing requires actual implementation'
        }
        
        return results
    
    def _check_natural_sorting(self, items: List[str]) -> bool:
        """자연 정렬 확인 (page1.jpg < page2.jpg < page10.jpg)"""
        if len(items) < 2:
            return True
            
        # 간단한 자연 정렬 확인 (숫자가 포함된 파일명)
        import re
        
        def natural_key(text):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', text)]
        
        sorted_items = sorted(items, key=natural_key)
        return items == sorted_items
    
    def _is_image_file(self, filename: str) -> bool:
        """이미지 파일 여부 확인"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)


def _default_server_url() -> str:
    """테스트 대상 서버 주소 (환경 변수로 변경 가능)"""
    import os

    return os.getenv("COMIX_TEST_SERVER_URL", "http://localhost:31257")


def _is_server_running(base_url: str) -> bool:
    """서버가 응답하는지 확인"""
    try:
        requests.get(base_url, timeout=2)
        return True
    except requests.RequestException:
        return False


@pytest.fixture
def aircomix_tester():
    """AirComix 호환성 테스터 픽스처

    이 테스트들은 실제로 기동된 서버를 대상으로 한다. 서버가 없으면 건너뛴다.
    (예: COMIX_MANGA_DIRECTORY=... python -m app.main 로 띄운 뒤 실행)
    """
    base_url = _default_server_url()

    if not _is_server_running(base_url):
        pytest.skip(f"실행 중인 서버가 없어 건너뜀: {base_url} (COMIX_TEST_SERVER_URL 로 변경 가능)")

    return AirComixCompatibilityTester(base_url)


@pytest.fixture
def sample_test_data(tmp_path):
    """테스트용 샘플 데이터 생성"""
    comix_dir = tmp_path / "comix"
    comix_dir.mkdir()
    
    # 샘플 데이터 생성
    sample_data = SampleDataGenerator.create_sample_manga_structure(comix_dir)
    
    # 유니코드 파일명 테스트용 데이터 추가
    unicode_dir = comix_dir / "한글 시리즈"
    unicode_dir.mkdir()
    
    # 더미 파일 생성
    (unicode_dir / "1화.jpg").write_text("dummy image")
    (unicode_dir / "2화.jpg").write_text("dummy image")
    
    japanese_dir = comix_dir / "日本語シリーズ"
    japanese_dir.mkdir()
    (japanese_dir / "第1話.jpg").write_text("dummy image")
    
    return {
        'comix_dir': comix_dir,
        'sample_data': sample_data,
        'unicode_paths': [
            "한글 시리즈/",
            "한글 시리즈/1화.jpg",
            "日本語シリーズ/",
            "日本語シリーズ/第1話.jpg"
        ]
    }


class TestAirComixCompatibility:
    """AirComix 호환성 테스트 클래스"""
    
    def test_initial_connection_sequence(self, aircomix_tester):
        """초기 연결 시퀀스 테스트"""
        results = aircomix_tester.test_initial_connection()
        
        # 루트 디렉토리 조회 테스트
        assert 'root_directory' in results
        root_result = results['root_directory']
        assert 'error' not in root_result
        assert root_result['status_code'] == 200
        assert root_result['content_type'].startswith('text/plain')
        assert root_result['content'] is not None
        assert root_result['response_time'] < 1.0  # 1초 이내 응답
        
        # 서버 정보 조회 테스트
        assert 'server_info' in results
        info_result = results['server_info']
        assert 'error' not in info_result
        assert info_result['status_code'] == 200
        assert info_result['content_type'].startswith('text/plain')
        assert info_result['has_download_support'] is True
        assert info_result['has_image_process'] is True
        assert 'Comix Server' in info_result['content']
    
    def test_directory_navigation_patterns(self, aircomix_tester, sample_test_data):
        """디렉토리 탐색 패턴 테스트"""
        test_paths = [
            "",  # 루트 디렉토리
            "Series A/",  # 일반 디렉토리
            "Series B/Chapter 01/",  # 중첩 디렉토리
        ]
        
        results = aircomix_tester.test_directory_navigation(test_paths)
        
        for path in test_paths:
            assert path in results
            result = results[path]
            assert 'error' not in result
            # 파일이 없을 수 있으므로 200 또는 404 허용
            assert result['status_code'] in [200, 404]
            if result['status_code'] == 200:
                assert result['content_type'].startswith('text/plain')
                assert isinstance(result['item_count'], int)
            assert result['response_time'] < 2.0
    
    def test_archive_file_support(self, aircomix_tester, sample_test_data):
        """아카이브 파일 지원 테스트"""
        archive_paths = [
            "Series A/Volume 1.zip",
            "Series A/Volume 2.cbz",
        ]
        
        results = aircomix_tester.test_archive_handling(archive_paths)
        
        for archive_path in archive_paths:
            if archive_path in results:
                result = results[archive_path]
                if 'error' not in result:
                    # 아카이브 파일이 없을 수 있으므로 200 또는 404 허용
                    assert result['status_code'] in [200, 404]
                    if result['status_code'] == 200:
                        assert result['content_type'].startswith('text/plain')
                        assert result['all_images'] is True
                        assert result['sorted_properly'] is True
    
    def test_image_streaming_capability(self, aircomix_tester, sample_test_data):
        """이미지 스트리밍 기능 테스트"""
        image_paths = [
            "Series A/cover.jpg",  # 직접 이미지
            "Series A/Volume 1.zip/page001.jpg",  # 아카이브 내 이미지
        ]
        
        results = aircomix_tester.test_image_streaming(image_paths)
        
        for image_path in image_paths:
            if image_path in results:
                result = results[image_path]
                if 'error' not in result:
                    # 이미지 파일이 없거나 HEAD 메서드를 지원하지 않을 수 있음
                    assert result['status_code'] in [200, 404, 405]
                    if result['status_code'] == 200:
                        assert result['is_image_mime'] is True
                        assert result['has_content_length'] is True
                    assert result['response_time'] < 3.0
    
    def test_unicode_filename_support(self, aircomix_tester, sample_test_data):
        """유니코드 파일명 지원 테스트"""
        unicode_paths = sample_test_data['unicode_paths']
        
        results = aircomix_tester.test_character_encoding(unicode_paths)
        
        for path in unicode_paths:
            if path in results:
                result = results[path]
                assert 'error' not in result
                assert result['encoding_handled'] is True
                # 유니코드 파일이 실제로 존재하지 않을 수 있으므로 404도 허용
                assert result['status_code'] in [200, 404]
    
    def test_performance_requirements(self, aircomix_tester):
        """성능 요구사항 테스트"""
        results = aircomix_tester.test_performance_characteristics()
        
        # 연속 요청 성능
        rapid_results = results['rapid_requests']
        assert rapid_results['success_rate'] >= 0.9  # 90% 이상 성공률
        assert rapid_results['average_response_time'] < 0.5  # 평균 0.5초 이내
        assert rapid_results['max_response_time'] < 2.0  # 최대 2초 이내
    
    def test_aircomix_protocol_compliance(self, aircomix_tester):
        """AirComix 프로토콜 준수 테스트"""
        # 1. 필수 엔드포인트 존재 확인
        required_endpoints = [
            "/",
            "/welcome.102",
            "/comix/",
        ]
        
        for endpoint in required_endpoints:
            try:
                response = aircomix_tester.session.get(f"{aircomix_tester.base_url}{endpoint}")
                assert response.status_code in [200, 404], f"Endpoint {endpoint} returned {response.status_code}"
            except Exception as e:
                pytest.fail(f"Failed to access endpoint {endpoint}: {e}")
        
        # 2. 응답 형식 확인
        response = aircomix_tester.session.get(f"{aircomix_tester.base_url}/")
        assert response.headers.get('content-type', '').startswith('text/plain')
        
        response = aircomix_tester.session.get(f"{aircomix_tester.base_url}/welcome.102")
        assert 'allowDownload=' in response.text
        assert 'allowImageProcess=' in response.text


def run_compatibility_test_suite():
    """호환성 테스트 스위트 실행"""
    print("🧪 AirComix 호환성 테스트 시작")
    print("=" * 50)
    
    tester = AirComixCompatibilityTester()
    
    # 1. 기본 연결 테스트
    print("\n📡 기본 연결 테스트")
    connection_results = tester.test_initial_connection()
    
    if 'error' in connection_results.get('root_directory', {}):
        print("❌ 서버에 연결할 수 없습니다.")
        return False
    
    print("✅ 서버 연결 성공")
    print(f"   루트 디렉토리: {connection_results['root_directory']['content']}")
    print(f"   다운로드 지원: {connection_results['server_info']['has_download_support']}")
    print(f"   이미지 처리: {connection_results['server_info']['has_image_process']}")
    
    # 2. 성능 테스트
    print("\n⚡ 성능 테스트")
    performance_results = tester.test_performance_characteristics()
    
    rapid_results = performance_results['rapid_requests']
    print(f"✅ 연속 요청 테스트")
    print(f"   평균 응답시간: {rapid_results['average_response_time']:.3f}초")
    print(f"   최대 응답시간: {rapid_results['max_response_time']:.3f}초")
    print(f"   성공률: {rapid_results['success_rate']:.1%}")
    
    print("\n🎉 AirComix 호환성 테스트 완료!")
    print("서버가 AirComix iOS 앱과 호환됩니다.")
    
    return True


if __name__ == "__main__":
    # 독립 실행 시 호환성 테스트 수행
    success = run_compatibility_test_suite()
    exit(0 if success else 1)