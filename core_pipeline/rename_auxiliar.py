from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable


PreviewEntry = dict[str, str]
ProgressCallback = Callable[[int, int], None]


def find_json_candidates(folder_path: str | Path) -> list[str]:
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        return []

    return [
        str(path.resolve())
        for path in sorted(
            folder.iterdir(),
            key=lambda item: item.name.lower(),
        )
        if path.is_file() and path.suffix.lower() == ".json"
    ]


def load_json_with_fallback(json_path: str | Path) -> dict:
    path = Path(json_path).expanduser().resolve()
    encodings = ("utf-8", "utf-8-sig", "latin-1", "cp1252")

    for encoding in encodings:
        try:
            raw_text = path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            return {
                "success": False,
                "status": "json_invalido",
                "message": f"No se pudo leer el archivo JSON: {exc}",
                "data": None,
                "encoding": None,
                "sanitized": False,
            }

        try:
            return {
                "success": True,
                "status": "ok",
                "message": "JSON cargado correctamente.",
                "data": json.loads(raw_text),
                "encoding": encoding,
                "sanitized": False,
            }
        except json.JSONDecodeError:
            sanitized_text = re.sub(r",(\s*[\]}])", r"\1", raw_text)
            if sanitized_text == raw_text:
                continue

            try:
                return {
                    "success": True,
                    "status": "ok",
                    "message": "JSON cargado con correccion automatica de coma final.",
                    "data": json.loads(sanitized_text),
                    "encoding": encoding,
                    "sanitized": True,
                }
            except json.JSONDecodeError:
                continue

    return {
        "success": False,
        "status": "json_invalido",
        "message": "No se pudo leer el archivo JSON con un formato valido.",
        "data": None,
        "encoding": None,
        "sanitized": False,
    }


def build_rename_mapping(json_data: object) -> dict:
    if not isinstance(json_data, list):
        return {
            "success": False,
            "status": "json_invalido",
            "message": "El JSON debe ser una lista de registros.",
            "mapping": {},
            "duplicate_sources": [],
            "invalid_entries": 0,
            "raw_count": 0,
        }

    mapping: dict[str, str] = {}
    duplicate_sources: list[str] = []
    invalid_entries = 0

    for item in json_data:
        if not isinstance(item, dict):
            invalid_entries += 1
            continue

        original_name = item.get("ARCHIVO ORIGINAL")
        new_name = item.get("NUEVO NOMBRE")

        if not original_name or not new_name:
            invalid_entries += 1
            continue

        if original_name in mapping and original_name not in duplicate_sources:
            duplicate_sources.append(original_name)

        mapping[str(original_name)] = str(new_name)

    if not mapping:
        status = "json_vacio" if len(json_data) == 0 else "mapeo_vacio"
        message = (
            "El JSON de renombrado esta vacio."
            if status == "json_vacio"
            else "El JSON no produjo un mapeo valido de renombrado."
        )
        return {
            "success": False,
            "status": status,
            "message": message,
            "mapping": {},
            "duplicate_sources": duplicate_sources,
            "invalid_entries": invalid_entries,
            "raw_count": len(json_data),
        }

    return {
        "success": True,
        "status": "ok",
        "message": "Mapeo de renombrado construido correctamente.",
        "mapping": mapping,
        "duplicate_sources": duplicate_sources,
        "invalid_entries": invalid_entries,
        "raw_count": len(json_data),
    }


def build_preview(folder_path: str | Path, mapping: dict[str, str]) -> dict:
    folder = Path(folder_path).expanduser().resolve()
    entries: list[dict[str, str]] = []
    lines: list[str] = []
    stats = {"ready": 0, "missing": 0, "same_name": 0, "target_exists": 0}

    for old_name, new_name in mapping.items():
        old_path = folder / old_name
        new_path = folder / new_name

        if not old_path.exists():
            status = "missing"
            stats["missing"] += 1
            line = f"FALTA       {old_name}"
        elif old_name == new_name:
            status = "same_name"
            stats["same_name"] += 1
            line = f"SIN CAMBIO  {old_name}"
        elif new_path.exists():
            status = "target_exists"
            stats["target_exists"] += 1
            line = f"YA EXISTE   {new_name}"
        else:
            status = "ready"
            stats["ready"] += 1
            line = f"RENOMBRAR   {old_name} -> {new_name}"

        entry = {
            "status": status,
            "old_name": old_name,
            "new_name": new_name,
            "line": line,
        }
        entries.append(entry)
        lines.append(line)

    return {
        "entries": entries,
        "lines": lines,
        "stats": stats,
    }


