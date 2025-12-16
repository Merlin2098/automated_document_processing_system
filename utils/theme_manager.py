"""
Theme Manager - Gestión de temas visuales (Refactorizado)
Carga temas desde archivos JSON en resources/themes/
"""
import json
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QObject, Signal

# Importar sistema de logging
from utils.logger import get_logger, log_exception
# Importar helper de rutas
from utils.path_helper import get_resource_path

# Obtener logger para este módulo
logger = get_logger('utils.theme_manager')


class ThemeManager(QObject):
    """Gestor de temas de la aplicación"""
    
    theme_changed = Signal(str)  # Señal emitida cuando cambia el tema
    
    def __init__(self):
        super().__init__()
        
        logger.debug("Inicializando Theme Manager...")
        
        # Rutas de recursos (usando helper centralizado)
        self.themes_dir = get_resource_path("resources/themes")
        self.config_file = get_resource_path("resources/config.json")
        
        logger.debug(f"Directorio de temas: {self.themes_dir}")
        logger.debug(f"Archivo de configuración: {self.config_file}")
        
        # Estado
        self.available_themes = {}
        self.current_theme_name = "dark"
        self.current_theme_data = {}
        
        # Inicialización
        self._load_themes()
        self._load_config()
        
        logger.info(f"✅ Theme Manager inicializado - Tema activo: {self.current_theme_name}")
    
    def _load_themes(self):
        """Carga todos los temas disponibles desde resources/themes/"""
        try:
            logger.debug("Cargando temas desde disco...")
            
            if not self.themes_dir.exists():
                logger.warning(f"⚠️  Directorio de temas no encontrado: {self.themes_dir}")
                self._create_default_themes()
                return
            
            # Cargar todos los archivos theme_*.json
            theme_files = list(self.themes_dir.glob("theme_*.json"))
            
            if not theme_files:
                logger.warning("⚠️  No se encontraron archivos de tema")
                self._create_default_themes()
                return
            
            logger.debug(f"Encontrados {len(theme_files)} archivos de tema")
            
            for theme_file in theme_files:
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = theme_data['name']
                        self.available_themes[theme_name] = theme_data
                        logger.info(f"✅ Tema cargado: {theme_name} ({theme_data['description']})")
                except Exception as e:
                    logger.error(f"❌ Error cargando tema {theme_file.name}: {e}")
            
            # Verificar que se cargó al menos un tema
            if not self.available_themes:
                logger.warning("⚠️  No se pudo cargar ningún tema, usando valores por defecto")
                self._create_default_themes()
                
        except Exception as e:
            log_exception(logger, e, "carga de temas")
            self._create_default_themes()
    
    def _create_default_themes(self):
        """Crea temas por defecto en memoria si no se pueden cargar desde archivos"""
        logger.info("Creando temas por defecto en memoria...")
        
        self.available_themes = {
            'dark': {
                'name': 'dark',
                'description': 'Tema oscuro por defecto',
                'colors': {
                    'background': '#0D0F22',
                    'surface': '#1B2233',
                    'text': {'primary': '#E2E8F0'},
                    'primary': '#38BDF8'
                },
                'pyqt5': {'stylesheet': 'QWidget { background-color: #0D0F22; color: #E2E8F0; }'}
            }
        }
        
        logger.info("✅ Tema por defecto creado: dark")
    
    def _load_config(self):
        """Carga la configuración del usuario desde config.json"""
        try:
            logger.debug("Cargando configuración de usuario...")
            
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme_name = config.get('theme', 'dark')
                    logger.info(f"✅ Configuración cargada: tema '{self.current_theme_name}'")
            else:
                logger.info(f"ℹ️  Archivo de configuración no encontrado, usando tema por defecto")
                self.current_theme_name = 'dark'
                
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            self.current_theme_name = 'dark'
        
        # Establecer tema actual
        if self.current_theme_name in self.available_themes:
            self.current_theme_data = self.available_themes[self.current_theme_name]
            logger.debug(f"Tema actual establecido: {self.current_theme_name}")
        else:
            logger.warning(f"⚠️  Tema '{self.current_theme_name}' no encontrado, usando primer tema disponible")
            self.current_theme_name = list(self.available_themes.keys())[0]
            self.current_theme_data = self.available_themes[self.current_theme_name]
    
    def _save_config(self):
        """Guarda la configuración del usuario en config.json"""
        try:
            logger.debug(f"Guardando configuración: tema '{self.current_theme_name}'")
            
            # Leer configuración existente
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Actualizar tema y timestamp
            config['theme'] = self.current_theme_name
            config['last_modified'] = datetime.now().isoformat()
            
            # Guardar
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuración guardada: tema '{self.current_theme_name}'")
            
        except Exception as e:
            log_exception(logger, e, "guardado de configuración")
    
    def get_current_theme(self) -> str:
        """Retorna el nombre del tema actual"""
        return self.current_theme_name
    
    def get_available_themes(self) -> list:
        """Retorna lista de nombres de temas disponibles"""
        return list(self.available_themes.keys())
    
    def get_theme_data(self, theme_name: str = None) -> dict:
        """
        Retorna los datos completos del tema especificado o del actual
        
        Args:
            theme_name: Nombre del tema (opcional, usa actual por defecto)
            
        Returns:
            Diccionario con datos del tema
        """
        if theme_name is None:
            return self.current_theme_data
        return self.available_themes.get(theme_name, self.current_theme_data)
    
    def get_color(self, color_path: str, theme_name: str = None) -> str:
        """
        Obtiene un color específico usando notación de punto
        
        Args:
            color_path: Ruta al color (ej: 'text.primary', 'primary', 'success')
            theme_name: Nombre del tema (opcional)
            
        Returns:
            String con código de color hexadecimal
            
        Examples:
            >>> get_color('primary') → '#38BDF8'
            >>> get_color('text.primary') → '#E2E8F0'
            >>> get_color('components.button.hover') → '#0EA5E9'
        """
        theme_data = self.get_theme_data(theme_name)
        
        try:
            # Separar la ruta por puntos
            keys = color_path.split('.')
            value = theme_data
            
            # Navegar por la estructura
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key, value)
                else:
                    break
            
            # Si no se encontró, intentar en 'colors'
            if not isinstance(value, str) or not value.startswith('#'):
                value = theme_data.get('colors', {})
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key, value)
                    else:
                        break
            
            if isinstance(value, str) and value.startswith('#'):
                return value
            else:
                logger.warning(f"⚠️  Color '{color_path}' no encontrado, usando negro por defecto")
                return '#000000'
        
        except Exception as e:
            logger.warning(f"⚠️  Error obteniendo color '{color_path}': {e}")
            return '#000000'
    
    def set_theme(self, theme_name: str):
        """
        Cambia el tema actual
        
        Args:
            theme_name: Nombre del tema a activar
        """
        if theme_name in self.available_themes:
            logger.info(f"Cambiando tema a: {theme_name}")
            
            self.current_theme_name = theme_name
            self.current_theme_data = self.available_themes[theme_name]
            self._save_config()
            self.theme_changed.emit(theme_name)
            
            logger.info(f"✅ Tema cambiado exitosamente: {theme_name}")
        else:
            logger.error(f"❌ Tema '{theme_name}' no encontrado")
    
    def get_stylesheet(self) -> str:
        """
        Retorna el stylesheet QSS completo del tema actual
        
        Returns:
            String con código QSS
        """
        try:
            stylesheet = self.current_theme_data.get('pyqt5', {}).get('stylesheet', '')
            logger.debug(f"Stylesheet obtenido ({len(stylesheet)} caracteres)")
            return stylesheet
        except Exception as e:
            logger.error(f"❌ Error obteniendo stylesheet: {e}")
            return ''
    
    def get_palette(self) -> QPalette:
        """
        Genera una paleta de colores Qt nativa para el tema actual
        
        Returns:
            QPalette configurada con los colores del tema
        """
        palette = QPalette()
        
        try:
            # Obtener colores del tema
            bg = self.get_color('background')
            surface = self.get_color('surface')
            text_primary = self.get_color('text.primary')
            primary = self.get_color('primary')
            
            # Determinar si es tema oscuro
            is_dark = self.current_theme_name == 'dark'
            button_text = '#FFFFFF' if is_dark else '#FFFFFF'
            
            # Configurar paleta
            palette.setColor(QPalette.Window, QColor(bg))
            palette.setColor(QPalette.WindowText, QColor(text_primary))
            palette.setColor(QPalette.Base, QColor(surface))
            palette.setColor(QPalette.AlternateBase, QColor(self.get_color('surface_lighter')))
            palette.setColor(QPalette.Text, QColor(text_primary))
            palette.setColor(QPalette.Button, QColor(primary))
            palette.setColor(QPalette.ButtonText, QColor(button_text))
            palette.setColor(QPalette.Highlight, QColor(primary))
            palette.setColor(QPalette.HighlightedText, QColor(button_text))
            
            logger.debug("Paleta de colores generada correctamente")
            
        except Exception as e:
            logger.warning(f"⚠️  Error generando paleta: {e}")
        
        return palette
    
    def reload_themes(self):
        """Recarga todos los temas desde disco"""
        logger.info("🔄 Recargando temas desde disco...")
        
        self.available_themes.clear()
        self._load_themes()
        
        # Re-establecer tema actual
        if self.current_theme_name in self.available_themes:
            self.current_theme_data = self.available_themes[self.current_theme_name]
            self.theme_changed.emit(self.current_theme_name)
            logger.info(f"✅ Tema actual re-establecido: {self.current_theme_name}")
        else:
            # Si el tema actual ya no existe, usar el primero disponible
            logger.warning(f"⚠️  Tema actual '{self.current_theme_name}' ya no existe")
            self.current_theme_name = list(self.available_themes.keys())[0]
            self.current_theme_data = self.available_themes[self.current_theme_name]
            self._save_config()
            self.theme_changed.emit(self.current_theme_name)
            logger.info(f"Tema cambiado automáticamente a: {self.current_theme_name}")