"""
Theme Manager - Gestión de temas visuales (Refactorizado)
Carga temas desde archivos JSON en resources/themes/
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import QObject, Signal


class ThemeManager(QObject):
    """Gestor de temas de la aplicación"""
    
    theme_changed = Signal(str)  # Señal emitida cuando cambia el tema
    
    def __init__(self):
        super().__init__()
        
        # Rutas de recursos
        self.themes_dir = self._get_resource_path("resources/themes")
        self.config_file = self._get_resource_path("resources/config.json")
        
        # Estado
        self.available_themes = {}
        self.current_theme_name = "dark"
        self.current_theme_data = {}
        
        # Inicialización
        self._load_themes()
        self._load_config()
    
    def _get_resource_path(self, relative_path: str) -> Path:
        """
        Obtiene la ruta correcta para desarrollo y PyInstaller
        
        Args:
            relative_path: Ruta relativa desde la raíz del proyecto
            
        Returns:
            Path absoluto al recurso
        """
        if getattr(sys, 'frozen', False):
            # Ejecutable empaquetado con PyInstaller
            base_path = Path(sys._MEIPASS)
        else:
            # Modo desarrollo
            base_path = Path(__file__).parent.parent
        
        return base_path / relative_path
    
    def _load_themes(self):
        """Carga todos los temas disponibles desde resources/themes/"""
        try:
            if not self.themes_dir.exists():
                print(f"⚠️ Directorio de temas no encontrado: {self.themes_dir}")
                self._create_default_themes()
                return
            
            # Cargar todos los archivos theme_*.json
            theme_files = list(self.themes_dir.glob("theme_*.json"))
            
            if not theme_files:
                print("⚠️ No se encontraron archivos de tema")
                self._create_default_themes()
                return
            
            for theme_file in theme_files:
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_name = theme_data['name']
                        self.available_themes[theme_name] = theme_data
                        print(f"✅ Tema cargado: {theme_name} ({theme_data['description']})")
                except Exception as e:
                    print(f"❌ Error cargando tema {theme_file.name}: {e}")
            
            # Verificar que se cargó al menos un tema
            if not self.available_themes:
                print("⚠️ No se pudo cargar ningún tema, usando valores por defecto")
                self._create_default_themes()
                
        except Exception as e:
            print(f"❌ Error al cargar temas: {e}")
            self._create_default_themes()
    
    def _create_default_themes(self):
        """Crea temas por defecto en memoria si no se pueden cargar desde archivos"""
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
    
    def _load_config(self):
        """Carga la configuración del usuario desde config.json"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_theme_name = config.get('theme', 'dark')
                    print(f"✅ Configuración cargada: tema '{self.current_theme_name}'")
            else:
                print(f"ℹ️ Archivo de configuración no encontrado, usando tema por defecto")
                self.current_theme_name = 'dark'
        except Exception as e:
            print(f"❌ Error cargando configuración: {e}")
            self.current_theme_name = 'dark'
        
        # Establecer tema actual
        if self.current_theme_name in self.available_themes:
            self.current_theme_data = self.available_themes[self.current_theme_name]
        else:
            print(f"⚠️ Tema '{self.current_theme_name}' no encontrado, usando primer tema disponible")
            self.current_theme_name = list(self.available_themes.keys())[0]
            self.current_theme_data = self.available_themes[self.current_theme_name]
    
    def _save_config(self):
        """Guarda la configuración del usuario en config.json"""
        try:
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
            
            print(f"✅ Configuración guardada: tema '{self.current_theme_name}'")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
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
            
            return value if isinstance(value, str) and value.startswith('#') else '#000000'
        
        except Exception as e:
            print(f"⚠️ Error obteniendo color '{color_path}': {e}")
            return '#000000'
    
    def set_theme(self, theme_name: str):
        """
        Cambia el tema actual
        
        Args:
            theme_name: Nombre del tema a activar
        """
        if theme_name in self.available_themes:
            self.current_theme_name = theme_name
            self.current_theme_data = self.available_themes[theme_name]
            self._save_config()
            self.theme_changed.emit(theme_name)
            print(f"✅ Tema cambiado a: {theme_name}")
        else:
            print(f"❌ Tema '{theme_name}' no encontrado")
    
    def get_stylesheet(self) -> str:
        """
        Retorna el stylesheet QSS completo del tema actual
        
        Returns:
            String con código QSS
        """
        try:
            return self.current_theme_data.get('pyqt5', {}).get('stylesheet', '')
        except Exception as e:
            print(f"❌ Error obteniendo stylesheet: {e}")
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
            
        except Exception as e:
            print(f"⚠️ Error generando paleta: {e}")
        
        return palette
    
    def reload_themes(self):
        """Recarga todos los temas desde disco"""
        print("🔄 Recargando temas...")
        self.available_themes.clear()
        self._load_themes()
        
        # Re-establecer tema actual
        if self.current_theme_name in self.available_themes:
            self.current_theme_data = self.available_themes[self.current_theme_name]
            self.theme_changed.emit(self.current_theme_name)
        else:
            # Si el tema actual ya no existe, usar el primero disponible
            self.current_theme_name = list(self.available_themes.keys())[0]
            self.current_theme_data = self.available_themes[self.current_theme_name]
            self._save_config()
            self.theme_changed.emit(self.current_theme_name)