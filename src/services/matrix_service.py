# src/services/matrix_service.py
"""
Matrix service module that abstracts rgbmatrix vs RGBMatrixEmulator.
Automatically detects the platform and imports the appropriate module.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Try to detect if we're on a Raspberry Pi
def is_raspberry_pi():
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'Raspberry Pi' in f.read()
    except (FileNotFoundError, PermissionError, OSError):
        return False

# Allow manual override via environment variable
FORCE_MODE = os.getenv('MATRIX_MODE')  # Set to 'emulator' or 'hardware'

if FORCE_MODE == 'emulator':
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
    MATRIX_MODE = "emulator"
    logger.info("✓ Forced emulator mode via MATRIX_MODE environment variable")
elif FORCE_MODE == 'hardware':
    from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
    MATRIX_MODE = "hardware"
    logger.info("✓ Forced hardware mode via MATRIX_MODE environment variable")
elif is_raspberry_pi():
    try:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
        MATRIX_MODE = "hardware"
        logger.info("✓ Running on Raspberry Pi with rgbmatrix hardware")
    except ImportError:
        logger.error("On Raspberry Pi but rgbmatrix not installed!")
        raise
else:
    try:
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
        MATRIX_MODE = "emulator"
        logger.info("✓ Running with RGBMatrixEmulator (development mode)")
    except ImportError:
        logger.error("Not on Pi and RGBMatrixEmulator not installed!")
        raise

# Export the modules so other files can import from here
__all__ = ['RGBMatrix', 'RGBMatrixOptions', 'graphics', 'MATRIX_MODE', 'is_hardware']

def is_hardware():
    """Returns True if running on actual hardware, False if emulator"""
    return MATRIX_MODE == "hardware"
