"""
Logger Config - Configuracion centralizada del sistema de logging
Sistema simplificado: app.log + errors.log + consola
"""
import logging
import logging.handlers
import platform
from pathlib import Path


# ============================================================================
# CONFIGURACION DE RUTAS
# ============================================================================

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Detectar si estamos en Windows
IS_WINDOWS = platform.system() == 'Windows'


# ============================================================================
# CONFIGURACION DE ROTACION
# ============================================================================

APP_LOG_MAX_SIZE = 10 * 1024 * 1024    # 10 MB
ERROR_LOG_MAX_SIZE = 5 * 1024 * 1024   # 5 MB
APP_LOG_BACKUP_COUNT = 5
ERROR_LOG_BACKUP_COUNT = 3


# ============================================================================
# FORMATOS DE LOG
# ============================================================================

DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(message)s"
DETAILED_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
SIMPLE_FORMAT = "%(levelname)-8s | %(name)-25s | %(message)s"
ERROR_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(funcName)-20s | %(pathname)s:%(lineno)d | %(message)s"


# ============================================================================
# HANDLER SEGURO PARA WINDOWS
# ============================================================================

class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    RotatingFileHandler que maneja errores de Windows gracefully.
    Si falla la rotacion, continua escribiendo sin rotar.
    """

    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            try:
                import time
                self.stream.close()
                self.stream = self._open()
            except Exception:
                pass
        except Exception:
            pass


def create_safe_handler(filename, max_bytes, backup_count, level, formatter):
    """
    Crea un handler seguro para Windows que no falla en rotaciones.
    """
    if IS_WINDOWS:
        handler = SafeRotatingFileHandler(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
            delay=True
        )
    else:
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
# HANDLERS
# ============================================================================

def get_app_handler():
    """Handler para app.log - Log general (INFO+)"""
    formatter = logging.Formatter(DETAILED_FORMAT, DETAILED_DATE_FORMAT)
    return create_safe_handler(
        filename=LOGS_DIR / "app.log",
        max_bytes=APP_LOG_MAX_SIZE,
        backup_count=APP_LOG_BACKUP_COUNT,
        level=logging.INFO,
        formatter=formatter
    )


def get_error_handler():
    """Handler para errors.log - Solo errores (ERROR+), incluye pathname:lineno"""
    formatter = logging.Formatter(ERROR_FORMAT, DETAILED_DATE_FORMAT)
    return create_safe_handler(
        filename=LOGS_DIR / "errors.log",
        max_bytes=ERROR_LOG_MAX_SIZE,
        backup_count=ERROR_LOG_BACKUP_COUNT,
        level=logging.ERROR,
        formatter=formatter
    )


def get_console_handler():
    """Handler para consola - Solo warnings y errores (WARNING+)"""
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter(SIMPLE_FORMAT)
    handler.setFormatter(formatter)
    return handler


# ============================================================================
# CONFIGURACION PRINCIPAL
# ============================================================================

def setup_logging():
    """
    Configura el sistema de logging completo.
    Debe llamarse UNA VEZ al inicio de la aplicacion (en main.py).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    root_logger.addHandler(get_app_handler())
    root_logger.addHandler(get_error_handler())
    root_logger.addHandler(get_console_handler())

    logger = logging.getLogger('main')
    logger.info("=" * 80)
    logger.info("Sistema de logging inicializado correctamente")
    logger.info(f"Directorio de logs: {LOGS_DIR.absolute()}")
    if IS_WINDOWS:
        logger.info("Sistema: Windows - Usando SafeRotatingFileHandler")
    logger.info("=" * 80)


def configure_logger(logger_name: str) -> logging.Logger:
    """
    Retorna un logger configurado. Todo el output va a traves de los handlers
    del root logger (app.log, errors.log, consola).
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    return logger
