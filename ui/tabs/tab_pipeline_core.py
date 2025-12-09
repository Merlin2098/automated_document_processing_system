"""
Tab Pipeline Core - Pipeline de procesamiento completo (5 pasos)
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QListWidget, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt

from ui.widgets.file_selector import FileSelector
from ui.widgets.stepper_widget import StepperWidget


class TabPipelineCore(QWidget):
    """Tab de Pipeline Core con 5 pasos secuenciales"""
    
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
                "Generar\nEstructura",
                "Dividir y\nClasificar",
                "Generar\nDiagnóstico",
                "Renombrar\nArchivos",
                "Unir y\nGenerar Packs"
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
        self.step_widgets.append(self._create_step4())
        self.step_widgets.append(self._create_step5())
        
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
        """Paso 1: Generar Estructura"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("1️⃣ Generar Estructura de Carpetas")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta de trabajo")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step1_folder = FileSelector(mode="folder", placeholder="Seleccionar carpeta de trabajo...")
        group_layout.addWidget(self.step1_folder)
        
        # Info
        info = QLabel("""
Se crearán las siguientes subcarpetas:
- 1_Boletas
- 2_Afp
- 3_5ta
- 4_Convocatoria
- 5_CertificadosTrabajo
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
        """Paso 2: Dividir y Clasificar"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("2️⃣ Dividir y Clasificar PDFs")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta de trabajo")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step2_folder = FileSelector(mode="folder", placeholder="Carpeta donde se creó la estructura...")
        group_layout.addWidget(self.step2_folder)
        
        # Info
        info = QLabel("""
<b>Instrucciones:</b><br>
Coloque los PDFs masivos en la carpeta madre. El sistema detectará automáticamente 
archivos que contengan las palabras clave: <b>boleta</b>, <b>afp</b>, <b>quinta</b> 
y los dividirá en páginas individuales dentro de las subcarpetas correspondientes.
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
        """Paso 3: Generar Diagnóstico"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("3️⃣ Generar Diagnóstico de Datos")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta de trabajo")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step3_folder = FileSelector(mode="folder", placeholder="Carpeta con subcarpetas pobladas...")
        group_layout.addWidget(self.step3_folder)
        
        # Info
        info = QLabel("""
Se generará un archivo Excel con múltiples hojas conteniendo:
- Datos extraídos de cada PDF (Nombre, DNI, Fecha)
- Estado de extracción (éxito/error)
- Observaciones y errores encontrados
        """)
        info.setProperty("labelStyle", "secondary")
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(2)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step4(self) -> QWidget:
        """Paso 4: Renombrar Archivos"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("4️⃣ Renombrar Archivos según JSON")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta madre")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step4_folder = FileSelector(mode="folder", placeholder="Carpeta madre con subcarpetas...")
        group_layout.addWidget(self.step4_folder)
        
        # Info
        info = QLabel("""
<b>Requisito previo:</b> Coloque los archivos JSON de renombrado en cada subcarpeta 
(1_Boletas, 2_Afp, 3_5ta).<br><br>
El sistema buscará automáticamente los JSONs y renombrará los archivos según el mapeo 
de "ARCHIVO ORIGINAL" → "NUEVO NOMBRE".
        """)
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(3)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(group)
        layout.addStretch()
        
        return widget
    
    def _create_step5(self) -> QWidget:
        """Paso 5: Unir y Generar Packs"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("5️⃣ Unir y Generar Packs Documentarios")
        group_layout = QVBoxLayout(group)
        
        # Selector de carpeta
        label = QLabel("📂 Carpeta madre")
        label.setProperty("labelStyle", "header")
        group_layout.addWidget(label)
        
        self.step5_folder = FileSelector(mode="folder", placeholder="Carpeta madre con archivos renombrados...")
        group_layout.addWidget(self.step5_folder)
        
        # Info
        info = QLabel("""
El sistema:
1. Copiará todos los PDFs a una carpeta temporal
2. Analizará y agrupará por número de contrato
3. Fusionará los PDFs del mismo contrato en un único archivo
4. Generará carpeta "Documentos_Enviar" con los packs listos
        """)
        info.setProperty("labelStyle", "secondary")
        group_layout.addWidget(info)
        
        # Botones
        btn_layout = self._create_step_buttons(4)
        group_layout.addLayout(btn_layout)
        
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
        if step_index < 4:
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
        self.log_message.emit("info", f"▶️ Ejecutando Paso {step_index + 1}...")
        self.log_message.emit("warning", "⚠️ Funcionalidad en desarrollo")
        
        # TODO: Implementar lógica de cada paso
        # Marcar como completado
        self.stepper.mark_step_completed(step_index)