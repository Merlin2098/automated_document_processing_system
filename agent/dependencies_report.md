# Project Dependency Analysis

> **Purpose**: This document maps dependencies between Python modules, configuration files, and external libraries. Use it to understand the architecture and relationships between components.

## Executive Summary

- **Total Python modules**: 51
- **Project entry points**: 51
- **Configuration files**: 12
- **Unique external libraries**: 33

---

## 1. Project Entry Points

These modules are the **main scripts** that initiate execution (they are not imported by other modules):

### `__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `agent_tools.analyze_dependencies`

**Direct dependencies**: 7 (0 modules, 0 configs, 7 libraries)

- **External libraries**: `pathlib`, `re`, `os`, `ast`, `sys` (+2 more)

### `agent_tools.treemap`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `sys`, `os`, `pathspec`

### `core_pipeline.step1_generar`

**Direct dependencies**: 4 (1 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PySide6`, `os`

### `core_pipeline.step2_mover`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `datetime`, `pathlib`, `PyPDF2`, `re`, `os` (+2 more)

### `core_pipeline.step3_generar_diagnostico`

**Direct dependencies**: 19 (7 modules, 0 configs, 12 libraries)

- **Internal modules**: `utils`, `extractores`, `extractores`, `extractores`, `extractores`, `extractores`, `extractores`
- **External libraries**: `re`, `openpyxl`, `os`, `typing`, `duckdb` (+7 more)

### `core_pipeline.step4_rename`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `pathlib`, `os`, `json`, `sys`, `PySide6`

### `core_pipeline.step5_unir_final`

**Direct dependencies**: 18 (2 modules, 2 configs, 14 libraries)

- **Internal modules**: `utils`, `extractores`
- **Config files**: `diagnostico_merge_{timestamp}.json`, `     ├── diagnostico_merge_{timestamp}.json`
- **External libraries**: `datetime`, `PyPDF2`, `re`, `pyarrow`, `os` (+9 more)

### `core_sunat.sunat`

**Direct dependencies**: 10 (2 modules, 0 configs, 8 libraries)

- **Internal modules**: `extractores`, `utils`
- **External libraries**: `datetime`, `pathlib`, `tkinter`, `openpyxl`, `os` (+3 more)

### `core_sunat.sunat_duplicados`

**Direct dependencies**: 9 (1 modules, 0 configs, 8 libraries)

- **Internal modules**: `utils`
- **External libraries**: `tkinter`, `re`, `os`, `typing`, `time` (+3 more)

### `core_sunat.sunat_rename`

**Direct dependencies**: 9 (1 modules, 0 configs, 8 libraries)

- **Internal modules**: `utils`
- **External libraries**: `datetime`, `pathlib`, `tkinter`, `os`, `json` (+3 more)

### `core_tools.dividir_pdf`

**Direct dependencies**: 5 (1 modules, 0 configs, 4 libraries)

- **Internal modules**: `utils`
- **External libraries**: `traceback`, `sys`, `PyPDF2`, `os`

### `extractores.__init__`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `openpyxl`, `subprocess`, `typing`, `json`, `sys`

### `extractores.contract_number_extractor`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `pdfplumber`, `re`, `os`, `typing`, `sys`

### `extractores.extractor_afp`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `re`, `pathlib`, `pdfplumber`, `typing`

### `extractores.extractor_boleta`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `re`, `pathlib`, `PyPDF2`, `typing`

### `extractores.extractor_quinta`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `re`, `pathlib`, `pdfplumber`, `typing`

### `extractores.extractor_sunat`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `re`, `pathlib`, `pdfplumber`, `typing`

### `generar_onedir`

**Direct dependencies**: 14 (0 modules, 5 configs, 9 libraries)

- **Config files**: `   ✅ config.json`, `config.json`, `*.json`, `theme_dark.json`, `theme_light.json`
- **External libraries**: `pkg_resources`, `pathlib`, `os`, `subprocess`, `shutil` (+4 more)

### `hooks.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `hooksi_rth_multiprocessing`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `sys`, `os`, `multiprocessing`

### `main`

**Direct dependencies**: 6 (3 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`, `ui`, `ui`
- **External libraries**: `sys`, `PySide6`, `multiprocessing`

### `ui.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `main_window`

### `ui.main_window`

**Direct dependencies**: 10 (8 modules, 0 configs, 2 libraries)

- **Internal modules**: `utils`, `ui`, `ui`, `utils`, `ui`, `ui`, `ui`, `ui`
- **External libraries**: `PySide6`, `os`

### `ui.splash_screen`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `PySide6`, `os`

### `ui.tabs.__init__`

**Direct dependencies**: 4 (4 modules, 0 configs, 0 libraries)

- **Internal modules**: `tab_quick_tools`, `tab_pipeline_core`, `tab_pipeline_sunat`, `tab_settings`

### `ui.tabs.tab_pipeline_core`

**Direct dependencies**: 9 (7 modules, 0 configs, 2 libraries)

- **Internal modules**: `ui`, `ui`, `ui`, `ui`, `ui`, `ui`, `ui`
- **External libraries**: `PySide6`, `os`

### `ui.tabs.tab_pipeline_sunat`

**Direct dependencies**: 10 (5 modules, 2 configs, 3 libraries)

- **Internal modules**: `ui`, `ui`, `ui`, `ui`, `ui`
- **Config files**: `config.json`, `Carga configuración desde config.json`
- **External libraries**: `json`, `PySide6`, `os`

### `ui.tabs.tab_quick_tools`

**Direct dependencies**: 5 (2 modules, 0 configs, 3 libraries)

- **Internal modules**: `ui`, `ui`
- **External libraries**: `sys`, `PySide6`, `os`

### `ui.tabs.tab_settings`

**Direct dependencies**: 9 (1 modules, 2 configs, 6 libraries)

- **Internal modules**: `utils`
- **Config files**: `config.json`, `Carga la configuración actual desde config.json`
- **External libraries**: `datetime`, `pathlib`, `psutil`, `os`, `json` (+1 more)

### `ui.widgets.__init__`

**Direct dependencies**: 4 (4 modules, 0 configs, 0 libraries)

- **Internal modules**: `monitoring_panel`, `console_widget`, `file_selector`, `stepper_widget`

### `ui.widgets.console_widget`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `datetime`, `PySide6`

### `ui.widgets.file_selector`

**Direct dependencies**: 1 (0 modules, 0 configs, 1 libraries)

- **External libraries**: `PySide6`

### `ui.widgets.monitoring_panel`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `datetime`, `PySide6`

### `ui.widgets.stepper_widget`

**Direct dependencies**: 1 (0 modules, 0 configs, 1 libraries)

- **External libraries**: `PySide6`

### `ui.workers.__init__`

**Direct dependencies**: 9 (9 modules, 0 configs, 0 libraries)

- **Internal modules**: `pdf_splitter_worker`, `sunat_diagnostic_worker`, `sunat_rename_worker`, `sunat_duplicates_worker`, `core_pipeline_step1_worker`, `core_pipeline_step2_worker`, `core_pipeline_step3_worker`, `core_pipeline_step4_worker`, `core_pipeline_step5_worker`

### `ui.workers.core_pipeline_step1_worker`

**Direct dependencies**: 3 (1 modules, 0 configs, 2 libraries)

- **Internal modules**: `utils`
- **External libraries**: `PySide6`, `os`

### `ui.workers.core_pipeline_step2_worker`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `traceback`, `datetime`, `PyPDF2`, `os`, `sys` (+2 more)

### `ui.workers.core_pipeline_step3_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `traceback`, `os`, `time`, `sys`, `core_pipeline` (+1 more)

### `ui.workers.core_pipeline_step4_worker`

**Direct dependencies**: 9 (1 modules, 0 configs, 8 libraries)

- **Internal modules**: `utils`
- **External libraries**: `traceback`, `os`, `time`, `sys`, `concurrent` (+3 more)

### `ui.workers.core_pipeline_step5_worker`

**Direct dependencies**: 10 (1 modules, 0 configs, 9 libraries)

- **Internal modules**: `utils`
- **External libraries**: `traceback`, `PyPDF2`, `os`, `pandas`, `time` (+4 more)

### `ui.workers.pdf_splitter_worker`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `datetime`, `PyPDF2`, `core_tools`, `os`, `sys` (+2 more)

### `ui.workers.sunat_diagnostic_worker`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `os`, `core_sunat`, `sys`, `traceback`, `PySide6`

### `ui.workers.sunat_duplicates_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `os`, `core_sunat`, `time`, `sys`, `traceback` (+1 more)

### `ui.workers.sunat_rename_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `os`, `core_sunat`, `time`, `sys`, `traceback` (+1 more)

### `utils.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `excel_converter`

### `utils.excel_converter`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `openpyxl`, `subprocess`, `typing`, `json`, `sys`

### `utils.logger`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `pathlib`, `typing`, `sys`, `logging`, `traceback`

### `utils.logger_config`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `pathlib`, `os`, `time`, `platform`, `logging`

### `utils.path_helper`

**Direct dependencies**: 4 (0 modules, 2 configs, 2 libraries)

- **Config files**: `config.json`, `theme_dark.json`
- **External libraries**: `sys`, `pathlib`

### `utils.theme_manager`

**Direct dependencies**: 10 (2 modules, 4 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`
- **Config files**: `config.json`, `theme_*.json`, `Carga la configuración del usuario desde config.json`, `Guarda la configuración del usuario en config.json`
- **External libraries**: `PySide6`, `json`, `datetime`, `pathlib`

---

## 2. Full Dependency Map

This tree shows **all recursive dependencies** for each entry point:

**Legend**:
- 📦 Project Python Module
- 📄 Configuration File (JSON, YAML, SQL, etc.)
- 🔗 External Library (installed via pip)

### __init__

```
__init__

```

### agent_tools.analyze_dependencies

```
agent_tools.analyze_dependencies
├── 🔗 pathlib
├── 🔗 re
├── 🔗 os
├── 🔗 ast
├── 🔗 sys
├── 🔗 pathspec
└── 🔗 collections
```

### agent_tools.treemap

```
agent_tools.treemap
├── 🔗 sys
├── 🔗 os
└── 🔗 pathspec
```

### core_pipeline.step1_generar

```
core_pipeline.step1_generar
├── 📦 utils
├── 🔗 sys
├── 🔗 PySide6
└── 🔗 os
```

### core_pipeline.step2_mover

```
core_pipeline.step2_mover
├── 📦 utils
├── 🔗 datetime
├── 🔗 pathlib
├── 🔗 PyPDF2
├── 🔗 re
├── 🔗 os
├── 🔗 sys
└── 🔗 PySide6
```

### core_pipeline.step3_generar_diagnostico

```
core_pipeline.step3_generar_diagnostico
├── 📦 utils
├── 📦 extractores
├── 📦 extractores
├── 📦 extractores
├── 📦 extractores
├── 📦 extractores
├── 📦 extractores
├── 🔗 re
├── 🔗 openpyxl
├── 🔗 os
├── 🔗 typing
├── 🔗 duckdb
├── 🔗 gc
├── 🔗 sys
├── 🔗 time
├── 🔗 pandas
├── 🔗 traceback
├── 🔗 PySide6
└── 🔗 multiprocessing
```

### core_pipeline.step4_rename

```
core_pipeline.step4_rename
├── 📦 utils
├── 🔗 pathlib
├── 🔗 os
├── 🔗 json
├── 🔗 sys
└── 🔗 PySide6
```

### core_pipeline.step5_unir_final

```
core_pipeline.step5_unir_final
├── 📦 utils
├── 📦 extractores
├── 📄 diagnostico_merge_{timestamp}.json
├── 📄      ├── diagnostico_merge_{timestamp}.json
├── 🔗 datetime
├── 🔗 PyPDF2
├── 🔗 re
├── 🔗 pyarrow
├── 🔗 os
├── 🔗 typing
├── 🔗 shutil
├── 🔗 json
├── 🔗 sys
├── 🔗 pandas
├── 🔗 concurrent
├── 🔗 traceback
├── 🔗 PySide6
└── 🔗 threading
```

### core_sunat.sunat

```
core_sunat.sunat
├── 📦 extractores
├── 📦 utils
├── 🔗 datetime
├── 🔗 pathlib
├── 🔗 tkinter
├── 🔗 openpyxl
├── 🔗 os
├── 🔗 sys
├── 🔗 concurrent
└── 🔗 traceback
```

### core_sunat.sunat_duplicados

```
core_sunat.sunat_duplicados
├── 📦 utils
├── 🔗 tkinter
├── 🔗 re
├── 🔗 os
├── 🔗 typing
├── 🔗 time
├── 🔗 sys
├── 🔗 collections
└── 🔗 traceback
```

### core_sunat.sunat_rename

```
core_sunat.sunat_rename
├── 📦 utils
├── 🔗 datetime
├── 🔗 pathlib
├── 🔗 tkinter
├── 🔗 os
├── 🔗 json
├── 🔗 sys
├── 🔗 time
└── 🔗 traceback
```

### core_tools.dividir_pdf

```
core_tools.dividir_pdf
├── 📦 utils
├── 🔗 traceback
├── 🔗 sys
├── 🔗 PyPDF2
└── 🔗 os
```

### extractores.__init__

```
extractores.__init__
├── 🔗 openpyxl
├── 🔗 subprocess
├── 🔗 typing
├── 🔗 json
└── 🔗 sys
```

### extractores.contract_number_extractor

```
extractores.contract_number_extractor
├── 📦 utils
├── 🔗 pdfplumber
├── 🔗 re
├── 🔗 os
├── 🔗 typing
└── 🔗 sys
```

### extractores.extractor_afp

```
extractores.extractor_afp
├── 🔗 re
├── 🔗 pathlib
├── 🔗 pdfplumber
└── 🔗 typing
```

### extractores.extractor_boleta

```
extractores.extractor_boleta
├── 🔗 re
├── 🔗 pathlib
├── 🔗 PyPDF2
└── 🔗 typing
```

### extractores.extractor_quinta

```
extractores.extractor_quinta
├── 🔗 re
├── 🔗 pathlib
├── 🔗 pdfplumber
└── 🔗 typing
```

### extractores.extractor_sunat

```
extractores.extractor_sunat
├── 🔗 re
├── 🔗 pathlib
├── 🔗 pdfplumber
└── 🔗 typing
```

### generar_onedir

```
generar_onedir
├── 📄    ✅ config.json
├── 📄 config.json
├── 📄 *.json
├── 📄 theme_dark.json
├── 📄 theme_light.json
├── 🔗 pkg_resources
├── 🔗 pathlib
├── 🔗 os
├── 🔗 subprocess
├── 🔗 shutil
├── 🔗 sys
├── 🔗 time
├── 🔗 threading
└── 🔗 traceback
```

### hooks.__init__

```
hooks.__init__

```

### hooksi_rth_multiprocessing

```
hooksi_rth_multiprocessing
├── 🔗 sys
├── 🔗 os
└── 🔗 multiprocessing
```

### main

```
main
├── 📦 utils
├── 📦 ui
├── 📦 ui
├── 🔗 sys
├── 🔗 PySide6
└── 🔗 multiprocessing
```

### ui.__init__

```
ui.__init__
└── 📦 main_window
```

### ui.main_window

```
ui.main_window
├── 📦 utils
├── 📦 ui
├── 📦 ui
├── 📦 utils
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 🔗 PySide6
└── 🔗 os
```

### ui.splash_screen

```
ui.splash_screen
├── 🔗 PySide6
└── 🔗 os
```

### ui.tabs.__init__

```
ui.tabs.__init__
├── 📦 tab_quick_tools
├── 📦 tab_pipeline_core
├── 📦 tab_pipeline_sunat
└── 📦 tab_settings
```

### ui.tabs.tab_pipeline_core

```
ui.tabs.tab_pipeline_core
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 🔗 PySide6
└── 🔗 os
```

### ui.tabs.tab_pipeline_sunat

```
ui.tabs.tab_pipeline_sunat
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📦 ui
├── 📄 config.json
├── 📄 Carga configuración desde config.json
├── 🔗 json
├── 🔗 PySide6
└── 🔗 os
```

### ui.tabs.tab_quick_tools

```
ui.tabs.tab_quick_tools
├── 📦 ui
├── 📦 ui
├── 🔗 sys
├── 🔗 PySide6
└── 🔗 os
```

### ui.tabs.tab_settings

```
ui.tabs.tab_settings
├── 📦 utils
├── 📄 config.json
├── 📄 Carga la configuración actual desde config.json
├── 🔗 datetime
├── 🔗 pathlib
├── 🔗 psutil
├── 🔗 os
├── 🔗 json
└── 🔗 PySide6
```

### ui.widgets.__init__

```
ui.widgets.__init__
├── 📦 monitoring_panel
├── 📦 console_widget
├── 📦 file_selector
└── 📦 stepper_widget
```

### ui.widgets.console_widget

```
ui.widgets.console_widget
├── 🔗 datetime
└── 🔗 PySide6
```

### ui.widgets.file_selector

```
ui.widgets.file_selector
└── 🔗 PySide6
```

### ui.widgets.monitoring_panel

```
ui.widgets.monitoring_panel
├── 🔗 datetime
└── 🔗 PySide6
```

### ui.widgets.stepper_widget

```
ui.widgets.stepper_widget
└── 🔗 PySide6
```

### ui.workers.__init__

```
ui.workers.__init__
├── 📦 pdf_splitter_worker
├── 📦 sunat_diagnostic_worker
├── 📦 sunat_rename_worker
├── 📦 sunat_duplicates_worker
├── 📦 core_pipeline_step1_worker
├── 📦 core_pipeline_step2_worker
├── 📦 core_pipeline_step3_worker
├── 📦 core_pipeline_step4_worker
└── 📦 core_pipeline_step5_worker
```

### ui.workers.core_pipeline_step1_worker

```
ui.workers.core_pipeline_step1_worker
├── 📦 utils
├── 🔗 PySide6
└── 🔗 os
```

### ui.workers.core_pipeline_step2_worker

```
ui.workers.core_pipeline_step2_worker
├── 📦 utils
├── 🔗 traceback
├── 🔗 datetime
├── 🔗 PyPDF2
├── 🔗 os
├── 🔗 sys
├── 🔗 core_pipeline
└── 🔗 PySide6
```

### ui.workers.core_pipeline_step3_worker

```
ui.workers.core_pipeline_step3_worker
├── 📦 utils
├── 🔗 traceback
├── 🔗 os
├── 🔗 time
├── 🔗 sys
├── 🔗 core_pipeline
└── 🔗 PySide6
```

### ui.workers.core_pipeline_step4_worker

```
ui.workers.core_pipeline_step4_worker
├── 📦 utils
├── 🔗 traceback
├── 🔗 os
├── 🔗 time
├── 🔗 sys
├── 🔗 concurrent
├── 🔗 core_pipeline
├── 🔗 PySide6
└── 🔗 threading
```

### ui.workers.core_pipeline_step5_worker

```
ui.workers.core_pipeline_step5_worker
├── 📦 utils
├── 🔗 traceback
├── 🔗 PyPDF2
├── 🔗 os
├── 🔗 pandas
├── 🔗 time
├── 🔗 sys
├── 🔗 threading
├── 🔗 core_pipeline
└── 🔗 PySide6
```

### ui.workers.pdf_splitter_worker

```
ui.workers.pdf_splitter_worker
├── 📦 utils
├── 🔗 datetime
├── 🔗 PyPDF2
├── 🔗 core_tools
├── 🔗 os
├── 🔗 sys
├── 🔗 traceback
└── 🔗 PySide6
```

### ui.workers.sunat_diagnostic_worker

```
ui.workers.sunat_diagnostic_worker
├── 📦 utils
├── 🔗 os
├── 🔗 core_sunat
├── 🔗 sys
├── 🔗 traceback
└── 🔗 PySide6
```

### ui.workers.sunat_duplicates_worker

```
ui.workers.sunat_duplicates_worker
├── 📦 utils
├── 🔗 os
├── 🔗 core_sunat
├── 🔗 time
├── 🔗 sys
├── 🔗 traceback
└── 🔗 PySide6
```

### ui.workers.sunat_rename_worker

```
ui.workers.sunat_rename_worker
├── 📦 utils
├── 🔗 os
├── 🔗 core_sunat
├── 🔗 time
├── 🔗 sys
├── 🔗 traceback
└── 🔗 PySide6
```

### utils.__init__

```
utils.__init__
└── 📦 excel_converter
```

### utils.excel_converter

```
utils.excel_converter
├── 🔗 openpyxl
├── 🔗 subprocess
├── 🔗 typing
├── 🔗 json
└── 🔗 sys
```

### utils.logger

```
utils.logger
├── 📦 utils
├── 🔗 pathlib
├── 🔗 typing
├── 🔗 sys
├── 🔗 logging
└── 🔗 traceback
```

### utils.logger_config

```
utils.logger_config
├── 🔗 pathlib
├── 🔗 os
├── 🔗 time
├── 🔗 platform
└── 🔗 logging
```

### utils.path_helper

```
utils.path_helper
├── 📄 config.json
├── 📄 theme_dark.json
├── 🔗 sys
└── 🔗 pathlib
```

### utils.theme_manager

```
utils.theme_manager
├── 📦 utils
├── 📦 utils
├── 📄 config.json
├── 📄 theme_*.json
├── 📄 Carga la configuración del usuario desde config.json
├── 📄 Guarda la configuración del usuario en config.json
├── 🔗 PySide6
├── 🔗 json
├── 🔗 datetime
└── 🔗 pathlib
```

---

## 3. All Modules Index

Tabular view of all modules and their dependency counts:

| Module | Type | Local Deps. | Config Files | External Libs |
|--------|------|---------------|-----------------|---------------|
| __init__ | Entry Point | 0 | 0 | 0 |
| agent_tools.analyze_dependencies | Entry Point | 0 | 0 | 7 |
| agent_tools.treemap | Entry Point | 0 | 0 | 3 |
| core_pipeline.step1_generar | Entry Point | 1 | 0 | 3 |
| core_pipeline.step2_mover | Entry Point | 1 | 0 | 7 |
| core_pipeline.step3_generar_diagnostico | Entry Point | 7 | 0 | 12 |
| core_pipeline.step4_rename | Entry Point | 1 | 0 | 5 |
| core_pipeline.step5_unir_final | Entry Point | 2 | 2 | 14 |
| core_sunat.sunat | Entry Point | 2 | 0 | 8 |
| core_sunat.sunat_duplicados | Entry Point | 1 | 0 | 8 |
| core_sunat.sunat_rename | Entry Point | 1 | 0 | 8 |
| core_tools.dividir_pdf | Entry Point | 1 | 0 | 4 |
| extractores.__init__ | Entry Point | 0 | 0 | 5 |
| extractores.contract_number_extractor | Entry Point | 1 | 0 | 5 |
| extractores.extractor_afp | Entry Point | 0 | 0 | 4 |
| extractores.extractor_boleta | Entry Point | 0 | 0 | 4 |
| extractores.extractor_quinta | Entry Point | 0 | 0 | 4 |
| extractores.extractor_sunat | Entry Point | 0 | 0 | 4 |
| generar_onedir | Entry Point | 0 | 5 | 9 |
| hooks.__init__ | Entry Point | 0 | 0 | 0 |
| hooksi_rth_multiprocessing | Entry Point | 0 | 0 | 3 |
| main | Entry Point | 3 | 0 | 3 |
| ui.__init__ | Entry Point | 1 | 0 | 0 |
| ui.main_window | Entry Point | 8 | 0 | 2 |
| ui.splash_screen | Entry Point | 0 | 0 | 2 |
| ui.tabs.__init__ | Entry Point | 4 | 0 | 0 |
| ui.tabs.tab_pipeline_core | Entry Point | 7 | 0 | 2 |
| ui.tabs.tab_pipeline_sunat | Entry Point | 5 | 2 | 3 |
| ui.tabs.tab_quick_tools | Entry Point | 2 | 0 | 3 |
| ui.tabs.tab_settings | Entry Point | 1 | 2 | 6 |
| ui.widgets.__init__ | Entry Point | 4 | 0 | 0 |
| ui.widgets.console_widget | Entry Point | 0 | 0 | 2 |
| ui.widgets.file_selector | Entry Point | 0 | 0 | 1 |
| ui.widgets.monitoring_panel | Entry Point | 0 | 0 | 2 |
| ui.widgets.stepper_widget | Entry Point | 0 | 0 | 1 |
| ui.workers.__init__ | Entry Point | 9 | 0 | 0 |
| ui.workers.core_pipeline_step1_worker | Entry Point | 1 | 0 | 2 |
| ui.workers.core_pipeline_step2_worker | Entry Point | 1 | 0 | 7 |
| ui.workers.core_pipeline_step3_worker | Entry Point | 1 | 0 | 6 |
| ui.workers.core_pipeline_step4_worker | Entry Point | 1 | 0 | 8 |
| ui.workers.core_pipeline_step5_worker | Entry Point | 1 | 0 | 9 |
| ui.workers.pdf_splitter_worker | Entry Point | 1 | 0 | 7 |
| ui.workers.sunat_diagnostic_worker | Entry Point | 1 | 0 | 5 |
| ui.workers.sunat_duplicates_worker | Entry Point | 1 | 0 | 6 |
| ui.workers.sunat_rename_worker | Entry Point | 1 | 0 | 6 |
| utils.__init__ | Entry Point | 1 | 0 | 0 |
| utils.excel_converter | Entry Point | 0 | 0 | 5 |
| utils.logger | Entry Point | 1 | 0 | 5 |
| utils.logger_config | Entry Point | 0 | 0 | 5 |
| utils.path_helper | Entry Point | 0 | 2 | 2 |
| utils.theme_manager | Entry Point | 2 | 4 | 4 |

---

## 4. Configuration Files

Data/configuration files detected in code and modules using them:

- **`     ├── diagnostico_merge_{timestamp}.json`** → Used by: `core_pipeline.step5_unir_final`
- **`   ✅ config.json`** → Used by: `generar_onedir`
- **`*.json`** → Used by: `generar_onedir`
- **`Carga configuración desde config.json`** → Used by: `ui.tabs.tab_pipeline_sunat`
- **`Carga la configuración actual desde config.json`** → Used by: `ui.tabs.tab_settings`
- **`Carga la configuración del usuario desde config.json`** → Used by: `utils.theme_manager`
- **`Guarda la configuración del usuario en config.json`** → Used by: `utils.theme_manager`
- **`config.json`** → Used by: `generar_onedir`, `ui.tabs.tab_pipeline_sunat`, `ui.tabs.tab_settings`, `utils.path_helper`, `utils.theme_manager`
- **`diagnostico_merge_{timestamp}.json`** → Used by: `core_pipeline.step5_unir_final`
- **`theme_*.json`** → Used by: `utils.theme_manager`
- **`theme_dark.json`** → Used by: `generar_onedir`, `utils.path_helper`
- **`theme_light.json`** → Used by: `generar_onedir`

---

## Notes

- This file is **automatically generated** via a pre-commit hook.
- Imports are detected through static analysis (AST) of Python code.
- Configuration files are detected via regex of common patterns (`open()`, `read_csv()`, etc.).
- Circular dependencies might cause some modules to be missing from the full tree.
