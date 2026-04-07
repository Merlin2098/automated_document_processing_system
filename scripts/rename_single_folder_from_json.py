from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core_pipeline.step4_rename import convertir_json_a_mapeo, renombrar_archivos


DEFAULT_SAMPLE_FOLDER = PROJECT_ROOT / "data" / "4_Convocatoria"


def ensure_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def select_folder(initial_dir: Path | None = None) -> Path | None:
    ensure_app()
    folder = QFileDialog.getExistingDirectory(
        None,
        "Selecciona la carpeta a renombrar",
        str(initial_dir or PROJECT_ROOT),
        QFileDialog.Option.ShowDirsOnly,
    )
    return Path(folder) if folder else None


def select_json_file(initial_dir: Path) -> Path | None:
    ensure_app()
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Selecciona el JSON de renombrado",
        str(initial_dir),
        "Archivos JSON (*.json)",
    )
    return Path(file_path) if file_path else None


def find_json_candidates(folder: Path) -> list[Path]:
    return sorted(
        [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".json"],
        key=lambda path: path.name.lower(),
    )


def load_json_with_fallback(json_path: Path):
    encodings = ("utf-8", "utf-8-sig", "latin-1", "cp1252")
    for encoding in encodings:
        try:
            raw_text = json_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            sanitized_text = re.sub(r",(\s*[\]}])", r"\1", raw_text)
            try:
                data = json.loads(sanitized_text)
                print("Se aplico una correccion automatica al JSON para continuar.")
                return data
            except json.JSONDecodeError:
                continue

    return None


def resolve_folder(args: argparse.Namespace) -> Path:
    if args.folder:
        folder = Path(args.folder).expanduser().resolve()
    elif args.use_sample:
        folder = DEFAULT_SAMPLE_FOLDER.resolve()
    else:
        folder = select_folder(DEFAULT_SAMPLE_FOLDER if DEFAULT_SAMPLE_FOLDER.exists() else PROJECT_ROOT)
        if folder is None:
            raise SystemExit("No se selecciono ninguna carpeta.")

    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"La carpeta no existe o no es valida: {folder}")

    return folder


def resolve_json(folder: Path, args: argparse.Namespace) -> Path:
    if args.json:
        json_path = Path(args.json).expanduser().resolve()
        if not json_path.exists() or not json_path.is_file():
            raise SystemExit(f"El JSON indicado no existe: {json_path}")
        return json_path

    candidates = find_json_candidates(folder)
    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        print("Se encontraron multiples JSON en la carpeta:")
        for candidate in candidates:
            print(f"  - {candidate.name}")
        print(f"Se usara por defecto: {candidates[0].name}")
        print("Si deseas otro archivo, ejecuta el script con --json.")
        return candidates[0]

    selected = select_json_file(folder)
    if selected is None:
        raise SystemExit(
            "No se encontro ningun JSON en la carpeta y no se selecciono uno manualmente."
        )
    return selected.resolve()


def build_preview(folder: Path, mapeo: dict[str, str]) -> tuple[list[str], dict[str, int]]:
    preview_lines: list[str] = []
    stats = {"ready": 0, "missing": 0, "same_name": 0, "target_exists": 0}

    for old_name, new_name in mapeo.items():
        old_path = folder / old_name
        new_path = folder / new_name

        if not old_path.exists():
            stats["missing"] += 1
            preview_lines.append(f"FALTA       {old_name}")
            continue

        if old_name == new_name:
            stats["same_name"] += 1
            preview_lines.append(f"SIN CAMBIO  {old_name}")
            continue

        if new_path.exists():
            stats["target_exists"] += 1
            preview_lines.append(f"YA EXISTE   {new_name}")
            continue

        stats["ready"] += 1
        preview_lines.append(f"RENOMBRAR   {old_name} -> {new_name}")

    return preview_lines, stats


def print_preview(folder: Path, json_path: Path, mapeo: dict[str, str], preview_lines: list[str], stats: dict[str, int], show: int) -> None:
    print(f"Carpeta: {folder}")
    print(f"JSON: {json_path}")
    print(f"Registros en mapeo: {len(mapeo)}")
    print(
        "Resumen previo: "
        f"{stats['ready']} listos, "
        f"{stats['same_name']} sin cambio, "
        f"{stats['target_exists']} ya existen, "
        f"{stats['missing']} faltantes"
    )

    if show <= 0 or not preview_lines:
        return

    print("")
    print(f"Primeros {min(show, len(preview_lines))} movimientos evaluados:")
    for line in preview_lines[:show]:
        print(f"  {line}")

    if len(preview_lines) > show:
        print(f"  ... {len(preview_lines) - show} registros adicionales")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renombra los PDFs de una sola carpeta usando un JSON de mapeo."
    )
    parser.add_argument("--folder", help="Ruta de la carpeta a procesar.")
    parser.add_argument("--json", help="Ruta del JSON de renombrado. Si se omite, se busca dentro de la carpeta.")
    parser.add_argument(
        "--use-sample",
        action="store_true",
        help="Usa data/4_Convocatoria como carpeta de ejemplo.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta el renombrado. Si se omite, solo muestra la vista previa.",
    )
    parser.add_argument(
        "--show",
        type=int,
        default=10,
        help="Cantidad de movimientos a mostrar en la vista previa. Usa 0 para ocultarlos.",
    )
    args = parser.parse_args()

    folder = resolve_folder(args)
    json_path = resolve_json(folder, args)

    datos_json = load_json_with_fallback(json_path)
    if datos_json is None:
        raise SystemExit("No se pudo leer el archivo JSON.")

    mapeo = convertir_json_a_mapeo(datos_json)
    if not mapeo:
        raise SystemExit("No se pudo construir el mapeo de renombrado desde el JSON.")

    preview_lines, preview_stats = build_preview(folder, mapeo)
    print_preview(folder, json_path, mapeo, preview_lines, preview_stats, args.show)

    if not args.apply:
        print("")
        print("Vista previa completada. Ejecuta nuevamente con --apply para renombrar.")
        return 0

    print("")
    print("Ejecutando renombrado...")
    exitosos, fallidos, omitidos, total = renombrar_archivos(str(folder), mapeo)
    print("")
    print("Resultado final:")
    print(f"  Total mapeado: {total}")
    print(f"  Renombrados: {exitosos}")
    print(f"  Omitidos: {omitidos}")
    print(f"  Fallidos: {fallidos}")
    return 0 if fallidos == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
