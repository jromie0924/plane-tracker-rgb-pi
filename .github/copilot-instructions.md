# Copilot Instructions for ADSB Plane Tracker

## Project Overview
This is a Python-based ADSB plane tracker that displays nearby aircraft information on an RGB LED matrix display. The project can run on a Raspberry Pi with a physical RGB matrix or in development mode using a browser-based emulator.

## Development Environment

### Python Environment
- **Python Version**: 3.9 (specified in Pipfile)
- **Package Manager**: pipenv
- **Virtual Environment**: Use `pipenv shell` to activate the virtual environment
- **Dependencies Installation**: `pipenv install --dev`

### Key Dependencies
- **Production**: boto3, requests
- **Development**: rgbmatrixemulator (0.11.6)

### Setup Tools
- **pipenv**: For Python package management
- **pyenv**: For Python version management (optional but recommended)

## Project Structure

### Core Directories
- `src/`: Main application code
  - `app.py`: Main application entry point
  - `config.py`: Configuration settings (ZIP code, coordinates, API keys, etc.)
  - `display/`: Display rendering logic for RGB matrix
  - `models/`: Data models
  - `scenes/`: Display scenes for different states
  - `services/`: Business logic services (ADSB tracking, geo, authentication, etc.)
  - `workers/`: Background worker processes
- `test/`: Unit tests (pytest-based)
- `scripts/`: Shell scripts for starting the application
- `docs/`: Documentation and images
- `logos/`: Logo assets
- `fonts/`: Font files for display rendering
- `icons/`: Icon assets

### Important Files
- `Pipfile` & `Pipfile.lock`: Python dependency definitions
- `environment.yml`: Conda environment configuration (alternative to pipenv)
- `emulator_config.json`: Configuration for the RGB matrix emulator
- `scripts/start-tracker.sh`: Script to start the tracker application

## Configuration

### User Configuration (`src/config.py`)
Key configuration values that users may need to customize:
- `ZIP_CODE` and `COUNTRY`: User's location
- `LOCATION_COORDINATES_OVERRIDE`: Optional coordinate override
- `RADIUS`: Search radius for nearby aircraft (nautical miles)
- `MIN_ALTITUDE` / `MAX_ALTITUDE`: Altitude filters
- `BRIGHTNESS` / `BRIGHTNESS_NIGHT`: Display brightness settings
- `DISTANCE_UNITS`: "imperial" or "metric"
- `CLOCK_FORMAT`: "12hr" or "24hr"

### AWS Configuration
The project uses AWS Secrets Manager for storing API keys:
- RapidAPI key for geocoding services
- AWS credentials stored in `~/.aws_secret`

## Running the Application

### Development Mode (Emulator)
To run with the browser-based RGB matrix emulator:
1. Replace imports from `rgbmatrix` to `RGBMatrixEmulator` in relevant files
2. Run: `scripts/start-tracker.sh`
3. Open browser to `localhost:8888`

### Production Mode (Physical RGB Matrix)
Run: `scripts/start-tracker.sh` (with rgbmatrix imports)

## Testing

### Test Framework
- **Framework**: pytest
- **Test Location**: `test/` directory
- **Running Tests**: Use pytest command
- **Test Pattern**: Tests use mocks for external dependencies (HTTP calls, config)

### Test Structure Example
Tests use fixtures and unittest.mock for mocking:
```python
@pytest.fixture
def mock_config():
    with patch('services.adsbTracker.config') as mock_config:
        yield mock_config
```

## Code Style Guidelines

### Python Conventions
- **Import Organization**: Standard library, third-party, local imports
- **Logging**: Use the configured logger from `config.APP_NAME`
- **Path Handling**: Use `os.path` for file operations
- **Error Handling**: Proper exception handling especially for HTTP requests

### Display Code
- Display logic is separated into scenes (e.g., loading, tracking, error states)
- Font and icon resources are loaded from respective directories
- Display coordinates use PIL/Pillow for rendering

### Services
- Services are stateless classes with focused responsibilities
- HTTP requests should include timeouts to prevent deadlocks
- External API calls should be wrapped in try-except blocks

## Key Technical Details

### RGB Matrix Display
- The project uses either:
  - Physical RGB LED matrix (via `rgbmatrix` library) for production
  - Browser-based emulator (via `RGBMatrixEmulator` library) for development
- Display rendering uses PIL/Pillow for image composition

### ADSB Data Source
- Uses adsb.lol API for nearby aircraft data
- Queries based on location coordinates and radius
- Filters by altitude range

### Geocoding
- Uses RapidAPI's forward-reverse geocoding service
- Fallback to default coordinates (Chicago, IL) if API unavailable
- Can be overridden with specific coordinates in config

### Logging
- Centralized logging configuration in `app.py`
- Rotating file handler (1MB per file, 2 backup files)
- Logs stored in `logs/plane-tracker.log`
- Console and file output

## Common Tasks

### Adding a New Service
1. Create a new file in `src/services/`
2. Follow the pattern of existing services (e.g., `adsbTracker.py`)
3. Use configuration from `config.py`
4. Add corresponding tests in `test/service/` (note: singular 'service')

### Adding a New Display Scene
1. Create a new scene class in `src/scenes/`
2. Implement rendering logic using PIL/Pillow
3. Register the scene in the display controller

### Modifying Configuration
1. Update `src/config.py` with new configuration constants
2. Use uppercase naming convention for configuration values
3. Provide sensible defaults

## Dependencies and Security

### External APIs
- **adsb.lol**: ADSB flight data
- **RapidAPI**: Geocoding services (requires API key)
- **AWS Secrets Manager**: Secure credential storage

### Security Considerations
- API keys should never be committed to the repository
- Use AWS Secrets Manager or environment variables for credentials
- HTTP requests should have appropriate timeouts

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure you're in the pipenv virtual environment
2. **Display Not Working**: Check if using correct import (rgbmatrix vs RGBMatrixEmulator)
3. **API Failures**: Verify AWS credentials and API keys are configured
4. **Coordinates Not Found**: Use `LOCATION_COORDINATES_OVERRIDE` as fallback

### Development Tips
- Use the emulator for faster iteration during development
- Check logs in `logs/plane-tracker.log` for debugging
- Test with mock data to avoid API rate limits
