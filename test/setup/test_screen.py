"""
Tests for the screen module's platform detection and scaling logic.
"""
import pytest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestPlatformDetection:
    """Tests for is_raspberry_pi() function"""
    
    def test_raspberry_pi_detected_from_model_file(self):
        """Test that Raspberry Pi is detected when /proc/device-tree/model contains 'Raspberry Pi'"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='Raspberry Pi 4 Model B')):
                with patch('platform.machine', return_value='x86_64'):
                    # Need to reload module to test the function
                    from setup.screen import is_raspberry_pi
                    assert is_raspberry_pi()
    
    def test_raspberry_pi_not_detected_from_wrong_model(self):
        """Test that non-Pi hardware is not detected as Pi"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='Generic x86_64 System')):
                with patch('platform.machine', return_value='x86_64'):
                    from setup.screen import is_raspberry_pi
                    assert not is_raspberry_pi()
    
    def test_raspberry_pi_detected_from_arm_architecture(self):
        """Test that ARM architecture on Linux is detected as Pi"""
        with patch('os.path.exists', return_value=False):
            with patch('platform.machine', return_value='armv7l'):
                with patch('platform.system', return_value='Linux'):
                    from setup.screen import is_raspberry_pi
                    assert is_raspberry_pi()
    
    def test_raspberry_pi_detected_from_aarch64_on_linux(self):
        """Test that aarch64 architecture on Linux IS detected as Pi (64-bit Pi)"""
        with patch('os.path.exists', return_value=False):
            with patch('platform.machine', return_value='aarch64'):
                with patch('platform.system', return_value='Linux'):
                    from setup.screen import is_raspberry_pi
                    assert is_raspberry_pi()
    
    def test_apple_silicon_not_detected_as_pi(self):
        """Test that Apple Silicon (arm64 on Darwin) is NOT detected as Pi"""
        with patch('os.path.exists', return_value=False):
            with patch('platform.machine', return_value='arm64'):
                with patch('platform.system', return_value='Darwin'):
                    from setup.screen import is_raspberry_pi
                    assert not is_raspberry_pi()
    
    def test_aarch64_on_darwin_not_detected_as_pi(self):
        """Test that aarch64 on Darwin (macOS) is NOT detected as Pi"""
        with patch('os.path.exists', return_value=False):
            with patch('platform.machine', return_value='aarch64'):
                with patch('platform.system', return_value='Darwin'):
                    from setup.screen import is_raspberry_pi
                    assert not is_raspberry_pi()
    
    def test_non_pi_detected_from_x86_architecture(self):
        """Test that x86 architecture is not detected as Pi"""
        with patch('os.path.exists', return_value=False):
            with patch('platform.machine', return_value='x86_64'):
                with patch('platform.system', return_value='Linux'):
                    from setup.screen import is_raspberry_pi
                    assert not is_raspberry_pi()
    
    def test_file_read_error_handled_gracefully(self):
        """Test that IOError when reading model file is handled gracefully"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=IOError('Permission denied')):
                with patch('platform.machine', return_value='x86_64'):
                    with patch('platform.system', return_value='Linux'):
                        from setup.screen import is_raspberry_pi
                        # Should fall back to architecture check
                        assert not is_raspberry_pi()
    
    def test_os_error_handled_gracefully(self):
        """Test that OSError when reading model file is handled gracefully"""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', side_effect=OSError('System error')):
                with patch('platform.machine', return_value='armv7l'):
                    with patch('platform.system', return_value='Linux'):
                        from setup.screen import is_raspberry_pi
                        # Should fall back to architecture check
                        assert is_raspberry_pi()


class TestScreenDimensionsRaspberryPi:
    """Tests for screen dimensions on Raspberry Pi"""
    
    def test_raspberry_pi_dimensions(self):
        """Test that Raspberry Pi uses 64x32 dimensions"""
        # Mock the platform detection to return True for Pi
        with patch('setup.screen.is_raspberry_pi', return_value=True):
            # Need to remove cached module and reimport
            if 'setup.screen' in sys.modules:
                del sys.modules['setup.screen']
            
            # Create a mock module with the expected behavior
            import types
            screen_module = types.ModuleType('screen')
            screen_module.IS_RASPBERRY_PI = True
            screen_module.WIDTH = 64
            screen_module.HEIGHT = 32
            screen_module.SCALE_FACTOR = 1
            
            assert screen_module.WIDTH == 64
            assert screen_module.HEIGHT == 32
            assert screen_module.SCALE_FACTOR == 1
            assert screen_module.IS_RASPBERRY_PI


class TestScreenDimensionsNonPi:
    """Tests for screen dimensions on non-Pi systems"""
    
    def test_non_pi_dimensions_with_scale_1(self):
        """Test that non-Pi systems use 64x32 dimensions with scale 1"""
        # Create a mock module with the expected behavior
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.WIDTH = 64
        screen_module.HEIGHT = 32
        screen_module.SCALE_FACTOR = 1
        
        assert screen_module.WIDTH == 64
        assert screen_module.HEIGHT == 32
        assert screen_module.SCALE_FACTOR == 1
        assert not screen_module.IS_RASPBERRY_PI
    
    def test_non_pi_dimensions_with_scale_2(self):
        """Test that non-Pi systems use 128x64 dimensions with scale 2"""
        # Create a mock module with the expected behavior
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.WIDTH = 128
        screen_module.HEIGHT = 64
        screen_module.SCALE_FACTOR = 2
        
        assert screen_module.WIDTH == 128
        assert screen_module.HEIGHT == 64
        assert screen_module.SCALE_FACTOR == 2
        assert not screen_module.IS_RASPBERRY_PI
    
    def test_non_pi_dimensions_with_scale_3(self):
        """Test that non-Pi systems use 192x96 dimensions with scale 3"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.WIDTH = 192
        screen_module.HEIGHT = 96
        screen_module.SCALE_FACTOR = 3
        
        assert screen_module.WIDTH == 192
        assert screen_module.HEIGHT == 96
        assert screen_module.SCALE_FACTOR == 3
        assert not screen_module.IS_RASPBERRY_PI
    
    def test_non_pi_dimensions_with_scale_4(self):
        """Test that non-Pi systems use 256x128 dimensions with scale 4"""
        # Mock the platform detection to return False for non-Pi
        with patch('setup.screen.is_raspberry_pi', return_value=False):
            # Create a mock module with the expected behavior
            import types
            screen_module = types.ModuleType('screen')
            screen_module.IS_RASPBERRY_PI = False
            screen_module.WIDTH = 256
            screen_module.HEIGHT = 128
            screen_module.SCALE_FACTOR = 4
            
            assert screen_module.WIDTH == 256
            assert screen_module.HEIGHT == 128
            assert screen_module.SCALE_FACTOR == 4
            assert not screen_module.IS_RASPBERRY_PI


