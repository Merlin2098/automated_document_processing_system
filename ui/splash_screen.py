"""
Splash Screen - Pantalla de carga inicial con lazy loading simulado
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QIcon
import os


class SplashScreen(QWidget):
    """Pantalla de splash con progreso simulado"""
    
    finished = Signal()  # Señal emitida cuando termina la carga
    
    def __init__(self):
        super().__init__()
        self.progress = 0
        self.messages = [
            "Iniciando aplicación...",
            "Cargando temas...",
            "Inicializando interfaz...",
            "Preparando componentes...",
            "¡Listo!"
        ]
        self.current_message_index = 0
        
        self._init_ui()
        self._setup_timer()
    
    def _init_ui(self):
        """Inicializa la interfaz del splash"""
        # Configuración de la ventana
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(500, 300)
        
        # Centrar en pantalla
        self._center_on_screen()
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Container con fondo
        container = QWidget()
        container.setObjectName("splashContainer")
        container.setStyleSheet("""
            QWidget#splashContainer {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0D0F22,
                    stop:0.5 #1B2233,
                    stop:1 #0D0F22
                );
                border: 2px solid #38BDF8;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # Icono
        icon_label = QLabel()
        icon_path = self._get_icon_path()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(icon_label)
        
        # Título
        self.title_label = QLabel("DocFlow Eventuales")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #38BDF8;
                font-size: 28px;
                font-weight: 700;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        container_layout.addWidget(self.title_label)
        
        # Versión
        self.version_label = QLabel("v4.0")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #94A3B8;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        container_layout.addWidget(self.version_label)
        
        # Espaciador
        container_layout.addSpacing(20)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(28)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: 2px solid #2C3549;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #38BDF8,
                    stop:1 #0EA5E9
                );
                border-radius: 4px;
            }
        """)
        container_layout.addWidget(self.progress_bar)
        
        # Mensaje de estado
        self.status_label = QLabel(self.messages[0])
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #E2E8F0;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        container_layout.addWidget(self.status_label)
        
        layout.addWidget(container)
    
    def _get_icon_path(self) -> str:
        """Obtiene la ruta del icono de la aplicación"""
        # Intentar ruta relativa
        icon_path = os.path.join("resources", "app.ico")
        
        # Si no existe, intentar ruta desde el script
        if not os.path.exists(icon_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "..", "..", "resources", "app.ico")
        
        return icon_path
    
    def _center_on_screen(self):
        """Centra la ventana en la pantalla"""
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def _setup_timer(self):
        """Configura el timer para simular progreso"""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        # 3 segundos totales / 100 pasos = 30ms por paso
        self.timer.start(30)
    
    def _update_progress(self):
        """Actualiza el progreso de carga"""
        self.progress += 1
        self.progress_bar.setValue(self.progress)
        
        # Actualizar mensaje según el progreso
        if self.progress == 25:
            self.current_message_index = 1
            self.status_label.setText(self.messages[1])
        elif self.progress == 50:
            self.current_message_index = 2
            self.status_label.setText(self.messages[2])
        elif self.progress == 75:
            self.current_message_index = 3
            self.status_label.setText(self.messages[3])
        elif self.progress == 100:
            self.current_message_index = 4
            self.status_label.setText(self.messages[4])
            self.timer.stop()
            
            # Esperar 200ms adicionales antes de cerrar
            QTimer.singleShot(200, self._finish)
    
    def _finish(self):
        """Finaliza el splash screen"""
        self.finished.emit()
        self.close()