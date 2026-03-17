# Technical Architecture of DocFlow

## Core Stack

- **Language:** Python
- **UI:** PySide6 for the desktop interface
- **Technical preference:** use standard libraries when they are sufficient and avoid unnecessary framework complexity

## Extraction and Rule Engine

Data extraction and regex-based pattern matching are handled with:

- **PyPDF2**
- **pdfplumber**
- **pdfminer.six**
- **pypdfium2**

## Processing Pipeline

The main document ETL flow is organized into the following stages:

1. **Cleaning:** validate inputs and remove invalid files.
2. **Splitting:** split PDFs by page boundaries or business rules.
3. **Renaming:** rename files based on pre-generated **JSON** mappings.
4. **Grouping:** group and consolidate final output documents.

## Performance

- Parallel processing to support high-volume workloads.
- Configurable worker execution based on machine capacity.

## Observability

- Integrated logging system.
- Automatic reports for auditing and traceability.

## Integrity Validation

- Processed-versus-expected file count checks.
- Stage-level result verification.
- Error and warning records for faster diagnosis.

## Confidentiality Note

- The full business workflow includes an intermediate macro layer for domain-specific rules.
- Those macros are not included in this repository due to confidentiality requirements.