def prepare_single_folder_rename(folder_path: str | Path, json_path: str | Path | None = None) -> dict:
    folder = Path(folder_path).expanduser().resolve()
    result = {
        "success": False,
        "status": "error",
        "message": "",
        "folder_path": str(folder),
        "json_path": None,
        "json_candidates": find_json_candidates(folder),
        "json_selection_required": False,
        "json_sanitized": False,
        "encoding": None,
        "raw_entry_count": 0,
        "mapping_count": 0,
        "duplicate_sources": [],
        "invalid_entries": 0,
        "mapping": {},
        "preview": [],
        "preview_lines": [],
        "stats": {"ready": 0, "missing": 0, "same_name": 0, "target_exists": 0},
    }

    if not folder.exists() or not folder.is_dir():
        result["status"] = "folder_missing"
        result["message"] = f"La carpeta no existe o no es valida: {folder}"
        return result

    selected_json: Path | None = None
    if json_path:
        selected_json = Path(json_path).expanduser().resolve()
        if not selected_json.exists() or not selected_json.is_file():
            result["status"] = "json_missing"
            result["message"] = f"El JSON indicado no existe: {selected_json}"
            return result
    else:
        candidates = result["json_candidates"]
        if len(candidates) == 1:
            selected_json = Path(candidates[0])
        elif len(candidates) == 0:
            result["status"] = "missing_json"
            result["message"] = "No se encontro ningun JSON de renombrado en la carpeta."
            return result
        else:
            result["status"] = "multiple_json"
            result["message"] = "Se encontraron multiples JSON. Seleccione uno manualmente."
            result["json_selection_required"] = True
            return result

    result["json_path"] = str(selected_json)

    json_result = load_json_with_fallback(selected_json)
    if not json_result["success"]:
        result["status"] = json_result["status"]
        result["message"] = json_result["message"]
        return result

    result["json_sanitized"] = json_result["sanitized"]
    result["encoding"] = json_result["encoding"]

    mapping_result = build_rename_mapping(json_result["data"])
    result["raw_entry_count"] = mapping_result["raw_count"]
    result["mapping_count"] = len(mapping_result["mapping"])
    result["duplicate_sources"] = mapping_result["duplicate_sources"]
    result["invalid_entries"] = mapping_result["invalid_entries"]

    if not mapping_result["success"]:
        result["status"] = mapping_result["status"]
        result["message"] = mapping_result["message"]
        return result

    result["mapping"] = mapping_result["mapping"]

    preview_result = build_preview(folder, mapping_result["mapping"])
    result["preview"] = preview_result["entries"]
    result["preview_lines"] = preview_result["lines"]
    result["stats"] = preview_result["stats"]
    result["status"] = "ok"
    result["message"] = "Vista previa generada correctamente."
    result["success"] = True
    return result


def apply_single_folder_rename(
    folder_path: str | Path,
    json_path: str | Path,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    preparation = prepare_single_folder_rename(folder_path, json_path)
    if not preparation["success"]:
        return {
            "success": False,
            "status": preparation["status"],
            "message": preparation["message"],
            "folder_path": preparation["folder_path"],
            "json_path": preparation["json_path"],
            "total": 0,
            "renombrados": 0,
            "omitidos": 0,
            "fallidos": 0,
            "errors": [],
            "warnings": [],
            "stats": preparation["stats"],
        }

    folder = Path(preparation["folder_path"])
    mapping = preparation["mapping"]
    total = len(mapping)
    renamed = 0
    omitted = 0
    failed = 0
    errors: list[str] = []
    warnings: list[str] = []

    for index, (old_name, new_name) in enumerate(mapping.items(), 1):
        old_path = folder / old_name
        new_path = folder / new_name

        if not old_path.exists():
            failed += 1
            errors.append(f"No encontrado: {old_name}")
        elif new_path.exists():
            omitted += 1
            warnings.append(f"Ya existe: {new_name}")
        elif old_name == new_name:
            omitted += 1
            warnings.append(f"Sin cambio: {old_name}")
        else:
            try:
                os.rename(old_path, new_path)
                renamed += 1
            except OSError as exc:
                failed += 1
                errors.append(f"Error al renombrar '{old_name}': {exc}")

        if progress_callback:
            progress_callback(index, total)

    return {
        "success": failed == 0,
        "status": "ok" if failed == 0 else "completed_with_errors",
        "message": "Renombrado completado." if failed == 0 else "Renombrado completado con errores.",
        "folder_path": preparation["folder_path"],
        "json_path": preparation["json_path"],
        "total": total,
        "renombrados": renamed,
        "omitidos": omitted,
        "fallidos": failed,
        "errors": errors,
        "warnings": warnings,
        "stats": preparation["stats"],
        "mapping_count": preparation["mapping_count"],
        "json_sanitized": preparation["json_sanitized"],
    }
