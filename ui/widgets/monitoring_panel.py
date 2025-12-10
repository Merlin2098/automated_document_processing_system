"""
Monitoring Panel - Panel de monitoreo de estado y progreso
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot
from datetime import datetime, timedelta


class MonitoringPanel(QWidget):
    """Panel de monitoreo con progreso y estadísticas"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        
        # Estado interno
        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.error_count = 0
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Crear group box
        group = QGroupBox("📊 Monitor de Estado")
        group_layout = QVBoxLayout(group)
        
        # Header con título y estadísticas
        header_layout = QHBoxLayout()
        
        # Título
        self.status_label = QLabel("⚡ Sistema listo")
        self.status_label.setProperty("labelStyle", "header")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Estadísticas en línea
        self.time_label = QLabel("⏱️ Tiempo: 00:00:00")
        self.files_label = QLabel("📁 Archivos: 0/0")
        self.errors_label = QLabel("⚠️ Errores: 0")
        
        for label in [self.time_label, self.files_label, self.errors_label]:
            label.setProperty("labelStyle", "secondary")
            header_layout.addWidget(label)
        
        group_layout.addLayout(header_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(25)  # Aumentado de 24 a 25
        group_layout.addWidget(self.progress_bar)
        
        layout.addWidget(group)
    
    @Slot(int, int)
    def update_progress(self, current: int, total: int):
        """
        Actualiza la barra de progreso
        
        Args:
            current: Archivos procesados
            total: Total de archivos
        """
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            
            self.processed_files = current
            self.total_files = total
            
            # Actualizar label de archivos
            self.files_label.setText(f"📁 Archivos: {current}/{total}")
            
            # Actualizar status
            if current == total:
                self.status_label.setText("✅ Proceso completado")
            else:
                self.status_label.setText(f"🔄 Procesando: {percentage}%")
    
    @Slot(dict)
    def update_stats(self, stats: dict):
        """
        Actualiza las estadísticas
        
        Args:
            stats: Diccionario con estadísticas (time, errors, etc)
        """
        # Actualizar tiempo
        if 'time' in stats:
            elapsed = stats['time']
            if isinstance(elapsed, (int, float)):
                # Convertir segundos a formato HH:MM:SS
                hours = int(elapsed // 3600)
                minutes = int((elapsed % 3600) // 60)
                seconds = int(elapsed % 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.setText(f"⏱️ Tiempo: {time_str}")
            else:
                self.time_label.setText(f"⏱️ Tiempo: {elapsed}")
        
        # Actualizar errores
        if 'errors' in stats:
            self.error_count = stats['errors']
            self.errors_label.setText(f"⚠️ Errores: {self.error_count}")
        
        # Actualizar archivos si se proporcionan
        if 'current' in stats and 'total' in stats:
            self.update_progress(stats['current'], stats['total'])
    
    def start_monitoring(self, total_files: int = 0):
        """
        Inicia el monitoreo de un proceso
        
        Args:
            total_files: Total de archivos a procesar
        """
        self.start_time = datetime.now()
        self.total_files = total_files
        self.processed_files = 0
        self.error_count = 0
        
        self.progress_bar.setValue(0)
        self.status_label.setText("🔄 Procesando...")
        self.files_label.setText(f"📁 Archivos: 0/{total_files}")
        self.errors_label.setText("⚠️ Errores: 0")
        self.time_label.setText("⏱️ Tiempo: 00:00:00")
    
    def complete_monitoring(self):
        """Marca el monitoreo como completado"""
        self.progress_bar.setValue(100)
        self.status_label.setText("✅ Proceso completado")
    
    def set_indeterminate(self):
        """Establece modo indeterminado (sin porcentaje conocido)"""
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.status_label.setText("🔄 Procesando...")
    
    def set_determinate(self):
        """Vuelve a modo determinado (con porcentaje)"""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimum(0)
    
    def reset(self):
        """Reinicia el panel a su estado inicial"""
        self.start_time = None
        self.total_files = 0
        self.processed_files = 0
        self.error_count = 0
        
        self.progress_bar.setValue(0)
        self.status_label.setText("⚡ Sistema listo")
        self.files_label.setText("📁 Archivos: 0/0")
        self.errors_label.setText("⚠️ Errores: 0")
        self.time_label.setText("⏱️ Tiempo: 00:00:00")