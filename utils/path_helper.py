"""
Path Helper - Manejo centralizado de rutas para desarrollo y PyInstaller
"""
import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """
    Obtiene la ruta correcta para desarrollo y PyInstaller
    
    Args:
        relative_path: Ruta relativa desde la raíz del proyecto
        
    Returns:
        Path absoluto al recurso
        
    Examples:
        >>> get_resource_path("resources/config.json")
        Path('/path/to/resources/config.json')
        
        >>> get_resource_path("resources/themes/theme_dark.json")
        Path('/path/to/resources/themes/theme_dark.json')
    """
    if getattr(sys, 'frozen', False):
        # Ejecutable empaquetado con PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # Modo desarrollo - buscar desde la raíz del proyecto
        # Este archivo está en utils/, entonces parent es la raíz
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path