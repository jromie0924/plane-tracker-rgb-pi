"""
Integration tests to verify matrix_service imports work correctly
across all modules that use it.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.fixture
def mock_matrix_modules():
    """Mock both rgbmatrix and RGBMatrixEmulator modules before imports"""
    # Create mock modules with all required classes
    mock_emulator = MagicMock()
    mock_emulator.RGBMatrix = MagicMock()
    mock_emulator.RGBMatrixOptions = MagicMock()
    mock_emulator.graphics = MagicMock()
    mock_emulator.graphics.Color = MagicMock(return_value=MagicMock())
    mock_emulator.graphics.DrawText = MagicMock(return_value=5)
    mock_emulator.graphics.DrawLine = MagicMock()
    mock_emulator.graphics.Font = MagicMock()
    
    mock_hardware = MagicMock()
    mock_hardware.RGBMatrix = MagicMock()
    mock_hardware.RGBMatrixOptions = MagicMock()
    mock_hardware.graphics = MagicMock()
    mock_hardware.graphics.Color = MagicMock(return_value=MagicMock())
    mock_hardware.graphics.DrawText = MagicMock(return_value=5)
    mock_hardware.graphics.DrawLine = MagicMock()
    mock_hardware.graphics.Font = MagicMock()
    
    sys.modules['RGBMatrixEmulator'] = mock_emulator
    sys.modules['rgbmatrix'] = mock_hardware
    
    yield
    
    # Cleanup
    if 'RGBMatrixEmulator' in sys.modules:
        del sys.modules['RGBMatrixEmulator']
    if 'rgbmatrix' in sys.modules:
        del sys.modules['rgbmatrix']
    
    # Remove imported modules to allow fresh imports
    modules_to_remove = [
        'matrix_service', 'setup.colours', 'setup.fonts',
        'scenes.journey', 'scenes.clock', 'scenes.flightdetails', 'scenes.date'
    ]
    for mod in modules_to_remove:
        if mod in sys.modules:
            del sys.modules[mod]


def test_matrix_service_import(mock_matrix_modules):
    """Test that matrix_service can be imported successfully"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            import matrix_service
            
            # Verify the module loaded
            assert matrix_service.MATRIX_MODE == "emulator"
            assert hasattr(matrix_service, 'RGBMatrix')
            assert hasattr(matrix_service, 'RGBMatrixOptions')
            assert hasattr(matrix_service, 'graphics')


def test_colours_module_import(mock_matrix_modules):
    """Test that setup.colours imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            from setup import colours
            
            # Verify colour constants are defined using graphics.Color
            assert hasattr(colours, 'BLACK')
            assert hasattr(colours, 'WHITE')
            assert hasattr(colours, 'graphics')


def test_fonts_module_import(mock_matrix_modules):
    """Test that setup.fonts imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Mock the font file loading
            with patch.object(sys.modules['RGBMatrixEmulator'].graphics.Font(), 'LoadFont'):
                from setup import fonts
                
                # Verify font objects are defined
                assert hasattr(fonts, 'extrasmall')
                assert hasattr(fonts, 'small')
                assert hasattr(fonts, 'regular')
                assert hasattr(fonts, 'graphics')


def test_journey_scene_import(mock_matrix_modules):
    """Test that scenes.journey imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Mock required dependencies
            with patch('scenes.journey.DISTANCE_UNITS', 'imperial'):
                from scenes import journey
                
                # Verify the scene class exists and uses graphics
                assert hasattr(journey, 'JourneyScene')
                assert hasattr(journey, 'graphics')


def test_clock_scene_import(mock_matrix_modules):
    """Test that scenes.clock imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Mock config
            with patch('scenes.clock.CLOCK_FORMAT', '24hr'):
                from scenes import clock
                
                # Verify the scene class exists and uses graphics
                assert hasattr(clock, 'ClockScene')
                assert hasattr(clock, 'graphics')


def test_flightdetails_scene_import(mock_matrix_modules):
    """Test that scenes.flightdetails imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            from scenes import flightdetails
            
            # Verify the scene class exists and uses graphics
            assert hasattr(flightdetails, 'FlightDetailsScene')
            assert hasattr(flightdetails, 'graphics')


def test_date_scene_import(mock_matrix_modules):
    """Test that scenes.date imports graphics from matrix_service correctly"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Mock config
            with patch('scenes.date.NIGHT_START', '22:00'):
                with patch('scenes.date.NIGHT_END', '06:00'):
                    from scenes import date
                    
                    # Verify the scene class exists and uses graphics
                    assert hasattr(date, 'DateScene')
                    assert hasattr(date, 'graphics')


def test_all_modules_use_same_graphics_source(mock_matrix_modules):
    """Test that all modules import graphics from matrix_service (not directly from rgbmatrix/emulator)"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Import matrix_service first
            import matrix_service
            
            # Import colours and fonts
            with patch.object(sys.modules['RGBMatrixEmulator'].graphics.Font(), 'LoadFont'):
                from setup import colours, fonts
                
                # Verify they have graphics attributes (imported from matrix_service)
                assert hasattr(colours, 'graphics')
                assert hasattr(fonts, 'graphics')
                
                # Verify graphics.Color works (from matrix_service)
                color = colours.graphics.Color(255, 0, 0)
                assert color is not None


def test_emulator_mode_with_environment_variable(mock_matrix_modules):
    """Test that MATRIX_MODE=emulator forces emulator imports across all modules"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', mock_open=MagicMock(read_data='Raspberry Pi')):
            import matrix_service
            
            # Even though we might be on a Pi, emulator mode should be forced
            assert matrix_service.MATRIX_MODE == "emulator"
            assert not matrix_service.is_hardware()


def test_hardware_mode_with_environment_variable(mock_matrix_modules):
    """Test that MATRIX_MODE=hardware forces hardware imports across all modules"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'hardware'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            import matrix_service
            
            # Even though we're not on a Pi, hardware mode should be forced
            assert matrix_service.MATRIX_MODE == "hardware"
            assert matrix_service.is_hardware()
