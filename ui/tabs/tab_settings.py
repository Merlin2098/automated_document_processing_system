"""
Tab Settings - Tab de configuración y preferencias
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QRadioButton, QCheckBox,
    QComboBox, QColorDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QColor


class TabSettings(QWidget):
    """Tab de configuración"""
    
    # Señales
    log_message = Signal(str, str)
    progress_updated = Signal(int, int)
    stats_updated = Signal(dict)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Área de scroll para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget contenedor del contenido
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Crear cards
        appearance_card = self._create_appearance_card()
        layout.addWidget(appearance_card)
        
        sounds_card = self._create_sounds_card()
        layout.addWidget(sounds_card)
        
        performance_card = self._create_performance_card()
        layout.addWidget(performance_card)
        
        about_card = self._create_about_card()
        layout.addWidget(about_card)
        
        # Botón guardar
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.btn_save = QPushButton("💾 Guardar Configuración")
        self.btn_save.clicked.connect(self._save_settings)
        save_layout.addWidget(self.btn_save)
        save_layout.addStretch()
        layout.addLayout(save_layout)
        
        # Spacer
        layout.addStretch()
        
        # Establecer el widget de contenido en el scroll
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_appearance_card(self) -> QGroupBox:
        """Card de apariencia"""
        group = QGroupBox("🎨 Apariencia")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Tema visual
        theme_label = QLabel("Tema visual")
        theme_label.setProperty("labelStyle", "header")
        layout.addWidget(theme_label)
        
        theme_layout = QHBoxLayout()
        self.radio_dark = QRadioButton("Tema Oscuro")
        self.radio_light = QRadioButton("Tema Claro")
        
        # Establecer tema actual usando el método correcto
        current_theme = self.theme_manager.get_current_theme()
        if current_theme == "dark":
            self.radio_dark.setChecked(True)
        else:
            self.radio_light.setChecked(True)
        
        theme_layout.addWidget(self.radio_dark)
        theme_layout.addWidget(self.radio_light)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Color primario
        color_label = QLabel("Color primario")
        color_label.setProperty("labelStyle", "header")
        layout.addWidget(color_label)
        
        color_layout = QHBoxLayout()
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 40)
        self.color_btn.clicked.connect(self._choose_color)
        
        current_color = self.theme_manager.get_color('primary')
        self.color_btn.setStyleSheet(f"background-color: {current_color}; border: 2px solid #888;")
        
        self.color_label = QLabel(current_color)
        self.color_label.setProperty("labelStyle", "secondary")
        
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        return group
    
    def _create_sounds_card(self) -> QGroupBox:
        """Card de sonidos"""
        group = QGroupBox("🔊 Sonidos del Sistema")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        self.check_sounds_enabled = QCheckBox("Habilitar notificaciones sonoras")
        self.check_sounds_enabled.setChecked(True)
        layout.addWidget(self.check_sounds_enabled)
        
        self.check_sound_complete = QCheckBox("Sonido al completar proceso")
        self.check_sound_complete.setChecked(True)
        layout.addWidget(self.check_sound_complete)
        
        return group
    
    def _create_performance_card(self) -> QGroupBox:
        """Card de rendimiento"""
        group = QGroupBox("⚡ Rendimiento")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Workers paralelos
        workers_label = QLabel("Workers paralelos")
        workers_label.setProperty("labelStyle", "header")
        layout.addWidget(workers_label)
        
        self.workers_combo = QComboBox()
        self.workers_combo.addItems([
            "2 Workers",
            "4 Workers (Recomendado)",
            "8 Workers"
        ])
        self.workers_combo.setCurrentIndex(1)
        layout.addWidget(self.workers_combo)
        
        # Intervalo de consola
        console_label = QLabel("Intervalo de actualización de consola")
        console_label.setProperty("labelStyle", "header")
        layout.addWidget(console_label)
        
        self.console_combo = QComboBox()
        self.console_combo.addItems([
            "2 segundos",
            "4 segundos (Recomendado)",
            "8 segundos"
        ])
        self.console_combo.setCurrentIndex(1)
        layout.addWidget(self.console_combo)
        
        return group
    
    def _create_about_card(self) -> QGroupBox:
        """Card de acerca de"""
        group = QGroupBox("ℹ️ Acerca de")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        info = QLabel("""
<b style="font-size: 16px; color: #2196F3;">DocFlow Eventuales v4.0</b><br>
Desarrollado para procesamiento empresarial de documentos<br>
Framework: PySide6 | Python 3.11+<br><br>
© Diciembre 2025 Ricardo Fabian Uculmana Quispe<br>
Todos los derechos reservados.
        """)
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        return group
    
    @Slot()
    def _choose_color(self):
        """Abre diálogo de selección de color"""
        current_color = QColor(self.theme_manager.get_color('primary'))
        color = QColorDialog.getColor(current_color, self, "Seleccionar color primario")
        
        if color.isValid():
            color_hex = color.name()
            self.color_btn.setStyleSheet(f"background-color: {color_hex}; border: 2px solid #888;")
            self.color_label.setText(color_hex)
            self.log_message.emit("info", f"🎨 Color primario cambiado a: {color_hex}")
    
    def _load_settings(self):
        """Carga la configuración actual"""
        # Aquí se cargarían las configuraciones desde un archivo
        pass
    
    @Slot()
    def _save_settings(self):
        """Guarda la configuración"""
        # Aplicar tema
        if self.radio_dark.isChecked():
            new_theme = "dark"
        else:
            new_theme = "light"
        
        # Comparar usando el método correcto
        if new_theme != self.theme_manager.get_current_theme():
            self.theme_manager.set_theme(new_theme)
            self.log_message.emit("success", f"✅ Tema cambiado a: {new_theme}")
        
        # TODO: Guardar otras configuraciones
        
        QMessageBox.information(
            self,
            "Configuración Guardada",
            "La configuración se ha guardado correctamente."
        )
        
        self.log_message.emit("success", "✅ Configuración guardada exitosamente")