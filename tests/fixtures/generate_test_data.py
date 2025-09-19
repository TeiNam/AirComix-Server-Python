#!/usr/bin/env python3
"""
테스트 데이터 생성 스크립트

이 스크립트는 테스트에 필요한 모든 샘플 데이터를 생성합니다.
개발자가 수동으로 테스트 데이터를 생성하거나 CI/CD에서 사용할 수 있습니다.
"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.fixture_manager import FixtureManager


def main():
    parser = argparse.ArgumentParser(description="테스트 데이터 생성")
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("test_data"),
        help="출력 디렉토리 (기본값: test_data)"
    )
    parser.add_argument(
        "--type",
        choices=["minimal", "complete"],
        default="complete",
        help="생성할 데이터 타입 (기본값: complete)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="기존 출력 디렉토리를 삭제하고 새로 생성"
    )
    
    args = parser.parse_args()
    
    # 출력 디렉토리 준비
    if args.clean and args.output_dir.exists():
        import shutil
        shutil.rmtree(args.output_dir)
    
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"테스트 데이터를 {args.output_dir}에 생성합니다...")
    
    # 픽스처 매니저 생성
    manager = FixtureManager(args.output_dir)
    
    try:
        if args.type == "minimal":
            print("최소한의 테스트 환경을 생성합니다...")
            data = manager.create_minimal_test_environment()
            print("✓ 최소 테스트 환경 생성 완료")
        else:
            print("완전한 테스트 환경을 생성합니다...")
            data = manager.create_complete_test_environment()
            print("✓ 완전한 테스트 환경 생성 완료")
        
        # 생성된 데이터 요약 출력
        print("\n생성된 테스트 데이터:")
        for category, items in data.items():
            if isinstance(items, dict):
                print(f"  {category}: {len(items)}개 항목")
            else:
                print(f"  {category}: 1개 항목")
        
        print(f"\n테스트 데이터가 {args.output_dir}에 성공적으로 생성되었습니다.")
        
        # 사용 예시 출력
        print("\n사용 예시:")
        print(f"  export COMIX_MANGA_DIRECTORY={args.output_dir}/comix")
        print(f"  python -m pytest tests/ -v")
        
    except Exception as e:
        print(f"❌ 테스트 데이터 생성 중 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()