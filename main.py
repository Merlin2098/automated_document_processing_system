"""
Matrix File Processor v3.0
Aplicación principal - Punto de entrada
"""
import sys
import multiprocessing
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Importar sistema de logging
from utils.logger import initialize_logging_system, get_logger


def main():
    """Función principal de la aplicación"""
    # =========================================================================
    # PASO 1: Inicializar sistema de logging (PRIMERO, antes de todo)
    # =========================================================================
    initialize_logging_system()
    logger = get_logger('main')
    
    logger.info("="*80)
    logger.info("DocFlow Eventuales v4.0 - Iniciando aplicación")
    logger.info("="*80)
    logger.info("Sistema operativo: " + sys.platform)
    logger.info("Versión Python: " + sys.version.split()[0])
    logger.info("-"*80)
    
    # =========================================================================
    # PASO 2: Configurar aplicación Qt
    # =========================================================================
    logger.info("Configurando aplicación Qt...")
    
    # Configurar atributos de aplicación de alta DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("DocFlow Eventuales")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("Ricardo Fabian Uculmana Quispe")
    
    logger.info("✅ Aplicación Qt configurada correctamente")
    
    # =========================================================================
    # PASO 3: Mostrar splash screen
    # =========================================================================
    logger.info("Mostrando splash screen...")
    
    try:
        from ui.splash_screen import SplashScreen
        splash = SplashScreen()
        splash.show()
        
        # Procesar eventos para que el splash se muestre
        app.processEvents()
        
        logger.info("✅ Splash screen mostrado")
    except Exception as e:
        logger.error(f"❌ Error mostrando splash screen: {e}", exc_info=True)
        # Continuar sin splash si falla
    
    # =========================================================================
    # PASO 4: Cargar ventana principal (lazy loading)
    # =========================================================================
    # Variable para almacenar la ventana principal
    main_window = None
    
    def on_splash_finished():
        """Callback cuando el splash termina"""
        nonlocal main_window
        
        logger.info("Splash screen completado, cargando ventana principal...")
        
        try:
            # Cargar ventana principal (lazy loading)
            from ui.main_window import MainWindow
            main_window = MainWindow()
            main_window.show()
            
            logger.info("✅ Ventana principal cargada y mostrada")
            logger.info("-"*80)
            logger.info("🚀 Aplicación lista para usar")
            logger.info("="*80)
            
        except Exception as e:
            logger.critical(f"❌ ERROR CRÍTICO al cargar ventana principal: {e}", exc_info=True)
            # Cerrar aplicación si falla la ventana principal
            app.quit()
    
    # Conectar señal de finalización
    if 'splash' in locals():
        splash.finished.connect(on_splash_finished)
    else:
        # Si no hay splash, cargar ventana directamente
        on_splash_finished()
    
    # =========================================================================
    # PASO 5: Ejecutar loop de eventos
    # =========================================================================
    logger.info("Iniciando event loop de Qt...")
    
    try:
        exit_code = app.exec()
        
        logger.info("-"*80)
        logger.info(f"Aplicación cerrada con código: {exit_code}")
        logger.info("="*80)
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.critical(f"❌ ERROR CRÍTICO en event loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # CRÍTICO: freeze_support() DEBE estar antes de cualquier código
    # Esto previene bucles infinitos cuando multiprocessing crea subprocesos
    # en aplicaciones empaquetadas con PyInstaller
    multiprocessing.freeze_support()
    
    # Configurar método de inicio para multiprocessing (solo en Windows)
    if sys.platform.startswith('win'):
        # En Windows, forzar 'spawn' para evitar problemas con PyInstaller
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            # Ya configurado, ignorar
            pass
    
    # Ejecutar aplicación
    main()