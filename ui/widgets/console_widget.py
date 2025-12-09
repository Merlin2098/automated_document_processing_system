"""
Console Widget - Widget de consola para logs
"""
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCharFormat, QColor, QFont, QTextCursor
from datetime import datetime


class ConsoleWidget(QWidget):
    """Widget de consola con colores para diferentes tipos de mensajes"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self._init_ui()
        
        # Formatos de texto por tipo de mensaje
        self._init_formats()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Text Edit
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMinimumHeight(250)
        self.text_edit.setMaximumHeight(400)
        
        # Fuente monospace
        font = QFont("Fira Code", 10)
        if not font.exactMatch():
            font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        
        self.text_edit.setFont(font)
        
        layout.addWidget(self.text_edit)
    
    def _init_formats(self):
        """Inicializa los formatos de texto para cada tipo de mensaje"""
        # Formato timestamp
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor(self.theme_manager.get_color('text.muted')))
        
        # Formato success
        self.success_format = QTextCharFormat()
        self.success_format.setForeground(QColor(self.theme_manager.get_color('success')))
        self.success_format.setFontWeight(QFont.Bold)
        
        # Formato error
        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor(self.theme_manager.get_color('error')))
        self.error_format.setFontWeight(QFont.Bold)
        
        # Formato warning
        self.warning_format = QTextCharFormat()
        self.warning_format.setForeground(QColor(self.theme_manager.get_color('warning')))
        self.warning_format.setFontWeight(QFont.Bold)
        
        # Formato info
        self.info_format = QTextCharFormat()
        self.info_format.setForeground(QColor(self.theme_manager.get_color('info')))
        self.info_format.setFontWeight(QFont.Bold)
        
        # Formato normal
        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor(self.theme_manager.get_color('text.primary')))
    
    @Slot(str, str)
    def append_log(self, log_type: str, message: str):
        """
        Añade un mensaje de log a la consola
        
        Args:
            log_type: Tipo de mensaje (success, error, warning, info, normal)
            message: Mensaje a mostrar
        """
        # Obtener timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Obtener cursor
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Insertar timestamp
        cursor.insertText(f"[{timestamp}] ", self.timestamp_format)
        
        # Seleccionar formato según tipo
        if log_type == "success":
            format_to_use = self.success_format
            icon = "✅"
        elif log_type == "error":
            format_to_use = self.error_format
            icon = "❌"
        elif log_type == "warning":
            format_to_use = self.warning_format
            icon = "⚠️"
        elif log_type == "info":
            format_to_use = self.info_format
            icon = "📄"
        else:
            format_to_use = self.normal_format
            icon = ""
        
        # Insertar mensaje
        full_message = f"{icon} {message}" if icon else message
        cursor.insertText(full_message + "\n", format_to_use)
        
        # Auto-scroll al final
        self.text_edit.ensureCursorVisible()
    
    def clear(self):
        """Limpia la consola"""
        self.text_edit.clear()
    
    def get_text(self) -> str:
        """Obtiene todo el texto de la consola"""
        return self.text_edit.toPlainText()
    
    def export_to_file(self, filepath: str):
        """
        Exporta el contenido de la consola a un archivo
        
        Args:
            filepath: Ruta del archivo de destino
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.get_text())
            return True
        except Exception as e:
            print(f"Error exporting console to file: {e}")
            return False