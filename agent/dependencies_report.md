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

- **External libraries**: `sys`, `pathspec`, `re`, `pathlib`, `ast` (+2 more)

### `agent_tools.treemap`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `sys`, `pathspec`, `os`

### `core_pipeline.step1_generar`

**Direct dependencies**: 4 (1 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PySide6`, `os`

### `core_pipeline.step2_mover`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PySide6`, `re`, `datetime`, `pathlib` (+2 more)

### `core_pipeline.step3_generar_diagnostico`

**Direct dependencies**: 19 (7 modules, 0 configs, 12 libraries)

- **Internal modules**: `utils`, `extractores`, `extractores`, `extractores`, `extractores`, `extractores`, `extractores`
- **External libraries**: `sys`, `multiprocessing`, `pandas`, `duckdb`, `openpyxl` (+7 more)

### `core_pipeline.step4_rename`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PySide6`, `json`, `pathlib`, `os`

### `core_pipeline.step5_unir_final`

**Direct dependencies**: 17 (2 modules, 2 configs, 13 libraries)

- **Internal modules**: `utils`, `extractores`
- **Config files**: `     ├── diagnostico_merge_{timestamp}.json`, `diagnostico_merge_{timestamp}.json`
- **External libraries**: `concurrent`, `sys`, `pandas`, `PySide6`, `re` (+8 more)

### `core_sunat.sunat`

**Direct dependencies**: 10 (2 modules, 0 configs, 8 libraries)

- **Internal modules**: `extractores`, `utils`
- **External libraries**: `concurrent`, `sys`, `openpyxl`, `datetime`, `tkinter` (+3 more)

### `core_sunat.sunat_duplicados`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `time`, `re`, `tkinter`, `os` (+2 more)

### `core_sunat.sunat_rename`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `time`, `datetime`, `tkinter`, `pathlib` (+2 more)

### `core_tools.dividir_pdf`

**Direct dependencies**: 4 (1 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PyPDF2`, `os`

### `extractores.__init__`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `sys`, `openpyxl`, `typing`, `json`, `subprocess`

### `extractores.contract_number_extractor`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `re`, `typing`, `pdfplumber`, `os`

### `extractores.extractor_afp`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `pdfplumber`, `re`, `typing`, `pathlib`

### `extractores.extractor_boleta`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `re`, `typing`, `PyPDF2`, `pathlib`

### `extractores.extractor_quinta`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `pdfplumber`, `re`, `typing`, `pathlib`

### `extractores.extractor_sunat`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `pdfplumber`, `re`, `typing`, `pathlib`

### `generar_onedir`

**Direct dependencies**: 14 (0 modules, 5 configs, 9 libraries)

- **Config files**: `theme_light.json`, `theme_dark.json`, `   ✅ config.json`, `config.json`, `*.json`
- **External libraries**: `sys`, `time`, `shutil`, `pathlib`, `pkg_resources` (+4 more)

### `hooks.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `hooksi_rth_multiprocessing`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `sys`, `multiprocessing`, `os`

### `main`

**Direct dependencies**: 6 (3 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`, `ui`, `ui`
- **External libraries**: `sys`, `multiprocessing`, `PySide6`

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
- **Config files**: `Carga configuración desde config.json`, `config.json`
- **External libraries**: `PySide6`, `json`, `os`

### `ui.tabs.tab_quick_tools`

**Direct dependencies**: 5 (2 modules, 0 configs, 3 libraries)

- **Internal modules**: `ui`, `ui`
- **External libraries**: `sys`, `PySide6`, `os`

### `ui.tabs.tab_settings`

**Direct dependencies**: 9 (1 modules, 2 configs, 6 libraries)

- **Internal modules**: `utils`
- **Config files**: `Carga la configuración actual desde config.json`, `config.json`
- **External libraries**: `PySide6`, `psutil`, `datetime`, `json`, `pathlib` (+1 more)

### `ui.widgets.__init__`

**Direct dependencies**: 4 (4 modules, 0 configs, 0 libraries)

- **Internal modules**: `monitoring_panel`, `console_widget`, `file_selector`, `stepper_widget`

### `ui.widgets.console_widget`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `PySide6`, `datetime`

### `ui.widgets.file_selector`

**Direct dependencies**: 1 (0 modules, 0 configs, 1 libraries)

- **External libraries**: `PySide6`

### `ui.widgets.monitoring_panel`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `PySide6`, `datetime`

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
- **External libraries**: `sys`, `PySide6`, `datetime`, `core_pipeline`, `PyPDF2` (+2 more)

### `ui.workers.core_pipeline_step3_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `PySide6`, `time`, `core_pipeline`, `os` (+1 more)

### `ui.workers.core_pipeline_step4_worker`

**Direct dependencies**: 9 (1 modules, 0 configs, 8 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `concurrent`, `PySide6`, `time`, `core_pipeline` (+3 more)

### `ui.workers.core_pipeline_step5_worker`

**Direct dependencies**: 10 (1 modules, 0 configs, 9 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `pandas`, `PySide6`, `time`, `core_pipeline` (+4 more)

### `ui.workers.pdf_splitter_worker`

**Direct dependencies**: 8 (1 modules, 0 configs, 7 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `core_tools`, `PySide6`, `datetime`, `PyPDF2` (+2 more)

### `ui.workers.sunat_diagnostic_worker`

**Direct dependencies**: 6 (1 modules, 0 configs, 5 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `core_sunat`, `PySide6`, `os`, `traceback`

### `ui.workers.sunat_duplicates_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `core_sunat`, `PySide6`, `time`, `os` (+1 more)

### `ui.workers.sunat_rename_worker`

**Direct dependencies**: 7 (1 modules, 0 configs, 6 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `core_sunat`, `PySide6`, `time`, `os` (+1 more)

### `utils.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `excel_converter`

### `utils.excel_converter`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `sys`, `openpyxl`, `typing`, `json`, `subprocess`

### `utils.logger`

**Direct dependencies**: 4 (1 modules, 0 configs, 3 libraries)

- **Internal modules**: `utils`
- **External libraries**: `sys`, `logging`, `typing`

### `utils.logger_config`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `time`, `pathlib`, `logging`, `platform`

### `utils.path_helper`

**Direct dependencies**: 4 (0 modules, 2 configs, 2 libraries)

- **Config files**: `config.json`, `theme_dark.json`
- **External libraries**: `sys`, `pathlib`

### `utils.theme_manager`

**Direct dependencies**: 10 (2 modules, 4 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`
- **Config files**: `Carga la configuración del usuario desde config.json`, `theme_*.json`, `Guarda la configuración del usuario en config.json`, `config.json`
- **External libraries**: `PySide6`, `datetime`, `json`, `pathlib`

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
├── 🔗 sys
├── 🔗 pathspec
├── 🔗 re
├── 🔗 pathlib
├── 🔗 ast
├── 🔗 os
└── 🔗 collections
```

### agent_tools.treemap

```
agent_tools.treemap
├── 🔗 sys
├── 🔗 pathspec
└── 🔗 os
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
├── 🔗 sys
├── 🔗 PySide6
├── 🔗 re
├── 🔗 datetime
├── 🔗 pathlib
├── 🔗 PyPDF2
└── 🔗 os
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
├── 🔗 sys
├── 🔗 multiprocessing
├── 🔗 pandas
├── 🔗 duckdb
├── 🔗 openpyxl
├── 🔗 time
├── 🔗 re
├── 🔗 PySide6
├── 🔗 os
├── 🔗 typing
├── 🔗 traceback
└── 🔗 gc
```

### core_pipeline.step4_rename

```
core_pipeline.step4_rename
├── 📦 utils
├── 🔗 sys
├── 🔗 PySide6
├── 🔗 json
├── 🔗 pathlib
└── 🔗 os
```

### core_pipeline.step5_unir_final

```
core_pipeline.step5_unir_final
├── 📦 utils
├── 📦 extractores
├── 📄      ├── diagnostico_merge_{timestamp}.json
├── 📄 diagnostico_merge_{timestamp}.json
├── 🔗 concurrent
├── 🔗 sys
├── 🔗 pandas
├── 🔗 PySide6
├── 🔗 re
├── 🔗 datetime
├── 🔗 typing
├── 🔗 shutil
├── 🔗 json
├── 🔗 pyarrow
├── 🔗 PyPDF2
├── 🔗 os
└── 🔗 threading
```

### core_sunat.sunat

```
core_sunat.sunat
├── 📦 extractores
├── 📦 utils
├── 🔗 concurrent
├── 🔗 sys
├── 🔗 openpyxl
├── 🔗 datetime
├── 🔗 tkinter
├── 🔗 pathlib
├── 🔗 os
└── 🔗 traceback
```

### core_sunat.sunat_duplicados

```
core_sunat.sunat_duplicados
├── 📦 utils
├── 🔗 sys
├── 🔗 time
├── 🔗 re
├── 🔗 tkinter
├── 🔗 os
├── 🔗 typing
└── 🔗 collections
```

### core_sunat.sunat_rename

```
core_sunat.sunat_rename
├── 📦 utils
├── 🔗 sys
├── 🔗 time
├── 🔗 datetime
├── 🔗 tkinter
├── 🔗 pathlib
├── 🔗 json
└── 🔗 os
```

### core_tools.dividir_pdf

```
core_tools.dividir_pdf
├── 📦 utils
├── 🔗 sys
├── 🔗 PyPDF2
└── 🔗 os
```

### extractores.__init__

```
extractores.__init__
├── 🔗 sys
├── 🔗 openpyxl
├── 🔗 typing
├── 🔗 json
└── 🔗 subprocess
```

### extractores.contract_number_extractor

```
extractores.contract_number_extractor
├── 📦 utils
├── 🔗 sys
├── 🔗 re
├── 🔗 typing
├── 🔗 pdfplumber
└── 🔗 os
```

### extractores.extractor_afp

```
extractores.extractor_afp
├── 🔗 pdfplumber
├── 🔗 re
├── 🔗 typing
└── 🔗 pathlib
```

### extractores.extractor_boleta

```
extractores.extractor_boleta
├── 🔗 re
├── 🔗 typing
├── 🔗 PyPDF2
└── 🔗 pathlib
```

### extractores.extractor_quinta

```
extractores.extractor_quinta
├── 🔗 pdfplumber
├── 🔗 re
├── 🔗 typing
└── 🔗 pathlib
```

### extractores.extractor_sunat

```
extractores.extractor_sunat
├── 🔗 pdfplumber
├── 🔗 re
├── 🔗 typing
└── 🔗 pathlib
```

### generar_onedir

```
generar_onedir
├── 📄 theme_light.json
├── 📄 theme_dark.json
├── 📄    ✅ config.json
├── 📄 config.json
├── 📄 *.json
├── 🔗 sys
├── 🔗 time
├── 🔗 shutil
├── 🔗 pathlib
├── 🔗 pkg_resources
├── 🔗 os
├── 🔗 subprocess
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
├── 🔗 multiprocessing
└── 🔗 os
```

### main

```
main
├── 📦 utils
├── 📦 ui
├── 📦 ui
├── 🔗 sys
├── 🔗 multiprocessing
└── 🔗 PySide6
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
├── 📄 Carga configuración desde config.json
├── 📄 config.json
├── 🔗 PySide6
├── 🔗 json
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
├── 📄 Carga la configuración actual desde config.json
├── 📄 config.json
├── 🔗 PySide6
├── 🔗 psutil
├── 🔗 datetime
├── 🔗 json
├── 🔗 pathlib
└── 🔗 os
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
├── 🔗 PySide6
└── 🔗 datetime
```

### ui.widgets.file_selector

```
ui.widgets.file_selector
└── 🔗 PySide6
```

### ui.widgets.monitoring_panel

```
ui.widgets.monitoring_panel
├── 🔗 PySide6
└── 🔗 datetime
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
├── 🔗 sys
├── 🔗 PySide6
├── 🔗 datetime
├── 🔗 core_pipeline
├── 🔗 PyPDF2
├── 🔗 os
└── 🔗 traceback
```

### ui.workers.core_pipeline_step3_worker

```
ui.workers.core_pipeline_step3_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 PySide6
├── 🔗 time
├── 🔗 core_pipeline
├── 🔗 os
└── 🔗 traceback
```

### ui.workers.core_pipeline_step4_worker

```
ui.workers.core_pipeline_step4_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 concurrent
├── 🔗 PySide6
├── 🔗 time
├── 🔗 core_pipeline
├── 🔗 os
├── 🔗 threading
└── 🔗 traceback
```

### ui.workers.core_pipeline_step5_worker

```
ui.workers.core_pipeline_step5_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 pandas
├── 🔗 PySide6
├── 🔗 time
├── 🔗 core_pipeline
├── 🔗 os
├── 🔗 threading
├── 🔗 PyPDF2
└── 🔗 traceback
```

### ui.workers.pdf_splitter_worker

```
ui.workers.pdf_splitter_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 core_tools
├── 🔗 PySide6
├── 🔗 datetime
├── 🔗 PyPDF2
├── 🔗 os
└── 🔗 traceback
```

### ui.workers.sunat_diagnostic_worker

```
ui.workers.sunat_diagnostic_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 core_sunat
├── 🔗 PySide6
├── 🔗 os
└── 🔗 traceback
```

### ui.workers.sunat_duplicates_worker

```
ui.workers.sunat_duplicates_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 core_sunat
├── 🔗 PySide6
├── 🔗 time
├── 🔗 os
└── 🔗 traceback
```

### ui.workers.sunat_rename_worker

```
ui.workers.sunat_rename_worker
├── 📦 utils
├── 🔗 sys
├── 🔗 core_sunat
├── 🔗 PySide6
├── 🔗 time
├── 🔗 os
└── 🔗 traceback
```

### utils.__init__

```
utils.__init__
└── 📦 excel_converter
```

### utils.excel_converter

```
utils.excel_converter
├── 🔗 sys
├── 🔗 openpyxl
├── 🔗 typing
├── 🔗 json
└── 🔗 subprocess
```

### utils.logger

```
utils.logger
├── 📦 utils
├── 🔗 sys
├── 🔗 logging
└── 🔗 typing
```

### utils.logger_config

```
utils.logger_config
├── 🔗 time
├── 🔗 pathlib
├── 🔗 logging
└── 🔗 platform
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
├── 📄 Carga la configuración del usuario desde config.json
├── 📄 theme_*.json
├── 📄 Guarda la configuración del usuario en config.json
├── 📄 config.json
├── 🔗 PySide6
├── 🔗 datetime
├── 🔗 json
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
| core_pipeline.step5_unir_final | Entry Point | 2 | 2 | 13 |
| core_sunat.sunat | Entry Point | 2 | 0 | 8 |
| core_sunat.sunat_duplicados | Entry Point | 1 | 0 | 7 |
| core_sunat.sunat_rename | Entry Point | 1 | 0 | 7 |
| core_tools.dividir_pdf | Entry Point | 1 | 0 | 3 |
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
| utils.logger | Entry Point | 1 | 0 | 3 |
| utils.logger_config | Entry Point | 0 | 0 | 4 |
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
