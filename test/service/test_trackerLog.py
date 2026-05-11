import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.trackerLog import TrackerLog

NOW_MS = 1_000_000_000
TTL_HOURS = 168
SAVE_INTERVAL_MINUTES = 5
TTL_MS = TTL_HOURS * 60 * 60 * 1000
SAVE_INTERVAL_MS = SAVE_INTERVAL_MINUTES * 60 * 1000


@pytest.fixture(autouse=True)
def reset_singleton():
    TrackerLog._instance = None
    yield
    TrackerLog._instance = None


@pytest.fixture
def mock_config():
    with patch('services.trackerLog.config') as mc:
        mc.APP_NAME = 'test_app'
        mc.TRACKER_LOG_FILE = 'tracker_log/log.json'
        mc.TRACKER_LOG_TTL_HOURS = TTL_HOURS
        mc.TRACKER_LOG_SAVE_INTERVAL_MINUTES = SAVE_INTERVAL_MINUTES
        yield mc


@pytest.fixture
def mock_time():
    with patch('services.trackerLog.TimeUtils') as mt:
        mt.current_time_milli.return_value = NOW_MS
        yield mt


@pytest.fixture
def tracker(mock_config, mock_time):
    with patch.object(TrackerLog, '_load_file', return_value={}):
        with patch.object(TrackerLog, 'save_file', return_value=True):
            instance = TrackerLog()
    return instance


# --- Singleton ---

def test_singleton_returns_same_instance(mock_config, mock_time):
    with patch.object(TrackerLog, '_load_file', return_value={}):
        with patch.object(TrackerLog, 'save_file', return_value=True):
            a = TrackerLog()
            b = TrackerLog()
    assert a is b


# --- __init__ ---

def test_init_sets_last_save_time_to_current_time(tracker):
    assert tracker._last_save_time == NOW_MS


def test_init_loads_file_into_data(mock_config, mock_time):
    initial_data = {'AAL123': [{'flight': 'AAL123', 'timestamp': NOW_MS}]}
    with patch.object(TrackerLog, '_load_file', return_value=initial_data):
        with patch.object(TrackerLog, 'save_file', return_value=True):
            t = TrackerLog()
    assert t.data == initial_data


def test_init_cleanses_stale_entries_on_startup(mock_config, mock_time):
    stale_data = {'OLD': [{'flight': 'OLD', 'timestamp': NOW_MS - TTL_MS - 1}]}
    with patch.object(TrackerLog, '_load_file', return_value=stale_data):
        with patch.object(TrackerLog, 'save_file', return_value=True):
            t = TrackerLog()
    assert t.data['OLD'] == []


# --- _load_file ---

def test_load_file_returns_parsed_json(mock_config, mock_time):
    file_content = json.dumps({'UAL100': [{'flight': 'UAL100', 'timestamp': NOW_MS}]})
    with patch.object(TrackerLog, 'save_file', return_value=True):
        with patch('builtins.open', mock_open(read_data=file_content)):
            t = TrackerLog()
    assert 'UAL100' in t.data


def test_load_file_returns_empty_dict_when_file_missing(mock_config, mock_time):
    with patch.object(TrackerLog, 'save_file', return_value=True):
        with patch('builtins.open', side_effect=FileNotFoundError):
            t = TrackerLog()
    assert t.data == {}


# --- cleanse_log ---

def test_cleanse_log_removes_expired_entries(tracker, mock_time):
    tracker.data = {
        'FRESH': [{'flight': 'FRESH', 'timestamp': NOW_MS}],
        'STALE': [{'flight': 'STALE', 'timestamp': NOW_MS - TTL_MS - 1}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['FRESH']) == 1
    assert tracker.data['STALE'] == []


def test_cleanse_log_keeps_entries_within_ttl(tracker, mock_time):
    tracker.data = {'VALID': [{'flight': 'VALID', 'timestamp': NOW_MS - TTL_MS + 1000}]}
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['VALID']) == 1


