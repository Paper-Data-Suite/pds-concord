"""Install Concord/Core wheels in isolation and smoke-test issue #103 scan routing."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import tempfile
import textwrap
import venv
from pathlib import Path

EXPECTED_CORE_SHA256 = (
    "98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5"
)


def _python(venv_root: Path) -> Path:
    return (
        venv_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else venv_root / "bin" / "python"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _smoke_code() -> str:
    return textwrap.dedent(
        r"""
        from __future__ import annotations

        import hashlib
        import os
        import subprocess
        import sys
        import tempfile
        from importlib import metadata
        from pathlib import Path

        import concord
        import pds_core
        from pds_core.scan_routes import (
            routing_review_dir,
            scans_inbox_dir,
            scans_source_dir,
        )
        from pds_core.workspace import ensure_workspace_root

        def stage(name: str) -> None:
            print(f"issue103 installed wheel: {name}: PASS", flush=True)


        def require_installed(module: object, distribution: str) -> None:
            origin = Path(getattr(module, "__file__")).resolve()
            if "site-packages" not in str(origin).casefold():
                raise AssertionError(
                    f"{distribution} did not import from isolated "
                    f"site-packages: {origin}"
                )


        def tree_fingerprint(root: Path) -> tuple[
            tuple[str, ...],
            tuple[tuple[str, str], ...],
        ]:
            directories = tuple(
                sorted(
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*")
                    if path.is_dir()
                )
            )
            files = []
            for path in sorted(
                (item for item in root.rglob("*") if item.is_file()),
                key=lambda item: item.relative_to(root).as_posix(),
            ):
                files.append(
                    (
                        path.relative_to(root).as_posix(),
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )
                )
            return directories, tuple(files)


        require_installed(pds_core, "pds-core")
        require_installed(concord, "pds-concord")
        assert metadata.version("pds-core") == "0.6.3"
        assert metadata.version("pds-concord") == "0.3.0"
        stage("isolated installed provenance")

        with tempfile.TemporaryDirectory(
            prefix="concord-issue103-installed-"
        ) as raw:
            root = ensure_workspace_root(Path(raw) / "workspace")
            inbox = scans_inbox_dir(root)
            first = inbox / "alpha.pdf"
            selected = inbox / "beta.pdf"
            unsupported = inbox / "notes.txt"
            first.write_bytes(b"issue103 synthetic alpha scan")
            selected.write_bytes(b"issue103 synthetic beta scan")
            unsupported.write_text("not a routable scan", encoding="utf-8")

            before = tree_fingerprint(root)
            console = Path(sys.executable).parent / (
                "concord.exe" if os.name == "nt" else "concord"
            )
            assert console.is_file(), console

            env = {
                **os.environ,
                "PDS_WORKSPACE_ROOT": str(root),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            completed = subprocess.run(
                [str(console)],
                cwd=Path(raw),
                input="4\n1\n2\n\nb\nq\n",
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
            rendered = completed.stdout

            assert "4. Scan Routing" in rendered
            assert "Scan Routing — Route Scans" in rendered
            assert "Available scans:" in rendered
            assert "1. alpha.pdf" in rendered
            assert "2. beta.pdf" in rendered
            assert "notes.txt" not in rendered
            assert "C. Choose custom file/folder path" in rendered
            assert "R. Refresh" in rendered
            assert f"Source: {selected}" in rendered
            assert "Type ROUTE to confirm" in rendered
            assert "Scan Routing Complete" not in rendered
            stage("bare console inbox selection and ROUTE cancellation")

            after = tree_fingerprint(root)
            assert after == before
            assert first.read_bytes() == b"issue103 synthetic alpha scan"
            assert selected.read_bytes() == b"issue103 synthetic beta scan"
            assert unsupported.read_text(encoding="utf-8") == "not a routable scan"
            assert not any(scans_source_dir(root).iterdir())
            assert not any(routing_review_dir(root).iterdir())
            stage("browse/select/cancel workspace nonmutation")

        print(
            "Issue #103 shared installed-wheel scan-inbox acceptance: PASS",
            flush=True,
        )
        """
    )


def smoke(concord_wheel: Path, core_wheel: Path) -> None:
    """Exercise Issue #103 using only isolated installed wheel imports."""
    if not concord_wheel.is_file():
        raise FileNotFoundError(concord_wheel)
    if not core_wheel.is_file():
        raise FileNotFoundError(core_wheel)
    core_sha = _sha256(core_wheel)
    if core_sha != EXPECTED_CORE_SHA256:
        raise RuntimeError(
            "Issue #103 requires the exact released Core 0.6.3 qualification wheel."
        )

    with tempfile.TemporaryDirectory(prefix="concord-issue103-wheel-") as raw:
        work = Path(raw)
        env_root = work / "venv"
        venv.EnvBuilder(with_pip=True).create(env_root)
        python = _python(env_root)
        _run([str(python), "-m", "pip", "install", str(core_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "install", str(concord_wheel.resolve())], work)
        _run([str(python), "-m", "pip", "check"], work)

        smoke_path = work / "issue103_installed_acceptance.py"
        smoke_path.write_text(_smoke_code(), encoding="utf-8")
        _run([str(python), "-I", str(smoke_path)], work)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("concord_wheel", type=Path)
    parser.add_argument("core_wheel", type=Path)
    args = parser.parse_args()
    smoke(args.concord_wheel, args.core_wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
