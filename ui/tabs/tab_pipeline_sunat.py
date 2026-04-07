"""
Tab Pipeline SUNAT - Pipeline para documentos SUNAT (3 pasos)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QScrollArea,
    QMessageBox, QDialog, QTextEdit, QDialogButtonBox
)
from PySide6.QtCore import Signal, Slot, Qt
import json
from PySide6.QtGui import QCursor

from ui.widgets.file_selector import FileSelector
from ui.widgets.stepper_widget import StepperWidget
from ui.workers.sunat_diagnostic_worker import SunatDiagnosticWorker
from ui.workers.sunat_rename_worker import SunatRenameWorker
from ui.workers.sunat_duplicates_worker import (
    SunatDuplicatesWorker,
    SunatDuplicatesPreviewWorker
)
import os


class TabPipelineSunat(QWidget):
    """Tab de Pipeline SUNAT con 3 pasos"""
    
    # Señales
    log_message = Signal(str, str)
    progress_updated = Signal(int, int)
    stats_updated = Signal(dict)
    config_updated = Signal()  # Nueva señal para notificar actualizaciones
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_step = 0
        
        # Workers
        self.current_worker = None
        self.preview_worker = None
        
        # Estado de botones
        self.execute_buttons = []
        
        # Cargar configuración
        self.config = self._load_config()
        
        self._init_ui()
        
        # Actualizar información después de inicializar UI
        self.update_workers_info()
    
    def update_workers_info(self):
        """Actualiza la información de workers mostrada al usuario"""
        # Verificar si el widget ya fue creado
        if not hasattr(self, 'step1_workers_info'):
            return
            
        # Obtener workers óptimos de la configuración
        performance_config = self.config.get('preferences', {}).get('performance', {})
        optimal_workers = performance_config.get('workers', 4)
        
        # Mostrar información
        info_text = f"""
<b>Workers paralelos:</b> {optimal_workers} (configurado automáticamente)<br>
<small><i>Basado en las capacidades de tu equipo</i></small>
        """
        self.step1_workers_info.setText(info_text)
        self.step1_workers_info.setTextFormat(Qt.RichText)
    
    def on_config_updated(self):
        """Se llama cuando la configuración se actualiza desde otro lugar"""
        self.config = self._load_config()
        self.update_workers_info()
        self.log_message.emit("info", "⚙️ Configuración SUNAT actualizada")
    
    def _load_config(self):
        """Carga configuración desde config.json"""
        try:
            with open("resources/config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando config: {e}")
            return {"preferences": {"performance": {"workers": 4}}}
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        # Layout principal del tab
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear widget contenedor para el contenido scrolleable
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Stepper
        self.stepper = StepperWidget(
            steps=[
                "Generar\nDiagnóstico",
                "Renombrar\nDocumentos",
                "Limpiar\nDuplicados"
            ],
            theme_manager=self.theme_manager
        )
        
        # Conectar señal de clic en paso del stepper
        self.stepper.step_clicked.connect(self._go_to_step)
        
        content_layout.addWidget(self.stepper)
        
        # Contenedor de pasos (stack)
        self.step_widgets = []
        
        # Crear widgets para cada paso
        self.step_widgets.append(self._create_step1())
        self.step_widgets.append(self._create_step2())
        self.step_widgets.append(self._create_step3())
        
        # Agregar todos los widgets (solo uno visible a la vez)
        for widget in self.step_widgets:
            content_layout.addWidget(widget)
            widget.hide()
        
        # Mostrar primer paso
        self.step_widgets[0].show()
        self.stepper.set_active_step(0)
        
        # Crear el scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Agregar scroll area al layout principal
        main_layout.addWidget(scroll_area)
    
    def _create_step1(self) -> QWidget:
        """Paso 1: Generar Diagnóstico SUNAT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("1️⃣ Generar Diagnóstico SUNAT")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs SUNAT")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step1_folder = FileSelector(
            mode="folder",
            placeholder="Seleccionar carpeta con documentos CIR..."
        )
        group_layout.addWidget(self.step1_folder)
        
        # Configuración de procesamiento (automática)
        workers_label = QLabel("⚡ Configuración de procesamiento")
        workers_label.setProperty("labelStyle", "header")
        group_layout.addWidget(workers_label)
        
        # Label informativo (no editable)
        self.step1_workers_info = QLabel()
        self.step1_workers_info.setProperty("labelStyle", "secondary")
        self.step1_workers_info.setWordWrap(True)
        group_layout.addWidget(self.step1_workers_info)
        
        # Info
        info = QLabel("""
Se generará un archivo Excel con:
• Datos extraídos (Nombre, DNI, Fecha)
• Clasificación: ALTA/BAJA/OTROS
• Detección de errores y archivos sin datos
        """)
        info.setProperty("labelStyle", "secondary")
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(0)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step2(self) -> QWidget:
        """Paso 2: Renombrar Documentos SUNAT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("2️⃣ Renombrar Documentos SUNAT")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs y JSON de renombrado")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step2_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs y archivo JSON..."
        )
        group_layout.addWidget(self.step2_folder)
        
        # Info
        info = QLabel("""
