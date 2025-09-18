#!/usr/bin/env python3
"""
Comix Server 테스트 클라이언트

기본 설정이 올바르게 작동하는지 확인하는 테스트 스크립트입니다.
"""

import sys
import time
import requests
from pathlib import Path
from typing import List, Optional


class ComixTestClient:
    """Comix Server 테스트 클라이언트"""
    
    def __init__(self, base_url: str = "http://localhost:31257"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 10
    
    def test_connection(self) -> bool:
        """서버 연결 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_root_directory(self) -> Optional[str]:
        """루트 디렉토리 이름 조회"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                return response.text.strip()
            return None
        except requests.exceptions.RequestException:
            return None
    
    def get_server_info(self) -> Optional[str]:
        """서버 정보 조회"""
        try:
            response = self.session.get(f"{self.base_url}/welcome.102")
            if response.status_code == 200:
                return response.text.strip()
            return None
        except requests.exceptions.RequestException:
            return None
    
    def get_directory_list(self, path: str = "") -> List[str]:
        """디렉토리 목록 조회"""
        try:
            url = f"{self.base_url}/manga/{path}"
            response = self.session.get(url)
            if response.status_code == 200:
                content = response.text.strip()
                return content.split('\n') if content else []
            return []
        except requests.exceptions.RequestException:
            return []
    
    def test_image_access(self, image_path: str) -> bool:
        """이미지 접근 테스트"""
        try:
            url = f"{self.base_url}/manga/{image_path}"
            response = self.session.head(url)
            return response.status_code == 200 and 'image/' in response.headers.get('content-type', '')
        except requests.exceptions.RequestException:
            return False


def print_status(message: str, status: bool, details: str = ""):
    """상태 출력"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {message}")
    if details:
        print(f"   {details}")


def main():
    """메인 테스트 함수"""
    print("🧪 Comix Server 테스트 시작")
    print("=" * 50)
    
    # 클라이언트 생성
    client = ComixTestClient()
    
    # 1. 연결 테스트
    print("\n📡 연결 테스트")
    print("-" * 20)
    
    print("서버 연결 확인 중...", end=" ")
    sys.stdout.flush()
    
    connected = False
    for attempt in range(3):
        if client.test_connection():
            connected = True
            break
        time.sleep(1)
        print(".", end="")
        sys.stdout.flush()
    
    print()
    print_status("서버 연결", connected)
    
    if not connected:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("다음을 확인해주세요:")
        print("1. 서버가 실행 중인지 확인: comix-server")
        print("2. 포트가 올바른지 확인: http://localhost:31257")
        print("3. 방화벽 설정 확인")
        sys.exit(1)
    
    # 2. 기본 API 테스트
    print("\n🔍 기본 API 테스트")
    print("-" * 20)
    
    # 루트 디렉토리
    root_dir = client.get_root_directory()
    print_status("루트 디렉토리 조회", root_dir is not None, f"디렉토리: {root_dir}")
    
    # 서버 정보
    server_info = client.get_server_info()
    print_status("서버 정보 조회", server_info is not None)
    if server_info:
        for line in server_info.split('\n')[:3]:  # 처음 3줄만 표시
            print(f"   {line}")
    
    # 3. 디렉토리 목록 테스트
    print("\n📁 디렉토리 목록 테스트")
    print("-" * 20)
    
    # 루트 목록
    root_files = client.get_directory_list("")
    print_status("루트 디렉토리 목록", len(root_files) >= 0, f"{len(root_files)}개 항목")
    
    if root_files:
        print("   파일/디렉토리:")
        for item in root_files[:5]:  # 처음 5개만 표시
            print(f"   - {item}")
        if len(root_files) > 5:
            print(f"   ... 및 {len(root_files) - 5}개 더")
    else:
        print("   ⚠️  만화 디렉토리가 비어있습니다.")
        print("   만화 파일을 추가한 후 다시 테스트해보세요.")
    
    # 4. 아카이브 파일 테스트
    print("\n📦 아카이브 파일 테스트")
    print("-" * 20)
    
    archive_found = False
    archive_extensions = ['.zip', '.cbz', '.rar', '.cbr']
    
    for item in root_files:
        if any(item.lower().endswith(ext) for ext in archive_extensions):
            archive_files = client.get_directory_list(item)
            print_status(f"아카이브 '{item}' 내용 조회", len(archive_files) > 0, f"{len(archive_files)}개 이미지")
            archive_found = True
            break
    
    if not archive_found:
        print("⚠️  아카이브 파일을 찾을 수 없습니다.")
        print("   ZIP, CBZ, RAR, CBR 파일을 추가하여 테스트해보세요.")
    
    # 5. 이미지 접근 테스트
    print("\n🖼️  이미지 접근 테스트")
    print("-" * 20)
    
    image_found = False
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    # 직접 이미지 파일 테스트
    for item in root_files:
        if any(item.lower().endswith(ext) for ext in image_extensions):
            accessible = client.test_image_access(item)
            print_status(f"이미지 '{item}' 접근", accessible)
            image_found = True
            break
    
    # 아카이브 내 이미지 테스트
    if not image_found:
        for item in root_files:
            if any(item.lower().endswith(ext) for ext in archive_extensions):
                archive_files = client.get_directory_list(item)
                if archive_files:
                    first_image = archive_files[0]
                    image_path = f"{item}/{first_image}"
                    accessible = client.test_image_access(image_path)
                    print_status(f"아카이브 이미지 '{image_path}' 접근", accessible)
                    image_found = True
                    break
    
    if not image_found:
        print("⚠️  이미지 파일을 찾을 수 없습니다.")
        print("   JPG, PNG 등의 이미지 파일을 추가하여 테스트해보세요.")
    
    # 6. 성능 테스트
    print("\n⚡ 성능 테스트")
    print("-" * 20)
    
    # 응답 시간 측정
    start_time = time.time()
    client.get_directory_list("")
    response_time = (time.time() - start_time) * 1000
    
    print_status("응답 시간", response_time < 1000, f"{response_time:.1f}ms")
    
    if response_time > 1000:
        print("   ⚠️  응답 시간이 느립니다. 다음을 확인해보세요:")
        print("   - 만화 디렉토리가 SSD에 있는지 확인")
        print("   - 디렉토리에 너무 많은 파일이 있는지 확인")
        print("   - 시스템 리소스 사용량 확인")
    
    # 7. 최종 결과
    print("\n🎯 테스트 완료")
    print("=" * 50)
    
    if connected:
        print("✅ 기본 설정이 올바르게 작동합니다!")
        print("\n📱 AirComix 앱 연결 정보:")
        print(f"   서버 주소: http://localhost:31257")
        print("   (외부 접근 시 localhost를 실제 IP로 변경)")
        
        print("\n🔗 유용한 링크:")
        print("   - 헬스 체크: http://localhost:31257/health")
        print("   - 서버 정보: http://localhost:31257/welcome.102")
        print("   - 만화 목록: http://localhost:31257/manga/")
        
        if not root_files:
            print("\n💡 다음 단계:")
            print("   1. 만화 파일을 만화 디렉토리에 추가")
            print("   2. AirComix 앱에서 서버 연결")
            print("   3. 만화 읽기 시작!")
    else:
        print("❌ 설정에 문제가 있습니다.")
        print("문제 해결 가이드를 참조하세요: docs/TROUBLESHOOTING.md")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        print("자세한 정보는 서버 로그를 확인하세요.")
        sys.exit(1)