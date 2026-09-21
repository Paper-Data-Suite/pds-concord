from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from pds_core.scan_routes import scans_inbox_dir

import concord.menu_scan as menu_scan


def test_scan_inbox_sources_uses_core_shared_inbox_and_does_not_create(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    expected = scans_inbox_dir(workspace)

    inbox, sources = menu_scan._scan_inbox_sources(workspace)

    assert inbox == expected
    assert sources == ()
    assert not expected.exists()


def test_scan_inbox_sources_filters_supported_top_level_regular_files(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)

    supported = (
        inbox / "A.PDF",
        inbox / "b.png",
        inbox / "c.JPG",
        inbox / "d.jpeg",
        inbox / "e.TIF",
        inbox / "f.tiff",
    )
    for path in supported:
        path.write_bytes(b"synthetic scan")

    (inbox / "ignore.txt").write_text("not a scan", encoding="utf-8")
    (inbox / "ignore.csv").write_text("not a scan", encoding="utf-8")
    nested = inbox / "nested"
    nested.mkdir()
    (nested / "nested.pdf").write_bytes(b"nested scan")

    resolved_inbox, sources = menu_scan._scan_inbox_sources(workspace)

    assert resolved_inbox == inbox
    assert sources == supported


def test_scan_inbox_sources_sorts_case_insensitively_with_stable_tiebreaker(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    for name in ("scan-c.pdf", "Scan-B.pdf", "scan-a.pdf", "alpha.PDF"):
        (inbox / name).write_bytes(name.encode("utf-8"))

    _, sources = menu_scan._scan_inbox_sources(workspace)

    assert tuple(path.name for path in sources) == (
        "alpha.PDF",
        "scan-a.pdf",
        "Scan-B.pdf",
        "scan-c.pdf",
    )


def test_scan_inbox_sources_does_not_offer_symlinked_file(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    backing = tmp_path / "backing.pdf"
    backing.write_bytes(b"synthetic scan")
    linked = inbox / "linked.pdf"
    try:
        linked.symlink_to(backing)
    except OSError as error:
        pytest.skip(f"filesystem cannot create scan symlink: {error}")

    _, sources = menu_scan._scan_inbox_sources(workspace)

    assert sources == ()


def test_scan_inbox_sources_rejects_non_directory_inbox(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    inbox = scans_inbox_dir(workspace)
    inbox.write_bytes(b"not a directory")

    with pytest.raises(
        NotADirectoryError,
        match="Shared scan inbox is not a directory",
    ):
        menu_scan._scan_inbox_sources(workspace)


def test_scan_inbox_sources_is_read_only_for_existing_files(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    first = inbox / "first.pdf"
    second = inbox / "second.png"
    first.write_bytes(b"first bytes")
    second.write_bytes(b"second bytes")
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (first, second)
    }

    _, sources = menu_scan._scan_inbox_sources(workspace)

    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (first, second)
    }
    assert sources == (first, second)
    assert after == before

def _patch_scan_browser_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menu_scan, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_scan, "pause_for_user", lambda *args, **kwargs: None)


def test_choose_route_sources_selects_exact_displayed_inbox_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    first = inbox / "alpha.pdf"
    second = inbox / "beta.pdf"
    first.write_bytes(b"alpha")
    second.write_bytes(b"beta")
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=True, is_dir=True),
    )
    _patch_scan_browser_ui(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")

    selected = menu_scan._choose_route_sources()

    assert selected == (second,)


def test_choose_route_sources_refreshes_current_inbox_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    scan = inbox / "new.pdf"
    calls = 0

    def discover(_root: Path) -> tuple[Path, tuple[Path, ...]]:
        nonlocal calls
        calls += 1
        return (inbox, ()) if calls == 1 else (inbox, (scan,))

    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    monkeypatch.setattr(menu_scan, "_scan_inbox_sources", discover)
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["r", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    selected = menu_scan._choose_route_sources()

    assert selected == (scan,)
    assert calls == 2
    assert not workspace.exists()


def test_choose_route_sources_pages_more_than_ten_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    scans = tuple(inbox / f"scan-{index:02d}.pdf" for index in range(12))
    for scan in scans:
        scan.write_bytes(scan.name.encode("utf-8"))
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=True, is_dir=True),
    )
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["n", "2"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    selected = menu_scan._choose_route_sources()

    assert selected == (scans[11],)


def test_choose_route_sources_absent_workspace_can_use_custom_path_without_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "missing-workspace"
    custom = tmp_path / "external.pdf"
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["c", str(custom)])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    selected = menu_scan._choose_route_sources()

    assert selected == (custom,)
    assert not workspace.exists()


