"""
Tab Pipeline SUNAT - Pipeline para documentos SUNAT (3 pasos)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QComboBox, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt

from ui.widgets.file_selector import FileSelector
from ui.widgets.stepper_widget import StepperWidget


class TabPipelineSunat(QWidget):
    """Tab de Pipeline SUNAT con 3 pasos"""
    
    # Señales
    log_message = Signal(str, str)
    progress_updated = Signal(int, int)
    stats_updated = Signal(dict)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        # Layout principal con scroll
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Área de scroll para el contenido
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget contenedor del contenido
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Stepper
        self.stepper = StepperWidget(
            steps=[
                "Generar\nDiagnóstico",
                "Renombrar\nDocumentos",
                "Limpiar\nDuplicados"
            ],
            theme_manager=self.theme_manager
        )
        layout.addWidget(self.stepper)
        
        # Espaciado adicional después del stepper
        layout.addSpacing(10)
        
        # Cards para cada paso (todos visibles)
        step1_card = self._create_step1_card()
        layout.addWidget(step1_card)
        
        step2_card = self._create_step2_card()
        layout.addWidget(step2_card)
        
        step3_card = self._create_step3_card()
        layout.addWidget(step3_card)
        
        # Spacer
        layout.addStretch()
        
        # Establecer el widget de contenido en el scroll
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
    
    def _create_step1_card(self) -> QGroupBox:
        """Paso 1: Generar Diagnóstico SUNAT"""
        group = QGroupBox("1️⃣ Generar Diagnóstico SUNAT")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs SUNAT")
        label.setProperty("labelStyle", "header")
        layout.addWidget(label)
        
        self.step1_folder = FileSelector(
            mode="folder",
            placeholder="Seleccionar carpeta con documentos CIR..."
        )
        layout.addWidget(self.step1_folder)
        
        # Workers paralelos
        workers_label = QLabel("⚡ Procesamiento paralelo")
        workers_label.setProperty("labelStyle", "header")
        layout.addWidget(workers_label)
        
        self.workers_combo = QComboBox()
        self.workers_combo.addItems([
            "4 Workers (Recomendado)",
            "2 Workers",
            "8 Workers"
        ])
        layout.addWidget(self.workers_combo)
        
        # Info
        info = QLabel("""
Se generará un archivo Excel con:
- Datos extraídos (Nombre, DNI, Fecha)
- Clasificación: ALTA/BAJA/OTROS
- Detección de errores y archivos sin datos
        """)
        info.setProperty("labelStyle", "secondary")
        layout.addWidget(info)
        
        # Botón
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_step1 = QPushButton("▶️ Generar Diagnóstico")
        self.btn_step1.clicked.connect(self._execute_step1)
        btn_layout.addWidget(self.btn_step1)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_step2_card(self) -> QGroupBox:
        """Paso 2: Renombrar Documentos SUNAT"""
        group = QGroupBox("2️⃣ Renombrar Documentos SUNAT")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs y JSON de renombrado")
        label.setProperty("labelStyle", "header")
        layout.addWidget(label)
        
        self.step2_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs y archivo JSON..."
        )
        layout.addWidget(self.step2_folder)
        
        # Info
        info = QLabel("""
El sistema buscará automáticamente el archivo JSON que contenga <b>"rename"</b> 
en su nombre. Los archivos se renombrarán al formato: <b>NUMERO NOMBRE.pdf</b>
        """)
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)
        
        # Botón
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_step2 = QPushButton("▶️ Renombrar Documentos")
        self.btn_step2.clicked.connect(self._execute_step2)
        btn_layout.addWidget(self.btn_step2)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    def _create_step3_card(self) -> QGroupBox:
        """Paso 3: Limpiar Duplicados"""
        group = QGroupBox("3️⃣ Limpiar Duplicados por Contrato")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con archivos renombrados")
        label.setProperty("labelStyle", "header")
        layout.addWidget(label)
        
        self.step3_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs renombrados..."
        )
        layout.addWidget(self.step3_folder)
        
        # Warning info
        warning_layout = QHBoxLayout()
        warning_icon = QLabel("⚠️")
        warning_text = QLabel(
            "<b>Advertencia:</b> Esta operación eliminará archivos duplicados "
            "conservando solo el primero de cada contrato. Se mostrará una vista "
            "previa antes de proceder."
        )
        warning_text.setProperty("labelStyle", "secondary")
        warning_text.setWordWrap(True)
        warning_text.setTextFormat(Qt.RichText)
        
        warning_layout.addWidget(warning_icon)
        warning_layout.addWidget(warning_text, 1)
        layout.addLayout(warning_layout)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_preview = QPushButton("👁️ Vista Previa")
        self.btn_preview.setProperty("buttonStyle", "secondary")
        self.btn_preview.clicked.connect(self._preview_duplicates)
        btn_layout.addWidget(self.btn_preview)
        
        self.btn_step3 = QPushButton("▶️ Limpiar Duplicados")
        self.btn_step3.clicked.connect(self._execute_step3)
        btn_layout.addWidget(self.btn_step3)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return group
    
    @Slot()
    def _execute_step1(self):
        """Ejecuta el paso 1: Generar diagnóstico"""
        folder = self.step1_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        self.log_message.emit("info", "🚀 Generando diagnóstico SUNAT...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
        self.stepper.mark_step_completed(0)
        self.stepper.set_active_step(1)
    
    @Slot()
    def _execute_step2(self):
        """Ejecuta el paso 2: Renombrar"""
        folder = self.step2_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        self.log_message.emit("info", "📄 Renombrando documentos SUNAT...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
        self.stepper.mark_step_completed(1)
        self.stepper.set_active_step(2)
    
    @Slot()
    def _preview_duplicates(self):
        """Muestra vista previa de duplicados"""
        folder = self.step3_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        self.log_message.emit("info", "👁️ Analizando duplicados...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
    
    @Slot()
    def _execute_step3(self):
        """Ejecuta el paso 3: Limpiar duplicados"""
        folder = self.step3_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        self.log_message.emit("info", "🧹 Limpiando duplicados...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
        self.stepper.mark_step_completed(2)