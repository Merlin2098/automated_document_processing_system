"""
Logger - Utilidad wrapper para simplificar el uso del sistema de logging.

Formato estandar para mensajes de error:
    logger.error("component=X step=Y file=Z | Descripcion del error", exc_info=True)

El ERROR_FORMAT en logger_config.py agrega automaticamente:
    timestamp | LEVEL | logger_name | function_name | filepath:lineno | message
"""
import logging
import sys
from typing import Optional

from utils.logger_config import configure_logger, setup_logging


# ============================================================================
# CLASE LOGGER (WRAPPER ORIENTADO A OBJETOS)
# ============================================================================

class Logger:
    """
    Wrapper orientado a objetos sobre el sistema de logging de Python.

    Examples:
        >>> logger = Logger("CorePipelineStep1")
        >>> logger.info("Proceso iniciado")
        >>> logger.error("Error procesando archivo")
    """

    def __init__(self, module_name: str):
        self.module_name = module_name
        self._logger = get_logger(module_name)

    def debug(self, message: str):
        self._logger.debug(message)

    def info(self, message: str):
        self._logger.info(message)

    def warning(self, message: str):
        self._logger.warning(message)

    def error(self, message: str):
        self._logger.error(message)

    def critical(self, message: str):
        self._logger.critical(message)

    def exception(self, message: str, exc_info=True):
        """Loguea una excepcion con traceback completo."""
        self._logger.error(message, exc_info=exc_info)


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def get_logger(module_name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el modulo especificado.

    Args:
        module_name: Nombre del modulo (ej: 'main', 'CorePipelineStep1')

    Returns:
        Logger configurado
    """
    if module_name is None:
        module_name = _auto_detect_module()

    return configure_logger(module_name)


def _auto_detect_module() -> str:
    """Detecta automaticamente el nombre del modulo llamante."""
    try:
        frame = sys._getframe(2)
        module = frame.f_globals.get('__name__', 'unknown')
        return module
    except Exception:
        return 'unknown'


# ============================================================================
# FUNCIONES DE LOGGING
# ============================================================================

def log_exception(logger, exception: Exception, context: str = None):
    """
    Loguea una excepcion con contexto completo a nivel ERROR.

    Args:
        logger: Logger a usar
        exception: Excepcion a loguear
        context: Contexto adicional (donde ocurrio)

    Example:
        >>> try:
        ...     # codigo que puede fallar
        ... except Exception as e:
        ...     log_exception(logger, e, "procesando archivo datos.xlsx")
    """
    error_msg = f"EXCEPTION [{type(exception).__name__}]: {str(exception)}"

    if context:
        error_msg = f"{error_msg} | Context: {context}"

    logger.error(error_msg, exc_info=True)


# ============================================================================
# UTILIDADES DE FORMATO
# ============================================================================

def format_time_elapsed(seconds: float) -> str:
    """
    Formatea tiempo transcurrido en formato legible.

    Returns:
        String formateado (ej: "01:23:45" o "45.2s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """
    Formatea tamano de archivo en formato legible.

    Returns:
        String formateado (ej: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0

    return f"{bytes_size:.2f} PB"


# ============================================================================
# INICIALIZACION DEL SISTEMA
# ============================================================================

def initialize_logging_system():
    """
    Inicializa el sistema de logging completo.
    Debe llamarse UNA VEZ al inicio de la aplicacion (en main.py).
    """
    setup_logging()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Logger',
    'get_logger',
    'initialize_logging_system',
    'log_exception',
    'format_time_elapsed',
    'format_file_size',
]
