"""
Logger - Utilidad wrapper para simplificar el uso del sistema de logging
Proporciona funciones convenientes para obtener y usar loggers
"""
import logging
import traceback
import sys
from typing import Optional
from pathlib import Path

from utils.logger_config import configure_logger, setup_logging


# ============================================================================
# CLASE LOGGER (WRAPPER ORIENTADO A OBJETOS)
# ============================================================================

class Logger:
    """
    Clase wrapper para logging que proporciona una interfaz orientada a objetos
    simplificada sobre el sistema de logging de Python.
    
    Esta clase es una alternativa conveniente a get_logger() para usar en workers
    y otros módulos que prefieren un enfoque orientado a objetos.
    
    Examples:
        >>> logger = Logger("CorePipelineStep1")
        >>> logger.info("Proceso iniciado")
        >>> logger.error("Error procesando archivo")
        >>> logger.warning("Archivo no encontrado")
    """
    
    def __init__(self, module_name: str):
        """
        Inicializa el logger para un módulo específico
        
        Args:
            module_name: Nombre del módulo (ej: "CorePipelineStep1", "SunatDiagnostic")
        """
        self.module_name = module_name
        self._logger = get_logger(f"workers.{module_name}")
    
    def debug(self, message: str):
        """Loguea mensaje de nivel DEBUG"""
        self._logger.debug(message)
    
    def info(self, message: str):
        """Loguea mensaje de nivel INFO"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """Loguea mensaje de nivel WARNING"""
        self._logger.warning(message)
    
    def error(self, message: str):
        """Loguea mensaje de nivel ERROR"""
        self._logger.error(message)
    
    def critical(self, message: str):
        """Loguea mensaje de nivel CRITICAL"""
        self._logger.critical(message)
    
    def exception(self, message: str, exc_info=True):
        """
        Loguea una excepción con traceback completo
        
        Args:
            message: Mensaje descriptivo del error
            exc_info: Si True, incluye información de la excepción actual
        """
        self._logger.error(message, exc_info=exc_info)
    
    def log_start(self, process_name: str, **kwargs):
        """
        Loguea el inicio de un proceso con formato estándar
        
        Args:
            process_name: Nombre del proceso
            **kwargs: Parámetros adicionales a loguear
        """
        log_start(self._logger, process_name, **kwargs)
    
    def log_end(self, process_name: str, success: bool = True, **stats):
        """
        Loguea el fin de un proceso con estadísticas
        
        Args:
            process_name: Nombre del proceso
            success: Si el proceso terminó exitosamente
            **stats: Estadísticas del proceso
        """
        log_end(self._logger, process_name, success, **stats)
    
    def log_progress(self, current: int, total: int, item_name: str = "archivos"):
        """
        Loguea progreso de procesamiento
        
        Args:
            current: Cantidad actual procesada
            total: Cantidad total
            item_name: Nombre de los items (plural)
        """
        log_progress(self._logger, current, total, item_name)


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def get_logger(module_name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado
    
    Args:
        module_name: Nombre del módulo (ej: 'workers.core_pipeline_step1')
                    Si es None, intenta detectar automáticamente
    
    Returns:
        Logger configurado con handlers y niveles apropiados
    
    Examples:
        >>> logger = get_logger('workers.core_pipeline_step1')
        >>> logger.info("Proceso iniciado")
        >>> logger.error("Error procesando archivo", exc_info=True)
    """
    if module_name is None:
        module_name = _auto_detect_module()
    
    return configure_logger(module_name)


def _auto_detect_module() -> str:
    """
    Intenta detectar automáticamente el nombre del módulo llamante
    
    Returns:
        Nombre del módulo detectado o 'unknown' si falla
    """
    try:
        # Obtener el frame del llamante (2 niveles arriba)
        frame = sys._getframe(2)
        module = frame.f_globals.get('__name__', 'unknown')
        return module
    except:
        return 'unknown'


# ============================================================================
# FUNCIONES DE LOGGING CONVENIENTES
# ============================================================================

def log_start(logger, process_name: str, **kwargs):
    """
    Loguea el inicio de un proceso con formato estándar
    
    Args:
        logger: Logger a usar
        process_name: Nombre del proceso
        **kwargs: Parámetros adicionales a loguear
    
    Example:
        >>> logger = get_logger('workers.step1')
        >>> log_start(logger, "Generación de Excel", carpeta="C:/data", total_files=100)
    """
    logger.info("="*60)
    logger.info(f"▶️  INICIANDO: {process_name}")
    
    if kwargs:
        logger.info("Parámetros:")
        for key, value in kwargs.items():
            logger.info(f"  • {key}: {value}")
    
    logger.info("-"*60)


def log_end(logger, process_name: str, success: bool = True, **stats):
    """
    Loguea el fin de un proceso con estadísticas
    
    Args:
        logger: Logger a usar
        process_name: Nombre del proceso
        success: Si el proceso terminó exitosamente
        **stats: Estadísticas del proceso
    
    Example:
        >>> log_end(logger, "Generación de Excel", success=True, 
        ...         procesados=100, errores=2, tiempo="00:05:32")
    """
    logger.info("-"*60)
    
    if success:
        logger.info(f"✅ COMPLETADO: {process_name}")
    else:
        logger.warning(f"⚠️  COMPLETADO CON ERRORES: {process_name}")
    
    if stats:
        logger.info("Estadísticas:")
        for key, value in stats.items():
            logger.info(f"  • {key}: {value}")
    
    logger.info("="*60)


