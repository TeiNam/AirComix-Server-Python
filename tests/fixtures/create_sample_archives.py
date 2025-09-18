#!/usr/bin/env python3
"""
실제 테스트용 아카이브 파일 생성 스크립트

이 스크립트는 실제 ZIP, CBZ 파일과 가능한 경우 RAR, CBR 파일을 생성합니다.
"""

import zipfile
import sys
from pathlib import Path
from typing import List, Dict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.fixtures.sample_data import SampleDataGenerator


def create_realistic_comic_archive(archive_path: Path, format_type: str = "zip", page_count: int = 20) -> bool:
    """실제적인 만화 아카이브를 생성합니다
    
    Args:
        archive_path: 아카이브 파일 경로
        format_type: 아카이브 형식 (zip, cbz)
        page_count: 페이지 수
        
    Returns:
        생성 성공 여부
    """
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 표지 이미지 (더 큰 크기)
            cover_data = SampleDataGenerator.create_sample_image(800, 1200, "JPEG")
            zf.writestr("000_cover.jpg", cover_data)
            
            # 내용 페이지들
            for i in range(1, page_count + 1):
                page_data = SampleDataGenerator.create_sample_image(600, 900, "JPEG")
                zf.writestr(f"{i:03d}_page.jpg", page_data)
            
            # 뒷표지
            back_cover_data = SampleDataGenerator.create_sample_image(800, 1200, "JPEG")
            zf.writestr(f"{page_count+1:03d}_back_cover.jpg", back_cover_data)
            
            # 메타데이터 파일 (일부 만화 아카이브에 포함됨)
            metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Title>Test Comic</Title>
    <Series>Test Series</Series>
    <Number>1</Number>
    <Count>{page_count}</Count>
    <Year>2024</Year>
    <Month>1</Month>
    <Genre>Test</Genre>
    <LanguageISO>ko</LanguageISO>
    <Format>Digital</Format>
    <PageCount>{page_count + 2}</PageCount>
