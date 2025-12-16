"""
Tab Settings - Tab de configuración y preferencias
"""
import datetime
import json
import os
import psutil
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QRadioButton, QCheckBox,
    QColorDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QColor

# Importar helper de rutas
from utils.path_helper import get_resource_path


class TabSettings(QWidget):
    """Tab de configuración"""
    
    # Señales
    log_message = Signal(str, str)
    progress_updated = Signal(int, int)
    stats_updated = Signal(dict)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.config_file = get_resource_path("resources/config.json")
        
        self._init_ui()
        self._load_settings()
        self._update_performance_info()
    
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
        layout.addWidget(self.check_sounds_enabled)
        
        self.check_sound_complete = QCheckBox("Sonido al completar proceso")
        layout.addWidget(self.check_sound_complete)
        
        self.check_sound_error = QCheckBox("Sonido al detectar error")
        layout.addWidget(self.check_sound_error)
        
        return group
    
    def _create_performance_card(self) -> QGroupBox:
        """Card de rendimiento - Configuración automática"""
        group = QGroupBox("⚡ Rendimiento")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Información del sistema
        sys_label = QLabel("Información del Sistema")
        sys_label.setProperty("labelStyle", "header")
        layout.addWidget(sys_label)
        
        # Detalles del sistema
        self.system_info_label = QLabel()
        self.system_info_label.setProperty("labelStyle", "secondary")
        self.system_info_label.setWordWrap(True)
        layout.addWidget(self.system_info_label)
        
        # Configuración automática
        auto_label = QLabel("Configuración Automática")
        auto_label.setProperty("labelStyle", "header")
        layout.addWidget(auto_label)
        
        self.performance_info_label = QLabel()
        self.performance_info_label.setProperty("labelStyle", "secondary")
        self.performance_info_label.setWordWrap(True)
        layout.addWidget(self.performance_info_label)
        
        # Botón para recalcular
        recalc_layout = QHBoxLayout()
        recalc_layout.addStretch()
        self.btn_recalc = QPushButton("🔄 Recalcular Configuración Óptima")
        self.btn_recalc.clicked.connect(self._recalculate_performance)
        recalc_layout.addWidget(self.btn_recalc)
        recalc_layout.addStretch()
        layout.addLayout(recalc_layout)
        
        # Nota informativa
        info_label = QLabel("<small><i>La configuración se ajusta automáticamente según las capacidades de tu equipo</i></small>")
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)
        
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
    
    def _detect_hardware(self):
        """Detecta las capacidades del hardware del sistema"""
        try:
            cpu_count = os.cpu_count() or 4
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memoria
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Discos
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_free_gb = disk.free / (1024**3)
            
            return {
                'cpu_count': cpu_count,
                'cpu_percent': cpu_percent,
                'memory_total_gb': round(memory_total_gb, 1),
                'memory_available_gb': round(memory_available_gb, 1),
                'disk_total_gb': round(disk_total_gb, 1),
                'disk_free_gb': round(disk_free_gb, 1)
            }
        except Exception as e:
            print(f"Error detectando hardware: {e}")
            return {
                'cpu_count': 4,
                'cpu_percent': 0,
                'memory_total_gb': 8.0,
                'memory_available_gb': 4.0,
                'disk_total_gb': 500.0,
                'disk_free_gb': 200.0
            }
    
    def _calculate_optimal_settings(self, hardware_info):
        """Calcula configuración óptima basada en hardware"""
        cpu_count = hardware_info['cpu_count']
        memory_gb = hardware_info['memory_total_gb']
        
        # Cálculo de workers óptimos
        if memory_gb < 4.0:
            # Equipos con poca RAM
            workers = max(2, min(cpu_count, 2))
            console_interval = 4
            batch_size = 50
        elif memory_gb < 8.0:
            # Equipos con RAM moderada
            workers = max(2, min(cpu_count, 4))
            console_interval = 2
            batch_size = 100
        else:
            # Equipos con buena RAM
            workers = max(2, min(cpu_count - 1, 8))  # Dejar 1 CPU libre
            console_interval = 1
            batch_size = 200
        
        # Ajustar según uso actual de CPU
        if hardware_info['cpu_percent'] > 70:
            workers = max(2, workers - 1)
            console_interval = max(2, console_interval)
        
        # Ajustar según RAM disponible
        if hardware_info['memory_available_gb'] < 2.0:
            workers = max(2, workers - 1)
            batch_size = max(50, batch_size - 50)
        
        return {
            'workers': workers,
            'console_interval': console_interval,
            'batch_size': batch_size
        }
    
    def _update_performance_info(self):
        """Actualiza la información de rendimiento en la UI"""
        hardware = self._detect_hardware()
        optimal = self._calculate_optimal_settings(hardware)
        
        # Actualizar información del sistema
        system_text = f"""
        <b>Procesador:</b> {hardware['cpu_count']} núcleos<br>
        <b>Memoria RAM:</b> {hardware['memory_total_gb']} GB total, {hardware['memory_available_gb']} GB disponible<br>
        <b>Disco:</b> {hardware['disk_total_gb']} GB total, {hardware['disk_free_gb']} GB libre
        """
        self.system_info_label.setText(system_text)
        
        # Actualizar configuración óptima
        perf_text = f"""
        <b>Workers paralelos:</b> {optimal['workers']} (óptimo para tu equipo)<br>
        <b>Intervalo de consola:</b> {optimal['console_interval']} segundos<br>
        <b>Tamaño de lote:</b> {optimal['batch_size']} documentos
        """
        self.performance_info_label.setText(perf_text)
        
        # Guardar valores calculados para usar al guardar
        self.optimal_settings = optimal
    
    @Slot()
    def _recalculate_performance(self):
        """Recalcula la configuración óptima"""
        self._update_performance_info()
        self.log_message.emit("info", "🔄 Configuración de rendimiento recalculada")
    
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
        """Carga la configuración actual desde config.json"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Cargar tema
                theme = config.get('theme', 'dark')
                if theme == 'dark':
                    self.radio_dark.setChecked(True)
                else:
                    self.radio_light.setChecked(True)
                
                # Cargar sonidos
                sounds = config.get('preferences', {}).get('sounds', {})
                self.check_sounds_enabled.setChecked(sounds.get('enabled', True))
                self.check_sound_complete.setChecked(sounds.get('sound_complete', True))
                self.check_sound_error.setChecked(sounds.get('sound_error', True))
                
                self.log_message.emit("success", "✅ Configuración cargada exitosamente")
            else:
                self.log_message.emit("warning", "⚠️ Archivo de configuración no encontrado, usando valores por defecto")
        except Exception as e:
            self.log_message.emit("error", f"❌ Error cargando configuración: {str(e)}")
    
    @Slot()
    def _save_settings(self):
        """Guarda la configuración"""
        try:
            # Cargar configuración existente
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Aplicar tema
            if self.radio_dark.isChecked():
                new_theme = "dark"
            else:
                new_theme = "light"
            
            # Comparar usando el método correcto
            if new_theme != self.theme_manager.get_current_theme():
                self.theme_manager.set_theme(new_theme)
                self.log_message.emit("success", f"✅ Tema cambiado a: {new_theme}")
            
            config['theme'] = new_theme
            config['last_modified'] = datetime.datetime.now().isoformat()
            
            # Aplicar configuración de sonidos
            if 'preferences' not in config:
                config['preferences'] = {}
            
            if 'sounds' not in config['preferences']:
                config['preferences']['sounds'] = {}
            
            config['preferences']['sounds']['enabled'] = self.check_sounds_enabled.isChecked()
            config['preferences']['sounds']['sound_complete'] = self.check_sound_complete.isChecked()
            config['preferences']['sounds']['sound_error'] = self.check_sound_error.isChecked()
            
            # Aplicar configuración de rendimiento óptima
            if 'performance' not in config['preferences']:
                config['preferences']['performance'] = {}
            
            if hasattr(self, 'optimal_settings'):
                config['preferences']['performance']['workers'] = self.optimal_settings['workers']
                config['preferences']['performance']['console_interval'] = self.optimal_settings['console_interval']
                config['preferences']['performance']['batch_size'] = self.optimal_settings['batch_size']
            
            # Guardar archivo
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "La configuración se ha guardado correctamente.\n\n"
                f"• Workers: {self.optimal_settings['workers']} (configurados automáticamente)\n"
                f"• Intervalo consola: {self.optimal_settings['console_interval']} segundos\n"
                f"• Tamaño lote: {self.optimal_settings['batch_size']} documentos"
            )
            
            self.log_message.emit("success", "✅ Configuración guardada exitosamente")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar la configuración:\n{str(e)}"
            )
            self.log_message.emit("error", f"❌ Error guardando configuración: {str(e)}")