def log_progress(logger, current: int, total: int, item_name: str = "archivos"):
    """
    Loguea progreso de procesamiento
    
    Args:
        logger: Logger a usar
        current: Cantidad actual procesada
        total: Cantidad total
        item_name: Nombre de los items (plural)
    
    Example:
        >>> log_progress(logger, 45, 100, "archivos")
        # 📊 Progreso: 45/100 archivos (45%)
    """
    percentage = (current / total * 100) if total > 0 else 0
    logger.info(f"📊 Progreso: {current}/{total} {item_name} ({percentage:.1f}%)")


def log_file_operation(logger, operation: str, filepath: str, success: bool = True):
    """
    Loguea operaciones con archivos
    
    Args:
        logger: Logger a usar
        operation: Tipo de operación (crear, copiar, mover, eliminar, etc)
        filepath: Ruta del archivo
        success: Si la operación fue exitosa
    
    Example:
        >>> log_file_operation(logger, "crear", "output/result.xlsx", success=True)
    """
    filename = Path(filepath).name
    
    if success:
        logger.debug(f"📁 {operation.capitalize()}: {filename}")
    else:
        logger.error(f"❌ Error al {operation}: {filename}")


def log_exception(logger, exception: Exception, context: str = None):
    """
    Loguea una excepción con contexto completo
    
    Args:
        logger: Logger a usar
        exception: Excepción a loguear
        context: Contexto adicional (dónde ocurrió)
    
    Example:
        >>> try:
        ...     # código que puede fallar
        ... except Exception as e:
        ...     log_exception(logger, e, "procesando archivo datos.xlsx")
    """
    error_msg = f"❌ EXCEPCIÓN: {type(exception).__name__}: {str(exception)}"
    
    if context:
        error_msg = f"{error_msg} | Contexto: {context}"
    
    logger.error(error_msg)
    logger.debug("Traceback completo:", exc_info=True)


def log_warning_with_count(logger, message: str, count: int):
    """
    Loguea un warning con contador
    
    Args:
        logger: Logger a usar
        message: Mensaje base
        count: Cantidad de ocurrencias
    
    Example:
        >>> log_warning_with_count(logger, "Archivos sin procesar", 5)
    """
    logger.warning(f"⚠️  {message}: {count}")


# ============================================================================
# DECORADORES DE LOGGING
# ============================================================================

def log_function_call(logger=None):
    """
    Decorador para loguear entrada y salida de funciones
    
    Args:
        logger: Logger a usar (si es None, se crea uno automático)
    
    Example:
        >>> @log_function_call()
        ... def procesar_archivo(filename):
        ...     return True
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtener logger
            nonlocal logger
            if logger is None:
                module_name = func.__module__
                logger = get_logger(module_name)
            
            # Log de entrada
            func_name = func.__name__
            logger.debug(f"→ Entrando a {func_name}()")
            
            try:
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Log de salida exitosa
                logger.debug(f"← Saliendo de {func_name}() [OK]")
                return result
                
            except Exception as e:
                # Log de error
                logger.error(f"← Saliendo de {func_name}() [ERROR]: {e}")
                raise
        
        return wrapper
    return decorator


def log_errors_only(logger=None):
    """
    Decorador para loguear solo errores (sin entrada/salida)
    
    Args:
        logger: Logger a usar (si es None, se crea uno automático)
    
    Example:
        >>> @log_errors_only()
        ... def operacion_critica():
        ...     # código que puede fallar
        ...     pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtener logger
            nonlocal logger
            if logger is None:
                module_name = func.__module__
                logger = get_logger(module_name)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_name = func.__name__
                log_exception(logger, e, f"función {func_name}()")
                raise
        
        return wrapper
    return decorator


# ============================================================================
# UTILIDADES DE FORMATO
# ============================================================================

def format_time_elapsed(seconds: float) -> str:
    """
    Formatea tiempo transcurrido en formato legible
    
    Args:
        seconds: Segundos transcurridos
    
    Returns:
        String formateado (ej: "01:23:45" o "45.2s")
    
    Example:
        >>> format_time_elapsed(125.5)
        '02:05'
        >>> format_time_elapsed(3.2)
        '3.2s'
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
    Formatea tamaño de archivo en formato legible
    
    Args:
        bytes_size: Tamaño en bytes
    
    Returns:
        String formateado (ej: "1.5 MB")
    
    Example:
        >>> format_file_size(1536000)
        '1.46 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    
    return f"{bytes_size:.2f} PB"


# ============================================================================
# INICIALIZACIÓN DEL SISTEMA
# ============================================================================

def initialize_logging_system():
    """
    Inicializa el sistema de logging completo
    Debe llamarse UNA VEZ al inicio de la aplicación (en main.py)
    
    Example:
        >>> # En main.py
        >>> from utils.logger import initialize_logging_system
        >>> initialize_logging_system()
    """
    setup_logging()


# ============================================================================
# EXPORTS CONVENIENTES
# ============================================================================

__all__ = [
    # Clase wrapper
    'Logger',
    
    # Principal
    'get_logger',
    'initialize_logging_system',
    
    # Funciones de logging
    'log_start',
    'log_end',
    'log_progress',
    'log_file_operation',
    'log_exception',
    'log_warning_with_count',
    
    # Decoradores
    'log_function_call',
    'log_errors_only',
    
    # Utilidades
    'format_time_elapsed',
    'format_file_size',
]