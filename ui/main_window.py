"""
Main Window - Ventana principal de la aplicación
Contiene el tab widget y los componentes comunes
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
import os

from utils.theme_manager import ThemeManager
from ui.widgets.monitoring_panel import MonitoringPanel
from ui.widgets.console_widget import ConsoleWidget
from ui.tabs.tab_quick_tools import TabQuickTools
from ui.tabs.tab_pipeline_core import TabPipelineCore
from ui.tabs.tab_pipeline_sunat import TabPipelineSunat
from ui.tabs.tab_settings import TabSettings


class MainWindow(QMainWindow):
    """Ventana principal de Matrix File Processor"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar gestor de temas
        self.theme_manager = ThemeManager()
        
        # Configurar ventana
        self.setWindowTitle("Matrix File Processor v3.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Establecer ícono de la aplicación
        self._set_window_icon()
        
        # Inicializar UI
        self._init_ui()
        
        # Aplicar tema
        self._apply_theme()
        
        # Conectar señales
        self.theme_manager.theme_changed.connect(self._apply_theme)
    
    def _set_window_icon(self):
        """Establece el ícono de la ventana"""
        # Buscar el ícono en resources/app.ico
        icon_path = os.path.join("resources", "app.ico")
        
        # Si no existe en esa ruta, intentar ruta relativa al script
        if not os.path.exists(icon_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "..", "resources", "app.ico")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
    
    def _init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Crear tabs
        self.tab_quick_tools = TabQuickTools(self.theme_manager)
        self.tab_pipeline_core = TabPipelineCore(self.theme_manager)
        self.tab_pipeline_sunat = TabPipelineSunat(self.theme_manager)
        self.tab_settings = TabSettings(self.theme_manager)
        
        # Agregar tabs
        self.tab_widget.addTab(self.tab_quick_tools, "📄 Herramientas")
        self.tab_widget.addTab(self.tab_pipeline_core, "📋 Pipeline Core")
        self.tab_widget.addTab(self.tab_pipeline_sunat, "💼 Pipeline SUNAT")
        self.tab_widget.addTab(self.tab_settings, "⚙️ Configuración")
        
        main_layout.addWidget(self.tab_widget)
        
        # Panel de monitoreo
        self.monitoring_panel = MonitoringPanel(self.theme_manager)
        main_layout.addWidget(self.monitoring_panel)
        
        # Consola
        self.console_widget = ConsoleWidget(self.theme_manager)
        main_layout.addWidget(self.console_widget)
        
        # Action bar
        action_bar = self._create_action_bar()
        main_layout.addWidget(action_bar)
        
        # Conectar tabs con consola y monitoring
        self._connect_tabs()
    
    def _create_header(self) -> QWidget:
        """Crea el header de la aplicación"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel("Diciembre 2025 - Desarrollado por Ricardo Uculmana Quispe")
        title_label.setProperty("labelStyle", "title")
        
        version_label = QLabel("v3.0")
        version_label.setProperty("labelStyle", "secondary")
        
        # Layout de título
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        # Controles de ventana (opcional)
        # Por ahora no los implementamos ya que Qt maneja esto nativamente
        
        return header_widget
    
    def _create_action_bar(self) -> QWidget:
        """Crea la barra de acciones inferior"""
        action_bar = QWidget()
        layout = QHBoxLayout(action_bar)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.addStretch()
        
        # Botón abrir carpeta
        self.btn_open_folder = QPushButton("📂 Abrir Carpeta")
        self.btn_open_folder.setProperty("buttonStyle", "secondary")
        self.btn_open_folder.clicked.connect(self._on_open_folder)
        
        # Botón limpiar
        self.btn_clear = QPushButton("🧹 Limpiar")
        self.btn_clear.setProperty("buttonStyle", "secondary")
        self.btn_clear.clicked.connect(self._on_clear)
        
        # Botón exportar log
        self.btn_export_log = QPushButton("💾 Exportar Log")
        self.btn_export_log.setProperty("buttonStyle", "secondary")
        self.btn_export_log.clicked.connect(self._on_export_log)
        
        layout.addWidget(self.btn_open_folder)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_export_log)
        
        return action_bar
    
    def _connect_tabs(self):
        """Conecta las señales de los tabs con los widgets comunes"""
        # Conectar tabs con consola
        self.tab_quick_tools.log_message.connect(self.console_widget.append_log)
        self.tab_pipeline_core.log_message.connect(self.console_widget.append_log)
        self.tab_pipeline_sunat.log_message.connect(self.console_widget.append_log)
        
        # Conectar tabs con monitoring panel
        self.tab_quick_tools.progress_updated.connect(self.monitoring_panel.update_progress)
        self.tab_pipeline_core.progress_updated.connect(self.monitoring_panel.update_progress)
        self.tab_pipeline_sunat.progress_updated.connect(self.monitoring_panel.update_progress)
        
        self.tab_quick_tools.stats_updated.connect(self.monitoring_panel.update_stats)
        self.tab_pipeline_core.stats_updated.connect(self.monitoring_panel.update_stats)
        self.tab_pipeline_sunat.stats_updated.connect(self.monitoring_panel.update_stats)
    
    def _apply_theme(self):
        """Aplica el tema actual a la ventana"""
        stylesheet = self.theme_manager.get_stylesheet()
        self.setStyleSheet(stylesheet)
        
        # Actualizar paleta si es necesario
        palette = self.theme_manager.get_palette()
        self.setPalette(palette)
    
    def _on_open_folder(self):
        """Handler para abrir carpeta"""
        # TODO: Implementar apertura de carpeta de salida
        self.console_widget.append_log("info", "Función 'Abrir Carpeta' pendiente de implementar")
    
    def _on_clear(self):
        """Handler para limpiar"""
        self.console_widget.clear()
        self.monitoring_panel.reset()
        self.console_widget.append_log("success", "🧹 Interfaz limpiada - Sistema listo")
    
    def _on_export_log(self):
        """Handler para exportar log"""
        # TODO: Implementar exportación de log
        self.console_widget.append_log("info", "Función 'Exportar Log' pendiente de implementar")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        # Aquí se pueden agregar confirmaciones si hay procesos en ejecución
        event.accept()