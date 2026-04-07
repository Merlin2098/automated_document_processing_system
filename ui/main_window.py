"""
Main Window - Ventana principal de la aplicación
Contiene el tab widget y los componentes comunes
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon
import os

from utils.theme_manager import ThemeManager
from ui.widgets.monitoring_panel import MonitoringPanel
from ui.widgets.console_widget import ConsoleWidget

# Importar sistema de logging
from utils.logger import get_logger, log_exception

# Obtener logger para este módulo
logger = get_logger('ui.main_window')


class MainWindow(QMainWindow):
    """Ventana principal de Matrix File Processor"""
    
    def __init__(self):
        super().__init__()
        
        logger.info("Inicializando ventana principal...")
        
        try:
            # Inicializar gestor de temas
            logger.debug("Cargando gestor de temas...")
            self.theme_manager = ThemeManager()
            logger.info(f"✅ Tema cargado: {self.theme_manager.get_current_theme()}")
            
            # Configurar ventana
            logger.debug("Configurando ventana principal...")
            self.setWindowTitle("DocFlow Eventuales v4.0")
            self.setMinimumSize(1200, 800)
            self.resize(1400, 900)
            
            # Establecer ícono de la aplicación
            self._set_window_icon()
            
            # Inicializar UI
            logger.debug("Inicializando interfaz de usuario...")
            self._init_ui()
            logger.info("✅ Interfaz de usuario creada")
            
            # Aplicar tema
            logger.debug("Aplicando tema visual...")
            self._apply_theme()
            
            # Conectar señales
            self.theme_manager.theme_changed.connect(self._apply_theme)
            
            # Lazy loading de tabs (se cargan después de mostrar la ventana)
            logger.debug("Programando carga lazy de tabs...")
            QTimer.singleShot(0, self._load_tabs)
            
            logger.info("✅ Ventana principal inicializada correctamente")
            
        except Exception as e:
            log_exception(logger, e, "inicialización de ventana principal")
            raise
    
    def _set_window_icon(self):
        """Establece el ícono de la ventana"""
        try:
            # Buscar el ícono en resources/app.ico
            icon_path = os.path.join("resources", "app.ico")
            
            # Si no existe en esa ruta, intentar ruta relativa al script
            if not os.path.exists(icon_path):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                icon_path = os.path.join(script_dir, "..", "resources", "app.ico")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logger.debug(f"✅ Ícono de ventana establecido: {icon_path}")
            else:
                logger.warning(f"⚠️  Ícono no encontrado: {icon_path}")
                
        except Exception as e:
            logger.warning(f"⚠️  Error estableciendo ícono: {e}")
    
    def _init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Header - altura fija
        header = self._create_header()
        main_layout.addWidget(header, 0)  # Stretch 0 = altura fija
        
        # Tab Widget - DEBE EXPANDIRSE AL MÁXIMO
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        # Inicialmente sin tabs (se cargarán después)
        main_layout.addWidget(self.tab_widget, 10)  # Stretch 10 = MÁXIMA EXPANSIÓN
        logger.debug("Tab widget creado (tabs se cargarán después)")
        
        # Panel de monitoreo - altura fija compacta
        self.monitoring_panel = MonitoringPanel(self.theme_manager)
        self.monitoring_panel.setMaximumHeight(120)  # Limitar altura
        main_layout.addWidget(self.monitoring_panel, 0)  # Stretch 0 = altura fija
        logger.debug("Panel de monitoreo creado")
        
        # Consola - OCULTA por defecto
        self.console_widget = ConsoleWidget(self.theme_manager)
        self.console_widget.setVisible(False)  # Ocultar consola
        main_layout.addWidget(self.console_widget, 0)  # Stretch 0 = altura fija
        logger.debug("Widget de consola creado (oculto)")
    
    def _load_tabs(self):
        """Carga los tabs de forma lazy (después de mostrar la ventana)"""
        logger.info("Iniciando carga lazy de tabs...")
        
        try:
            # Importar tabs solo cuando se necesitan
            from ui.tabs.tab_quick_tools import TabQuickTools
            from ui.tabs.tab_rename_auxiliar import TabRenameAuxiliar
            from ui.tabs.tab_pipeline_core import TabPipelineCore
            from ui.tabs.tab_pipeline_sunat import TabPipelineSunat
            from ui.tabs.tab_settings import TabSettings
            
            logger.debug("Módulos de tabs importados correctamente")
            
            # Crear tabs
            logger.debug("Creando tab: Herramientas Rápidas...")
            self.tab_quick_tools = TabQuickTools(self.theme_manager)

            logger.debug("Creando tab: Rename Auxiliar...")
            self.tab_rename_auxiliar = TabRenameAuxiliar(self.theme_manager)
            
            logger.debug("Creando tab: Pipeline Core...")
            self.tab_pipeline_core = TabPipelineCore(self.theme_manager)
            
            logger.debug("Creando tab: Pipeline SUNAT...")
            self.tab_pipeline_sunat = TabPipelineSunat(self.theme_manager)
            
            logger.debug("Creando tab: Configuración...")
            self.tab_settings = TabSettings(self.theme_manager)
            
            # Agregar tabs
            self.tab_widget.addTab(self.tab_quick_tools, "📄 Herramientas")
            self.tab_widget.addTab(self.tab_rename_auxiliar, "🗂️ Rename Auxiliar")
            self.tab_widget.addTab(self.tab_pipeline_core, "📋 Boletas")
            self.tab_widget.addTab(self.tab_pipeline_sunat, "💼 SUNAT")
            self.tab_widget.addTab(self.tab_settings, "⚙️ Configuración")
            
            logger.info("✅ Todos los tabs cargados correctamente")
            
            # Conectar tabs con consola y monitoring
            self._connect_tabs()
            logger.info("✅ Señales de tabs conectadas")
            
        except Exception as e:
            log_exception(logger, e, "carga lazy de tabs")
            logger.error("❌ Error crítico cargando tabs, la aplicación puede no funcionar correctamente")
    
    def _create_header(self) -> QWidget:
        """Crea el header de la aplicación"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel("Pipeline de Procesamiento y Nomenclatura para Documentos de la División de Eventuales (Metso)")
        title_label.setProperty("labelStyle", "title")
        
        version_label = QLabel("v4.0")
        version_label.setProperty("labelStyle", "secondary")
        
        # Layout de título
        title_layout = QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        
        header_layout.addLayout(title_layout)
        
        return header_widget
    
    def _connect_tabs(self):
        """Conecta las señales de los tabs con los widgets comunes"""
        logger.debug("Conectando señales de tabs...")
        
        try:
            # Conectar cambio de tab para detener flashing
            self.tab_widget.currentChanged.connect(self._stop_flashing)
            
            # Conectar tabs con consola
            self.tab_quick_tools.log_message.connect(self.console_widget.append_log)
            self.tab_rename_auxiliar.log_message.connect(self.console_widget.append_log)
            self.tab_pipeline_core.log_message.connect(self.console_widget.append_log)
            self.tab_pipeline_sunat.log_message.connect(self.console_widget.append_log)
            logger.debug("✅ Señales de consola conectadas")
            
            # Conectar tabs con monitoring panel
            self.tab_quick_tools.progress_updated.connect(self.monitoring_panel.update_progress)
            self.tab_rename_auxiliar.progress_updated.connect(self.monitoring_panel.update_progress)
            self.tab_pipeline_core.progress_updated.connect(self.monitoring_panel.update_progress)
            self.tab_pipeline_sunat.progress_updated.connect(self.monitoring_panel.update_progress)
            
            self.tab_quick_tools.stats_updated.connect(self.monitoring_panel.update_stats)
            self.tab_rename_auxiliar.stats_updated.connect(self.monitoring_panel.update_stats)
            self.tab_pipeline_core.stats_updated.connect(self.monitoring_panel.update_stats)
            self.tab_pipeline_sunat.stats_updated.connect(self.monitoring_panel.update_stats)
            logger.debug("✅ Señales de monitoring conectadas")
            
        except Exception as e:
            log_exception(logger, e, "conexión de señales de tabs")
    
    def _apply_theme(self):
        """Aplica el tema actual a la ventana"""
        try:
            logger.debug(f"Aplicando tema: {self.theme_manager.get_current_theme()}")
            
            stylesheet = self.theme_manager.get_stylesheet()
            self.setStyleSheet(stylesheet)
            
            # Actualizar paleta si es necesario
            palette = self.theme_manager.get_palette()
            self.setPalette(palette)
            
            logger.debug("✅ Tema aplicado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error aplicando tema: {e}")
    
    def flash_window(self, times: int = 5):
        """Hace parpadear la ventana para notificar al usuario"""
        logger.debug(f"Iniciando parpadeo de ventana ({times} veces)")
        
        self.flash_count = 0
        self.flash_max = times
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_step)
        self.flash_timer.start(500)  # Parpadeo cada 0.5s
    
    def _flash_step(self):
        """Step individual del parpadeo"""
        if self.flash_count >= self.flash_max * 2:  # *2 porque alternamos
            self.flash_timer.stop()
            self.setWindowOpacity(1.0)  # Restaurar estado normal
            logger.debug("Parpadeo de ventana completado")
            return
        
        if self.flash_count % 2 == 0:
            self.setWindowOpacity(0.5)  # Oscurecer
        else:
            self.setWindowOpacity(1.0)  # Normal
        
        self.flash_count += 1
    
    def _stop_flashing(self):
        """Detiene el parpadeo si está activo"""
        if hasattr(self, 'flash_timer') and self.flash_timer.isActive():
            self.flash_timer.stop()
            self.setWindowOpacity(1.0)
            logger.debug("Parpadeo de ventana detenido")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        logger.info("Usuario solicitó cerrar la aplicación")
        
        # Aquí se pueden agregar confirmaciones si hay procesos en ejecución
        # Por ahora, aceptar el cierre directamente
        
        logger.info("Cerrando ventana principal...")
        event.accept()