def test_cleanse_log_removes_exactly_at_ttl_boundary(tracker, mock_time):
    tracker.data = {'EXACT': [{'flight': 'EXACT', 'timestamp': NOW_MS - TTL_MS}]}
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert tracker.data['EXACT'] == []


def test_cleanse_log_calls_save_file(tracker):
    with patch.object(tracker, 'save_file', return_value=True) as mock_save:
        tracker.cleanse_log()
    mock_save.assert_called_once()


def test_cleanse_log_leaves_empty_data_empty(tracker):
    tracker.data = {}
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert tracker.data == {}


def test_cleanse_log_handles_mix_of_fresh_and_stale(tracker, mock_time):
    tracker.data = {
        'A': [{'timestamp': NOW_MS}],
        'B': [{'timestamp': NOW_MS - TTL_MS - 1}],
        'C': [{'timestamp': NOW_MS - TTL_MS + 500}],
        'D': [{'timestamp': 0}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['A']) == 1
    assert tracker.data['B'] == []
    assert len(tracker.data['C']) == 1
    assert tracker.data['D'] == []


# --- update_log ---

def test_update_log_adds_entry_by_flight_callsign(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'DAL456', 'hex': 'abc'}])
    assert 'DAL456' in tracker.data


def test_update_log_falls_back_to_r_field(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'r': 'N12345', 'hex': 'abc'}])
    assert 'N12345' in tracker.data


def test_update_log_prefers_flight_over_r(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'r': 'N12345', 'hex': 'a'}])
    assert 'AAL1' in tracker.data
    assert 'N12345' not in tracker.data


def test_update_log_strips_whitespace_from_callsign(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': '  UAL789  ', 'hex': 'abc'}])
    assert 'UAL789' in tracker.data
    assert '  UAL789  ' not in tracker.data


def test_update_log_stamps_entries_with_current_timestamp(tracker, mock_time):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'SWA001', 'hex': 'def'}])
    assert tracker.data['SWA001'][0]['timestamp'] == NOW_MS


def test_update_log_skips_entry_with_no_identifier_and_logs_warning(tracker):
    with patch.object(tracker, 'cleanse_log'):
        with patch.object(tracker.logger, 'warning') as mock_warn:
            tracker.update_log([{'hex': 'xyz'}])
    assert len(tracker.data) == 0
    mock_warn.assert_called_once()


def test_update_log_skips_entry_with_none_identifier(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': None, 'r': None, 'hex': 'xyz'}])
    assert len(tracker.data) == 0


def test_update_log_processes_valid_entries_after_invalid_one(tracker):
    entries = [
        {'hex': 'bad'},
        {'flight': 'AAL1', 'hex': 'good'},
    ]
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log(entries)
    assert 'AAL1' in tracker.data
    assert len(tracker.data) == 1


def test_update_log_adds_multiple_entries(tracker):
    entries = [
        {'flight': 'AAL1', 'hex': 'a'},
        {'flight': 'UAL2', 'hex': 'b'},
        {'flight': 'DAL3', 'hex': 'c'},
    ]
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log(entries)
    assert tracker.data.keys() == {'AAL1', 'UAL2', 'DAL3'}


def test_update_log_appends_to_existing_callsign_entry(tracker):
    tracker.data = {'AAL1': [{'flight': 'AAL1', 'hex': 'old', 'timestamp': 0}]}
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'hex': 'new'}])
    assert len(tracker.data['AAL1']) == 2
    assert tracker.data['AAL1'][0]['hex'] == 'old'
    assert tracker.data['AAL1'][1]['hex'] == 'new'


def test_update_log_calls_cleanse_log(tracker):
    with patch.object(tracker, 'cleanse_log') as mock_cleanse:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    mock_cleanse.assert_called_once()


def test_update_log_calls_cleanse_log_even_with_all_invalid_entries(tracker):
    with patch.object(tracker, 'cleanse_log') as mock_cleanse:
        tracker.update_log([{'hex': 'bad'}])
    mock_cleanse.assert_called_once()