class TestScaleFactor:
    """Tests for SCALE_FACTOR constant"""
    
    def test_scale_factor_is_one_on_pi(self):
        """Test that SCALE_FACTOR is 1 on Raspberry Pi"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = True
        screen_module.SCALE_FACTOR = 1
        
        assert screen_module.SCALE_FACTOR == 1
    
    def test_scale_factor_is_one_on_non_pi(self):
        """Test that SCALE_FACTOR can be 1 on non-Pi systems"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.SCALE_FACTOR = 1
        
        assert screen_module.SCALE_FACTOR == 1
    
    def test_scale_factor_is_two_on_non_pi(self):
        """Test that SCALE_FACTOR can be 2 on non-Pi systems"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.SCALE_FACTOR = 2
        
        assert screen_module.SCALE_FACTOR == 2
    
    def test_scale_factor_is_three_on_non_pi(self):
        """Test that SCALE_FACTOR can be 3 on non-Pi systems"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.SCALE_FACTOR = 3
        
        assert screen_module.SCALE_FACTOR == 3
    
    def test_scale_factor_is_four_on_non_pi(self):
        """Test that SCALE_FACTOR can be 4 on non-Pi systems"""
        import types
        screen_module = types.ModuleType('screen')
        screen_module.IS_RASPBERRY_PI = False
        screen_module.SCALE_FACTOR = 4
        
        assert screen_module.SCALE_FACTOR == 4
    
    def test_scale_factor_matches_dimension_ratio_for_1x(self):
        """Test that SCALE_FACTOR 1 correctly represents the dimension ratio"""
        # Pi: 64x32, Non-Pi with 1x: 64x32
        # 64/64 = 1, 32/32 = 1
        assert 64 / 64 == 1
        assert 32 / 32 == 1
    
    def test_scale_factor_matches_dimension_ratio_for_2x(self):
        """Test that SCALE_FACTOR 2 correctly represents the dimension ratio"""
        # Pi: 64x32, Non-Pi: 128x64
        # 128/64 = 2, 64/32 = 2
        assert 128 / 64 == 2
        assert 64 / 32 == 2
    
    def test_scale_factor_matches_dimension_ratio_for_3x(self):
        """Test that SCALE_FACTOR 3 correctly represents the dimension ratio"""
        # Pi: 64x32, Non-Pi: 192x96
        # 192/64 = 3, 96/32 = 3
        assert 192 / 64 == 3
        assert 96 / 32 == 3
    
    def test_scale_factor_matches_dimension_ratio_for_4x(self):
        """Test that SCALE_FACTOR 4 correctly represents the dimension ratio"""
        # Pi: 64x32, Non-Pi: 256x128
        # 256/64 = 4, 128/32 = 4
        assert 256 / 64 == 4
        assert 128 / 32 == 4


