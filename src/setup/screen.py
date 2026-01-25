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
    except:
        pass
    
    # Fallback: check CPU architecture (ARM typically indicates Pi)
    machine = platform.machine()
    return machine.startswith('arm') or machine.startswith('aarch')

# Determine if we're on a Raspberry Pi
IS_RASPBERRY_PI = is_raspberry_pi()

# Set screen dimensions based on platform
# Raspberry Pi: 64x32 (physical RGB matrix)
# Non-Pi (development): 256x128 (4x scaled for emulator)
if IS_RASPBERRY_PI:
    WIDTH = 64
    HEIGHT = 32
    SCALE_FACTOR = 1
else:
    WIDTH = 256
    HEIGHT = 128
    SCALE_FACTOR = 4
