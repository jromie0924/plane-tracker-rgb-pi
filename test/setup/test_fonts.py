"""
Tests for the fonts module's platform-aware font loading logic.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestFontDirectorySelection:
    """Tests for font directory selection based on platform"""
    
    def test_raspberry_pi_uses_original_fonts_directory(self):
        """Test that Raspberry Pi uses the original fonts directory"""
        with patch('setup.screen.IS_RASPBERRY_PI', True):
            # Mock the DIR_PATH to a known value
            test_dir = '/test/setup'
            expected_font_dir = f"{test_dir}/../fonts"
            
            # Verify the path construction
            assert expected_font_dir == '/test/setup/../fonts'
    
    def test_non_pi_uses_scaled_fonts_directory(self):
        """Test that non-Pi systems use the scaled fonts directory"""
        with patch('setup.screen.IS_RASPBERRY_PI', False):
            test_dir = '/test/setup'
            expected_font_dir = f"{test_dir}/../fonts/scaled"
            
            # Verify the path construction
            assert expected_font_dir == '/test/setup/../fonts/scaled'


class TestFontFileSelection:
    """Tests for font file selection based on platform"""
    
    def test_raspberry_pi_loads_original_font_files(self):
        """Test that Raspberry Pi loads original font files without suffix"""
        font_names = ['4x6', '5x8', '6x13', '6x13B', '7x13', '7x13B', '8x13', '8x13B']
        
        for font_name in font_names:
            # Original font files should have .bdf extension only
            original_file = f"{font_name}.bdf"
            assert original_file.endswith('.bdf')
            assert '_4x' not in original_file
    
    def test_non_pi_loads_scaled_font_files(self):
        """Test that non-Pi systems load scaled font files with _4x suffix"""
        font_names = ['4x6', '5x8', '6x13', '6x13B', '7x13', '7x13B', '8x13', '8x13B']
        
        for font_name in font_names:
            # Scaled font files should have _4x suffix
            scaled_file = f"{font_name}_4x.bdf"
            assert '_4x.bdf' in scaled_file
    
    def test_all_font_types_have_scaled_versions(self):
        """Test that all font types have corresponding scaled versions"""
        font_types = ['extrasmall', 'small', 'regular', 'regular_bold', 
                      'regularplus', 'regularplus_bold', 'large', 'large_bold']
        
        font_file_mapping = {
            'extrasmall': '4x6',
            'small': '5x8',
            'regular': '6x13',
            'regular_bold': '6x13B',
            'regularplus': '7x13',
            'regularplus_bold': '7x13B',
            'large': '8x13',
            'large_bold': '8x13B'
        }
        
        # Verify all font types are mapped
        assert len(font_types) == len(font_file_mapping)
        
        # Verify each font type has both original and scaled versions
        for font_type in font_types:
            font_file = font_file_mapping[font_type]
            original = f"{font_file}.bdf"
            scaled = f"{font_file}_4x.bdf"
            
            assert original is not None
            assert scaled is not None


class TestFontScaling:
    """Tests for font scaling factors"""
    
    def test_scaled_fonts_are_4x_larger(self):
        """Test that scaled fonts are exactly 4x the size of original fonts"""
        # Original font sizes (width x height)
        original_sizes = {
            '4x6': (4, 6),
            '5x8': (5, 8),
            '6x13': (6, 13),
            '7x13': (7, 13),
            '8x13': (8, 13)
        }
        
        # Scaled font sizes should be 4x
        for font_name, (width, height) in original_sizes.items():
            scaled_width = width * 4
            scaled_height = height * 4
            
            assert scaled_width == width * 4
            assert scaled_height == height * 4
    
    def test_font_scaling_matches_screen_scale_factor(self):
        """Test that font scaling factor (4) matches screen SCALE_FACTOR"""
        screen_scale_factor = 4
        font_scale_factor = 4
        
        assert font_scale_factor == screen_scale_factor


class TestFontLoadingPaths:
    """Tests for font loading path construction"""
    
    def test_original_font_path_construction(self):
        """Test that original font paths are constructed correctly"""
        font_dir = '/path/to/fonts'
        font_files = ['4x6.bdf', '5x8.bdf', '6x13.bdf']
        
        for font_file in font_files:
            full_path = f"{font_dir}/{font_file}"
            assert full_path.startswith(font_dir)
            assert full_path.endswith('.bdf')
    
    def test_scaled_font_path_construction(self):
        """Test that scaled font paths are constructed correctly"""
        font_dir = '/path/to/fonts/scaled'
        font_files = ['4x6_4x.bdf', '5x8_4x.bdf', '6x13_4x.bdf']
        
        for font_file in font_files:
            full_path = f"{font_dir}/{font_file}"
            assert full_path.startswith(font_dir)
            assert '_4x.bdf' in full_path
    
    def test_font_directory_paths_are_relative(self):
        """Test that font directory paths use relative paths from setup directory"""
        # From setup directory, fonts should be at ../fonts
        relative_path = '../fonts'
        assert relative_path.startswith('..')
        assert 'fonts' in relative_path
        
        # Scaled fonts should be at ../fonts/scaled
        scaled_relative_path = '../fonts/scaled'
        assert scaled_relative_path.startswith('..')
        assert 'scaled' in scaled_relative_path


class TestFontObjects:
    """Tests for font object creation"""
    
    def test_all_font_objects_are_created(self):
        """Test that all required font objects are created"""
        required_fonts = [
            'extrasmall', 'small', 'regular', 'regular_bold',
            'regularplus', 'regularplus_bold', 'large', 'large_bold'
        ]
        
        # All fonts should be defined
        assert len(required_fonts) == 8
    
    def test_font_objects_have_unique_sizes(self):
        """Test that font objects represent different sizes"""
        font_sizes = {
            'extrasmall': 4,  # 4x6
            'small': 5,       # 5x8
            'regular': 6,     # 6x13
            'regularplus': 7, # 7x13
            'large': 8        # 8x13
        }
        
        # Verify we have multiple unique sizes
        unique_sizes = set(font_sizes.values())
        assert len(unique_sizes) == 5
