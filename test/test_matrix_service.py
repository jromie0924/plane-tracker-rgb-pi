import pytest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


def test_is_raspberry_pi_detection_true():
    """Test that is_raspberry_pi() returns True when Raspberry Pi model file exists"""
    # We need to test the function before the module is fully imported
    # So we'll import and test the function directly
    with patch('builtins.open', mock_open(read_data='Raspberry Pi 4 Model B')):
        # Import the function dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "matrix_service_test", 
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/matrix_service.py'))
        )
        module = importlib.util.module_from_spec(spec)
        
        # Mock the imports before loading
        sys.modules['rgbmatrix'] = MagicMock()
        sys.modules['RGBMatrixEmulator'] = MagicMock()
        
        try:
            spec.loader.exec_module(module)
            assert module.is_raspberry_pi()
        finally:
            # Cleanup
            if 'rgbmatrix' in sys.modules:
                del sys.modules['rgbmatrix']
            if 'RGBMatrixEmulator' in sys.modules:
                del sys.modules['RGBMatrixEmulator']


def test_is_raspberry_pi_detection_false():
    """Test that is_raspberry_pi() returns False when model file doesn't exist"""
    with patch('builtins.open', side_effect=FileNotFoundError()):
        # Import the function dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "matrix_service_test2", 
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/matrix_service.py'))
        )
        module = importlib.util.module_from_spec(spec)
        
        # Mock the imports before loading
        sys.modules['rgbmatrix'] = MagicMock()
        sys.modules['RGBMatrixEmulator'] = MagicMock()
        
        try:
            spec.loader.exec_module(module)
            assert not module.is_raspberry_pi()
        finally:
            # Cleanup
            if 'rgbmatrix' in sys.modules:
                del sys.modules['rgbmatrix']
            if 'RGBMatrixEmulator' in sys.modules:
                del sys.modules['RGBMatrixEmulator']


def test_force_emulator_mode():
    """Test that MATRIX_MODE='emulator' forces emulator mode"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', mock_open(read_data='Raspberry Pi 4 Model B')):
            # Import the module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "matrix_service_test3", 
                os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/matrix_service.py'))
            )
            module = importlib.util.module_from_spec(spec)
            
            # Mock the imports
            mock_emulator = MagicMock()
            mock_hardware = MagicMock()
            sys.modules['RGBMatrixEmulator'] = mock_emulator
            sys.modules['rgbmatrix'] = mock_hardware
            
            try:
                spec.loader.exec_module(module)
                assert module.MATRIX_MODE == "emulator"
                assert not module.is_hardware()
            finally:
                # Cleanup
                if 'rgbmatrix' in sys.modules:
                    del sys.modules['rgbmatrix']
                if 'RGBMatrixEmulator' in sys.modules:
                    del sys.modules['RGBMatrixEmulator']


def test_force_hardware_mode():
    """Test that MATRIX_MODE='hardware' forces hardware mode"""
    with patch.dict(os.environ, {'MATRIX_MODE': 'hardware'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            # Import the module dynamically
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "matrix_service_test4", 
                os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/matrix_service.py'))
            )
            module = importlib.util.module_from_spec(spec)
            
            # Mock the imports
            mock_emulator = MagicMock()
            mock_hardware = MagicMock()
            sys.modules['RGBMatrixEmulator'] = mock_emulator
            sys.modules['rgbmatrix'] = mock_hardware
            
            try:
                spec.loader.exec_module(module)
                assert module.MATRIX_MODE == "hardware"
                assert module.is_hardware()
            finally:
                # Cleanup
                if 'rgbmatrix' in sys.modules:
                    del sys.modules['rgbmatrix']
                if 'RGBMatrixEmulator' in sys.modules:
                    del sys.modules['RGBMatrixEmulator']


def test_matrix_service_exports():
    """Test that matrix_service exports the expected symbols"""
    # Mock the imports
    mock_emulator = MagicMock()
    mock_emulator.RGBMatrix = MagicMock()
    mock_emulator.RGBMatrixOptions = MagicMock()
    mock_emulator.graphics = MagicMock()
    
    sys.modules['RGBMatrixEmulator'] = mock_emulator
    
    with patch.dict(os.environ, {'MATRIX_MODE': 'emulator'}):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "matrix_service_test5", 
                os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/matrix_service.py'))
            )
            module = importlib.util.module_from_spec(spec)
            
            try:
                spec.loader.exec_module(module)
                
                # Check that all expected exports are present
                assert 'RGBMatrix' in module.__all__
                assert 'RGBMatrixOptions' in module.__all__
                assert 'graphics' in module.__all__
                assert 'MATRIX_MODE' in module.__all__
                assert 'is_hardware' in module.__all__
                
                # Check that the functions/classes exist
                assert hasattr(module, 'RGBMatrix')
                assert hasattr(module, 'RGBMatrixOptions')
                assert hasattr(module, 'graphics')
                assert hasattr(module, 'MATRIX_MODE')
                assert hasattr(module, 'is_hardware')
            finally:
                # Cleanup
                if 'RGBMatrixEmulator' in sys.modules:
                    del sys.modules['RGBMatrixEmulator']
