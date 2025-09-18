"""문자 인코딩 테스트용 데이터 생성 유틸리티"""

import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
import io


class EncodingTestDataGenerator:
    """문자 인코딩 테스트용 데이터를 생성하는 클래스"""
    
    # 다양한 언어의 테스트 문자열
    TEST_STRINGS = {
        "korean": [
            "한국어 만화",
            "웹툰 시리즈",
            "판타지 소설",
            "로맨스 코믹",
            "액션 만화책"
        ],
        "japanese": [
            "日本語マンガ",
            "少年ジャンプ",
            "週刊少年マガジン",
            "ドラゴンボール",
            "ワンピース"
        ],
        "chinese_simplified": [
            "中文漫画",
            "连载漫画",
            "武侠小说",
            "科幻故事",
            "爱情漫画"
        ],
        "chinese_traditional": [
            "中文漫畫",
            "連載漫畫",
            "武俠小說",
            "科幻故事",
            "愛情漫畫"
        ],
        "russian": [
            "Русский комикс",
            "Графический роман",
            "Супергерои",
            "Фантастика",
            "Приключения"
        ],
        "arabic": [
            "كتاب مصور",
            "قصة مصورة",
            "مغامرات",
            "خيال علمي",
            "رومانسية"
        ],
        "french": [
            "Bande dessinée",
            "Album BD",
            "Aventure",
            "Science-fiction",
            "Romance"
        ],
        "german": [
            "Deutscher Comic",
            "Graphic Novel",
            "Abenteuer",
            "Science Fiction",
            "Romantik"
        ]
    }
    
    # 레거시 인코딩 테스트용
    LEGACY_ENCODINGS = {
        "euc-kr": "korean",
        "shift_jis": "japanese", 
        "gb2312": "chinese_simplified",
        "big5": "chinese_traditional",
        "cp1251": "russian",
        "cp1256": "arabic",
        "iso-8859-1": "french",
        "cp1252": "german"
    }
    
    @staticmethod
    def create_unicode_test_files(base_dir: Path) -> Dict[str, Path]:
        """유니코드 파일명 테스트용 파일들을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        for lang, strings in EncodingTestDataGenerator.TEST_STRINGS.items():
            lang_dir = base_dir / f"unicode_{lang}"
            lang_dir.mkdir(exist_ok=True)
            paths[f"dir_{lang}"] = lang_dir
            
            for i, string in enumerate(strings):
                # 이미지 파일 생성
                img_path = lang_dir / f"{string}.jpg"
                try:
                    # 간단한 JPEG 더미 데이터
                    img_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                    img_path.write_bytes(img_data)
                    paths[f"file_{lang}_{i}"] = img_path
                except OSError as e:
                    # 일부 파일 시스템에서 지원하지 않는 문자가 있을 수 있음
                    print(f"Warning: Could not create file with name '{string}': {e}")
        
        return paths
    
    @staticmethod
    def create_legacy_encoding_archives(base_dir: Path) -> Dict[str, Path]:
        """레거시 인코딩이 포함된 아카이브 파일들을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 아카이브 파일 경로들의 딕셔너리
        """
        paths = {}
        
        for encoding, lang in EncodingTestDataGenerator.LEGACY_ENCODINGS.items():
            if lang not in EncodingTestDataGenerator.TEST_STRINGS:
                continue
                
            archive_path = base_dir / f"legacy_{encoding}.zip"
            
            try:
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    strings = EncodingTestDataGenerator.TEST_STRINGS[lang]
                    
                    for i, string in enumerate(strings[:3]):  # 처음 3개만 사용
                        # 문자열을 해당 인코딩으로 인코딩
                        try:
                            encoded_name = string.encode(encoding)
                            filename = f"page{i+1:03d}.jpg"
                            
                            # 간단한 이미지 데이터
                            img_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100 + b'\xff\xd9'
                            
                            # 아카이브에 추가 (인코딩된 파일명 사용)
                            info = zipfile.ZipInfo(filename)
                            info.filename = encoded_name.decode('latin1')  # ZIP에서 사용하는 방식
                            zf.writestr(info, img_data)
                            
                        except (UnicodeEncodeError, UnicodeDecodeError) as e:
                            print(f"Warning: Could not encode '{string}' with {encoding}: {e}")
                            continue
                
                paths[f"archive_{encoding}"] = archive_path
                
            except Exception as e:
                print(f"Warning: Could not create archive for {encoding}: {e}")
        
        return paths
    
    @staticmethod
    def create_mixed_encoding_archive(base_dir: Path) -> Path:
        """다양한 인코딩이 혼합된 아카이브를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 아카이브 파일 경로
        """
        archive_path = base_dir / "mixed_encoding.zip"
        
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # UTF-8 파일명
            zf.writestr("한국어파일.jpg", b"Korean file content")
            zf.writestr("日本語ファイル.jpg", b"Japanese file content")
            
            # ASCII 파일명
            zf.writestr("english_file.jpg", b"English file content")
            zf.writestr("numbers_123.jpg", b"Numbers file content")
            
            # 특수 문자가 포함된 파일명
            zf.writestr("file with spaces.jpg", b"Spaces file content")
            zf.writestr("file-with-dashes.jpg", b"Dashes file content")
            zf.writestr("file_with_underscores.jpg", b"Underscores file content")
        
        return archive_path
    
    @staticmethod
    def create_url_encoding_test_data(base_dir: Path) -> Dict[str, Path]:
        """URL 인코딩 테스트용 데이터를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # URL에서 특별한 의미를 가지는 문자들
        special_chars = [
            "file with spaces",
            "file%20with%20encoded%20spaces",
            "file+with+plus",
            "file&with&ampersand",
            "file?with?question",
            "file#with#hash",
            "file=with=equals",
            "file[with]brackets",
            "file{with}braces",
            "file(with)parentheses"
        ]
        
        for i, filename in enumerate(special_chars):
            safe_filename = f"{filename}.jpg"
            file_path = base_dir / safe_filename
            
            try:
                # 간단한 이미지 데이터
                img_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100 + b'\xff\xd9'
                file_path.write_bytes(img_data)
                
                # 안전한 키 이름 생성
                safe_key = f"url_test_{i}"
                paths[safe_key] = file_path
                
            except OSError as e:
                print(f"Warning: Could not create file '{safe_filename}': {e}")
        
        return paths
    
    @staticmethod
    def create_normalization_test_data(base_dir: Path) -> Dict[str, Path]:
        """유니코드 정규화 테스트용 데이터를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # 같은 문자의 다른 유니코드 표현
        # 예: é는 "e + ´" (조합형)과 "é" (완성형)으로 표현 가능
        normalization_tests = [
            ("cafe\u0301.jpg", "cafe_combining"),  # e + combining acute accent
            ("café.jpg", "cafe_precomposed"),      # precomposed é
            ("나\u0308.jpg", "korean_combining"),   # 나 + combining diaeresis  
            ("나.jpg", "korean_normal"),           # normal 나
        ]
        
        for filename, key in normalization_tests:
            file_path = base_dir / filename
            
            try:
                # 간단한 이미지 데이터
                img_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100 + b'\xff\xd9'
                file_path.write_bytes(img_data)
                paths[key] = file_path
                
            except OSError as e:
                print(f"Warning: Could not create normalization test file '{filename}': {e}")
        
        return paths
    
    @staticmethod
    def create_all_encoding_test_data(base_dir: Path) -> Dict[str, Dict[str, Path]]:
        """모든 인코딩 테스트 데이터를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            카테고리별로 그룹화된 파일 경로들의 딕셔너리
        """
        results = {}
        
        # 유니코드 파일명 테스트
        unicode_dir = base_dir / "unicode_tests"
        unicode_dir.mkdir(exist_ok=True)
        results["unicode"] = EncodingTestDataGenerator.create_unicode_test_files(unicode_dir)
        
        # 레거시 인코딩 아카이브 테스트
        legacy_dir = base_dir / "legacy_encoding_tests"
        legacy_dir.mkdir(exist_ok=True)
        results["legacy"] = EncodingTestDataGenerator.create_legacy_encoding_archives(legacy_dir)
        
        # URL 인코딩 테스트
        url_dir = base_dir / "url_encoding_tests"
        url_dir.mkdir(exist_ok=True)
        results["url"] = EncodingTestDataGenerator.create_url_encoding_test_data(url_dir)
        
        # 유니코드 정규화 테스트
        norm_dir = base_dir / "normalization_tests"
        norm_dir.mkdir(exist_ok=True)
        results["normalization"] = EncodingTestDataGenerator.create_normalization_test_data(norm_dir)
        
        # 혼합 인코딩 아카이브
        mixed_archive = EncodingTestDataGenerator.create_mixed_encoding_archive(base_dir)
        results["mixed_archive"] = {"mixed_encoding_zip": mixed_archive}
        
        return results