"""
Logger Config - Configuración centralizada del sistema de logging
Sistema híbrido con 3 niveles: app.log + errors.log + detailed/
"""
import os
from pathlib import Path
import logging
import logging.handlers


# ============================================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================================

# Directorio base de logs
LOGS_DIR = Path("logs")
DETAILED_LOGS_DIR = LOGS_DIR / "detailed"
ARCHIVE_LOGS_DIR = LOGS_DIR / "archive"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)
DETAILED_LOGS_DIR.mkdir(exist_ok=True)
ARCHIVE_LOGS_DIR.mkdir(exist_ok=True)


# ============================================================================
# CONFIGURACIÓN DE ROTACIÓN
# ============================================================================

# Tamaños máximos de archivos de log (en bytes)
APP_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
ERROR_LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
DETAILED_LOG_MAX_SIZE = 5 * 1024 * 1024  # 5 MB

# Cantidad de backups a mantener
APP_LOG_BACKUP_COUNT = 5
ERROR_LOG_BACKUP_COUNT = 3
DETAILED_LOG_BACKUP_COUNT = 3


# ============================================================================
# FORMATOS DE LOG
# ============================================================================

# Formato detallado (para archivos)
DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s"
DETAILED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Formato simple (para consola)
SIMPLE_FORMAT = "%(levelname)-8s | %(name)-25s | %(message)s"

# Formato para errores (incluye más info)
ERROR_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(pathname)s:%(lineno)d | %(message)s"


# ============================================================================
# NIVELES DE LOG POR MÓDULO
# ============================================================================

LOG_LEVELS = {
    # UI - Solo eventos importantes
    'ui': logging.INFO,
    'ui.main_window': logging.INFO,
    'ui.tabs': logging.INFO,
    'ui.widgets': logging.INFO,
    
    # Workers - Detalle completo para debugging
    'workers': logging.DEBUG,
    'workers.core_pipeline': logging.DEBUG,
    'workers.sunat': logging.DEBUG,
    'workers.tools': logging.DEBUG,
    
    # Core Pipeline - Información de procesos
    'core': logging.INFO,
    'core.pipeline': logging.INFO,
    'core.sunat': logging.INFO,
    'core.tools': logging.INFO,
    
    # Extractores - Info + warnings
    'extractors': logging.INFO,
    
    # Utils - Solo warnings y errores
    'utils': logging.WARNING,
    'utils.theme_manager': logging.INFO,  # Excepción: tema es importante
    'utils.excel_converter': logging.WARNING,
    
    # Main - Todo
    'main': logging.INFO,
    
    # Root (fallback)
    'root': logging.INFO,
}


# ============================================================================
# CONFIGURACIÓN DE HANDLERS
# ============================================================================