<b>Instrucciones:</b><br>
La carpeta debe contener exactamente un archivo JSON de renombrado con <b>"rename"</b>
en su nombre y ese JSON debe cubrir <b>todos</b> los PDFs presentes.<br><br>
Si falta el JSON, hay más de uno, o algún PDF no aparece en el JSON, el Paso 2
se bloqueará antes de renombrar.
        """)
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(1)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step3(self) -> QWidget:
        """Paso 3: Limpiar Duplicados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("3️⃣ Limpiar Duplicados por Contrato")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con archivos renombrados")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step3_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs renombrados..."
        )
        group_layout.addWidget(self.step3_folder)
        
        # Warning info
        warning_layout = QHBoxLayout()
        warning_icon = QLabel("⚠️")
        warning_text = QLabel(
            "<b>Advertencia:</b> Esta operación eliminará archivos duplicados "
            "conservando solo el primero de cada contrato. Se mostrará una vista "
            "previa antes de proceder."
        )
        warning_text.setProperty("labelStyle", "secondary")
        warning_text.setWordWrap(True)
        warning_text.setTextFormat(Qt.RichText)
        
        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(warning_text, 1)
        group_layout.addLayout(warning_layout)
        
        # Botones principales
        btn_layout = self._create_step_buttons(2)
        group_layout.addLayout(btn_layout)
        
        # Botón de vista previa adicional (centrado debajo)
        preview_layout = QHBoxLayout()
        preview_layout.addStretch()
        self.btn_preview = QPushButton("👁️ Vista Previa de Duplicados")
        self.btn_preview.setProperty("buttonStyle", "secondary")
        self.btn_preview.clicked.connect(self._preview_duplicates)
        preview_layout.addWidget(self.btn_preview)
        preview_layout.addStretch()
        group_layout.addLayout(preview_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step_buttons(self, step_index: int) -> QHBoxLayout:
        """Crea los botones de navegación para un paso"""
        layout = QHBoxLayout()
        
        # Botón anterior (si no es el primer paso)
        if step_index > 0:
            btn_prev = QPushButton("⬅️ Paso Anterior")
            btn_prev.setProperty("buttonStyle", "secondary")
            btn_prev.clicked.connect(lambda: self._go_to_step(step_index - 1))
            layout.addWidget(btn_prev)
        else:
            layout.addStretch()
        
        # Botón ejecutar
        btn_execute = QPushButton(f"▶️ Ejecutar Paso {step_index + 1}")
        btn_execute.clicked.connect(lambda: self._execute_step(step_index))
        self.execute_buttons.append(btn_execute)
        layout.addWidget(btn_execute)
        
        # Botón siguiente (si no es el último paso)
        if step_index < 2:
            btn_next = QPushButton("Siguiente Paso ➡️")
            btn_next.setProperty("buttonStyle", "secondary")
            btn_next.clicked.connect(lambda: self._go_to_step(step_index + 1))
            layout.addWidget(btn_next)
        else:
            layout.addStretch()
        
        return layout
    
    def _go_to_step(self, step_index: int):
        """Navega a un paso específico"""
        # Ocultar paso actual
        self.step_widgets[self.current_step].hide()
        
        # Mostrar nuevo paso
        self.current_step = step_index
        self.step_widgets[self.current_step].show()
        
        # Actualizar stepper
        self.stepper.set_active_step(step_index)
        
        self.log_message.emit("info", f"📋 Navegando al Paso {step_index + 1}")
    
    def _execute_step(self, step_index: int):
        """Ejecuta el paso actual"""
        if step_index == 0:
            self._execute_step1()
        elif step_index == 1:
            self._execute_step2()
        elif step_index == 2:
            self._execute_step3()
    
    def _execute_step1(self):
        """Ejecuta el paso 1: Generar diagnóstico"""
        folder = self.step1_folder.get_path()
        
        # Validaciones
        if not folder:
            QMessageBox.warning(
                self,
                "Carpeta requerida",
                "Por favor selecciona una carpeta con documentos SUNAT."
            )
            return
        
        if not os.path.isdir(folder):
            QMessageBox.critical(
                self,
                "Carpeta inválida",
                f"La carpeta seleccionada no existe:\n{folder}"
            )
            return
        
        # Verificar archivos PDF
        pdf_files = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        if not pdf_files:
            QMessageBox.warning(
                self,
                "Sin archivos PDF",
                "No se encontraron archivos PDF en la carpeta seleccionada."
            )
            return
        
        # Obtener número de workers de la configuración (no del combobox)
        performance_config = self.config.get('preferences', {}).get('performance', {})
        optimal_workers = performance_config.get('workers', 4)
        
        # Informar al usuario
        self.log_message.emit("info", f"⚡ Usando {optimal_workers} workers (configuración automática)")
        
        # Deshabilitar botones
        self._set_buttons_enabled(False)
        self.setCursor(QCursor(Qt.WaitCursor))
        
        # Crear y configurar worker
        self.current_worker = SunatDiagnosticWorker(folder, optimal_workers)
        
        # Conectar señales
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step1_finished)
        self.current_worker.error_signal.connect(self._on_worker_error)
        self.current_worker.finished.connect(self._on_worker_complete)
        
        # Iniciar worker
        self.log_message.emit("info", "🚀 Iniciando generación de diagnóstico...")
        self.current_worker.start()
    
    def _execute_step2(self):
        """Ejecuta el paso 2: Renombrar"""
        folder = self.step2_folder.get_path()
        
        # Validaciones
        if not folder:
            QMessageBox.warning(
                self,
                "Carpeta requerida",
                "Por favor selecciona una carpeta con PDFs y JSON de renombrado."
            )
            return
        
        if not os.path.isdir(folder):
            QMessageBox.critical(
                self,
                "Carpeta inválida",
                f"La carpeta seleccionada no existe:\n{folder}"
            )
            return
        
        # Deshabilitar botones
        self._set_buttons_enabled(False)
        self.setCursor(QCursor(Qt.WaitCursor))
        
        # Crear y configurar worker
        self.current_worker = SunatRenameWorker(folder)
        
        # Conectar señales
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step2_finished)
        self.current_worker.error_signal.connect(self._on_worker_error)
        self.current_worker.finished.connect(self._on_worker_complete)
        
        # Iniciar worker
        self.log_message.emit("info", "🔄 Iniciando validación y renombrado de documentos...")
        self.current_worker.start()
    
    def _preview_duplicates(self):
        """Muestra vista previa de duplicados"""
        folder = self.step3_folder.get_path()
        
        # Validaciones
        if not folder:
            QMessageBox.warning(
                self,
                "Carpeta requerida",
                "Por favor selecciona una carpeta con archivos renombrados."
            )
            return
        
        if not os.path.isdir(folder):
            QMessageBox.critical(
                self,
                "Carpeta inválida",
                f"La carpeta seleccionada no existe:\n{folder}"
            )
            return
        
        # Deshabilitar botón de vista previa
        self.btn_preview.setEnabled(False)
        self.setCursor(QCursor(Qt.WaitCursor))
        
        # Crear worker de preview
        self.preview_worker = SunatDuplicatesPreviewWorker(folder)
        
        # Conectar señales
        self.preview_worker.log_signal.connect(self.log_message.emit)
        self.preview_worker.preview_ready.connect(self._show_preview_dialog)
        self.preview_worker.error_signal.connect(self._on_preview_error)
        self.preview_worker.finished.connect(self._on_preview_complete)
        
        # Iniciar análisis
        self.log_message.emit("info", "👁️ Analizando duplicados...")
        self.preview_worker.start()
    
    def _show_preview_dialog(self, duplicados: dict, total_archivos: int):
        """Muestra diálogo con vista previa de duplicados"""
        if not duplicados:
            QMessageBox.information(
                self,
                "Sin duplicados",
                f"✅ No se encontraron archivos duplicados.\n"
                f"Total de archivos únicos: {total_archivos}"
            )
            return
        
        # Crear diálogo
        dialog = QDialog(self)
        dialog.setWindowTitle("Vista Previa de Duplicados")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Info header
        total_duplicados = sum(len(files) - 1 for files in duplicados.values())
        info_label = QLabel(
            f"<b>Contratos con duplicados:</b> {len(duplicados)}<br>"
            f"<b>Archivos a eliminar:</b> {total_duplicados}<br>"
            f"<b>Archivos totales:</b> {total_archivos}"
        )
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
        # Text edit con listado
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        preview_text = ""
        for contrato, archivos in duplicados.items():
            preview_text += f"\n📋 Contrato: {contrato} ({len(archivos)} archivos)\n"
            for idx, archivo in enumerate(archivos, 1):
                marcador = "✅ CONSERVAR" if idx == 1 else "🗑️ ELIMINAR"
                preview_text += f"   [{idx}] {marcador}\n"
                preview_text += f"       {archivo}\n"
        
        text_edit.setPlainText(preview_text)
        layout.addWidget(text_edit)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def _execute_step3(self):
        """Ejecuta el paso 3: Limpiar duplicados"""
        folder = self.step3_folder.get_path()
        
        # Validaciones
        if not folder:
            QMessageBox.warning(
                self,
                "Carpeta requerida",
                "Por favor selecciona una carpeta con archivos renombrados."
            )
            return
        
        if not os.path.isdir(folder):
            QMessageBox.critical(
                self,
                "Carpeta inválida",
                f"La carpeta seleccionada no existe:\n{folder}"
            )
            return
        
        # Confirmación
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "⚠️ Esta operación eliminará permanentemente los archivos duplicados.\n\n"
            "¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            self.log_message.emit("warning", "⏹️ Operación cancelada por el usuario")
            return
        
        # Deshabilitar botones
        self._set_buttons_enabled(False)
        self.btn_preview.setEnabled(False)
        self.setCursor(QCursor(Qt.WaitCursor))
        
        # Crear y configurar worker
        self.current_worker = SunatDuplicatesWorker(folder)
        
        # Conectar señales
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step3_finished)
        self.current_worker.error_signal.connect(self._on_worker_error)
        self.current_worker.finished.connect(self._on_worker_complete)
        
        # Iniciar worker
        self.log_message.emit("info", "🗑️ Iniciando limpieza de duplicados...")
        self.current_worker.start()
    
    @Slot(str, dict)
    def _on_step1_finished(self, excel_path: str, stats: dict):
        """Handler cuando termina el paso 1"""
        self.stepper.mark_step_completed(0)
        
        QMessageBox.information(
            self,
            "Diagnóstico completado",
            f"✅ Proceso completado exitosamente\n\n"
            f"📄 Archivos procesados: {stats['processed']}\n"
            f"⚠️ Sin datos: {stats['sin_datos']}\n"
            f"❌ Errores: {stats['errors']}\n\n"
            f"Excel generado:\n{os.path.basename(excel_path)}"
        )
    
    @Slot(dict)
    def _on_step2_finished(self, result: dict):
        """Handler cuando termina el paso 2"""
        if not result.get('preflight_ok', True):
            self.log_message.emit("error", "❌ Paso 2 bloqueado por validación previa")
            return
        
        stats = result.get('stats') or {}
        self.stepper.mark_step_completed(1)
        
        QMessageBox.information(
            self,
            "Renombrado completado",
            f"✅ Proceso completado exitosamente\n\n"
            f"📄 Total archivos: {stats['total_files']}\n"
            f"✅ Renombrados: {stats['renamed']}\n"
            f"⏭️ Omitidos: {stats['skipped']}\n"
            f"❌ Errores: {stats['errors']}"
        )
    
    @Slot(int, int, int, int)
    def _on_step3_finished(self, total: int, duplicados: int, eliminados: int, errores: int):
        """Handler cuando termina el paso 3"""
        self.stepper.mark_step_completed(2)
        
        QMessageBox.information(
            self,
            "Limpieza completada",
            f"✅ Proceso completado exitosamente\n\n"
            f"📂 Archivos iniciales: {total}\n"
            f"🔍 Contratos duplicados: {duplicados}\n"
            f"✅ Archivos eliminados: {eliminados}\n"
            f"❌ Errores: {errores}\n"
            f"📄 Archivos finales: {total - eliminados}"
        )
    
    @Slot(str)
    def _on_worker_error(self, error_msg: str):
        """Handler para errores del worker"""
        title = "Validación previa" if error_msg.startswith("Validación previa") else "Error en el proceso"
        QMessageBox.critical(
            self,
            title,
            f"❌ {error_msg}"
        )
    
    @Slot()
    def _on_worker_complete(self):
        """Handler cuando el worker termina (éxito o error)"""
        self._set_buttons_enabled(True)
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.current_worker = None
    
    @Slot(str)
    def _on_preview_error(self, error_msg: str):
        """Handler para errores del preview worker"""
        QMessageBox.critical(
            self,
            "Error en análisis",
            f"❌ {error_msg}"
        )
    
    @Slot()
    def _on_preview_complete(self):
        """Handler cuando termina el preview"""
        self.btn_preview.setEnabled(True)
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.preview_worker = None
    
    def _set_buttons_enabled(self, enabled: bool):
        """Habilita/deshabilita todos los botones de ejecución"""
        for btn in self.execute_buttons:
            btn.setEnabled(enabled)