def test_choose_route_sources_custom_path_preserves_multiple_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    first = tmp_path / "one.pdf"
    second = tmp_path / "two"
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["c", f"{first}; {second}"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    selected = menu_scan._choose_route_sources()

    assert selected == (first, second)
    assert not workspace.exists()


def test_route_selection_cancelled_before_route_service_is_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected.pdf"
    routed: list[tuple[Path, ...]] = []
    monkeypatch.setattr(
        menu_scan,
        "_choose_route_sources",
        lambda: (selected,),
    )
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        menu_scan,
        "route_scan_sources",
        lambda sources: routed.append(tuple(sources)),
    )

    menu_scan._route()

    assert routed == []


def test_route_confirmed_selection_delegates_exact_sources_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected.pdf"
    routed: list[tuple[Path, ...]] = []
    shown: list[tuple[str, tuple[str, ...]]] = []
    result = SimpleNamespace(
        sources=(
            SimpleNamespace(
                source_path=selected,
                source_error=None,
            ),
        ),
        dispatched_count=2,
        failure_count=1,
    )
    monkeypatch.setattr(
        menu_scan,
        "_choose_route_sources",
        lambda: (selected,),
    )
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: True)

    def route(sources: tuple[Path, ...]) -> object:
        routed.append(tuple(sources))
        return result

    monkeypatch.setattr(menu_scan, "route_scan_sources", route)
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan._route()

    assert routed == [(selected,)]
    assert shown == [
        (
            "Scan Routing Complete",
            (
                "Sources: 1",
                "Dispatched: 2",
                "Review required: 1",
            ),
        )
    ]

def test_route_source_error_is_reported_truthfully(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "missing.pdf"
    shown: list[tuple[str, tuple[str, ...]]] = []
    result = SimpleNamespace(
        sources=(
            SimpleNamespace(
                source_path=selected,
                source_error="scan source must be a regular non-symlink file",
            ),
        ),
        dispatched_count=0,
        failure_count=0,
    )
    monkeypatch.setattr(menu_scan, "_choose_route_sources", lambda: (selected,))
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: True)
    monkeypatch.setattr(menu_scan, "route_scan_sources", lambda _sources: result)
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan._route()

    assert shown[0][0] == "Scan Routing Completed with Source Errors"
    assert "Source errors: 1" in shown[0][1]
    assert str(selected) in "\n".join(shown[0][1])
    assert "regular non-symlink file" in "\n".join(shown[0][1])


def test_disappeared_selected_source_is_never_substituted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected.pdf"
    replacement = tmp_path / "replacement.pdf"
    selected.write_bytes(b"selected")
    replacement.write_bytes(b"replacement")
    routed: list[tuple[Path, ...]] = []
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu_scan, "_choose_route_sources", lambda: (selected,))
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: True)

    def route(sources: tuple[Path, ...]) -> object:
        routed.append(tuple(sources))
        selected.unlink()
        return SimpleNamespace(
            sources=(
                SimpleNamespace(
                    source_path=selected,
                    source_error="scan source must be a regular non-symlink file",
                ),
            ),
            dispatched_count=0,
            failure_count=0,
        )

    monkeypatch.setattr(menu_scan, "route_scan_sources", route)
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan._route()

    assert routed == [(selected,)]
    assert replacement not in routed[0]
    assert shown[0][0] == "Scan Routing Completed with Source Errors"


