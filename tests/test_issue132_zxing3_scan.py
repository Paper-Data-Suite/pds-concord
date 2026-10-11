"""Issue #132: real ZXing-C++ 3.1.1 decoder compatibility (no mocks)."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path

import pytest
import qrcode
from packaging.version import Version
from PIL import Image

from concord.routing.scan_intake import _default_decode


def _require_zxing3() -> None:
    pytest.importorskip("zxingcpp")
    assert Version("3.1.1") <= Version(metadata.version("zxing-cpp")) < Version("4")


def _qr(payload: str) -> Image.Image:
    qr = qrcode.QRCode(
        box_size=12,
        border=4,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def test_issue132_real_zxing3_image_decoder(tmp_path: Path) -> None:
    _require_zxing3()
    value = "PDS2|issue132|image|concord"
    path = tmp_path / "qr.png"
    _qr(value).save(path)
    assert _default_decode(path) == ((value,),)


def test_issue132_real_zxing3_multipage_pdf_decoder(tmp_path: Path) -> None:
    _require_zxing3()
    first = "PDS2|issue132|pdf|page1"
    second = "PDS2|issue132|pdf|page2"
    path = tmp_path / "qr.pdf"
    img1 = _qr(first)
    img2 = _qr(second)
    img1.save(path, save_all=True, append_images=[img2], resolution=144.0)
    assert _default_decode(path) == ((first,), (second,))