</ComicInfo>"""
            zf.writestr("ComicInfo.xml", metadata.encode('utf-8'))
            
        return True
        
    except Exception as e:
        print(f"아카이브 생성 실패 {archive_path}: {e}")
        return False


def create_mixed_format_archive(archive_path: Path) -> bool:
    """다양한 이미지 형식이 혼합된 아카이브를 생성합니다"""
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 다양한 형식의 이미지들
            formats = [
                ("page001.jpg", "JPEG"),
                ("page002.png", "PNG"),
                ("page003.gif", "GIF"),
                ("page004.bmp", "BMP"),
                ("page005.tif", "TIFF"),
                ("page006.jpeg", "JPEG")
            ]
            
            for filename, format_name in formats:
                try:
                    img_data = SampleDataGenerator.create_sample_image(400, 600, format_name)
                    zf.writestr(filename, img_data)
                except Exception as e:
                    print(f"Warning: Could not create {filename}: {e}")
            
            # 지원되지 않는 파일들도 포함 (필터링 테스트용)
            zf.writestr("readme.txt", b"This is a text file")
            zf.writestr("info.pdf", b"Fake PDF content")
            zf.writestr(".hidden_file", b"Hidden file content")
            
        return True
        
    except Exception as e:
        print(f"혼합 형식 아카이브 생성 실패 {archive_path}: {e}")
        return False


def create_nested_archive(archive_path: Path) -> bool:
    """중첩된 구조의 아카이브를 생성합니다"""
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 디렉토리 구조가 있는 아카이브
            directories = [
                "Chapter 01/",
                "Chapter 02/", 
                "Extras/",
                "Covers/"
            ]
            
            for directory in directories:
                # 각 디렉토리에 이미지들 추가
                for i in range(1, 6):  # 5개씩
                    img_data = SampleDataGenerator.create_sample_image(500, 750, "JPEG")
                    zf.writestr(f"{directory}page{i:03d}.jpg", img_data)
            
            # 루트 레벨 파일들
            cover_data = SampleDataGenerator.create_sample_image(800, 1200, "JPEG")
            zf.writestr("cover.jpg", cover_data)
            
        return True
        
    except Exception as e:
        print(f"중첩 아카이브 생성 실패 {archive_path}: {e}")
        return False


def create_large_archive(archive_path: Path, page_count: int = 100) -> bool:
    """큰 아카이브 파일을 생성합니다 (성능 테스트용)"""
    try:
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(1, page_count + 1):
                # 더 큰 이미지 생성 (1MB 정도)
                img_data = SampleDataGenerator.create_sample_image(1200, 1800, "JPEG")
                zf.writestr(f"page{i:04d}.jpg", img_data)
                
                # 진행 상황 출력
                if i % 10 == 0:
                    print(f"  생성 중... {i}/{page_count} 페이지")
        
        return True
        
    except Exception as e:
        print(f"큰 아카이브 생성 실패 {archive_path}: {e}")
        return False


def create_corrupted_archives(base_dir: Path) -> Dict[str, Path]:
    """다양한 종류의 손상된 아카이브들을 생성합니다"""
    corrupted_files = {}
    
    # 1. 완전히 잘못된 데이터
    invalid_zip = base_dir / "completely_invalid.zip"
    invalid_zip.write_bytes(b"This is not a ZIP file at all")
    corrupted_files["completely_invalid"] = invalid_zip
    
    # 2. ZIP 헤더만 있는 파일
    header_only = base_dir / "header_only.zip"
    header_only.write_bytes(b'PK\x03\x04')  # ZIP 로컬 파일 헤더 시작
    corrupted_files["header_only"] = header_only
    
    # 3. 불완전한 ZIP 파일
    incomplete_zip = base_dir / "incomplete.zip"
    try:
        with zipfile.ZipFile(incomplete_zip, 'w') as zf:
            zf.writestr("test.jpg", b"test data")
        
        # 파일을 잘라서 불완전하게 만들기
        data = incomplete_zip.read_bytes()
        incomplete_zip.write_bytes(data[:len(data)//2])  # 절반만 남기기
        corrupted_files["incomplete"] = incomplete_zip
        
    except Exception as e:
        print(f"불완전한 ZIP 생성 실패: {e}")
    
    # 4. 빈 ZIP 파일
    empty_zip = base_dir / "empty.zip"
    try:
        with zipfile.ZipFile(empty_zip, 'w') as zf:
            pass  # 빈 아카이브
        corrupted_files["empty"] = empty_zip
    except Exception as e:
        print(f"빈 ZIP 생성 실패: {e}")
    
    # 5. 암호로 보호된 ZIP (지원되지 않음)
    password_zip = base_dir / "password_protected.zip"
    try:
        with zipfile.ZipFile(password_zip, 'w') as zf:
            img_data = SampleDataGenerator.create_sample_image(400, 600, "JPEG")
            zf.writestr("protected.jpg", img_data)
            # 실제로는 암호 설정이 복잡하므로 일반 파일로 생성
        corrupted_files["password_protected"] = password_zip
    except Exception as e:
        print(f"암호 보호 ZIP 생성 실패: {e}")
    
    return corrupted_files


def create_encoding_test_archives(base_dir: Path) -> Dict[str, Path]:
    """다양한 문자 인코딩 테스트용 아카이브들을 생성합니다"""
    encoding_files = {}
    
    # UTF-8 파일명이 포함된 아카이브
    utf8_archive = base_dir / "utf8_filenames.zip"
    try:
        with zipfile.ZipFile(utf8_archive, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 다양한 언어의 파일명
            filenames = [
                "한국어_파일.jpg",
                "日本語ファイル.jpg", 
                "中文文件.jpg",
                "Русский_файл.jpg",
                "Français_fichier.jpg"
            ]
            
            for filename in filenames:
                img_data = SampleDataGenerator.create_sample_image(400, 600, "JPEG")
                zf.writestr(filename, img_data)
        
        encoding_files["utf8"] = utf8_archive
        
    except Exception as e:
        print(f"UTF-8 아카이브 생성 실패: {e}")
    
    # 특수 문자가 포함된 파일명
    special_chars_archive = base_dir / "special_characters.zip"
    try:
        with zipfile.ZipFile(special_chars_archive, 'w', zipfile.ZIP_DEFLATED) as zf:
            special_names = [
                "file with spaces.jpg",
                "file-with-dashes.jpg",
                "file_with_underscores.jpg",
                "file(with)parentheses.jpg",
                "file[with]brackets.jpg",
                "file{with}braces.jpg",
                "file&with&ampersands.jpg",
                "file+with+plus.jpg"
            ]
            
            for filename in special_names:
                img_data = SampleDataGenerator.create_sample_image(400, 600, "JPEG")
                zf.writestr(filename, img_data)
        
        encoding_files["special_chars"] = special_chars_archive
        
    except Exception as e:
        print(f"특수 문자 아카이브 생성 실패: {e}")
    
    return encoding_files


def main():
    """메인 함수"""
    print("테스트용 아카이브 파일들을 생성합니다...")
    
    # 출력 디렉토리 생성
    output_dir = Path("test_archives")
    output_dir.mkdir(exist_ok=True)
    
    success_count = 0
    total_count = 0
    
    # 1. 기본 만화 아카이브들
    print("\n1. 기본 만화 아카이브 생성...")
    archives = [
        ("comic_volume_1.zip", "zip", 15),
        ("comic_volume_2.cbz", "cbz", 20),
        ("manga_chapter_1.zip", "zip", 25),
        ("manga_chapter_2.cbz", "cbz", 18)
    ]
    
    for filename, format_type, page_count in archives:
        total_count += 1
        archive_path = output_dir / filename
        if create_realistic_comic_archive(archive_path, format_type, page_count):
            print(f"  ✓ {filename} 생성 완료 ({page_count} 페이지)")
            success_count += 1
        else:
            print(f"  ❌ {filename} 생성 실패")
    
    # 2. 혼합 형식 아카이브
    print("\n2. 혼합 형식 아카이브 생성...")
    total_count += 1
    mixed_archive = output_dir / "mixed_formats.zip"
    if create_mixed_format_archive(mixed_archive):
        print("  ✓ mixed_formats.zip 생성 완료")
        success_count += 1
    else:
        print("  ❌ mixed_formats.zip 생성 실패")
    
    # 3. 중첩 구조 아카이브
    print("\n3. 중첩 구조 아카이브 생성...")
    total_count += 1
    nested_archive = output_dir / "nested_structure.zip"
    if create_nested_archive(nested_archive):
        print("  ✓ nested_structure.zip 생성 완료")
        success_count += 1
    else:
        print("  ❌ nested_structure.zip 생성 실패")
    
    # 4. 큰 아카이브 (선택적)
    print("\n4. 큰 아카이브 생성 (시간이 걸릴 수 있습니다)...")
    total_count += 1
    large_archive = output_dir / "large_comic.zip"
    if create_large_archive(large_archive, 50):  # 50 페이지로 줄임
        print("  ✓ large_comic.zip 생성 완료")
        success_count += 1
    else:
        print("  ❌ large_comic.zip 생성 실패")
    
    # 5. 손상된 아카이브들
    print("\n5. 손상된 아카이브들 생성...")
    corrupted_dir = output_dir / "corrupted"
    corrupted_dir.mkdir(exist_ok=True)
    corrupted_files = create_corrupted_archives(corrupted_dir)
    for name, path in corrupted_files.items():
        total_count += 1
        if path.exists():
            print(f"  ✓ {name} 생성 완료")
            success_count += 1
        else:
            print(f"  ❌ {name} 생성 실패")
    
    # 6. 인코딩 테스트 아카이브들
    print("\n6. 인코딩 테스트 아카이브들 생성...")
    encoding_dir = output_dir / "encoding_tests"
    encoding_dir.mkdir(exist_ok=True)
    encoding_files = create_encoding_test_archives(encoding_dir)
    for name, path in encoding_files.items():
        total_count += 1
        if path.exists():
            print(f"  ✓ {name} 아카이브 생성 완료")
            success_count += 1
        else:
            print(f"  ❌ {name} 아카이브 생성 실패")
    
    # 결과 요약
    print(f"\n생성 완료: {success_count}/{total_count} 파일")
    print(f"아카이브 파일들이 {output_dir}에 저장되었습니다.")
    
    if success_count < total_count:
        print("\n일부 파일 생성에 실패했습니다. 로그를 확인해주세요.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())