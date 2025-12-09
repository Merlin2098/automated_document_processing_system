"""
Tab Quick Tools - Tab de herramientas rápidas
Solo contiene: Dividir PDF
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QGroupBox, QMessageBox
)
from PySide6.QtCore import Signal, Slot, QThread
import os

from ui.widgets.file_selector import FileSelector


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
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Card: Dividir PDF
        card = self._create_split_pdf_card()
        layout.addWidget(card)
        
        # Spacer
        layout.addStretch()
    
    def _create_split_pdf_card(self) -> QGroupBox:
        """Crea la card de dividir PDF"""
        group = QGroupBox("📄 Dividir PDF por Páginas")
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Selector de archivo
        file_label = QLabel("📂 Archivo de entrada")
        file_label.setProperty("labelStyle", "header")
        layout.addWidget(file_label)
        
        self.file_selector = FileSelector(
            mode="file",
            file_filter="PDF Files (*.pdf)",
            placeholder="Seleccionar archivo PDF..."
        )
        layout.addWidget(self.file_selector)
        
        # Número de hojas
        pages_label = QLabel("📑 Número de hojas por división")
        pages_label.setProperty("labelStyle", "header")
        layout.addWidget(pages_label)
        
        self.pages_spinbox = QSpinBox()
        self.pages_spinbox.setMinimum(1)
        self.pages_spinbox.setMaximum(100)
        self.pages_spinbox.setValue(5)
        self.pages_spinbox.setFixedWidth(100)
        layout.addWidget(self.pages_spinbox)
        
        # Info box
        info_layout = QHBoxLayout()
        info_icon = QLabel("ℹ️")
        info_text = QLabel("Se crearán archivos de 5 páginas cada uno en la carpeta del archivo original")
        info_text.setProperty("labelStyle", "secondary")
        info_text.setWordWrap(True)
        
        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text, 1)
        layout.addLayout(info_layout)
        
        # Botón ejecutar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_split = QPushButton("▶️ Dividir PDF")
        self.btn_split.clicked.connect(self._on_split_pdf)
        button_layout.addWidget(self.btn_split)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return group
    
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
        
        # Log inicio
        self.log_message.emit("info", f"📄 Iniciando división de PDF: {os.path.basename(pdf_path)}")
        self.log_message.emit("info", f"📑 Páginas por archivo: {pages_per_file}")
        
        # TODO: Implementar lógica de división
        # Por ahora solo simulamos
        self.processing = True
        self.btn_split.setEnabled(False)
        
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo - Simulando proceso...")
        
        # Simular proceso
        import time
        time.sleep(1)
        
        self.log_message.emit("success", "✅ División de PDF completada")
        self.log_message.emit("info", f"📁 Archivos creados en: {os.path.dirname(pdf_path)}")
        
        self.processing = False
        self.btn_split.setEnabled(True)