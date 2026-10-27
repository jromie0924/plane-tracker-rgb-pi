import pytest
from decimal import Decimal
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.trackerLog import TrackerLog, _floats_to_decimal
from services.flightLogic import FlightLogic

NOW_MS = 1_000_000_000
TTL_HOURS = 168
EXPIRES_AT = int(NOW_MS / 1000) + TTL_HOURS * 3600


@pytest.fixture(autouse=True)
def reset_singleton():
    TrackerLog._instance = None
    FlightLogic._instance = None
    # TrackerLog builds a FlightLogic, whose GeoService would otherwise call AWS for the location.
    with patch('services.flightLogic.GeoService'):
        yield
    TrackerLog._instance = None
    FlightLogic._instance = None


@pytest.fixture
def mock_config():
    with patch('services.trackerLog.config') as mc:
        mc.APP_NAME = 'test_app'
        mc.TRACKER_LOG_TTL_HOURS = TTL_HOURS
        mc.AWS_REGION = 'us-east-2'
        yield mc


@pytest.fixture
def mock_time():
    with patch('services.trackerLog.TimeUtils') as mt:
        mt.current_time_milli.return_value = NOW_MS
        yield mt


@pytest.fixture
def mock_runtime():
    with patch('services.trackerLog.RuntimeService') as mr:
        mr.return_value.aws_access_key_id = 'fake_key'
        mr.return_value.aws_secret_access_key = 'fake_secret'
        yield mr


@pytest.fixture
def mock_boto3():
    with patch('services.trackerLog.boto3') as mb:
        yield mb


@pytest.fixture
def tracker(mock_config, mock_runtime, mock_boto3):
    t = TrackerLog()
    # Keep tests off the real route database; route tests set their own.
    with patch.object(t._adsb_service, 'get_routeset', return_value={}):
        yield t


def valid_entry(**overrides):
    # Has every field FlightLogic.validate_flight requires
    entry = {'flight': 'UAL123', 'hex': 'abc', 'lat': 41.9, 'lon': -87.7, 'alt_baro': 12000, 't': 'B738'}
    entry.update(overrides)
    return entry


def stop(icao):
    return {'airport_icao': icao, 'airport_iata': icao[1:], 'airport_lat': 0.0, 'airport_lon': 0.0}


ORD, JFK, DEN = stop('KORD'), stop('KJFK'), stop('KDEN')


# --- Singleton ---

def test_singleton_returns_same_instance(mock_config, mock_runtime, mock_boto3):
    a = TrackerLog()
    b = TrackerLog()
    assert a is b


# --- __init__ ---

def test_init_creates_dynamodb_resource_with_credentials(mock_config, mock_runtime, mock_boto3):
    TrackerLog()
    mock_boto3.resource.assert_called_once_with(
        'dynamodb',
        aws_access_key_id='fake_key',
        aws_secret_access_key='fake_secret',
        region_name='us-east-2',
    )


def test_init_table_assigned_from_boto3(tracker, mock_boto3):
    assert tracker._table is mock_boto3.resource.return_value.Table.return_value


# --- update_log: callsign extraction ---

def test_update_log_uses_flight_field(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'DAL456', 'hex': 'abc'}])
    assert mock_write.call_args[0][0][0]['callsign'] == 'DAL456'


def test_update_log_falls_back_to_r_field(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'r': 'N12345', 'hex': 'abc'}])
    assert mock_write.call_args[0][0][0]['callsign'] == 'N12345'


def test_update_log_prefers_flight_over_r(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'r': 'N12345', 'hex': 'a'}])
    assert mock_write.call_args[0][0][0]['callsign'] == 'AAL1'


def test_update_log_strips_whitespace_from_callsign(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': '  UAL789  ', 'hex': 'abc'}])
    assert mock_write.call_args[0][0][0]['callsign'] == 'UAL789'


# --- update_log: timestamp and TTL ---

def test_update_log_stamps_current_timestamp(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'SWA001', 'hex': 'def'}])
    assert mock_write.call_args[0][0][0]['timestamp'] == NOW_MS