def get_app_handler():
    """
    Handler para app.log - Log general de la aplicación
    Nivel: INFO+
    Rotación: 10MB, 5 backups
    """
    handler = logging.handlers.RotatingFileHandler(
        filename=LOGS_DIR / "app.log",
        maxBytes=APP_LOG_MAX_SIZE,
        backupCount=APP_LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(DETAILED_FORMAT, DETAILED_DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def get_error_handler():
    """
    Handler para errors.log - Solo errores críticos
    Nivel: ERROR+
    Rotación: 5MB, 3 backups
    """
    handler = logging.handlers.RotatingFileHandler(
        filename=LOGS_DIR / "errors.log",
        maxBytes=ERROR_LOG_MAX_SIZE,
        backupCount=ERROR_LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(ERROR_FORMAT, DETAILED_DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def get_console_handler():
    """
    Handler para consola - Solo warnings y errores
    Nivel: WARNING+
    """
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter(SIMPLE_FORMAT)
    handler.setFormatter(formatter)
    return handler


def get_detailed_handler(module_category: str):
    """
    Handler para logs detallados por categoría de módulo
    
    Args:
        module_category: Categoría del módulo (ui, workers, core, etc)
        
    Returns:
        RotatingFileHandler configurado
    """
    filename = DETAILED_LOGS_DIR / f"{module_category}.log"
    
    handler = logging.handlers.RotatingFileHandler(
        filename=filename,
        maxBytes=DETAILED_LOG_MAX_SIZE,
        backupCount=DETAILED_LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(DETAILED_FORMAT, DETAILED_DATE_FORMAT)
    handler.setFormatter(formatter)
    return handler


# ============================================================================
# MAPEO DE MÓDULOS A CATEGORÍAS
# ============================================================================

MODULE_CATEGORY_MAP = {
    'ui': 'ui',
    'ui.main_window': 'ui',
    'ui.tabs': 'ui',
    'ui.widgets': 'ui',
    'ui.splash_screen': 'ui',
    
    'workers': 'workers',
    'workers.core_pipeline': 'workers',
    'workers.core_pipeline_step1': 'workers',
    'workers.core_pipeline_step2': 'workers',
    'workers.core_pipeline_step3': 'workers',
    'workers.core_pipeline_step4': 'workers',
    'workers.core_pipeline_step5': 'workers',
    'workers.sunat_diagnostic': 'workers',
    'workers.sunat_duplicates': 'workers',
    'workers.sunat_rename': 'workers',
    'workers.pdf_splitter': 'workers',
    
    'core': 'core_pipeline',
    'core.pipeline': 'core_pipeline',
    'core.sunat': 'core_sunat',
    'core.tools': 'core_tools',
    
    'extractors': 'extractors',
    'extractors.afp': 'extractors',
    'extractors.boleta': 'extractors',
    'extractors.quinta': 'extractors',
    'extractors.sunat': 'extractors',
    
    'utils': 'utils',
    'utils.theme_manager': 'utils',
    'utils.excel_converter': 'utils',
    
    'main': 'main',
}


def get_module_category(logger_name: str) -> str:
    """
    Obtiene la categoría de un módulo para logging detallado
    
    Args:
        logger_name: Nombre del logger (ej: 'workers.core_pipeline_step1')
        
    Returns:
        Categoría del módulo (ej: 'workers')
    """
    # Buscar coincidencia exacta
    if logger_name in MODULE_CATEGORY_MAP:
        return MODULE_CATEGORY_MAP[logger_name]
    
    # Buscar por prefijo (ej: 'workers.algo' -> 'workers')
    for prefix, category in MODULE_CATEGORY_MAP.items():
        if logger_name.startswith(prefix + '.'):
            return category
    
    # Fallback: usar la primera parte del nombre
    parts = logger_name.split('.')
    if len(parts) > 0:
        return parts[0]
    
    return 'general'


# ============================================================================
# FUNCIÓN DE CONFIGURACIÓN PRINCIPAL
# ============================================================================

def setup_logging():
    """
    Configura el sistema de logging completo
    Debe llamarse UNA VEZ al inicio de la aplicación
    """
    # Obtener el root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturar todo, los handlers filtran
    
    # Limpiar handlers existentes (evitar duplicados)
    root_logger.handlers.clear()
    
    # Agregar handlers principales
    root_logger.addHandler(get_app_handler())
    root_logger.addHandler(get_error_handler())
    root_logger.addHandler(get_console_handler())
    
    # Log inicial
    logger = logging.getLogger('main')
    logger.info("="*80)
    logger.info("Sistema de logging inicializado correctamente")
    logger.info(f"Directorio de logs: {LOGS_DIR.absolute()}")
    logger.info("="*80)


def configure_logger(logger_name: str) -> logging.Logger:
    """
    Configura un logger específico con su nivel y handlers detallados
    
    Args:
        logger_name: Nombre del logger (ej: 'workers.core_pipeline_step1')
        
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(logger_name)
    
    # Establecer nivel según configuración
    level = LOG_LEVELS.get(logger_name, logging.INFO)
    
    # Buscar por prefijo si no hay coincidencia exacta
    if logger_name not in LOG_LEVELS:
        for prefix, prefix_level in LOG_LEVELS.items():
            if logger_name.startswith(prefix + '.'):
                level = prefix_level
                break
    
    logger.setLevel(level)
    
    # Agregar handler detallado para esta categoría
    category = get_module_category(logger_name)
    detailed_handler = get_detailed_handler(category)
    
    # Evitar duplicados
    if not any(isinstance(h, logging.handlers.RotatingFileHandler) and 
               str(DETAILED_LOGS_DIR) in str(getattr(h, 'baseFilename', ''))
               for h in logger.handlers):
        logger.addHandler(detailed_handler)
    
    # No propagar al root para evitar duplicados en app.log
    # (el root ya tiene sus propios handlers)
    logger.propagate = True
    
    return logger


# ============================================================================
# UTILIDADES DE LOGGING
# ============================================================================

def log_separator(logger, char="=", length=80):
    """
    Agrega un separador visual al log
    
    Args:
        logger: Logger a usar
        char: Caracter para el separador
        length: Longitud del separador
    """
    logger.info(char * length)


def log_section(logger, title: str):
    """
    Agrega una sección con título al log
    
    Args:
        logger: Logger a usar
        title: Título de la sección
    """
    logger.info("="*80)
    logger.info(f" {title} ".center(80, "="))
    logger.info("="*80)


def log_dict(logger, data: dict, title: str = None):
    """
    Loguea un diccionario de forma legible
    
    Args:
        logger: Logger a usar
        data: Diccionario a loguear
        title: Título opcional
    """
    if title:
        logger.info(f"--- {title} ---")
    
    for key, value in data.items():
        logger.info(f"  {key}: {value}")