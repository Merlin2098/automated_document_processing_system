"""
Tab Quick Tools - Tab de herramientas rápidas
Solo contiene: Dividir PDF
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QGroupBox, QMessageBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt
import os
import sys

# Intentar importar widgets con manejo de errores
try:
    from ui.widgets.file_selector import FileSelector
    print("✅ FileSelector importado correctamente")
except ImportError as e:
    print(f"❌ Error importando FileSelector: {e}")
    sys.exit(1)

try:
    from ui.workers.pdf_splitter_worker import PdfSplitterWorker
    print("✅ PdfSplitterWorker importado correctamente")
except ImportError as e:
    print(f"❌ Error importando PdfSplitterWorker: {e}")
    sys.exit(1)


class TabQuickTools(QWidget):
    """Tab de herramientas rápidas"""
    
    # Señales para comunicación con widgets comunes
    log_message = Signal(str, str)  # (tipo, mensaje)
    progress_updated = Signal(int, int)  # (current, total)
    stats_updated = Signal(dict)  # {time, errors, etc}
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.processing = False
        self.worker = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        print("🔧 Inicializando TabQuickTools UI...")
        
        # Layout principal del tab
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Widget contenedor dentro del scroll
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 20, 20, 20)
        scroll_layout.setSpacing(15)
        
        # Card: Dividir PDF
        print("📦 Creando card de dividir PDF...")
        card = self._create_split_pdf_card()
        scroll_layout.addWidget(card)
        print("✅ Card añadida al layout")
        
        # Spacer para empujar contenido hacia arriba
        scroll_layout.addStretch()
        
        # Asignar contenido al scroll area
        scroll_area.setWidget(scroll_content)
        
        # Agregar scroll area al layout principal
        main_layout.addWidget(scroll_area)
        
        print("✅ TabQuickTools UI inicializada con scroll")
    
    def _create_split_pdf_card(self) -> QGroupBox:
        """Crea la card de dividir PDF"""
        print("  📝 Creando QGroupBox...")
        group = QGroupBox("📄 Dividir PDF por Páginas")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setSpacing(20)
        
        # Selector de archivo
        print("  📝 Creando label de archivo...")
        file_label = QLabel("📂 Archivo de entrada")
        file_label.setProperty("labelStyle", "header")
        layout.addWidget(file_label)
        
        print("  📝 Creando FileSelector...")
        self.file_selector = FileSelector(
            mode="file",
            file_filter="PDF Files (*.pdf)",
            placeholder="Seleccionar archivo PDF..."
        )
        self.file_selector.setMinimumHeight(40)
        layout.addWidget(self.file_selector)
        print("  ✅ FileSelector añadido")
        
        # Espaciador
        layout.addSpacing(25)
        
        # Número de hojas
        print("  📝 Creando label de páginas...")
        pages_label = QLabel("🔢 Número de hojas por división")
        pages_label.setProperty("labelStyle", "header")
        layout.addWidget(pages_label)
        
        print("  📝 Creando QSpinBox...")
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setMinimum(1)
        self.pages_spinbox.setMaximum(100)
        self.pages_spinbox.setValue(5)
        self.pages_spinbox.setMinimumWidth(120)
        self.pages_spinbox.setMinimumHeight(38)
        self.pages_spinbox.valueChanged.connect(self._update_info_text)
        layout.addWidget(self.pages_spinbox)
        print("  ✅ QSpinBox añadido")
        
        # Espaciador flexible grande - empuja el contenido inferior hacia abajo
        layout.addStretch(2)
        
        # Info box
        print("  📝 Creando info box...")
        info_layout = QHBoxLayout()
        info_icon = QLabel("ℹ️")
        info_icon.setFixedSize(20, 20)
        self.info_text = QLabel("Se crearán archivos de 5 páginas cada uno en la carpeta del archivo original")
        self.info_text.setProperty("labelStyle", "secondary")
        self.info_text.setWordWrap(True)
        
        info_layout.addWidget(info_icon)
        info_layout.addWidget(self.info_text, 1)
        layout.addLayout(info_layout)
        print("  ✅ Info box añadido")
        
        # Espaciador
        layout.addSpacing(20)
        
        # Botón ejecutar
        print("  📝 Creando botón...")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_split = QPushButton("▶️ Dividir PDF")
        self.btn_split.setMinimumHeight(45)
        self.btn_split.setMinimumWidth(180)
        self.btn_split.clicked.connect(self._on_split_pdf)
        button_layout.addWidget(self.btn_split)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        print("  ✅ Botón añadido")
        
        print("  ✅ Card completada")
        return group
    
    @Slot(int)
    def _update_info_text(self, value: int):
        """Actualiza el texto informativo cuando cambia el spinbox"""
        self.info_text.setText(
            f"Se crearán archivos de {value} página{'s' if value != 1 else ''} "
            f"cada uno en la carpeta del archivo original"
        )
    
    @Slot()
    def _on_split_pdf(self):
        """Handler para dividir PDF"""
        if self.processing:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Ya hay un proceso en ejecución."
            )
            return
        
        # Validar entrada
        pdf_path = self.file_selector.get_path()
        pages_per_file = self.pages_spinbox.value()
        
        if not pdf_path:
            QMessageBox.warning(
                self,
                "Advertencia",
                "Debe seleccionar un archivo PDF."
            )
            return
        
        if not os.path.exists(pdf_path):
            QMessageBox.warning(
                self,
                "Error",
                f"El archivo no existe:\n{pdf_path}"
            )
            return
        
        # Iniciar procesamiento
        self.processing = True
        self.btn_split.setEnabled(False)
        
        # Log inicio
        self.log_message.emit("info", "=" * 50)
        self.log_message.emit("info", f"📄 Iniciando división de PDF: {os.path.basename(pdf_path)}")
        self.log_message.emit("info", f"🔢 Páginas por archivo: {pages_per_file}")
        self.log_message.emit("info", "=" * 50)
        
        # Crear y configurar worker
        self.worker = PdfSplitterWorker(pdf_path, pages_per_file)
        
        # Conectar señales del worker
        self.worker.log_message.connect(self._handle_worker_log)
        self.worker.progress_updated.connect(self._handle_worker_progress)
        self.worker.finished.connect(self._handle_worker_finished)
        self.worker.error.connect(self._handle_worker_error)
        
        # Iniciar worker
        self.worker.start()
    
    @Slot(str, str)
    def _handle_worker_log(self, log_type: str, message: str):
        """Propaga los logs del worker a la consola"""
        self.log_message.emit(log_type, message)
    
    @Slot(int, int)
    def _handle_worker_progress(self, current: int, total: int):
        """Propaga el progreso del worker"""
        self.progress_updated.emit(current, total)
    
    @Slot(dict)
    def _handle_worker_finished(self, resultado: dict):
        """Handler cuando el worker termina exitosamente"""
        # Emitir estadísticas finales
        stats = {
            'time': resultado.get('tiempo_transcurrido', 0),
            'errors': resultado.get('errores', 0),
            'current': resultado.get('pdfs_generados', 0),
            'total': resultado.get('pdfs_generados', 0)
        }
        self.stats_updated.emit(stats)
        
        # Mostrar diálogo de éxito
        QMessageBox.information(
            self,
            "Proceso Completado",
            f"✅ División completada exitosamente\n\n"
            f"📊 Archivos generados: {resultado['pdfs_generados']}\n"
            f"⏱️ Tiempo: {resultado['tiempo_transcurrido']:.2f}s\n"
            f"📂 Ubicación:\n{resultado['carpeta_salida']}"
        )
        
        # Limpiar
        self._cleanup_worker()
    
    @Slot(str)
    def _handle_worker_error(self, error_message: str):
        """Handler cuando el worker falla"""
        # Mostrar diálogo de error
        QMessageBox.critical(
            self,
            "Error",
            f"❌ Error durante el procesamiento:\n\n{error_message}"
        )
        
        # Limpiar
        self._cleanup_worker()
    
    def _cleanup_worker(self):
        """Limpia el worker y restaura el estado de la UI"""
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
        
        self.processing = False
        self.btn_split.setEnabled(True)
        
        self.log_message.emit("info", "=" * 50)