# --- save_file ---

def test_save_file_skips_write_when_within_interval(tracker, mock_time):
    tracker._last_save_time = NOW_MS
    with patch('builtins.open', mock_open()) as mocked_file:
        result = tracker.save_file()
    mocked_file.assert_not_called()
    assert result is True


def test_save_file_writes_when_interval_has_elapsed(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mocked_file:
            result = tracker.save_file()
    mocked_file.assert_called_once()
    assert result is True


def test_save_file_writes_to_correct_filepath(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mocked_file:
            tracker.save_file()
    mocked_file.assert_called_once_with('tracker_log/log.json', 'w')


def test_save_file_updates_last_save_time_after_write(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()):
            tracker.save_file()
    assert tracker._last_save_time == NOW_MS


def test_save_file_does_not_update_last_save_time_when_skipped(tracker, mock_time):
    tracker._last_save_time = NOW_MS
    with patch('builtins.open', mock_open()):
        tracker.save_file()
    assert tracker._last_save_time == NOW_MS


def test_save_file_creates_directory(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs') as mock_makedirs:
        with patch('builtins.open', mock_open()):
            tracker.save_file()
    mock_makedirs.assert_called_once_with('tracker_log', exist_ok=True)


def test_save_file_returns_false_on_write_exception(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs'):
        with patch('builtins.open', side_effect=OSError('disk full')):
            result = tracker.save_file()
    assert result is False


def test_save_file_logs_error_on_write_exception(tracker, mock_time):
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS - 1
    with patch('os.makedirs'):
        with patch('builtins.open', side_effect=OSError('disk full')):
            with patch.object(tracker.logger, 'error') as mock_error:
                tracker.save_file()
    mock_error.assert_called_once()


def test_save_file_does_not_update_last_save_time_on_exception(tracker, mock_time):
    original_time = NOW_MS - SAVE_INTERVAL_MS - 1
    tracker._last_save_time = original_time
    with patch('os.makedirs'):
        with patch('builtins.open', side_effect=OSError):
            tracker.save_file()
    assert tracker._last_save_time == original_time


def test_save_file_at_exact_interval_boundary_writes(tracker, mock_time):
    # condition is strict <, so elapsed == interval triggers a write
    tracker._last_save_time = NOW_MS - SAVE_INTERVAL_MS
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mocked_file:
            tracker.save_file()
    mocked_file.assert_called_once()


def test_save_file_overwrite_bypasses_interval_check(tracker, mock_time):
    tracker._last_save_time = NOW_MS  # would normally skip
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mocked_file:
            result = tracker.save_file(overwrite=True)
    mocked_file.assert_called_once()
    assert result is True


def test_save_file_overwrite_false_still_skips_within_interval(tracker, mock_time):
    tracker._last_save_time = NOW_MS
    with patch('builtins.open', mock_open()) as mocked_file:
        result = tracker.save_file(overwrite=False)
    mocked_file.assert_not_called()
    assert result is True


def test_save_file_overwrite_updates_last_save_time(tracker, mock_time):
    tracker._last_save_time = NOW_MS  # would normally skip
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()):
            tracker.save_file(overwrite=True)
    assert tracker._last_save_time == NOW_MS


def test_save_file_overwrite_returns_false_on_exception(tracker, mock_time):
    tracker._last_save_time = NOW_MS
    with patch('os.makedirs'):
        with patch('builtins.open', side_effect=OSError('disk full')):
            result = tracker.save_file(overwrite=True)
    assert result is False


# --- Multi-entry per callsign: update_log ---

def test_update_log_stores_entry_as_list(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    assert isinstance(tracker.data['AAL1'], list)
    assert len(tracker.data['AAL1']) == 1


def test_update_log_appends_second_entry_for_same_callsign(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'hex': 'first'}])
        tracker.update_log([{'flight': 'AAL1', 'hex': 'second'}])
    assert len(tracker.data['AAL1']) == 2


def test_update_log_preserves_earlier_entries_when_appending(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'hex': 'first'}])
        tracker.update_log([{'flight': 'AAL1', 'hex': 'second'}])
    hexes = [e['hex'] for e in tracker.data['AAL1']]
    assert 'first' in hexes
    assert 'second' in hexes


