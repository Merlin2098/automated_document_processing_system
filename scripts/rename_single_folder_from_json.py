from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QFileDialog

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core_pipeline.rename_auxiliar import (
    apply_single_folder_rename,
    find_json_candidates,
    prepare_single_folder_rename,
)


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

    candidates = [Path(path) for path in find_json_candidates(folder)]
    if len(candidates) == 1:
        return candidates[0]

    if len(candidates) > 1:
        print("Se encontraron multiples JSON en la carpeta:")
        for candidate in candidates:
            print(f"  - {candidate.name}")
        print("Seleccione uno manualmente.")
        selected = select_json_file(folder)
        if selected is None:
            raise SystemExit("No se selecciono ningun JSON.")
        return selected.resolve()

    selected = select_json_file(folder)
    if selected is None:
        raise SystemExit(
            "No se encontro ningun JSON en la carpeta y no se selecciono uno manualmente."
        )
    return selected.resolve()


def print_preview(preparation: dict, show: int) -> None:
    folder = preparation["folder_path"]
    json_path = preparation["json_path"]
    preview_lines = preparation["preview_lines"]
    stats = preparation["stats"]

    print(f"Carpeta: {folder}")
    print(f"JSON: {json_path}")
    print(f"Registros en mapeo: {preparation['mapping_count']}")
    print(
        "Resumen previo: "
        f"{stats['ready']} listos, "
        f"{stats['same_name']} sin cambio, "
        f"{stats['target_exists']} ya existen, "
        f"{stats['missing']} faltantes"
    )
    if preparation.get("json_sanitized"):
        print("Se aplico una correccion automatica al JSON para continuar.")

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

    preparation = prepare_single_folder_rename(folder, json_path)
    if not preparation["success"]:
        raise SystemExit(preparation["message"])

    print_preview(preparation, args.show)

    if not args.apply:
        print("")
        print("Vista previa completada. Ejecuta nuevamente con --apply para renombrar.")
        return 0

    print("")
    print("Ejecutando renombrado...")
    result = apply_single_folder_rename(folder, json_path)
    print("")
    print("Resultado final:")
    print(f"  Total mapeado: {result['total']}")
    print(f"  Renombrados: {result['renombrados']}")
    print(f"  Omitidos: {result['omitidos']}")
    print(f"  Fallidos: {result['fallidos']}")
    return 0 if result["fallidos"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