def test_route_result_preserves_success_summary_without_source_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = tmp_path / "selected.pdf"
    shown: list[tuple[str, tuple[str, ...]]] = []
    result = SimpleNamespace(
        sources=(SimpleNamespace(source_path=selected, source_error=None),),
        dispatched_count=3,
        failure_count=1,
    )
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan._show_scan_batch_result(result)

    assert shown == [
        (
            "Scan Routing Complete",
            (
                "Sources: 1",
                "Dispatched: 3",
                "Review required: 1",
            ),
        )
    ]


def test_choose_route_sources_help_returns_to_same_browser(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    scan = inbox / "teacher.pdf"
    scan.write_bytes(b"scan")
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=True, is_dir=True),
    )
    _patch_scan_browser_ui(monkeypatch)
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    values = iter(["h", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))

    selected = menu_scan._choose_route_sources()

    assert selected == (scan,)
    assert shown[0][0] == "Route Scans Help"
    help_text = "\n".join(shown[0][1])
    assert "shared Paper Data Suite inbox" in help_text
    assert "Custom Path" in help_text
    assert "do not route or modify" in help_text


def test_choose_route_sources_back_returns_to_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")

    with pytest.raises(menu_scan.CancelMenuAction):
        menu_scan._choose_route_sources()

    assert not workspace.exists()


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        ("m", menu_scan.ReturnToMainMenu),
        ("q", menu_scan.QuitPDS),
    ),
)
def test_choose_route_sources_main_and_quit_unwind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    raw: str,
    expected: type[Exception],
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda _prompt="": raw)

    with pytest.raises(expected):
        menu_scan._choose_route_sources()

    assert not workspace.exists()


@pytest.mark.parametrize("error_type", (KeyboardInterrupt, EOFError))
def test_choose_route_sources_interrupts_unwind(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[BaseException],
) -> None:
    workspace = tmp_path / "workspace"
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)

    def interrupt(_prompt: str = "") -> str:
        raise error_type

    monkeypatch.setattr("builtins.input", interrupt)

    with pytest.raises(error_type):
        menu_scan._choose_route_sources()

    assert not workspace.exists()


def test_scan_routing_menu_reports_inaccessible_inbox_as_controlled_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shown: list[tuple[str, tuple[str, ...]]] = []
    inputs = iter(["1", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(menu_scan, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_scan, "pause_for_user", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        menu_scan,
        "_choose_route_sources",
        lambda: (_ for _ in ()).throw(PermissionError("synthetic inbox denial")),
    )
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )

    menu_scan.launch_scan_routing_menu()

    assert shown == [
        ("Scan Routing Error", ("synthetic inbox denial",)),
    ]


def test_browse_select_cancel_preserves_inbox_bytes_and_names(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    first = inbox / "first.pdf"
    second = inbox / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    before = {path.name: path.read_bytes() for path in sorted(inbox.iterdir())}
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=True, is_dir=True),
    )
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["r", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        menu_scan,
        "route_scan_sources",
        lambda _sources: pytest.fail("routing service must not be called"),
    )

    menu_scan._route()

    after = {path.name: path.read_bytes() for path in sorted(inbox.iterdir())}
    assert after == before


def test_custom_directory_reaches_existing_routing_service_after_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    directory = tmp_path / "external-scans"
    directory.mkdir()
    routed: list[tuple[Path, ...]] = []
    monkeypatch.setattr(
        menu_scan,
        "inspect_workspace_root",
        lambda: SimpleNamespace(root=workspace, exists=False, is_dir=False),
    )
    _patch_scan_browser_ui(monkeypatch)
    values = iter(["c", str(directory)])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *args, **kwargs: True)

    def route(sources: tuple[Path, ...]) -> object:
        routed.append(tuple(sources))
        return SimpleNamespace(
            sources=(),
            dispatched_count=0,
            failure_count=0,
        )

    monkeypatch.setattr(menu_scan, "route_scan_sources", route)
    monkeypatch.setattr(menu_scan, "show_result", lambda *args, **kwargs: None)

    menu_scan._route()

    assert routed == [(directory,)]
