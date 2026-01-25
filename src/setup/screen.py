import platform
import os

def is_raspberry_pi():
    """Detect if running on a Raspberry Pi."""
    try:
        # Check for Raspberry Pi specific hardware
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                if 'Raspberry Pi' in model:
                    return True
    except (IOError, OSError, FileNotFoundError):
        pass
    
    # Fallback: check CPU architecture (ARM typically indicates Pi)
    # Note: Exclude aarch64 as it could be Apple Silicon Macs
    machine = platform.machine()
    return machine.startswith('arm')

# Determine if we're on a Raspberry Pi
IS_RASPBERRY_PI = is_raspberry_pi()

# Set screen dimensions based on platform
# Raspberry Pi: 64x32 (physical RGB matrix)
# Non-Pi (development): scaled for emulator based on config
if IS_RASPBERRY_PI:
    WIDTH = 64
    HEIGHT = 32
    SCALE_FACTOR = 1
else:
    # Import config to get the scale factor
    # Late import to avoid circular dependency
    try:
        from config import DISPLAY_SCALE_FACTOR
        # Validate scale factor is one of the supported values
        if DISPLAY_SCALE_FACTOR not in (2, 3, 4):
            print(f"Warning: DISPLAY_SCALE_FACTOR must be 2, 3, or 4. Got {DISPLAY_SCALE_FACTOR}. Using default of 3.")
            SCALE_FACTOR = 3
        else:
            SCALE_FACTOR = DISPLAY_SCALE_FACTOR
    except (ImportError, AttributeError):
        # Default to 3 if config not available
        SCALE_FACTOR = 3
    
    WIDTH = 64 * SCALE_FACTOR
    HEIGHT = 32 * SCALE_FACTOR