def test_update_log_sets_expires_at_in_epoch_seconds(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    assert mock_write.call_args[0][0][0]['expires_at'] == EXPIRES_AT


def test_update_log_expires_at_is_seconds_not_milliseconds(tracker, mock_time):
    # expires_at must be epoch seconds — if it were ms it would be ~1000x larger than NOW_MS/1000
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    assert mock_write.call_args[0][0][0]['expires_at'] < NOW_MS


def test_update_log_sets_readable_timestamp(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    assert 'timestamp_readable' in mock_write.call_args[0][0][0]


def test_update_log_same_expires_at_for_all_entries_in_batch(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([
            {'flight': 'AAL1', 'hex': 'a'},
            {'flight': 'UAL2', 'hex': 'b'},
        ])
    items = mock_write.call_args[0][0]
    assert items[0]['expires_at'] == items[1]['expires_at']


# --- update_log: invalid entries ---

def test_update_log_skips_entry_with_no_identifier(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'hex': 'xyz'}])
    assert mock_write.call_args[0][0] == []


def test_update_log_logs_warning_for_missing_identifier(tracker, mock_time):
    with patch.object(tracker, '_batch_write'):
        with patch.object(tracker.logger, 'warning') as mock_warn:
            tracker.update_log([{'hex': 'xyz'}])
    mock_warn.assert_called_once()


def test_update_log_skips_entry_with_none_identifier(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': None, 'r': None, 'hex': 'xyz'}])
    assert mock_write.call_args[0][0] == []


def test_update_log_logs_warning_for_none_identifier(tracker, mock_time):
    with patch.object(tracker, '_batch_write'):
        with patch.object(tracker.logger, 'warning') as mock_warn:
            tracker.update_log([{'flight': None, 'r': None, 'hex': 'xyz'}])
    mock_warn.assert_called_once()


def test_update_log_skips_entry_with_empty_string_flight_and_r(tracker, mock_time):
    # Regression: "" or "" evaluates to "" in Python — no AttributeError, so the original
    # `except AttributeError` guard missed this case and wrote an empty callsign to DynamoDB.
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': '', 'r': '', 'hex': 'xyz'}])
    assert mock_write.call_args[0][0] == []


def test_update_log_logs_warning_for_empty_string_identifiers(tracker, mock_time):
    with patch.object(tracker, '_batch_write'):
        with patch.object(tracker.logger, 'warning') as mock_warn:
            tracker.update_log([{'flight': '', 'r': '', 'hex': 'xyz'}])
    mock_warn.assert_called_once()


def test_update_log_skips_entry_with_empty_flight_and_no_r(tracker, mock_time):
    # "" or None → None → AttributeError on strip(), but worth being explicit
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': '', 'hex': 'xyz'}])
    assert mock_write.call_args[0][0] == []


def test_update_log_skips_entry_with_whitespace_only_flight_and_empty_r(tracker, mock_time):
    # "  " is truthy so or short-circuits, strip() yields "" — must still be rejected
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': '   ', 'r': '', 'hex': 'xyz'}])
    assert mock_write.call_args[0][0] == []


def test_update_log_processes_valid_entries_after_invalid(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'hex': 'bad'}, {'flight': 'AAL1', 'hex': 'good'}])
    items = mock_write.call_args[0][0]
    assert len(items) == 1
    assert items[0]['callsign'] == 'AAL1'


# --- update_log: float conversion ---

def test_update_log_converts_float_fields_to_decimal(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'lat': 41.85, 'lon': -87.65}])
    item = mock_write.call_args[0][0][0]
    assert isinstance(item['lat'], Decimal)
    assert isinstance(item['lon'], Decimal)


