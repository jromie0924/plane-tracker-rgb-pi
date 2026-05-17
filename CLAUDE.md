# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Python-based ADSB plane tracker that displays nearby aircraft on a 64×32 RGB LED matrix. Runs on Raspberry Pi with physical hardware or in development mode using a browser-based emulator at `localhost:8888`.

## Commands

```bash
# Install dependencies (dev includes emulator + pytest)
pipenv install --dev

# Run the application
scripts/start-tracker.sh  # auto-detects Pi vs dev, handles pipenv

# Run all tests
pipenv run pytest

# Run a single test file
pipenv run pytest test/service/test_flightLogic.py

# Run a specific test
pipenv run pytest test/service/test_flightLogic.py::test_choose_flight_returns_none_empty_dict_when_no_flights

# Force emulator mode without Pi detection
MATRIX_MODE=emulator pipenv run python src/app.py ~/.aws_secret
```

## Architecture

### Render Loop (`workers/animator.py`)
`Animator` is the core render engine. Methods decorated with `@Animator.KeyFrame.add(divisor, offset, scene_name)` are called every `divisor` frames (offset for phase-shifting). `divisor=0` means "run once on scene reset." `Display` inherits from all scene classes and `Animator` via Python multiple inheritance — scene methods are registered automatically through introspection.

### Display (`src/display/__init__.py`)
`Display` composes all scenes and the animator via multiple inheritance:
```python
class Display(FlightDetailsScene, FlightLogoScene, JourneyScene, ClockScene, Animator)
```
Key keyframes: `clear_screen` (divisor=0, on reset), `check_for_loaded_data` (every 5s), `grab_new_data` (every 42s), `sync` (every frame, calls `SwapOnVSync`).

### Data Flow
1. `Overhead._grab_data()` runs in a background daemon thread (Lock-protected)
2. Calls `AdsbTrackerService` → adsb.lol API for nearby flights
3. `FlightLogic.choose_flight()` selects the best flight: prioritizes flights with plausible routes, avoids duplicates via `flight_history_mapping` (TTL: `DUPLICATION_AVOIDANCE_TTL` minutes)
4. `Display.check_for_loaded_data()` polls `overhead.new_data` and triggers scene reset when data changes
5. `TrackerLog.update_log()` writes all visible flights to DynamoDB asynchronously

### Platform Detection (`src/services/matrix_service.py`)
Auto-detects Pi by reading `/proc/device-tree/model` and imports `rgbmatrix` (hardware) or `RGBMatrixEmulator` (development). All other files import from `services.matrix_service` — **never import directly from `rgbmatrix` or `RGBMatrixEmulator`**. Override with `MATRIX_MODE=emulator` or `MATRIX_MODE=hardware`.

### Singletons
`RuntimeService` and `TrackerLog` are thread-safe singletons (via `__new__` + Lock). `RuntimeService` holds AWS credentials loaded from a CSV at startup. `TrackerLog` connects to DynamoDB using those credentials — table name is `tracker_log` on Pi, `tracker_log_emu` in dev.

### AWS Setup
App entrypoint: `python src/app.py <aws_secret_dir>`. The directory must contain `flight_tracker_app_accessKeys.csv` with columns `Access key ID` and `Secret access key`. These credentials are used for both AWS Secrets Manager (RapidAPI key) and DynamoDB writes.

## Configuration (`src/config.py`)
Key values to customize: `ZIP_CODE`/`COUNTRY`, `RADIUS` (nautical miles), `MIN_ALTITUDE`/`MAX_ALTITUDE`, `BRIGHTNESS`/`BRIGHTNESS_NIGHT`, `NIGHT_START`/`NIGHT_END`, `DISTANCE_UNITS`, `CLOCK_FORMAT`, `DISPLAY_SCALE_FACTOR` (1/2/3 for emulator), `DUPLICATION_AVOIDANCE_TTL`.

## Testing
Tests live in `test/` with subdirectories `service/`, `scenes/`, `setup/`. All test files manually add `../../src` to `sys.path`. Mock the module-level config by patching `services.<module>.config`, not `config` directly (e.g., `patch('services.flightLogic.config')`).

## Adding a New Scene
1. Create scene class in `src/scenes/` with methods decorated via `@Animator.KeyFrame.add(...)`
2. Add it to `Display`'s inheritance list in `src/display/__init__.py`
3. The `Animator._register_keyframes()` introspection picks up decorated methods automatically

## Release Process
See `.github/workflows/promote-rc-to-main.yml` for RC → main promotion.
