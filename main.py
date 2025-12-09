"""
Matrix File Processor v3.0
Aplicación principal - Punto de entrada
"""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    """Función principal de la aplicación"""
    # Configurar atributos de aplicación de alta DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # Crear aplicación
    app = QApplication(sys.argv)
    app.setApplicationName("Matrix File Processor")
    app.setApplicationVersion("3.0")
    app.setOrganizationName("RichiDev")
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()