def test_update_log_preserves_int_fields(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'alt_baro': 35000, 'hex': 'abc'}])
    item = mock_write.call_args[0][0][0]
    assert item['alt_baro'] == 35000
    assert isinstance(item['alt_baro'], int)


# --- update_log: batch ---

def test_update_log_passes_all_valid_entries_to_batch_write(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([
            {'flight': 'AAL1', 'hex': 'a'},
            {'flight': 'UAL2', 'hex': 'b'},
            {'flight': 'DAL3', 'hex': 'c'},
        ])
    assert len(mock_write.call_args[0][0]) == 3


def test_update_log_calls_batch_write_once_per_invocation(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}, {'flight': 'UAL2', 'hex': 'b'}])
    mock_write.assert_called_once()


# --- update_log: origin and destination ---

def written_items(tracker, entries, routes, analyze=None):
    # Runs update_log with the given routeset and returns the items it would write.
    # analyze stands in for FlightLogic.analyze_route when given.
    tracker._adsb_service.get_routeset.return_value = routes
    with patch.object(tracker, '_batch_write') as mock_write:
        if analyze is None:
            tracker.update_log(entries)
        else:
            with patch.object(tracker._flight_logic, 'analyze_route', side_effect=analyze):
                tracker.update_log(entries)
    return mock_write.call_args[0][0]


def route_of(item):
    return item['origin'], item['destination']


def test_route_fields_are_origin_and_destination_icao(tracker, mock_time):
    items = written_items(tracker, [valid_entry()], {'UAL123': [ORD, JFK]},
                          analyze=lambda flight, stops: {'origin': ORD, 'destination': JFK})
    assert route_of(items[0]) == ('KORD', 'KJFK')


def test_route_fields_use_the_leg_analyze_route_picks(tracker, mock_time):
    # Multi-stop route: the fields hold the current leg, not the first and last stops
    items = written_items(tracker, [valid_entry()], {'UAL123': [DEN, ORD, JFK]},
                          analyze=lambda flight, stops: {'origin': ORD, 'destination': JFK})
    assert route_of(items[0]) == ('KORD', 'KJFK')


def test_route_fields_empty_when_callsign_not_in_routeset(tracker, mock_time):
    items = written_items(tracker, [valid_entry()], {})
    assert route_of(items[0]) == ('', '')


def test_route_fields_empty_when_route_not_plausible(tracker, mock_time):
    items = written_items(tracker, [valid_entry()], {'UAL123': [ORD, JFK]},
                          analyze=lambda flight, stops: None)
    assert route_of(items[0]) == ('', '')


def test_route_looked_up_by_stripped_callsign(tracker, mock_time):
    # readsb pads callsigns with spaces, while the route database doesn't
    items = written_items(tracker, [valid_entry(flight='UAL123  ')], {'UAL123': [ORD, JFK]},
                          analyze=lambda flight, stops: {'origin': ORD, 'destination': JFK})
    assert route_of(items[0]) == ('KORD', 'KJFK')


def test_route_analysis_skipped_for_entry_without_position(tracker, mock_time):
    entry = valid_entry()
    del entry['lat'], entry['lon']
    with patch.object(tracker._flight_logic, 'analyze_route') as mock_analyze:
        items = written_items(tracker, [entry], {'UAL123': [ORD, JFK]})
    mock_analyze.assert_not_called()
    assert route_of(items[0]) == ('', '')


def test_entry_without_position_is_still_logged(tracker, mock_time):
    items = written_items(tracker, [{'flight': 'UAL123', 'hex': 'abc'}], {'UAL123': [ORD, JFK]})
    assert len(items) == 1
    assert items[0]['callsign'] == 'UAL123'


