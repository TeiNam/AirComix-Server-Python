"""크기 상한 응답과 목록 본문 생성 테스트

교차 리뷰에서 확인된 두 가지 계약을 고정한다.
- 크기 상한 초과는 500 이 아니라 413 으로 클라이언트에 전달된다.
- 목록 본문은 개행이 포함된 이름을 광고하지 않는다.
"""

import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from app.api.handlers import _to_listing_body


def _jpeg_bytes(size=(40, 60)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, "red").save(buffer, "JPEG")
    return buffer.getvalue()


class TestListingBody:
    """목록 본문 생성"""

    def test_normal_names_are_joined_with_newline(self):
        assert _to_listing_body(["a.jpg", "b.zip"]) == "a.jpg\nb.zip"

    def test_names_with_newlines_are_dropped(self):
        """개행이 있는 이름은 요청 불가능하므로 목록에서 제외한다"""
        body = _to_listing_body(["ok.jpg", "bad\nname.jpg", "also\rbad.jpg"])

        assert body == "ok.jpg"

    def test_empty_list(self):
        assert _to_listing_body([]) == ""


@pytest.mark.usefixtures("override_settings")
class TestSizeLimitResponses:
    """최대 파일 크기 초과 응답"""

    def test_oversized_archive_member_returns_413(
        self, client, override_settings, monkeypatch
    ):
        from app.services import archive as archive_module

        manga_dir = Path(override_settings.manga_directory)
        archive_path = manga_dir / "volume1.zip"

        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("page001.jpg", _jpeg_bytes((400, 600)))

        # 아카이브 서비스는 모듈 전역 설정을 사용한다
        monkeypatch.setattr(archive_module.settings, "max_file_size", 100)

        response = client.get("/comix/volume1.zip/page001.jpg")

        assert response.status_code == 413

    def test_oversized_direct_image_returns_413(
        self, client, override_settings, monkeypatch
    ):
        manga_dir = Path(override_settings.manga_directory)
        image_path = manga_dir / "cover.jpg"
        image_path.write_bytes(_jpeg_bytes((400, 600)))

        monkeypatch.setattr(override_settings, "max_file_size", 100)

        response = client.get("/comix/cover.jpg")

        assert response.status_code == 413

    def test_within_limit_is_served(self, client, override_settings):
        manga_dir = Path(override_settings.manga_directory)
        image_path = manga_dir / "cover.jpg"
        payload = _jpeg_bytes()
        image_path.write_bytes(payload)

        response = client.get("/comix/cover.jpg")

        assert response.status_code == 200
        assert response.content == payload
