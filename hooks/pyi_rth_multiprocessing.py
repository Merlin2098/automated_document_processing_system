"""
PyInstaller Runtime Hook para Multiprocessing
Este hook se ejecuta antes del script principal cuando la aplicación está empaquetada.
Configura correctamente el contexto de multiprocessing para evitar bucles infinitos.

Ubicación sugerida: hooks/pyi_rth_multiprocessing.py
"""

import sys
import os

_DEVNULL_STREAM = None


def _ensure_standard_streams():
    """Evita que stdout/stderr nulos rompan el bootstrap de multiprocessing."""
    global _DEVNULL_STREAM

    if sys.stdout is not None and sys.stderr is not None:
        return

    if _DEVNULL_STREAM is None:
        _DEVNULL_STREAM = open(os.devnull, "w", encoding="utf-8")

    if sys.stdout is None:
        sys.stdout = _DEVNULL_STREAM
    if sys.stderr is None:
        sys.stderr = _DEVNULL_STREAM

# Solo ejecutar este hook si estamos en entorno frozen (PyInstaller)
if getattr(sys, 'frozen', False):
    _ensure_standard_streams()
    import multiprocessing
    import multiprocessing.spawn
    
    # Forzar el uso de 'spawn' en Windows (más seguro para frozen apps)
    if sys.platform.startswith('win'):
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # Ya está configurado, ignorar
            pass
    
    # Configurar ejecutable correcto para subprocesos
    # En PyInstaller, sys.executable apunta al ejecutable empaquetado
    multiprocessing.set_executable(sys.executable)
    
    # Asegurar que los subprocesos encuentren los módulos correctamente
    if hasattr(sys, '_MEIPASS'):
        # _MEIPASS es la carpeta temporal donde PyInstaller extrae los archivos
        os.environ['PYINSTALLER_MEIPASS'] = sys._MEIPASS
