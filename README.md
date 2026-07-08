# Commit Graph Time Machine

Commit Graph Time Machine is a Python and Pygame-based desktop tool for designing, visualizing, and exporting commit activity as a weekly contribution matrix. It is intended for developers who want to plan a year of contributions, experiment with commit patterns, save reusable templates, and drive local repository workflows from a single interface.

## Overview

This project combines:
- an interactive weekly contribution grid,
- JSON-backed persistence for matrix states,
- template loading and saving,
- random matrix generation,
- local repository operations such as commit, push, archive, and service integration.

The tool is designed to feel like a lightweight planning board for contribution history rather than a full Git client.

## Requirements

### Software requirements
- Python 3.13 or newer
- Git
- Pygame

### Python dependencies
Install the runtime dependency with:

```bash
pip install pygame
```

If you are using a virtual environment, activate it first and then install dependencies from the project folder.

## Installation

```bash
cd time_machine
python -m venv .venv
.venv\Scripts\activate
pip install pygame
```

Run the application with:

```bash
python main.py
```

## Features

- Interactive commit matrix editor
- Click and drag drawing for commit intensity levels
- Random matrix generation from configurable maximum levels
- Save and load reusable templates as JSON files
- Default dataset loading
- Settings panel for year, profile, max level, and behavior options
- Mock commit, push, and archive workflows
- Repository service integration panel for repository inspection/creation/deletion
- About dialog and footer branding

## Usage

### Start the app
```bash
python main.py
```

### Command-line options
```bash
python main.py --year 2025 --file data.json
python main.py --no-settings
```

### Main interactions
- Click cells to increase commit intensity
- Right-click to clear cells
- Drag to paint or erase when drag mode is enabled
- Press N for a new matrix
- Press R to generate a random matrix
- Press D to load the default template data
- Press S to open settings
- Press T to open the template panel
- Use 1-9 to load templates and Ctrl+1-9 to save templates
- Press Esc to exit or close panels

## Architecture

The application is organized around a single main UI loop in [src/matrix.py](src/matrix.py) and several supporting modules:

- [src/module/data_persistence.py](src/module/data_persistence.py): loads and saves matrix state, normalizes coordinates, and manages JSON persistence
- [src/module/daytime.py](src/module/daytime.py): converts between calendar dates and the weekly matrix layout
- [src/module/matrix_logic.py](src/module/matrix_logic.py): generates matrix data and random commit schedules
- [src/module/deploy.py](src/module/deploy.py): handles mock commit, archive, and push operations
- [src/module/repo_services.py](src/module/repo_services.py): repository service provider integration
- [src/module/visualization.py](src/module/visualization.py): visualization helpers for the matrix view

The app uses a state-driven UI structure with panels for settings, templates, services, and about information.

## Project Structure

```text
main.py                 # CLI entry point
pyproject.toml          # Python project metadata
README.md               # Project overview and usage guide
Requirements.md         # Original feature brief
LICENSE                 # Proprietary closed-source license
schema/                 # JSON templates and defaults
src/                    # Application source code
tests/                  # Regression tests for persistence and data handling
```

## Development

### Running locally
1. Create and activate a virtual environment
2. Install dependencies
3. Start the app with `python main.py`

### Syntax check
```bash
python -m py_compile src/matrix.py
```

### Testing
If regression tests are available, run:

```bash
python -m unittest discover -s tests
```

### Coding style and conventions
- Keep the UI and persistence logic separated where possible
- Prefer centralized helpers for data load/save behavior
- Keep matrix coordinate handling consistent across UI and JSON layers
- Update tests when changing persistence behavior

## License

This repository is distributed under a closed-source proprietary license. See [LICENSE](LICENSE) for details.

## Author

Bach Nguyen Ngoc <bachnn92@gmail.com>

## Notes

This tool is intended for local planning and workflow experiments. It is not a replacement for a full Git client, but it provides a compact way to model contribution patterns and repository actions visually.
