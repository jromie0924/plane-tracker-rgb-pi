import pytest
from unittest.mock import patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from services.ssmService import SsmService, GET_IP_URL

NOW = 1_000_000.0
UPDATE_FREQ_MINUTES = 15
WINDOW_SECONDS = UPDATE_FREQ_MINUTES * 60  # 900
PARAM_NAME = '/plane-tracker/api/allowed-cidrs'
REGION = 'us-east-2'


@pytest.fixture(autouse=True)
def reset_singleton():
    SsmService._instance = None
    yield
    SsmService._instance = None


@pytest.fixture
def mock_config():
    with patch('services.ssmService.config') as mc:
        mc.APP_NAME = 'test_app'
        mc.ALLOWED_IP_UPDATE_FREQUENCY_MINUTES = UPDATE_FREQ_MINUTES
        mc.AWS_REGION = REGION
        mc.SSM_API_ALLOWED_IP_NAME = PARAM_NAME
        yield mc


@pytest.fixture
def mock_runtime():
    with patch('services.ssmService.RuntimeService') as mr:
        mr.return_value.aws_access_key_id = 'fake_key'
        mr.return_value.aws_secret_access_key = 'fake_secret'
        yield mr


@pytest.fixture
def mock_boto3():
    with patch('services.ssmService.boto3') as mb:
        yield mb


@pytest.fixture
def mock_requests():
    with patch('services.ssmService.requests') as mr:
        mr.get.return_value.text = '203.0.113.7'
        yield mr


@pytest.fixture
def mock_datetime():
    with patch('services.ssmService.datetime') as md:
        md.now.return_value.timestamp.return_value = NOW
        yield md


@pytest.fixture
def service(mock_config, mock_runtime):
    return SsmService()


# --- Singleton / __init__ ---

def test_singleton_returns_same_instance(mock_config, mock_runtime):
    assert SsmService() is SsmService()


def test_init_sets_last_update_to_none(service):
    assert service._last_update is None


def test_init_loads_runtime_service(mock_config, mock_runtime):
    SsmService()
    mock_runtime.assert_called_once()


def test_init_runs_only_once(service):
    # __init__ is guarded by _initialized; a second construction must not reset state
    service._last_update = 12345.0
    SsmService()
    assert service._last_update == 12345.0


# --- _upload_to_ssm: client + put_parameter ---

def test_upload_creates_ssm_client_with_credentials(service, mock_boto3, mock_datetime):
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.assert_called_once_with(
        'ssm',
        aws_access_key_id='fake_key',
        aws_secret_access_key='fake_secret',
        region_name=REGION,
    )


def test_upload_calls_put_parameter_with_correct_args(service, mock_boto3, mock_datetime):
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.return_value.put_parameter.assert_called_once_with(
        Name=PARAM_NAME,
        Value='203.0.113.7',
        Type='String',
        Overwrite=True,
    )


def test_upload_sets_last_update_on_success(service, mock_boto3, mock_datetime):
    service._upload_to_ssm('203.0.113.7')
    assert service._last_update == NOW


def test_upload_logs_info_on_success(service, mock_boto3, mock_datetime):
    with patch.object(service.logger, 'info') as mock_info:
        service._upload_to_ssm('203.0.113.7')
    mock_info.assert_called()


# --- _upload_to_ssm: throttling ---

def test_upload_proceeds_when_no_previous_update(service, mock_boto3, mock_datetime):
    service._last_update = None
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.return_value.put_parameter.assert_called_once()


def test_upload_skips_when_within_throttle_window(service, mock_boto3, mock_datetime):
    service._last_update = NOW - 100  # 100s ago, window is 900s
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.assert_not_called()


def test_upload_skips_at_exact_window_boundary(service, mock_boto3, mock_datetime):
    # last_update + window == now -> condition uses >=, so still throttled
    service._last_update = NOW - WINDOW_SECONDS
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.assert_not_called()


def test_upload_proceeds_just_past_window(service, mock_boto3, mock_datetime):
    service._last_update = NOW - WINDOW_SECONDS - 1
    service._upload_to_ssm('203.0.113.7')
    mock_boto3.client.return_value.put_parameter.assert_called_once()


def test_upload_skipped_does_not_change_last_update(service, mock_boto3, mock_datetime):
    original = NOW - 100
    service._last_update = original
    service._upload_to_ssm('203.0.113.7')
    assert service._last_update == original


def test_upload_skipped_logs_info(service, mock_boto3, mock_datetime):
    service._last_update = NOW - 100
    with patch.object(service.logger, 'info') as mock_info:
        service._upload_to_ssm('203.0.113.7')
    mock_info.assert_called_once()


# --- _upload_to_ssm: error handling ---

def test_upload_logs_error_on_put_parameter_exception(service, mock_boto3, mock_datetime):
    mock_boto3.client.return_value.put_parameter.side_effect = Exception('access denied')
    with patch.object(service.logger, 'error') as mock_error:
        service._upload_to_ssm('203.0.113.7')
    mock_error.assert_called_once()


def test_upload_does_not_raise_on_exception(service, mock_boto3, mock_datetime):
    mock_boto3.client.return_value.put_parameter.side_effect = Exception('access denied')
    service._upload_to_ssm('203.0.113.7')  # must not propagate


def test_upload_does_not_set_last_update_on_exception(service, mock_boto3, mock_datetime):
    mock_boto3.client.return_value.put_parameter.side_effect = Exception('boom')
    service._upload_to_ssm('203.0.113.7')
    assert service._last_update is None


# --- update_allowed_ip_secret ---

def test_update_allowed_ip_fetches_public_ip(service, mock_requests):
    with patch.object(service, '_upload_to_ssm'):
        service.update_allowed_ip_secret()
    mock_requests.get.assert_called_once_with(GET_IP_URL, timeout=2)


def test_update_allowed_ip_raises_for_bad_status(service, mock_requests):
    with patch.object(service, '_upload_to_ssm'):
        service.update_allowed_ip_secret()
    mock_requests.get.return_value.raise_for_status.assert_called_once()


def test_update_allowed_ip_passes_ip_to_upload(service, mock_requests):
    mock_requests.get.return_value.text = '198.51.100.4'
    with patch.object(service, '_upload_to_ssm') as mock_upload:
        service.update_allowed_ip_secret()
    mock_upload.assert_called_once_with('198.51.100.4')


def test_update_allowed_ip_strips_whitespace_from_ip(service, mock_requests):
    mock_requests.get.return_value.text = '  198.51.100.4\n'
    with patch.object(service, '_upload_to_ssm') as mock_upload:
        service.update_allowed_ip_secret()
    mock_upload.assert_called_once_with('198.51.100.4')


def test_update_allowed_ip_propagates_http_error(service, mock_requests):
    mock_requests.get.return_value.raise_for_status.side_effect = Exception('500')
    with patch.object(service, '_upload_to_ssm') as mock_upload:
        with pytest.raises(Exception):
            service.update_allowed_ip_secret()
    mock_upload.assert_not_called()


def test_update_allowed_ip_end_to_end_calls_put_parameter(service, mock_requests, mock_boto3, mock_datetime):
    # No _upload_to_ssm mock — verifies the full fetch -> upload -> put_parameter wiring
    mock_requests.get.return_value.text = '203.0.113.99'
    service.update_allowed_ip_secret()
    mock_boto3.client.return_value.put_parameter.assert_called_once_with(
        Name=PARAM_NAME,
        Value='203.0.113.99',
        Type='String',
        Overwrite=True,
    )
