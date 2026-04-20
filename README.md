# DocFlow Eventuales

## Overview

DocFlow Eventuales is a Windows desktop application for high-volume PDF processing. It automates splitting, renaming, deduplication, diagnostics, grouping, and auxiliary document utilities used in administrative, accounting, and HR-oriented workflows.

The repository is organized as a practical PySide6 application with a modular UI, extractor modules for PDF/text parsing, and a step-based processing pipeline focused on auditability, repeatability, and packaging as a distributable Windows app.

## Processing Flow

`Input PDFs -> Validation/Cleaning -> Text Extraction -> Rule-Based Splitting -> JSON-Driven Renaming -> Diagnostics -> Grouping/Consolidation -> Validation and Logs`

## Project Structure

- `main.py`: desktop application entrypoint
- `ui/`: main window, tabs, widgets, splash screen, and worker threads
- `core_pipeline/`: main multi-step processing pipeline
- `core_sunat/`: SUNAT-focused processing and duplicate handling
- `core_tools/`: auxiliary processing tools
- `extractores/`: domain extractors and text parsing helpers
- `utils/`: logging, themes, path resolution, and utility helpers
- `resources/`: app icon, config, and light/dark themes
- `hooks/`: runtime hooks required by packaging
- `docs/`: architecture notes and developer guidance

## Tech Stack

- Python
- PySide6
- PyPDF2
- pdfplumber
- pdfminer.six
- pypdfium2
- pandas
- duckdb
- JSON-driven processing rules
- PyInstaller for Windows `onedir` builds

## Local Development

### 1. Create and activate the virtual environment

Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Run the application

```powershell
.venv\Scripts\python.exe main.py
```

## Windows Build

The repository includes [`generar_onedir.py`](./generar_onedir.py), which packages the application as a Windows distributable folder using PyInstaller.

Run it from the project root with the project virtual environment active:

```powershell
.venv\Scripts\python.exe generar_onedir.py
```

Expected output folders:

- `dist/`
- `build/`
- `spec/`

The final app is generated as a folder-based distribution. You should distribute the full generated directory, not only the `.exe`.

## Main Functional Areas

- Core pipeline tab for staged batch processing
- SUNAT tools for diagnosis, rename, and duplicate analysis
- Quick tools for focused document operations
- Auxiliary rename flow driven by JSON mappings
- Theme-aware desktop UI with integrated logging and worker execution

## Additional Documentation

- [Project Init Guide](docs/project_init.md)
- [Architecture Notes](docs/architect.md)
- [Maintenance Notes](docs/dev_suggestions.md)

## Notes

- This repository contains the application runtime, but not every external business asset used in the full internal workflow.
- Some domain-specific macro or normalization steps are intentionally excluded for confidentiality reasons.
