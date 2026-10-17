"""Focused teacher presentation tests for issue #134 Slice 3A."""

from __future__ import annotations

from types import SimpleNamespace as Record

import pytest

from concord import menu_packet, menu_packet_generation, menu_publication, menu_template
from concord.menu_teacher_history import (
    distinguish_equal_labels,
    teacher_planned_date,
    teacher_recorded_instant,
    teacher_version_line,
)


def test_date_and_time_are_distinct_and_offset_aware() -> None:
    assert teacher_planned_date('2026-10-12') == 'Planned Oct 12, 2026'
    assert teacher_planned_date(None) == 'Planned date not recorded'
    assert teacher_planned_date('2026-99-99') == 'Planned date unavailable'
    assert '2026' in teacher_recorded_instant(
        '2026-10-15T18:00:00+00:00', kind='Created'
    )
    assert teacher_recorded_instant(
        '2026-10-15T18:00:00', kind='Created'
    ) == 'Created time zone not recorded'


def test_identical_labels_are_explicitly_nonchronological() -> None:
    rows = distinguish_equal_labels(('Same', 'Other', 'Same'), noun='copy')
    assert rows[0].endswith('copy 1 of 2 (display order, not chronological)')
    assert rows[1] == 'Other'
    assert rows[2].endswith('copy 2 of 2 (display order, not chronological)')


def test_library_picker_uses_names_and_currentness_not_ids() -> None:
    template = Record(
        name='Peer feedback', status='active', template_id='secret-template-id',
        current_template_version_id='secret-version-id',
    )
    packet = Record(
        name='Seminar packet', status='active',
        packet_definition_id='secret-packet-id',
        current_packet_version_id=None,
    )
    assert 'Peer feedback' in menu_template._summary_label(template)
    assert 'Current version selected' in menu_template._summary_label(template)
    assert 'secret' not in menu_template._summary_label(template)
    assert 'No current version selected' in menu_packet._summary_label(packet)
    assert 'secret' not in menu_packet._summary_label(packet)
    assert teacher_version_line('Draft 1', 3, 'retired') == (
        'Revision 3: Draft 1 [retired]'
    )


def test_generation_picker_distinguishes_repeated_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = Record(
        generation_id='secret-run-a', packet_name='Discussion',
        session_label='Period 1', instance_count=2, page_count=4,
        routes_pending_count=0, planned_count=0, failed_count=0,
        cancelled_count=0, generated_count=2, rendering_count=0,
        generation_date='2026-10-12',
        created_at='2026-10-12T20:00:00+00:00',
    )
    second = Record(**{**vars(first), 'generation_id': 'secret-run-b'})
    monkeypatch.setattr(
        menu_packet_generation, 'list_packet_generations', lambda *_: (first, second)
    )
    captured: list[str] = []

    def choose(
        _title: str, items: object, labels: tuple[str, ...], **_: object
    ) -> object:
        captured.extend(labels)
        return first

    monkeypatch.setattr(menu_packet_generation, 'select_one', choose)
    activity = Record(class_id='c1', activity_id='a1')
    assert menu_packet_generation._choose_generation(activity, title='Pick') is first
    assert len(captured) == 2
    assert all('Planned Oct 12, 2026' in item for item in captured)
    assert all('Created' in item for item in captured)
    assert all('secret-' not in item for item in captured)
    assert 'not chronological' in captured[0]


def test_publication_history_is_head_aware_and_hides_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = Record(publication_id='secret-id-1', record_set_revision=1)
    second = Record(publication_id='secret-id-2', record_set_revision=2)
    state = Record(
        producer_head=Record(revision=2), core_head=second,
        core_head_withdrawal=False, current_selectable_publication=second,
        withdrawals=(Record(publication_id='secret-id-1'),),
        publications=(first, second), catalog_available=True, catalog_rows=(1,),
    )
    monkeypatch.setattr(menu_publication, '_root', lambda: None)
    monkeypatch.setattr(
        menu_publication, 'load_concord_publication_series_status',
        lambda *_args, **_kwargs: state,
    )
    shown: list[str] = []
    monkeypatch.setattr(
        menu_publication, 'show_result',
        lambda _title, lines: shown.extend(lines),
    )
    menu_publication._publication_status(
        Record(class_id='c1', activity_id='a1', title='Discussion')
    )
    assert 'Revision 1: withdrawn' in shown
    assert 'Revision 2: current selectable' in shown
    assert 'secret-' not in '\n'.join(shown)
