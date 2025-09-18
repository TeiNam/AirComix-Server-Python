"""테스트용 샘플 데이터 생성 유틸리티"""

import io
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False


class SampleDataGenerator:
    """테스트용 샘플 데이터를 생성하는 클래스"""
    
    @staticmethod
    def create_sample_image(width: int = 100, height: int = 100, format: str = "JPEG") -> bytes:
        """샘플 이미지를 생성합니다
        
        Args:
            width: 이미지 너비
            height: 이미지 높이  
            format: 이미지 포맷 (JPEG, PNG, GIF 등)
            
        Returns:
            이미지 바이트 데이터
        """
        if not PIL_AVAILABLE:
            # Pillow가 없으면 더미 이미지 데이터 반환
            if format.upper() == "JPEG":
                # 최소한의 JPEG 헤더
                return b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
            elif format.upper() == "PNG":
                # 최소한의 PNG 헤더
                return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x03\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
            else:
                return b'fake image data'
        
        # RGB 모드로 이미지 생성 (빨간색 배경)
        image = Image.new("RGB", (width, height), color="red")
        
        # 바이트 스트림으로 변환
        img_bytes = io.BytesIO()
        image.save(img_bytes, format=format)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()
    
    @staticmethod
    def create_sample_manga_structure(base_dir: Path) -> Dict[str, Path]:
        """샘플 만화 디렉토리 구조를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일/디렉토리 경로들의 딕셔너리
        """
        paths = {}
        
        # 시리즈 A 디렉토리
        series_a = base_dir / "Series A"
        series_a.mkdir(exist_ok=True)
        paths["series_a"] = series_a
        
        # 시리즈 A의 볼륨들
        volume1_dir = series_a / "Volume 1"
        volume1_dir.mkdir(exist_ok=True)
        paths["volume1_dir"] = volume1_dir
        
        # 시리즈 A/Volume 1의 개별 이미지들
        for i in range(1, 4):
            img_path = volume1_dir / f"page{i:03d}.jpg"
            img_data = SampleDataGenerator.create_sample_image(format="JPEG")
            img_path.write_bytes(img_data)
            paths[f"page{i}"] = img_path
        
        # 시리즈 B 디렉토리 (한국어 이름)
        series_b = base_dir / "시리즈 B"
        series_b.mkdir(exist_ok=True)
        paths["series_b"] = series_b
        
        # 시리즈 B의 아카이브 파일들
        archive_zip = series_b / "Chapter 001.zip"
        SampleDataGenerator.create_sample_zip_archive(archive_zip)
        paths["archive_zip"] = archive_zip
        
        archive_cbz = series_b / "Chapter 002.cbz"
        SampleDataGenerator.create_sample_zip_archive(archive_cbz)
        paths["archive_cbz"] = archive_cbz
        
        # 루트 레벨 이미지
        root_image = base_dir / "cover.png"
        img_data = SampleDataGenerator.create_sample_image(format="PNG")
        root_image.write_bytes(img_data)
        paths["root_image"] = root_image
        
        # 숨겨진 파일들 (필터링 테스트용)
        hidden_file = base_dir / ".hidden_file"
        hidden_file.write_text("hidden content")
        paths["hidden_file"] = hidden_file
        
        ds_store = base_dir / ".DS_Store"
        ds_store.write_bytes(b"DS_Store content")
        paths["ds_store"] = ds_store
        
        thumbs_db = base_dir / "Thumbs.db"
        thumbs_db.write_bytes(b"Thumbs.db content")
        paths["thumbs_db"] = thumbs_db
        
        # 지원되지 않는 파일
        text_file = base_dir / "readme.txt"
        text_file.write_text("This is a text file")
        paths["text_file"] = text_file
        
        return paths
    
    @staticmethod
    def create_sample_zip_archive(archive_path: Path, image_count: int = 3) -> None:
        """샘플 ZIP 아카이브를 생성합니다
        
        Args:
            archive_path: 아카이브 파일 경로
            image_count: 포함할 이미지 개수
        """
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for i in range(1, image_count + 1):
                # 이미지 데이터 생성
                img_data = SampleDataGenerator.create_sample_image(format="JPEG")
                
                # 아카이브에 추가
                zf.writestr(f"page{i:03d}.jpg", img_data)
            
            # 지원되지 않는 파일도 추가 (필터링 테스트용)
            zf.writestr("info.txt", "Archive info")
            zf.writestr(".hidden", "hidden file in archive")
    
    @staticmethod
    def create_character_encoding_test_data(base_dir: Path) -> Dict[str, Path]:
        """문자 인코딩 테스트용 데이터를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # 다양한 언어의 디렉토리/파일명
        test_names = [
            "한국어 만화",
            "日本語マンガ", 
            "中文漫画",
            "Français BD",
            "Русский комикс"
        ]
        
        for i, name in enumerate(test_names):
            # 디렉토리 생성
            dir_path = base_dir / name
            dir_path.mkdir(exist_ok=True)
            paths[f"dir_{i}"] = dir_path
            
            # 이미지 파일 생성
            img_path = dir_path / f"{name}_cover.jpg"
            img_data = SampleDataGenerator.create_sample_image(format="JPEG")
            img_path.write_bytes(img_data)
            paths[f"img_{i}"] = img_path
        
        return paths
    
    @staticmethod
    def create_corrupted_archive(archive_path: Path) -> None:
        """손상된 아카이브 파일을 생성합니다 (에러 테스트용)
        
        Args:
            archive_path: 아카이브 파일 경로
        """
        # 유효하지 않은 ZIP 데이터 작성
        archive_path.write_bytes(b"This is not a valid ZIP file")
    
    @staticmethod
    def create_large_image(path: Path, width: int = 2000, height: int = 2000) -> None:
        """큰 이미지 파일을 생성합니다 (성능 테스트용)
        
        Args:
            path: 이미지 파일 경로
            width: 이미지 너비
            height: 이미지 높이
        """
        if not PIL_AVAILABLE:
            # Pillow가 없으면 큰 더미 데이터 생성 (150KB)
            large_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 150000  # 150KB 더미 데이터
            path.write_bytes(large_data)
            return
            
        # 더 큰 이미지 생성 (3000x3000)
        image = Image.new("RGB", (3000, 3000), color="blue")
        image.save(path, "JPEG", quality=95)
    
    @staticmethod
    def create_all_image_formats(base_dir: Path) -> Dict[str, Path]:
        """지원되는 모든 이미지 형식의 샘플 파일을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 이미지 파일 경로들의 딕셔너리
        """
        paths = {}
        formats = [
            ("jpg", "JPEG"),
            ("jpeg", "JPEG"), 
            ("png", "PNG"),
            ("gif", "GIF"),
            ("bmp", "BMP"),
            ("tif", "TIFF"),
            ("tiff", "TIFF")
        ]
        
        for ext, format_name in formats:
            img_path = base_dir / f"sample.{ext}"
            try:
                img_data = SampleDataGenerator.create_sample_image(format=format_name)
                img_path.write_bytes(img_data)
                paths[ext] = img_path
            except Exception as e:
                # 일부 형식이 지원되지 않을 수 있음
                print(f"Warning: Could not create {ext} image: {e}")
        
        return paths
    
    @staticmethod
    def create_sample_rar_archive(archive_path: Path, image_count: int = 3) -> bool:
        """샘플 RAR 아카이브를 생성합니다 (가능한 경우)
        
        Args:
            archive_path: 아카이브 파일 경로
            image_count: 포함할 이미지 개수
            
        Returns:
            RAR 파일 생성 성공 여부
        """
        # RAR 파일 생성은 복잡하므로 더미 RAR 파일을 생성
        # 실제 테스트에서는 미리 준비된 RAR 파일을 사용하는 것이 좋음
        rar_header = b'Rar!\x1a\x07\x00'  # RAR 파일 시그니처
        dummy_content = b'\x00' * 1000  # 더미 내용
        
        try:
            archive_path.write_bytes(rar_header + dummy_content)
            return True
        except Exception:
            return False
    
    @staticmethod
    def create_mixed_content_directory(base_dir: Path) -> Dict[str, Path]:
        """혼합 콘텐츠가 있는 디렉토리를 생성합니다 (필터링 테스트용)
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # 지원되는 이미지 파일들
        for i, ext in enumerate(["jpg", "png", "gif"], 1):
            img_path = base_dir / f"image{i}.{ext}"
            img_data = SampleDataGenerator.create_sample_image(format=ext.upper() if ext != "jpg" else "JPEG")
            img_path.write_bytes(img_data)
            paths[f"image_{ext}"] = img_path
        
        # 지원되는 아카이브 파일들
        zip_path = base_dir / "archive.zip"
        SampleDataGenerator.create_sample_zip_archive(zip_path)
        paths["archive_zip"] = zip_path
        
        cbz_path = base_dir / "comic.cbz"
        SampleDataGenerator.create_sample_zip_archive(cbz_path)
        paths["archive_cbz"] = cbz_path
        
        # 지원되지 않는 파일들
        unsupported_files = [
            ("document.pdf", b"PDF content"),
            ("video.mp4", b"MP4 content"),
            ("audio.mp3", b"MP3 content"),
            ("text.txt", b"Text content"),
            ("data.json", b'{"key": "value"}'),
        ]
        
        for filename, content in unsupported_files:
            file_path = base_dir / filename
            file_path.write_bytes(content)
            paths[f"unsupported_{filename.split('.')[1]}"] = file_path
        
        # 시스템 파일들 (필터링되어야 함)
        system_files = [
            ".DS_Store",
            "Thumbs.db", 
            "@eaDir",
            ".hidden_file"
        ]
        
        for filename in system_files:
            file_path = base_dir / filename
            file_path.write_bytes(b"system file content")
            paths[f"system_{filename.replace('.', '').replace('@', '')}"] = file_path
        
        # __MACOSX 디렉토리 (필터링되어야 함)
        macosx_dir = base_dir / "__MACOSX"
        macosx_dir.mkdir(exist_ok=True)
        (macosx_dir / "._file").write_bytes(b"resource fork")
        paths["macosx_dir"] = macosx_dir
        
        return paths
    
    @staticmethod
    def create_nested_directory_structure(base_dir: Path, depth: int = 3) -> Dict[str, Path]:
        """중첩된 디렉토리 구조를 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            depth: 중첩 깊이
            
        Returns:
            생성된 디렉토리 경로들의 딕셔너리
        """
        paths = {}
        current_dir = base_dir
        
        for i in range(depth):
            current_dir = current_dir / f"level_{i+1}"
            current_dir.mkdir(exist_ok=True)
            paths[f"level_{i+1}"] = current_dir
            
            # 각 레벨에 이미지 파일 추가
            img_path = current_dir / f"image_level_{i+1}.jpg"
            img_data = SampleDataGenerator.create_sample_image(format="JPEG")
            img_path.write_bytes(img_data)
            paths[f"image_level_{i+1}"] = img_path
        
        return paths
    
    @staticmethod
    def create_edge_case_files(base_dir: Path) -> Dict[str, Path]:
        """엣지 케이스 테스트용 파일들을 생성합니다
        
        Args:
            base_dir: 기본 디렉토리 경로
            
        Returns:
            생성된 파일 경로들의 딕셔너리
        """
        paths = {}
        
        # 빈 파일
        empty_file = base_dir / "empty.jpg"
        empty_file.write_bytes(b"")
        paths["empty_file"] = empty_file
        
        # 매우 긴 파일명
        long_name = "a" * 200 + ".jpg"
        long_name_file = base_dir / long_name
        img_data = SampleDataGenerator.create_sample_image(format="JPEG")
        long_name_file.write_bytes(img_data)
        paths["long_name_file"] = long_name_file
        
        # 특수 문자가 포함된 파일명
        special_chars = [
            "file with spaces.jpg",
            "file-with-dashes.jpg", 
            "file_with_underscores.jpg",
            "file(with)parentheses.jpg",
            "file[with]brackets.jpg",
            "file{with}braces.jpg"
        ]
        
        for filename in special_chars:
            file_path = base_dir / filename
            img_data = SampleDataGenerator.create_sample_image(format="JPEG")
            file_path.write_bytes(img_data)
            safe_name = filename.replace(" ", "_").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "").replace("-", "_")
            paths[f"special_{safe_name.split('.')[0]}"] = file_path
        
        # 확장자가 없는 파일
        no_ext_file = base_dir / "no_extension"
        no_ext_file.write_bytes(b"file without extension")
        paths["no_extension"] = no_ext_file
        
        # 대소문자 혼합 확장자
        mixed_case_file = base_dir / "MixedCase.JPG"
        img_data = SampleDataGenerator.create_sample_image(format="JPEG")
        mixed_case_file.write_bytes(img_data)
        paths["mixed_case"] = mixed_case_file
        
        return paths