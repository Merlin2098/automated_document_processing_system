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
        self.current_step = 0
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        # Layout principal del tab
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Crear widget contenedor para el contenido scrolleable
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)
        
        # Stepper
        self.stepper = StepperWidget(
            steps=[
                "Generar\nDiagnóstico",
                "Renombrar\nDocumentos",
                "Limpiar\nDuplicados"
            ],
            theme_manager=self.theme_manager
        )
        
        # Conectar señal de clic en paso del stepper
        self.stepper.step_clicked.connect(self._go_to_step)
        
        content_layout.addWidget(self.stepper)
        
        # Contenedor de pasos (stack)
        self.step_widgets = []
        
        # Crear widgets para cada paso
        self.step_widgets.append(self._create_step1())
        self.step_widgets.append(self._create_step2())
        self.step_widgets.append(self._create_step3())
        
        # Agregar todos los widgets (solo uno visible a la vez)
        for widget in self.step_widgets:
            content_layout.addWidget(widget)
            widget.hide()
        
        # Mostrar primer paso
        self.step_widgets[0].show()
        self.stepper.set_active_step(0)
        
        # Crear el scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # Agregar scroll area al layout principal
        main_layout.addWidget(scroll_area)
    
    def _create_step1(self) -> QWidget:
        """Paso 1: Generar Diagnóstico SUNAT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("1️⃣ Generar Diagnóstico SUNAT")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs SUNAT")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step1_folder = FileSelector(
            mode="folder",
            placeholder="Seleccionar carpeta con documentos CIR..."
        )
        group_layout.addWidget(self.step1_folder)
        
        # Workers paralelos
        workers_label = QLabel("⚡ Procesamiento paralelo")
        workers_label.setProperty("labelStyle", "header")
        group_layout.addWidget(workers_label)
        
        self.workers_combo = QComboBox()
        self.workers_combo.addItems([
            "4 Workers (Recomendado)",
            "2 Workers",
            "8 Workers"
        ])
        group_layout.addWidget(self.workers_combo)
        
        # Info
        info = QLabel("""
Se generará un archivo Excel con:
• Datos extraídos (Nombre, DNI, Fecha)
• Clasificación: ALTA/BAJA/OTROS
• Detección de errores y archivos sin datos
        """)
        info.setProperty("labelStyle", "secondary")
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(0)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step2(self) -> QWidget:
        """Paso 2: Renombrar Documentos SUNAT"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("2️⃣ Renombrar Documentos SUNAT")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con PDFs y JSON de renombrado")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step2_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs y archivo JSON..."
        )
        group_layout.addWidget(self.step2_folder)
        
        # Info
        info = QLabel("""
<b>Instrucciones:</b><br>
El sistema buscará automáticamente el archivo JSON que contenga <b>"rename"</b> 
en su nombre. Los archivos se renombrarán al formato: <b>NUMERO NOMBRE.pdf</b>
        """)
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(1)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step3(self) -> QWidget:
        """Paso 3: Limpiar Duplicados"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("3️⃣ Limpiar Duplicados por Contrato")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta con archivos renombrados")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step3_folder = FileSelector(
            mode="folder",
            placeholder="Carpeta con PDFs renombrados..."
        )
        group_layout.addWidget(self.step3_folder)
        
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
        group_layout.addLayout(warning_layout)
        
        # Botones principales
        btn_layout = self._create_step_buttons(2)
        group_layout.addLayout(btn_layout)
        
        # Botón de vista previa adicional (centrado debajo)
        preview_layout = QHBoxLayout()
        preview_layout.addStretch()
        self.btn_preview = QPushButton("👁️ Vista Previa de Duplicados")
        self.btn_preview.setProperty("buttonStyle", "secondary")
        self.btn_preview.clicked.connect(self._preview_duplicates)
        preview_layout.addWidget(self.btn_preview)
        preview_layout.addStretch()
        group_layout.addLayout(preview_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step_buttons(self, step_index: int) -> QHBoxLayout:
        """Crea los botones de navegación para un paso"""
        layout = QHBoxLayout()
        
        # Botón anterior (si no es el primer paso)
        if step_index > 0:
            btn_prev = QPushButton("⬅️ Paso Anterior")
            btn_prev.setProperty("buttonStyle", "secondary")
            btn_prev.clicked.connect(lambda: self._go_to_step(step_index - 1))
            layout.addWidget(btn_prev)
        else:
            layout.addStretch()
        
        # Botón ejecutar
        btn_execute = QPushButton(f"▶️ Ejecutar Paso {step_index + 1}")
        btn_execute.clicked.connect(lambda: self._execute_step(step_index))
        layout.addWidget(btn_execute)
        
        # Botón siguiente (si no es el último paso)
        if step_index < 2:
            btn_next = QPushButton("Siguiente Paso ➡️")
            btn_next.setProperty("buttonStyle", "secondary")
            btn_next.clicked.connect(lambda: self._go_to_step(step_index + 1))
            layout.addWidget(btn_next)
        else:
            layout.addStretch()
        
        return layout
    
    def _go_to_step(self, step_index: int):
        """Navega a un paso específico"""
        # Ocultar paso actual
        self.step_widgets[self.current_step].hide()
        
        # Mostrar nuevo paso
        self.current_step = step_index
        self.step_widgets[self.current_step].show()
        
        # Actualizar stepper
        self.stepper.set_active_step(step_index)
        
        self.log_message.emit("info", f"📋 Navegando al Paso {step_index + 1}")
    
    def _execute_step(self, step_index: int):
        """Ejecuta el paso actual"""
        if step_index == 0:
            self._execute_step1()
        elif step_index == 1:
            self._execute_step2()
        elif step_index == 2:
            self._execute_step3()
    
    def _execute_step1(self):
        """Ejecuta el paso 1: Generar diagnóstico"""
        folder = self.step1_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        workers_text = self.workers_combo.currentText()
        workers = int(workers_text.split()[0])
        
        self.log_message.emit("info", f"🚀 Generando diagnóstico SUNAT con {workers} workers...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
        self.stepper.mark_step_completed(0)
    
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
    
    def _preview_duplicates(self):
        """Muestra vista previa de duplicados"""
        folder = self.step3_folder.get_path()
        if not folder:
            self.log_message.emit("warning", "⚠️ Debe seleccionar una carpeta")
            return
        
        self.log_message.emit("info", "👁️ Analizando duplicados...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica
    
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