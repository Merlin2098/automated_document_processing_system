# DocFlow Project Initialization Guide

## Purpose

This document gives a clean starting point for working on DocFlow Eventuales as a developer or maintainer. It explains what the project is, how it is laid out, and how to run or package it without reverse-engineering the repository first.

## What This Project Is

DocFlow Eventuales is a desktop application for structured PDF processing. The application combines:

- a PySide6 user interface
- background workers for long-running tasks
- extractor modules for parsing PDF content
- pipeline stages that transform, rename, validate, and consolidate document sets
- packaging support for Windows distribution via PyInstaller

## Startup Checklist

1. Open the repository root.
2. Create or activate the local virtual environment.
3. Install `requirements.txt`.
4. Run `main.py` to verify the desktop app starts.
5. Run `generar_onedir.py` only when you need a distributable Windows build.

## Recommended Commands

### Create environment

```powershell
py -3 -m venv .venv
```

### Activate environment

```powershell
.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Launch application

```powershell
.venv\Scripts\python.exe main.py
```

### Build Windows onedir package

```powershell
.venv\Scripts\python.exe generar_onedir.py
```

## Key Runtime Areas

### UI layer

- `ui/main_window.py`
- `ui/splash_screen.py`
- `ui/tabs/`
- `ui/widgets/`
- `ui/workers/`

This layer manages the desktop experience, themes, progress reporting, and async/background execution through worker classes.

### Processing layer

- `core_pipeline/`
- `core_sunat/`
- `core_tools/`

This is where the actual business logic lives. Most future behavior changes should happen here rather than inside packaging code.

### Extraction layer

- `extractores/`

These modules hold parsing and pattern-extraction logic for the supported document types.

### Shared utilities

- `utils/logger.py`
- `utils/logger_config.py`
- `utils/path_helper.py`
- `utils/theme_manager.py`

These files support logging, frozen-path resolution, and UI theme configuration.

### Packaging support

- `generar_onedir.py`
- `hooks/pyi_rth_multiprocessing.py`
- `resources/`

The packaging flow collects runtime dependencies, UI resources, themes, and multiprocessing support for the Windows executable distribution.

## Working Agreement For Safe Changes

- Prefer small, measurable changes over architectural rewrites.
- If PDF extraction breaks because upstream document formats changed, start in `extractores/`.
- If a UI behavior changes, inspect the relevant file under `ui/tabs/`, `ui/widgets/`, or `ui/workers/`.
- If packaging breaks, inspect `generar_onedir.py`, `hooks/`, and `resources/`.
- Keep performance-sensitive logic stable unless there is evidence a change is necessary.

## Expected Build Resources

The Windows packaging script expects these resources to be present:

- `resources/app.ico`
- `resources/config.json`
- `resources/themes/theme_dark.json`
- `resources/themes/theme_light.json`
- `hooks/pyi_rth_multiprocessing.py`

## Next Good Documentation Targets

- document the responsibility of each pipeline step in `core_pipeline/`
- add sample input and output folder conventions
- add a troubleshooting guide for packaging failures
- document expected JSON mapping formats for rename flows