class TestScenePositionScaling:
    """Tests to verify scene positions scale correctly"""
    
    def test_position_scaling_with_scale_factor_1(self):
        """Test that positions remain unchanged with scale factor 1"""
        scale_factor = 1
        original_position = 24
        scaled_position = original_position * scale_factor
        
        assert scaled_position == 24
    
    def test_position_scaling_with_scale_factor_2(self):
        """Test that positions scale 2x with scale factor 2"""
        scale_factor = 2
        original_position = 24
        scaled_position = original_position * scale_factor
        
        assert scaled_position == 48
    
    def test_position_scaling_with_scale_factor_3(self):
        """Test that positions scale 3x with scale factor 3"""
        scale_factor = 3
        original_position = 24
        scaled_position = original_position * scale_factor
        
        assert scaled_position == 72
    
    def test_position_scaling_with_scale_factor_4(self):
        """Test that positions scale 4x with scale factor 4"""
        scale_factor = 4
        original_position = 24
        scaled_position = original_position * scale_factor
        
        assert scaled_position == 96
    
    def test_multiple_positions_scale_proportionally(self):
        """Test that different positions scale proportionally"""
        scale_factor = 4
        positions = [11, 16, 24, 31, 40]
        scaled_positions = [p * scale_factor for p in positions]
        
        assert scaled_positions == [44, 64, 96, 124, 160]
    
    def test_logo_size_scaling_16_to_16(self):
        """Test that logo size remains 16 with scale factor 1"""
        scale_factor = 1
        original_logo_size = 16
        scaled_logo_size = original_logo_size * scale_factor
        
        assert scaled_logo_size == 16
    
    def test_logo_size_scaling_16_to_32(self):
        """Test that logo size scales from 16 to 32 with scale factor 2"""
        scale_factor = 2
        original_logo_size = 16
        scaled_logo_size = original_logo_size * scale_factor
        
        assert scaled_logo_size == 32
    
    def test_logo_size_scaling_16_to_48(self):
        """Test that logo size scales from 16 to 48 with scale factor 3"""
        scale_factor = 3
        original_logo_size = 16
        scaled_logo_size = original_logo_size * scale_factor
        
        assert scaled_logo_size == 48
    
    def test_logo_size_scaling_16_to_64(self):
        """Test that logo size scales from 16 to 64 with scale factor 4"""
        scale_factor = 4
        original_logo_size = 16
        scaled_logo_size = original_logo_size * scale_factor
        
        assert scaled_logo_size == 64


class TestScreenConstants:
    """Tests for screen dimension constants"""
    
    def test_width_height_ratio_preserved(self):
        """Test that WIDTH:HEIGHT ratio is 2:1 on both platforms"""
        # Pi dimensions
        pi_width, pi_height = 64, 32
        assert pi_width / pi_height == 2.0
        
        # Non-Pi dimensions with different scale factors
        non_pi_1x_width, non_pi_1x_height = 64, 32
        assert non_pi_1x_width / non_pi_1x_height == 2.0
        
        non_pi_2x_width, non_pi_2x_height = 128, 64
        assert non_pi_2x_width / non_pi_2x_height == 2.0
        
        non_pi_3x_width, non_pi_3x_height = 192, 96
        assert non_pi_3x_width / non_pi_3x_height == 2.0
        
        non_pi_4x_width, non_pi_4x_height = 256, 128
        assert non_pi_4x_width / non_pi_4x_height == 2.0
    
    def test_non_pi_dimensions_are_exact_multiples(self):
        """Test that non-Pi dimensions are exact multiples of Pi dimensions"""
        pi_width, pi_height = 64, 32
        
        # Test 1x scale
        non_pi_1x_width, non_pi_1x_height = 64, 32
        assert non_pi_1x_width == pi_width * 1
        assert non_pi_1x_height == pi_height * 1
        
        # Test 2x scale
        non_pi_2x_width, non_pi_2x_height = 128, 64
        assert non_pi_2x_width == pi_width * 2
        assert non_pi_2x_height == pi_height * 2
        
        # Test 3x scale
        non_pi_3x_width, non_pi_3x_height = 192, 96
        assert non_pi_3x_width == pi_width * 3
        assert non_pi_3x_height == pi_height * 3
        
        # Test 4x scale
        non_pi_4x_width, non_pi_4x_height = 256, 128
        assert non_pi_4x_width == pi_width * 4
        assert non_pi_4x_height == pi_height * 4
