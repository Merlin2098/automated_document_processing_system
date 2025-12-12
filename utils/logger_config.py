"""
Logger Config - Configuración centralizada del sistema de logging
Sistema híbrido con 3 niveles: app.log + errors.log + detailed/
VERSION 1.1: Fix para WinError 32 en Windows con múltiples workers
"""
import os
from pathlib import Path
import logging
import logging.handlers
import platform


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
DETAILED_LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB (aumentado para evitar rotaciones frecuentes)

# Cantidad de backups a mantener
APP_LOG_BACKUP_COUNT = 5
ERROR_LOG_BACKUP_COUNT = 3
DETAILED_LOG_BACKUP_COUNT = 3

# Detectar si estamos en Windows
IS_WINDOWS = platform.system() == 'Windows'


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
# HANDLER SEGURO PARA WINDOWS
# ============================================================================

class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    RotatingFileHandler mejorado que maneja errores de Windows gracefully.
    Si falla la rotación, continúa escribiendo sin rotar.
    """
    
    def doRollover(self):
        """
        Override de doRollover para manejar PermissionError en Windows
        """
        try:
            super().doRollover()
        except PermissionError as e:
            # En Windows, si el archivo está bloqueado, solo logueamos y continuamos
            # El archivo seguirá creciendo pero la app no se cae
            print(f"⚠️ No se pudo rotar log (archivo en uso): {self.baseFilename}")
            # Intentar crear un nuevo archivo con sufijo
            try:
                import time
                suffix = int(time.time())
                new_name = f"{self.baseFilename}.{suffix}"
                self.stream.close()
                self.stream = self._open()
            except:
                pass  # Si falla, seguimos con el archivo actual
        except Exception as e:
            # Cualquier otro error, lo logueamos pero no detenemos la app
            print(f"⚠️ Error al rotar log: {e}")


def create_safe_handler(filename, max_bytes, backup_count, level, formatter):
    """
    Crea un handler seguro para Windows que no falla en rotaciones.
    
    Args:
        filename: Ruta del archivo de log
        max_bytes: Tamaño máximo antes de rotar
        backup_count: Cantidad de backups
        level: Nivel de logging
        formatter: Formatter a usar
        
    Returns:
        Handler configurado
    """
    if IS_WINDOWS:
        # En Windows, usar SafeRotatingFileHandler
        handler = SafeRotatingFileHandler(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
            delay=True  # No abrir el archivo hasta que se necesite
        )
    else:
        # En Linux/Mac, usar el handler estándar
        handler = logging.handlers.RotatingFileHandler(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
    
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


# ============================================================================
# CONFIGURACIÓN DE HANDLERS
# ============================================================================

def get_app_handler():
    """
    Handler para app.log - Log general de la aplicación
    Nivel: INFO+
    Rotación: 10MB, 5 backups
    """
    formatter = logging.Formatter(DETAILED_FORMAT, DETAILED_DATE_FORMAT)
    return create_safe_handler(
        filename=LOGS_DIR / "app.log",
        max_bytes=APP_LOG_MAX_SIZE,
        backup_count=APP_LOG_BACKUP_COUNT,
        level=logging.INFO,
        formatter=formatter
    )


def get_error_handler():
    """
    Handler para errors.log - Solo errores críticos
    Nivel: ERROR+
    Rotación: 5MB, 3 backups
    """
    formatter = logging.Formatter(ERROR_FORMAT, DETAILED_DATE_FORMAT)
    return create_safe_handler(
        filename=LOGS_DIR / "errors.log",
        max_bytes=ERROR_LOG_MAX_SIZE,
        backup_count=ERROR_LOG_BACKUP_COUNT,
        level=logging.ERROR,
        formatter=formatter
    )


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


def get_detailed_handler(module_category: str, unique_suffix: str = None):
    """
    Handler para logs detallados por categoría de módulo.
    Ahora soporta sufijos únicos para evitar conflictos entre workers.
    
    Args:
        module_category: Categoría del módulo (ui, workers, core, etc)
        unique_suffix: Sufijo único opcional (ej: timestamp) para workers
        
    Returns:
        SafeRotatingFileHandler configurado
    """
    if unique_suffix:
        filename = DETAILED_LOGS_DIR / f"{module_category}_{unique_suffix}.log"
    else:
        filename = DETAILED_LOGS_DIR / f"{module_category}.log"
    
    formatter = logging.Formatter(DETAILED_FORMAT, DETAILED_DATE_FORMAT)
    return create_safe_handler(
        filename=filename,
        max_bytes=DETAILED_LOG_MAX_SIZE,
        backup_count=DETAILED_LOG_BACKUP_COUNT,
        level=logging.DEBUG,
        formatter=formatter
    )


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


def extract_unique_suffix(logger_name: str) -> str:
    """
    Extrae un sufijo único del nombre del logger para workers.
    Esto permite que cada worker tenga su propio archivo de log.
    
    Args:
        logger_name: Nombre completo del logger
        
    Returns:
        Sufijo único o None
    
    Examples:
        'workers.CorePipelineStep5Worker' -> 'CorePipelineStep5Worker'
        'workers.SunatDiagnostic' -> 'SunatDiagnostic'
    """
    # Si es un worker con nombre de clase, usar ese nombre
    if logger_name.startswith('workers.'):
        parts = logger_name.split('.')
        if len(parts) >= 2:
            # Retornar la última parte (nombre de la clase del worker)
            return parts[-1]
    
    return None


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
    if IS_WINDOWS:
        logger.info("Sistema: Windows - Usando SafeRotatingFileHandler")
    logger.info("="*80)


def configure_logger(logger_name: str) -> logging.Logger:
    """
    Configura un logger específico con su nivel y handlers detallados.
    Los workers obtienen archivos de log separados automáticamente.
    
    Args:
        logger_name: Nombre del logger (ej: 'workers.CorePipelineStep5Worker')
        
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
    
    # Obtener categoría y sufijo único (para workers)
    category = get_module_category(logger_name)
    unique_suffix = extract_unique_suffix(logger_name)
    
    # Agregar handler detallado para esta categoría
    # Si es un worker, tendrá su propio archivo (workers_NombreWorker.log)
    detailed_handler = get_detailed_handler(category, unique_suffix)
    
    # Evitar duplicados verificando el baseFilename
    handler_exists = False
    for h in logger.handlers:
        if isinstance(h, (logging.handlers.RotatingFileHandler, SafeRotatingFileHandler)):
            if hasattr(h, 'baseFilename') and h.baseFilename == str(detailed_handler.baseFilename):
                handler_exists = True
                break
    
    if not handler_exists:
        logger.addHandler(detailed_handler)
    
    # Propagar al root para que también se loguee en app.log y errors.log
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