# Project Dependency Analysis

> **Purpose**: This document maps dependencies between Python modules, configuration files, and external libraries. Use it to understand the architecture and relationships between components.

## Executive Summary

- **Total Python modules**: 33
- **Project entry points**: 33
- **Configuration files**: 11
- **Unique external libraries**: 19

---

## 1. Project Entry Points

These modules are the **main scripts** that initiate execution (they are not imported by other modules):

### `__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `agent_tools.analyze_dependencies`

**Direct dependencies**: 7 (0 modules, 0 configs, 7 libraries)

- **External libraries**: `collections`, `pathspec`, `os`, `pathlib`, `sys` (+2 more)

### `agent_tools.treemap`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `pathspec`, `os`, `sys`

### `etl_core.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `etl_core.step1`

**Direct dependencies**: 12 (4 modules, 1 configs, 7 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`
- **Config files**: `data_learning_bronzetosilver.yaml`
- **External libraries**: `traceback`, `pandas`, `polars`, `pathlib`, `sys` (+2 more)

### `etl_core.step2`

**Direct dependencies**: 9 (4 modules, 1 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`
- **Config files**: `data_learning_silvertogold.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`, `polars`

### `etl_forms.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `etl_forms.step1_forms`

**Direct dependencies**: 11 (4 modules, 1 configs, 6 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`
- **Config files**: `forms_step1.yaml`
- **External libraries**: `traceback`, `pandas`, `pathlib`, `sys`, `numpy` (+1 more)

### `etl_forms.step2_forms`

**Direct dependencies**: 13 (8 modules, 2 configs, 3 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `Por favor, verifica los datos o actualiza el esquema en likert_scale.json`, `forms_step2.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`

### `etl_ita_subordinates.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `etl_ita_subordinates.step1_ita`

**Direct dependencies**: 11 (6 modules, 1 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `step1_ita.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`, `datetime`

### `etl_ita_subordinates.step1_managers`

**Direct dependencies**: 11 (6 modules, 1 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `step1_managers.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`, `datetime`

### `etl_ita_subordinates.step2_ita`

**Direct dependencies**: 12 (8 modules, 1 configs, 3 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `step2_ita.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`

### `etl_psico.__init__`

**Direct dependencies**: 0 (0 modules, 0 configs, 0 libraries)


### `etl_psico.step1_psico`

**Direct dependencies**: 11 (6 modules, 1 configs, 4 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `step1_seguridad_psicologica.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`, `datetime`

### `etl_psico.step2_psico`

**Direct dependencies**: 12 (8 modules, 1 configs, 3 libraries)

- **Internal modules**: `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`
- **Config files**: `step2_seguridad_psicologica.yaml`
- **External libraries**: `pathlib`, `traceback`, `sys`

### `utils.__init__`

**Direct dependencies**: 18 (18 modules, 0 configs, 0 libraries)

- **Internal modules**: `core`, `core`, `utils`, `utils`, `etl`, `etl`, `etl`, `etl`, `etl`, `formatting`, `ui`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`, `utils`

### `utils.core.__init__`

**Direct dependencies**: 2 (2 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`, `utils`

### `utils.core.config_loader`

**Direct dependencies**: 5 (0 modules, 1 configs, 4 libraries)

- **Config files**: `pipeline.sql`
- **External libraries**: `json`, `typing`, `pathlib`, `yaml`

### `utils.core.path_manager`

**Direct dependencies**: 4 (0 modules, 1 configs, 3 libraries)

- **Config files**: `forms_step1.yaml`
- **External libraries**: `typing`, `os`, `pathlib`

### `utils.etl.__init__`

**Direct dependencies**: 3 (3 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`, `utils`, `utils`

### `utils.etl.converters.__init__`

**Direct dependencies**: 2 (2 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`, `utils`

### `utils.etl.converters.excel_to_parquet`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `pyarrow`, `openpyxl`, `typing`, `pathlib`, `datetime`

### `utils.etl.converters.parquet_to_excel`

**Direct dependencies**: 3 (0 modules, 0 configs, 3 libraries)

- **External libraries**: `typing`, `pathlib`, `polars`

### `utils.etl.database.__init__`

**Direct dependencies**: 2 (2 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`, `utils`

### `utils.etl.database.duckdb_manager`

**Direct dependencies**: 4 (0 modules, 0 configs, 4 libraries)

- **External libraries**: `typing`, `pathlib`, `polars`, `duckdb`

### `utils.etl.database.sql_query_loader`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `typing`, `pathlib`

### `utils.etl.validators.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`

### `utils.etl.validators.data_validator`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `typing`, `datetime`

### `utils.formatting.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`

### `utils.formatting.excel_formatter`

**Direct dependencies**: 2 (0 modules, 0 configs, 2 libraries)

- **External libraries**: `typing`, `openpyxl`

### `utils.ui.__init__`

**Direct dependencies**: 1 (1 modules, 0 configs, 0 libraries)

- **Internal modules**: `utils`

### `utils.ui.file_dialog_helper`

**Direct dependencies**: 5 (0 modules, 0 configs, 5 libraries)

- **External libraries**: `tkinter`, `typing`, `os`, `pathlib`, `sys`

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
├── 🔗 collections
├── 🔗 pathspec
├── 🔗 os
├── 🔗 pathlib
├── 🔗 sys
├── 🔗 ast
└── 🔗 re
```

### agent_tools.treemap

```
agent_tools.treemap
├── 🔗 pathspec
├── 🔗 os
└── 🔗 sys
```

### etl_core.__init__

```
etl_core.__init__

```

### etl_core.step1

```
etl_core.step1
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 data_learning_bronzetosilver.yaml
├── 🔗 traceback
├── 🔗 pandas
├── 🔗 polars
├── 🔗 pathlib
├── 🔗 sys
├── 🔗 numpy
└── 🔗 re
```

### etl_core.step2

```
etl_core.step2
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 data_learning_silvertogold.yaml
├── 🔗 pathlib
├── 🔗 traceback
├── 🔗 sys
└── 🔗 polars
```

### etl_forms.__init__

```
etl_forms.__init__

```

### etl_forms.step1_forms

```
etl_forms.step1_forms
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 forms_step1.yaml
├── 🔗 traceback
├── 🔗 pandas
├── 🔗 pathlib
├── 🔗 sys
├── 🔗 numpy
└── 🔗 datetime
```

### etl_forms.step2_forms

```
etl_forms.step2_forms
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 Por favor, verifica los datos o actualiza el esquema en likert_scale.json
├── 📄 forms_step2.yaml
├── 🔗 pathlib
├── 🔗 traceback
└── 🔗 sys
```

### etl_ita_subordinates.__init__

```
etl_ita_subordinates.__init__

```

### etl_ita_subordinates.step1_ita

```
etl_ita_subordinates.step1_ita
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 step1_ita.yaml
├── 🔗 pathlib
├── 🔗 traceback
├── 🔗 sys
└── 🔗 datetime
```

### etl_ita_subordinates.step1_managers

```
etl_ita_subordinates.step1_managers
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 step1_managers.yaml
├── 🔗 pathlib
├── 🔗 traceback
├── 🔗 sys
└── 🔗 datetime
```

### etl_ita_subordinates.step2_ita

```
etl_ita_subordinates.step2_ita
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 step2_ita.yaml
├── 🔗 pathlib
├── 🔗 traceback
└── 🔗 sys
```

### etl_psico.__init__

```
etl_psico.__init__

```

### etl_psico.step1_psico

```
etl_psico.step1_psico
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 step1_seguridad_psicologica.yaml
├── 🔗 pathlib
├── 🔗 traceback
├── 🔗 sys
└── 🔗 datetime
```

### etl_psico.step2_psico

```
etl_psico.step2_psico
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📄 step2_seguridad_psicologica.yaml
├── 🔗 pathlib
├── 🔗 traceback
└── 🔗 sys
```

### utils.__init__

```
utils.__init__
├── 📦 core
├── 📦 core
├── 📦 utils
├── 📦 utils
├── 📦 etl
├── 📦 etl
├── 📦 etl
├── 📦 etl
├── 📦 etl
├── 📦 formatting
├── 📦 ui
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
├── 📦 utils
└── 📦 utils
```

### utils.core.__init__

```
utils.core.__init__
├── 📦 utils
└── 📦 utils
```

### utils.core.config_loader

```
utils.core.config_loader
├── 📄 pipeline.sql
├── 🔗 json
├── 🔗 typing
├── 🔗 pathlib
└── 🔗 yaml
```

### utils.core.path_manager

```
utils.core.path_manager
├── 📄 forms_step1.yaml
├── 🔗 typing
├── 🔗 os
└── 🔗 pathlib
```

### utils.etl.__init__

```
utils.etl.__init__
├── 📦 utils
├── 📦 utils
└── 📦 utils
```

### utils.etl.converters.__init__

```
utils.etl.converters.__init__
├── 📦 utils
└── 📦 utils
```

### utils.etl.converters.excel_to_parquet

```
utils.etl.converters.excel_to_parquet
├── 🔗 pyarrow
├── 🔗 openpyxl
├── 🔗 typing
├── 🔗 pathlib
└── 🔗 datetime
```

### utils.etl.converters.parquet_to_excel

```
utils.etl.converters.parquet_to_excel
├── 🔗 typing
├── 🔗 pathlib
└── 🔗 polars
```

### utils.etl.database.__init__

```
utils.etl.database.__init__
├── 📦 utils
└── 📦 utils
```

### utils.etl.database.duckdb_manager

```
utils.etl.database.duckdb_manager
├── 🔗 typing
├── 🔗 pathlib
├── 🔗 polars
└── 🔗 duckdb
```

### utils.etl.database.sql_query_loader

```
utils.etl.database.sql_query_loader
├── 🔗 typing
└── 🔗 pathlib
```

### utils.etl.validators.__init__

```
utils.etl.validators.__init__
└── 📦 utils
```

### utils.etl.validators.data_validator

```
utils.etl.validators.data_validator
├── 🔗 typing
└── 🔗 datetime
```

### utils.formatting.__init__

```
utils.formatting.__init__
└── 📦 utils
```

### utils.formatting.excel_formatter

```
utils.formatting.excel_formatter
├── 🔗 typing
└── 🔗 openpyxl
```

### utils.ui.__init__

```
utils.ui.__init__
└── 📦 utils
```

### utils.ui.file_dialog_helper

```
utils.ui.file_dialog_helper
├── 🔗 tkinter
├── 🔗 typing
├── 🔗 os
├── 🔗 pathlib
└── 🔗 sys
```

---

## 3. All Modules Index

Tabular view of all modules and their dependency counts:

| Module | Type | Local Deps. | Config Files | External Libs |
|--------|------|---------------|-----------------|---------------|
| __init__ | Entry Point | 0 | 0 | 0 |
| agent_tools.analyze_dependencies | Entry Point | 0 | 0 | 7 |
| agent_tools.treemap | Entry Point | 0 | 0 | 3 |
| etl_core.__init__ | Entry Point | 0 | 0 | 0 |
| etl_core.step1 | Entry Point | 4 | 1 | 7 |
| etl_core.step2 | Entry Point | 4 | 1 | 4 |
| etl_forms.__init__ | Entry Point | 0 | 0 | 0 |
| etl_forms.step1_forms | Entry Point | 4 | 1 | 6 |
| etl_forms.step2_forms | Entry Point | 8 | 2 | 3 |
| etl_ita_subordinates.__init__ | Entry Point | 0 | 0 | 0 |
| etl_ita_subordinates.step1_ita | Entry Point | 6 | 1 | 4 |
| etl_ita_subordinates.step1_managers | Entry Point | 6 | 1 | 4 |
| etl_ita_subordinates.step2_ita | Entry Point | 8 | 1 | 3 |
| etl_psico.__init__ | Entry Point | 0 | 0 | 0 |
| etl_psico.step1_psico | Entry Point | 6 | 1 | 4 |
| etl_psico.step2_psico | Entry Point | 8 | 1 | 3 |
| utils.__init__ | Entry Point | 18 | 0 | 0 |
| utils.core.__init__ | Entry Point | 2 | 0 | 0 |
| utils.core.config_loader | Entry Point | 0 | 1 | 4 |
| utils.core.path_manager | Entry Point | 0 | 1 | 3 |
| utils.etl.__init__ | Entry Point | 3 | 0 | 0 |
| utils.etl.converters.__init__ | Entry Point | 2 | 0 | 0 |
| utils.etl.converters.excel_to_parquet | Entry Point | 0 | 0 | 5 |
| utils.etl.converters.parquet_to_excel | Entry Point | 0 | 0 | 3 |
| utils.etl.database.__init__ | Entry Point | 2 | 0 | 0 |
| utils.etl.database.duckdb_manager | Entry Point | 0 | 0 | 4 |
| utils.etl.database.sql_query_loader | Entry Point | 0 | 0 | 2 |
| utils.etl.validators.__init__ | Entry Point | 1 | 0 | 0 |
| utils.etl.validators.data_validator | Entry Point | 0 | 0 | 2 |
| utils.formatting.__init__ | Entry Point | 1 | 0 | 0 |
| utils.formatting.excel_formatter | Entry Point | 0 | 0 | 2 |
| utils.ui.__init__ | Entry Point | 1 | 0 | 0 |
| utils.ui.file_dialog_helper | Entry Point | 0 | 0 | 5 |

---

## 4. Configuration Files

Data/configuration files detected in code and modules using them:

- **`Por favor, verifica los datos o actualiza el esquema en likert_scale.json`** → Used by: `etl_forms.step2_forms`
- **`data_learning_bronzetosilver.yaml`** → Used by: `etl_core.step1`
- **`data_learning_silvertogold.yaml`** → Used by: `etl_core.step2`
- **`forms_step1.yaml`** → Used by: `etl_forms.step1_forms`, `utils.core.path_manager`
- **`forms_step2.yaml`** → Used by: `etl_forms.step2_forms`
- **`pipeline.sql`** → Used by: `utils.core.config_loader`
- **`step1_ita.yaml`** → Used by: `etl_ita_subordinates.step1_ita`
- **`step1_managers.yaml`** → Used by: `etl_ita_subordinates.step1_managers`
- **`step1_seguridad_psicologica.yaml`** → Used by: `etl_psico.step1_psico`
- **`step2_ita.yaml`** → Used by: `etl_ita_subordinates.step2_ita`
- **`step2_seguridad_psicologica.yaml`** → Used by: `etl_psico.step2_psico`

---

## Notes

- This file is **automatically generated** via a pre-commit hook.
- Imports are detected through static analysis (AST) of Python code.
- Configuration files are detected via regex of common patterns (`open()`, `read_csv()`, etc.).
- Circular dependencies might cause some modules to be missing from the full tree.
