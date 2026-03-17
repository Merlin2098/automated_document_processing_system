# DocFlow

## Overview

DocFlow is a Python-based desktop system for high-volume PDF processing. It automates document splitting, renaming, deduplication, and grouping for administrative, accounting, and HR workflows, reducing manual effort and improving output consistency.

## Architecture

DocFlow follows a rule-driven document processing architecture:

`Input PDFs -> Validation/Cleaning -> Text Extraction -> Rule-Based Splitting -> JSON-Driven Renaming -> Grouping/Consolidation -> Validation and Logs`

At a high level, the system combines a desktop UI, extractor modules for PDF parsing, and a batch-style processing pipeline focused on traceability and performance.

## Tech Stack

- Python
- PySide6
- PyPDF2
- pdfplumber
- pdfminer.six
- pypdfium2
- JSON-based mapping rules
- Windows standalone packaging (`.exe`)

## How It Works

1. Input files are validated and cleaned before processing starts.
2. PDF content is parsed to extract text and detect relevant patterns.
3. Business rules determine how documents should be split.
4. Pre-generated JSON mappings drive the renaming stage.
5. Processed files are grouped and consolidated into final outputs.
6. Logs, file counts, and output checks are generated for validation and traceability.

## Example / Output

Typical outputs include:

- Split PDF files based on document rules
- Renamed files following structured business mappings
- Grouped final document batches
- Processing logs for auditing
- Validation reports for quality control

Note: the full business workflow includes an intermediate macro-based normalization layer that is not included in this repository due to confidentiality constraints.