def test_update_log_accumulates_across_batch(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([
            {'flight': 'AAL1', 'hex': 'a'},
            {'flight': 'AAL1', 'hex': 'b'},
            {'flight': 'AAL1', 'hex': 'c'},
        ])
    assert len(tracker.data['AAL1']) == 3


def test_update_log_different_callsigns_stay_independent(tracker):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([
            {'flight': 'AAL1', 'hex': 'a'},
            {'flight': 'UAL2', 'hex': 'b'},
        ])
    assert len(tracker.data['AAL1']) == 1
    assert len(tracker.data['UAL2']) == 1


def test_update_log_stamps_timestamp_on_each_entry(tracker, mock_time):
    with patch.object(tracker, 'cleanse_log'):
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}, {'flight': 'AAL1', 'hex': 'b'}])
    for entry in tracker.data['AAL1']:
        assert entry['timestamp'] == NOW_MS


# --- Multi-entry per callsign: cleanse_log ---

def test_cleanse_log_removes_expired_entry_from_list(tracker, mock_time):
    tracker.data = {
        'AAL1': [{'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 1}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert tracker.data['AAL1'] == []


def test_cleanse_log_keeps_fresh_entry_in_list(tracker, mock_time):
    tracker.data = {
        'AAL1': [{'flight': 'AAL1', 'timestamp': NOW_MS}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1


def test_cleanse_log_keeps_entry_within_ttl(tracker, mock_time):
    tracker.data = {
        'AAL1': [{'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS + 1000}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1


def test_cleanse_log_removes_only_expired_from_mixed_list(tracker, mock_time):
    tracker.data = {
        'AAL1': [
            {'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 1},  # expired
            {'flight': 'AAL1', 'timestamp': NOW_MS},                 # fresh
        ]
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1
    assert tracker.data['AAL1'][0]['timestamp'] == NOW_MS


def test_cleanse_log_removes_multiple_adjacent_expired_entries(tracker, mock_time):
    # Catches the "pop while iterating" bug: popping index 0 shifts index 1 to
    # position 0, which enumerate then skips. Both expired entries must be gone.
    tracker.data = {
        'AAL1': [
            {'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 1},  # expired
            {'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 2},  # expired (adjacent)
            {'flight': 'AAL1', 'timestamp': NOW_MS},                 # fresh
        ]
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1
    assert tracker.data['AAL1'][0]['timestamp'] == NOW_MS


def test_cleanse_log_all_entries_expired_leaves_empty_list(tracker, mock_time):
    tracker.data = {
        'AAL1': [
            {'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 1},
            {'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS - 2},
        ]
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert tracker.data['AAL1'] == []


def test_cleanse_log_multiple_callsigns_cleansed_independently(tracker, mock_time):
    tracker.data = {
        'AAL1': [{'flight': 'AAL1', 'timestamp': NOW_MS}],
        'UAL2': [{'flight': 'UAL2', 'timestamp': NOW_MS - TTL_MS - 1}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1
    assert tracker.data['UAL2'] == []


def test_cleanse_log_expiry_uses_millisecond_ttl(tracker, mock_time):
    # TTL_MS = TTL_HOURS * 3600 * 1000. An entry 1ms inside the TTL must survive.
    # This catches the bug where the TTL check uses raw hours instead of ms.
    tracker.data = {
        'AAL1': [{'flight': 'AAL1', 'timestamp': NOW_MS - TTL_MS + 1}],
    }
    with patch.object(tracker, 'save_file', return_value=True):
        tracker.cleanse_log()
    assert len(tracker.data['AAL1']) == 1