def test_route_analysis_gets_each_flights_own_stops(tracker, mock_time):
    ual, dal = valid_entry(flight='UAL123', hex='a'), valid_entry(flight='DAL5', hex='b')
    with patch.object(tracker._flight_logic, 'analyze_route', return_value=None) as mock_analyze:
        written_items(tracker, [ual, dal], {'UAL123': [ORD, JFK], 'DAL5': [DEN, ORD]})
    mock_analyze.assert_any_call(flight=ual, stops=[ORD, JFK])
    mock_analyze.assert_any_call(flight=dal, stops=[DEN, ORD])


def test_routes_looked_up_once_per_batch(tracker, mock_time):
    written_items(tracker, [valid_entry(hex='a'), valid_entry(flight='DAL5', hex='b')], {})
    tracker._adsb_service.get_routeset.assert_called_once()


def test_route_fields_empty_when_route_analysis_raises(tracker, mock_time):
    def boom(flight, stops):
        raise ValueError('bad route data')
    items = written_items(tracker, [valid_entry()], {'UAL123': [ORD, JFK]}, analyze=boom)
    assert route_of(items[0]) == ('', '')


def test_route_fields_not_half_filled_when_destination_is_bad(tracker, mock_time):
    # origin reads fine, then destination fails: neither field should be kept
    items = written_items(tracker, [valid_entry()], {'UAL123': [ORD, JFK]},
                          analyze=lambda flight, stops: {'origin': ORD, 'destination': {}})
    assert route_of(items[0]) == ('', '')


def test_route_analysis_error_is_logged(tracker, mock_time):
    def boom(flight, stops):
        raise ValueError('bad route data')
    with patch.object(tracker.logger, 'error') as mock_error:
        written_items(tracker, [valid_entry()], {'UAL123': [ORD, JFK]}, analyze=boom)
    mock_error.assert_called_once()


def test_route_analysis_error_does_not_drop_other_entries(tracker, mock_time):
    def analyze(flight, stops):
        if flight['flight'] == 'UAL123':
            raise ValueError('bad route data')
        return {'origin': DEN, 'destination': ORD}
    items = written_items(tracker,
                          [valid_entry(flight='UAL123', hex='a'), valid_entry(flight='DAL5', hex='b')],
                          {'UAL123': [ORD, JFK], 'DAL5': [DEN, ORD]},
                          analyze=analyze)
    assert [route_of(i) for i in items] == [('', ''), ('KDEN', 'KORD')]


# --- _batch_write ---

def test_batch_write_calls_put_item_for_each_entry(tracker):
    items = [{'callsign': 'AAL1', 'timestamp': 1000}, {'callsign': 'UAL2', 'timestamp': 2000}]
    tracker._batch_write(items)
    batch = tracker._table.batch_writer.return_value.__enter__.return_value
    assert batch.put_item.call_count == 2


def test_batch_write_passes_correct_item_to_put_item(tracker):
    item = {'callsign': 'AAL1', 'timestamp': 1000}
    tracker._batch_write([item])
    batch = tracker._table.batch_writer.return_value.__enter__.return_value
    batch.put_item.assert_called_once_with(Item=item)


def test_batch_write_logs_error_on_exception(tracker):
    tracker._table.batch_writer.side_effect = Exception('connection error')
    with patch.object(tracker.logger, 'error') as mock_error:
        tracker._batch_write([{'callsign': 'AAL1'}])
    mock_error.assert_called_once()


def test_batch_write_does_not_raise_on_exception(tracker):
    tracker._table.batch_writer.side_effect = Exception('connection error')
    tracker._batch_write([{'callsign': 'AAL1'}])  # must not propagate


# --- _floats_to_decimal ---

def test_floats_to_decimal_converts_float():
    assert _floats_to_decimal(1.5) == Decimal('1.5')


def test_floats_to_decimal_leaves_int_unchanged():
    assert _floats_to_decimal(42) == 42


def test_floats_to_decimal_leaves_string_unchanged():
    assert _floats_to_decimal('hello') == 'hello'


def test_floats_to_decimal_leaves_none_unchanged():
    assert _floats_to_decimal(None) is None


