"""
File Selector Widget - Selector reutilizable de archivos/carpetas
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
)
from PySide6.QtCore import Signal, Slot


class FileSelector(QWidget):
    """
    Widget reutilizable para seleccionar archivos o carpetas
    Emite señal cuando se selecciona una ruta
    """
    
    path_selected = Signal(str)  # Señal emitida con la ruta seleccionada
    
    def __init__(self, 
                 mode="file",  # "file" o "folder"
                 file_filter="All Files (*.*)",
                 placeholder="Seleccionar...",
                 parent=None):
        super().__init__(parent)
        
        self.mode = mode
        self.file_filter = file_filter
        self.placeholder = placeholder
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Line Edit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(self.placeholder)
        self.line_edit.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.line_edit)
        
        # Botón de navegación
        self.browse_btn = QPushButton("📁")
        self.browse_btn.setFixedSize(40, 40)
        self.browse_btn.setProperty("buttonStyle", "secondary")
        self.browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(self.browse_btn)
    
    def _on_browse(self):
        """Handler para el botón de navegación"""
        if self.mode == "folder":
            path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta",
                self.line_edit.text() or ""
            )
        else:  # file
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo",
                self.line_edit.text() or "",
                self.file_filter
            )
        
        if path:
            self.line_edit.setText(path)
            self.path_selected.emit(path)
    
    def _on_text_changed(self, text: str):
        """Handler cuando cambia el texto manualmente"""
        if text:
            self.path_selected.emit(text)
    
    def get_path(self) -> str:
        """Obtiene la ruta actual"""
        return self.line_edit.text()
    
    def set_path(self, path: str):
        """Establece la ruta"""
        self.line_edit.setText(path)
    
    def clear(self):
        """Limpia el selector"""
        self.line_edit.clear()
    
    def set_enabled(self, enabled: bool):
        """Habilita/deshabilita el widget"""
        self.line_edit.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)