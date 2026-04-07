"""
Tab Rename Auxiliar - Renombrado manual de una sola carpeta con JSON.
"""
from pathlib import Path
import os

from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QScrollArea,
    QMessageBox,
    QTextEdit,
)

from core_pipeline.rename_auxiliar import find_json_candidates
from ui.widgets.file_selector import FileSelector
from ui.workers.rename_auxiliar_worker import (
    RenameAuxiliarApplyWorker,
    RenameAuxiliarPreviewWorker,
)


class TabRenameAuxiliar(QWidget):
    """Tab superior para renombrado auxiliar de una sola carpeta."""

    log_message = Signal(str, str)
    progress_updated = Signal(int, int)
    stats_updated = Signal(dict)

    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager

        self.preview_worker = None
        self.apply_worker = None
        self.preview_result = None
        self.preview_valid = False
        self._updating_paths = False

        self._init_ui()
        self._refresh_summary()
        self._update_buttons_state()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        group = QGroupBox("🗂️ Rename Auxiliar")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(20, 25, 20, 25)
        group_layout.setSpacing(18)

        info = QLabel(
            """
Renombra una sola carpeta usando un JSON de mapeo.
Primero genera una vista previa y luego aplica el renombrado solo si el resultado es correcto.
            """.strip()
        )
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        group_layout.addWidget(info)

        folder_label = QLabel("📂 Carpeta a renombrar")
        folder_label.setProperty("labelStyle", "header")
        group_layout.addWidget(folder_label)

        self.folder_selector = FileSelector(
            mode="folder",
            placeholder="Seleccionar carpeta con PDFs...",
        )
        self.folder_selector.path_selected.connect(self._on_folder_changed)
        group_layout.addWidget(self.folder_selector)

        json_label = QLabel("🧾 JSON de renombrado")
        json_label.setProperty("labelStyle", "header")
        group_layout.addWidget(json_label)

        json_row = QHBoxLayout()
        self.json_selector = FileSelector(
            mode="file",
            file_filter="Archivos JSON (*.json)",
            placeholder="Seleccionar JSON de renombrado...",
        )
        self.json_selector.path_selected.connect(self._on_json_changed)
        json_row.addWidget(self.json_selector, 1)

        self.btn_detect_json = QPushButton("🔎 Detectar JSON")
        self.btn_detect_json.setProperty("buttonStyle", "secondary")
        self.btn_detect_json.clicked.connect(self._detect_json)
        json_row.addWidget(self.btn_detect_json)
        group_layout.addLayout(json_row)

        summary_group = QGroupBox("Resumen")
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setSpacing(8)

        self.summary_folder_label = QLabel()
        self.summary_json_label = QLabel()
        self.summary_mapping_label = QLabel()
        self.summary_stats_label = QLabel()

        for label in (
            self.summary_folder_label,
            self.summary_json_label,
            self.summary_mapping_label,
            self.summary_stats_label,
        ):
            label.setProperty("labelStyle", "secondary")
            label.setWordWrap(True)
            summary_layout.addWidget(label)

        group_layout.addWidget(summary_group)

        preview_label = QLabel("👁️ Vista previa")
        preview_label.setProperty("labelStyle", "header")
        group_layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(260)
        self.preview_text.setPlainText(
            "Genera una vista previa para revisar los cambios antes de aplicar el renombrado."
        )
        group_layout.addWidget(self.preview_text)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_preview = QPushButton("👁️ Vista previa")
        self.btn_preview.clicked.connect(self._run_preview)
        button_layout.addWidget(self.btn_preview)

        self.btn_apply = QPushButton("▶️ Aplicar renombrado")
        self.btn_apply.clicked.connect(self._run_apply)
        button_layout.addWidget(self.btn_apply)

        button_layout.addStretch()
        group_layout.addLayout(button_layout)

        content_layout.addWidget(group)
        content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _normalize_path(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            return str(Path(value).expanduser().resolve())
        except OSError:
            return value

    def _refresh_summary(self, result: dict | None = None):
        folder_text = self.folder_selector.get_path().strip() or "-"
        json_text = self.json_selector.get_path().strip() or "-"
        mapping_count = 0
        stats = {"ready": 0, "missing": 0, "same_name": 0, "target_exists": 0}

        if result:
            folder_text = result.get("folder_path") or folder_text
            json_text = result.get("json_path") or json_text
            mapping_count = result.get("mapping_count", 0)
            stats = result.get("stats", stats)

        self.summary_folder_label.setText(f"Carpeta: {folder_text}")
        self.summary_json_label.setText(f"JSON: {json_text}")
        self.summary_mapping_label.setText(f"Registros en mapeo: {mapping_count}")
        self.summary_stats_label.setText(
            (
                f"Listos: {stats['ready']} | "
                f"Sin cambio: {stats['same_name']} | "
                f"Ya existen: {stats['target_exists']} | "
                f"Faltantes: {stats['missing']}"
            )
        )

    def _invalidate_preview(self, message: str | None = None):
        self.preview_result = None
        self.preview_valid = False
        self.preview_text.setPlainText(
            message
            or "Genera una vista previa para revisar los cambios antes de aplicar el renombrado."
        )
        self._refresh_summary()
        self._update_buttons_state()

    def _update_buttons_state(self):
        busy = self.preview_worker is not None or self.apply_worker is not None
        self.folder_selector.set_enabled(not busy)
        self.json_selector.set_enabled(not busy)
        self.btn_detect_json.setEnabled(not busy)
        self.btn_preview.setEnabled(not busy)
        self.btn_apply.setEnabled(
            (not busy)
            and self.preview_valid
            and self.preview_result is not None
        )

    def _reset_monitor(self):
        main_window = self.window()
        if hasattr(main_window, "monitoring_panel"):
            main_window.monitoring_panel.reset()

    def _set_json_path(self, json_path: str):
        self._updating_paths = True
        self.json_selector.set_path(json_path)
        self._updating_paths = False

    @Slot(str)
    def _on_folder_changed(self, folder_path: str):
        if self._updating_paths:
            return

        self._updating_paths = True
        self.json_selector.clear()
        self._updating_paths = False
        self._invalidate_preview("La carpeta cambio. Genera una nueva vista previa.")

        if folder_path.strip():
            self.log_message.emit("info", f"Carpeta seleccionada: {folder_path}")

    @Slot(str)
    def _on_json_changed(self, json_path: str):
        if self._updating_paths:
            return

        self._invalidate_preview("El JSON cambio. Genera una nueva vista previa.")

        if json_path.strip():
            self.log_message.emit("info", f"JSON seleccionado: {json_path}")

    def _detect_json(self):
        folder_path = self.folder_selector.get_path().strip()

        if not folder_path:
            QMessageBox.warning(self, "Carpeta requerida", "Selecciona una carpeta primero.")
            return

        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, "Carpeta invalida", f"La carpeta no existe:\n{folder_path}")
            return

        candidates = find_json_candidates(folder_path)
        if not candidates:
            self._updating_paths = True
            self.json_selector.clear()
            self._updating_paths = False
            self.log_message.emit("warning", "No se encontro ningun JSON en la carpeta seleccionada.")
            QMessageBox.warning(
                self,
                "JSON no encontrado",
                "No se encontro ningun JSON dentro de la carpeta seleccionada.",
            )
            self._invalidate_preview("No se encontro un JSON. Selecciona uno manualmente.")
            return

        if len(candidates) == 1:
            self._set_json_path(candidates[0])
            self.log_message.emit("success", f"JSON detectado automaticamente: {os.path.basename(candidates[0])}")
            self._invalidate_preview("JSON detectado. Genera la vista previa para continuar.")
            return

        self._updating_paths = True
        self.json_selector.clear()
        self._updating_paths = False
        self.log_message.emit(
            "warning",
            f"Se encontraron {len(candidates)} JSON. Selecciona uno manualmente.",
        )
        QMessageBox.warning(
            self,
            "Seleccion manual requerida",
            (
                "Se encontraron multiples JSON en la carpeta.\n\n"
                "Selecciona manualmente el archivo correcto antes de generar la vista previa."
            ),
        )
        self._invalidate_preview("Hay multiples JSON. Selecciona uno manualmente.")

    def _ensure_single_json_autofill(self):
        folder_path = self.folder_selector.get_path().strip()
        json_path = self.json_selector.get_path().strip()

        if not folder_path or json_path or not os.path.isdir(folder_path):
            return

        candidates = find_json_candidates(folder_path)
        if len(candidates) == 1:
            self._set_json_path(candidates[0])

    def _run_preview(self):
        if self.preview_worker or self.apply_worker:
            return

        folder_path = self.folder_selector.get_path().strip()
        if not folder_path:
            QMessageBox.warning(self, "Carpeta requerida", "Selecciona una carpeta para generar la vista previa.")
            return

        if not os.path.isdir(folder_path):
            QMessageBox.critical(self, "Carpeta invalida", f"La carpeta no existe:\n{folder_path}")
            return

        self._ensure_single_json_autofill()
        json_path = self.json_selector.get_path().strip() or None

        self._reset_monitor()
        self.preview_text.setPlainText("Generando vista previa...")
        self.preview_valid = False

        self.preview_worker = RenameAuxiliarPreviewWorker(folder_path, json_path)
        self._update_buttons_state()
        self.preview_worker.log_signal.connect(self.log_message.emit)
        self.preview_worker.stats_signal.connect(self.stats_updated.emit)
        self.preview_worker.preview_ready.connect(self._on_preview_ready)
        self.preview_worker.error_signal.connect(self._on_preview_error)
        self.preview_worker.finished.connect(self._on_preview_complete)

        self.log_message.emit("info", "Iniciando vista previa de Rename Auxiliar...")
        self.preview_worker.start()

    @Slot(dict)
    def _on_preview_ready(self, result: dict):
        self.preview_result = result
        self.preview_valid = True

        if result.get("json_path"):
            self._set_json_path(result["json_path"])

        preview_lines = result.get("preview_lines", [])
        self.preview_text.setPlainText(
            "\n".join(preview_lines)
            if preview_lines
            else "No hay movimientos para mostrar en la vista previa."
        )
        self._refresh_summary(result)
        self._update_buttons_state()

    @Slot(str)
    def _on_preview_error(self, error_message: str):
        self._invalidate_preview(error_message)
        QMessageBox.warning(self, "Vista previa no disponible", error_message)

    @Slot()
    def _on_preview_complete(self):
        if self.preview_worker:
            self.preview_worker.deleteLater()
            self.preview_worker = None
        self._update_buttons_state()

    def _preview_matches_current_input(self) -> bool:
        if not self.preview_result:
            return False

        current_folder = self._normalize_path(self.folder_selector.get_path().strip())
        current_json = self._normalize_path(self.json_selector.get_path().strip())
        preview_folder = self.preview_result.get("folder_path")
        preview_json = self.preview_result.get("json_path")

        return current_folder == preview_folder and current_json == preview_json

    def _run_apply(self):
        if self.preview_worker or self.apply_worker:
            return

        if not self.preview_valid or not self.preview_result:
            QMessageBox.warning(
                self,
                "Vista previa requerida",
                "Genera primero una vista previa valida antes de aplicar el renombrado.",
            )
            return

        if not self._preview_matches_current_input():
            self._invalidate_preview("La carpeta o el JSON cambiaron. Genera una nueva vista previa.")
            QMessageBox.warning(
                self,
                "Vista previa desactualizada",
                "La carpeta o el JSON cambiaron desde la ultima vista previa. Genera una nueva.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmar renombrado",
            (
                "Esta operacion renombrara los archivos de la carpeta seleccionada.\n\n"
                "¿Deseas continuar?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.No:
            self.log_message.emit("warning", "Operacion cancelada por el usuario.")
            return

        self._reset_monitor()

        self.apply_worker = RenameAuxiliarApplyWorker(
            self.preview_result["folder_path"],
            self.preview_result["json_path"],
        )
        self._update_buttons_state()
        self.apply_worker.log_signal.connect(self.log_message.emit)
        self.apply_worker.progress_signal.connect(self.progress_updated.emit)
        self.apply_worker.stats_signal.connect(self.stats_updated.emit)
        self.apply_worker.finished_signal.connect(self._on_apply_finished)
        self.apply_worker.error_signal.connect(self._on_apply_error)
        self.apply_worker.finished.connect(self._on_apply_complete)

        self.log_message.emit("info", "Iniciando renombrado auxiliar...")
        self.apply_worker.start()

    @Slot(dict)
    def _on_apply_finished(self, result: dict):
        title = "Renombrado completado"
        message = (
            f"Total mapeado: {result['total']}\n"
            f"Renombrados: {result['renombrados']}\n"
            f"Omitidos: {result['omitidos']}\n"
            f"Fallidos: {result['fallidos']}"
        )

        if result["fallidos"] > 0:
            QMessageBox.warning(self, title, message)
        else:
            QMessageBox.information(self, title, message)

        self._invalidate_preview("El estado de la carpeta cambio. Genera una nueva vista previa.")

    @Slot(str)
    def _on_apply_error(self, error_message: str):
        self._invalidate_preview("No se pudo aplicar el renombrado. Revisa los datos y genera una nueva vista previa.")
        QMessageBox.critical(self, "Error de renombrado", error_message)

    @Slot()
    def _on_apply_complete(self):
        if self.apply_worker:
            self.apply_worker.deleteLater()
            self.apply_worker = None
        self._update_buttons_state()