def test_floats_to_decimal_converts_float_in_dict():
    result = _floats_to_decimal({'lat': 41.85, 'name': 'ORD'})
    assert isinstance(result['lat'], Decimal)
    assert result['name'] == 'ORD'


def test_floats_to_decimal_converts_float_in_list():
    result = _floats_to_decimal([1.5, 2, 'hello'])
    assert isinstance(result[0], Decimal)
    assert result[1] == 2
    assert result[2] == 'hello'


def test_floats_to_decimal_handles_nested_dict():
    result = _floats_to_decimal({'outer': {'inner': 3.14}})
    assert isinstance(result['outer']['inner'], Decimal)


def test_floats_to_decimal_leaves_bool_unchanged():
    assert _floats_to_decimal(True) is True
    assert _floats_to_decimal(False) is False


def test_floats_to_decimal_leaves_decimal_unchanged():
    d = Decimal('3.14')
    assert _floats_to_decimal(d) == d
    assert isinstance(_floats_to_decimal(d), Decimal)


def test_floats_to_decimal_handles_list_in_dict():
    result = _floats_to_decimal({'speeds': [1.5, 2.5]})
    assert isinstance(result['speeds'][0], Decimal)
    assert isinstance(result['speeds'][1], Decimal)


# --- feature flag: _tracker_log_active initialization ---

def test_tracker_log_active_on_raspberry_pi(mock_config, mock_runtime, mock_boto3):
    mock_config.TRACKER_LOG_EMU_FLAG = False
    with patch('services.trackerLog.IS_RASPBERRY_PI', True):
        t = TrackerLog()
    assert t._tracker_log_active is True


def test_tracker_log_active_in_emu_when_flag_enabled(mock_config, mock_runtime, mock_boto3):
    mock_config.TRACKER_LOG_EMU_FLAG = True
    with patch('services.trackerLog.IS_RASPBERRY_PI', False):
        t = TrackerLog()
    assert t._tracker_log_active is True


def test_tracker_log_inactive_in_emu_when_flag_disabled(mock_config, mock_runtime, mock_boto3):
    mock_config.TRACKER_LOG_EMU_FLAG = False
    with patch('services.trackerLog.IS_RASPBERRY_PI', False):
        t = TrackerLog()
    assert t._tracker_log_active is False


def test_tracker_log_active_on_pi_even_when_flag_disabled(mock_config, mock_runtime, mock_boto3):
    mock_config.TRACKER_LOG_EMU_FLAG = False
    with patch('services.trackerLog.IS_RASPBERRY_PI', True):
        t = TrackerLog()
    assert t._tracker_log_active is True


# --- update_log: inactive feature flag ---

def test_update_log_does_nothing_when_inactive(tracker, mock_time):
    tracker._tracker_log_active = False
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    mock_write.assert_not_called()


def test_update_log_inactive_does_not_call_batch_write_even_with_multiple_entries(tracker, mock_time):
    tracker._tracker_log_active = False
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([
            {'flight': 'AAL1', 'hex': 'a'},
            {'flight': 'UAL2', 'hex': 'b'},
        ])
    mock_write.assert_not_called()


# --- update_log: empty list ---

def test_update_log_empty_list_calls_batch_write_with_empty_list(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([])
    mock_write.assert_called_once_with([])


# --- update_log: timestamp type ---

def test_update_log_timestamp_is_int(tracker, mock_time):
    with patch.object(tracker, '_batch_write') as mock_write:
        tracker.update_log([{'flight': 'AAL1', 'hex': 'a'}])
    assert isinstance(mock_write.call_args[0][0][0]['timestamp'], int)


# --- _batch_write: empty list ---

def test_batch_write_empty_list_calls_no_put_item(tracker):
    tracker._batch_write([])
    batch = tracker._table.batch_writer.return_value.__enter__.return_value
    batch.put_item.assert_not_called()
