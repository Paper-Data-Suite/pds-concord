"""Standalone, real-code installed wheel check for Issue #132.

Usage:
  python scripts/verify_issue132_composition.py CORE_WHEEL SCORE_WHEEL CONCORD_WHEEL

Creates one isolated temporary environment. Requires pip access to published
runtime dependencies and zxing-cpp==3.1.1; touches no Paper Data Suite workspace.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

TEST = r'''
from importlib import metadata
from pathlib import Path
import importlib
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image
import qrcode

from concord.routing.scan_intake import _default_decode
from scoreform.qr_zxing_fallback import decode_qr_with_zxing

expected = {
    "pds-core": "0.6.5",
    "scoreform": "0.13.0",
    "pds-concord": "0.3.2",
    "zxing-cpp": "3.1.1",
}
for name, version in expected.items():
    actual = metadata.version(name)
    assert actual == version, (name, actual, version)
    print("PASS distribution:", name, version)

for name in ("pds_core", "scoreform", "concord", "zxingcpp"):
    module = importlib.import_module(name)
    path = Path(module.__file__).resolve()
    assert path.is_relative_to(Path(sys.prefix).resolve()), path
    print("PASS installed import:", name, path)

values = ("PDS2|issue132|shared|1", "PDS2|issue132|shared|2")
def qr(text):
    code = qrcode.QRCode(box_size=12, border=4)
    code.add_data(text)
    code.make(fit=True)
    return code.make_image(fill_color="black", back_color="white").convert("RGB")
with tempfile.TemporaryDirectory(prefix="concord132-scans-") as folder:
    root = Path(folder)
    first, second = [qr(value) for value in values]
    image = root / "page.png"
    first.save(image)
    assert _default_decode(image) == ((values[0],),)
    assert decode_qr_with_zxing(np.asarray(first)).payload_texts == (values[0],)
    pdf = root / "pages.pdf"
    first.save(pdf, save_all=True, append_images=[second], resolution=144.0)
    assert _default_decode(pdf) == ((values[0],), (values[1],))
print("PASS: Concord real image/PDF; ScoreForm real ZXing QR adapter")
'''


def run(argv: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print("RUN", " ".join(argv[:3]), flush=True)
    subprocess.run(argv, cwd=cwd, env=env, check=True)


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: verify_issue132_composition.py CORE_WHEEL SCORE_WHEEL CONCORD_WHEEL"
        )
    core, score, concord = (Path(arg).resolve(strict=True) for arg in sys.argv[1:])
    if (core.name, score.name, concord.name) != (
        "pds_core-0.6.5-py3-none-any.whl",
        "scoreform-0.13.0-py3-none-any.whl",
        "pds_concord-0.3.2-py3-none-any.whl",
    ):
        raise SystemExit("Wheels must be the expected exact release names")
    with tempfile.TemporaryDirectory(prefix="concord132-composition-") as base:
        root = Path(base)
        venv.EnvBuilder(with_pip=True).create(root / "venv")
        exe = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        python = root / "venv" / exe
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        run(
            [
                str(python), "-m", "pip", "install",
                str(core), str(score), str(concord), "zxing-cpp==3.1.1",
            ],
            cwd=root, env=env,
        )
        run([str(python), "-m", "pip", "check"], cwd=root, env=env)
        run([str(python), "-I", "-c", TEST], cwd=root, env=env)
    print("=== ISSUE #132 ISOLATED CROSS-MODULE COMPOSITION PASSED ===")


if __name__ == "__main__":
    main()
