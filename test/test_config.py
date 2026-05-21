import os
import sys
from unittest.mock import patch, mock_open

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import config


# --- _is_raspberry_pi: SSM_IP_UPDATE env override ---

@pytest.mark.parametrize('value', ['true', 'TRUE', '  True ', '1', 'yes', 'YES'])
def test_env_override_truthy_values_enable(monkeypatch, value):
    monkeypatch.setenv('SSM_IP_UPDATE', value)
    assert config._is_raspberry_pi() is True


@pytest.mark.parametrize('value', ['false', 'False', '0', 'no', '', 'maybe'])
def test_env_override_falsy_values_disable(monkeypatch, value):
    monkeypatch.setenv('SSM_IP_UPDATE', value)
    assert config._is_raspberry_pi() is False


def test_env_override_beats_proc_file(monkeypatch):
    # The env var wins even on a real Pi — the escape hatch for handing
    # allowlist authority to another host.
    monkeypatch.setenv('SSM_IP_UPDATE', 'false')
    with patch('builtins.open', mock_open(read_data='Raspberry Pi 4 Model B')):
        assert config._is_raspberry_pi() is False


# --- _is_raspberry_pi: /proc/device-tree/model fallback ---

def test_detects_pi_from_proc_model(monkeypatch):
    monkeypatch.delenv('SSM_IP_UPDATE', raising=False)
    with patch('builtins.open', mock_open(read_data='Raspberry Pi 4 Model B')):
        assert config._is_raspberry_pi() is True


def test_non_pi_model_string_is_false(monkeypatch):
    monkeypatch.delenv('SSM_IP_UPDATE', raising=False)
    with patch('builtins.open', mock_open(read_data='Some Other SBC')):
        assert config._is_raspberry_pi() is False


def test_missing_proc_file_is_false(monkeypatch):
    # FileNotFoundError is an OSError subclass — the generic Linux box case.
    monkeypatch.delenv('SSM_IP_UPDATE', raising=False)
    with patch('builtins.open', side_effect=FileNotFoundError):
        assert config._is_raspberry_pi() is False


def test_unreadable_proc_file_is_false(monkeypatch):
    monkeypatch.delenv('SSM_IP_UPDATE', raising=False)
    with patch('builtins.open', side_effect=PermissionError):
        assert config._is_raspberry_pi() is False


# --- SSM_IP_UPDATE_ENABLED constant ---

def test_ssm_ip_update_enabled_is_bool():
    assert isinstance(config.SSM_IP_UPDATE_ENABLED, bool)
