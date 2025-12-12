"""
Tab Pipeline Core - Pipeline de procesamiento completo (5 pasos)
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QListWidget, QScrollArea
)
from PySide6.QtCore import Signal, Slot, Qt

from ui.widgets.file_selector import FileSelector
from ui.widgets.stepper_widget import StepperWidget
from ui.workers.core_pipeline_step1_worker import CorePipelineStep1Worker
from ui.workers.core_pipeline_step2_worker import CorePipelineStep2Worker
from ui.workers.core_pipeline_step3_worker import CorePipelineStep3Worker
from ui.workers.core_pipeline_step4_worker import CorePipelineStep4Worker
from ui.workers.core_pipeline_step5_worker import CorePipelineStep5Worker


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
        
        # Worker actual
        self.current_worker = None
        
        # Última carpeta procesada (para propagar entre pasos)
        self.last_folder_path = None
        
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
(1_Boletas, 2_Afp, 3_5ta, 4_Convocatoria, 5_CertificadosTrabajo).<br><br>
El sistema buscará automáticamente los JSONs y renombrará los archivos según el mapeo 
de "ARCHIVO ORIGINAL" → "NUEVO NOMBRE".
        """)
        info.setProperty("labelStyle", "secondary")
        info.setWordWrap(True)
        info.setTextFormat(Qt.RichText)
        group_layout.addWidget(info)
        
        # Labels de información de progreso
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)
        
        self.step4_time_label = QLabel("⏱️ Tiempo: --:--")
        self.step4_time_label.setProperty("labelStyle", "info")
        info_layout.addWidget(self.step4_time_label)
        
        self.step4_files_label = QLabel("📄 Archivos: 0 / 0")
        self.step4_files_label.setProperty("labelStyle", "info")
        info_layout.addWidget(self.step4_files_label)
        
        self.step4_folder_label = QLabel("📁 Carpeta: -")
        self.step4_folder_label.setProperty("labelStyle", "info")
        info_layout.addWidget(self.step4_folder_label)
        
        info_layout.addStretch()
        group_layout.addLayout(info_layout)
        
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
        btn_execute.setObjectName(f"btn_execute_step{step_index}")
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
        
        # Ejecutar según el paso
        if step_index == 0:
            self._execute_step1()
        elif step_index == 1:
            self._execute_step2()
        elif step_index == 2:
            self._execute_step3()
        elif step_index == 3:
            self._execute_step4()
        elif step_index == 4:
            self._execute_step5()
    
    def _execute_step1(self):
        """Ejecuta el Paso 1: Generar Estructura"""
        # Resetear contadores
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.reset()
        
        folder_path = self.step1_folder.get_path()
        
        if not folder_path:
            self.log_message.emit("error", "❌ Debe seleccionar una carpeta de trabajo")
            return
        
        # Deshabilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step0")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Procesando...")
        
        # Crear y configurar worker
        self.current_worker = CorePipelineStep1Worker(folder_path)
        
        # Conectar señales
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step1_completed)
        self.current_worker.error_signal.connect(self._on_step_error)
        
        # Iniciar worker
        self.current_worker.start()
    
    def _execute_step2(self):
        """Ejecuta el Paso 2: Dividir y Clasificar"""
        from PySide6.QtWidgets import QMessageBox
        
        # Resetear contadores
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.reset()
        
        folder_path = self.step2_folder.get_path()
        
        if not folder_path:
            self.log_message.emit("error", "❌ Debe seleccionar una carpeta de trabajo")
            return
        
        # Validar que existen las subcarpetas requeridas
        subcarpetas_requeridas = ['1_Boletas', '2_Afp', '3_5ta', '4_Convocatoria', '5_CertificadosTrabajo']
        carpetas_existentes = []
        
        for carpeta in subcarpetas_requeridas:
            ruta_carpeta = os.path.join(folder_path, carpeta)
            if os.path.exists(ruta_carpeta):
                carpetas_existentes.append(carpeta)
        
        if not carpetas_existentes:
            self.log_message.emit("error", "❌ No se encontraron las subcarpetas necesarias")
            return
        
        # VALIDACIÓN PREVIA: Verificar si hay archivos en las carpetas destino
        carpetas_con_archivos = {}
        for carpeta in carpetas_existentes:
            ruta_carpeta = os.path.join(folder_path, carpeta)
            archivos = [f for f in os.listdir(ruta_carpeta) 
                       if os.path.isfile(os.path.join(ruta_carpeta, f))]
            if archivos:
                carpetas_con_archivos[carpeta] = len(archivos)
        
        # Si hay archivos, preguntar al usuario
        if carpetas_con_archivos:
            total_archivos = sum(carpetas_con_archivos.values())
            carpetas_str = ", ".join(carpetas_con_archivos.keys())
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Carpetas con archivos existentes")
            msg.setText(f"Se encontraron {total_archivos} archivo(s) en las carpetas destino:")
            msg.setInformativeText(
                f"{carpetas_str}\n\n"
                "Para ejecutar el Paso 2, las carpetas deben estar vacías.\n"
                "Los archivos existentes serán eliminados antes de procesar.\n\n"
                "¿Desea continuar?"
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            
            respuesta = msg.exec()
            
            if respuesta == QMessageBox.No:
                self.log_message.emit("warning", "⚠️ Operación cancelada por el usuario")
                return
            
            # Usuario aceptó sobrescribir
            sobrescribir = True
            self.log_message.emit("info", f"🗑️ Se eliminarán {total_archivos} archivos existentes")
        else:
            sobrescribir = False
        
        # Deshabilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step1")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Procesando...")
        
        # Crear y configurar worker CON parámetro sobrescribir
        self.current_worker = CorePipelineStep2Worker(folder_path, sobrescribir=sobrescribir)
        
        # Conectar señales
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step2_completed)
        self.current_worker.error_signal.connect(self._on_step_error)
        
        # Iniciar worker
        self.current_worker.start()
    
    def _execute_step3(self):
        """Ejecuta el Paso 3: Generar Diagnóstico"""
        # Resetear contadores
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.reset()
        
        folder_path = self.step3_folder.get_path()
        
        if not folder_path:
            self.log_message.emit("error", "❌ Debe seleccionar una carpeta de trabajo")
            return
        
        # Validar que existen las subcarpetas con datos
        subcarpetas_requeridas = ['1_Boletas', '2_Afp', '3_5ta']
        carpetas_existentes = []
        
        for carpeta in subcarpetas_requeridas:
            ruta_carpeta = os.path.join(folder_path, carpeta)
            if os.path.exists(ruta_carpeta):
                carpetas_existentes.append(carpeta)
        
        if not carpetas_existentes:
            self.log_message.emit("error", "❌ No se encontraron subcarpetas con datos para procesar")
            return
        
        # Deshabilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step2")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Procesando...")
        
        # Crear y configurar worker
        self.current_worker = CorePipelineStep3Worker(folder_path)
        
        # Conectar señales
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step3_completed)
        self.current_worker.error_signal.connect(self._on_step_error)
        
        # Iniciar worker
        self.current_worker.start()
    
    def _execute_step4(self):
        """Ejecuta el Paso 4: Renombrar"""
        # Resetear contadores
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.reset()
        
        folder_path = self.step4_folder.get_path()
        
        if not folder_path:
            self.log_message.emit("error", "❌ Debe seleccionar una carpeta madre")
            return
        
        # Validar que existen las subcarpetas requeridas
        carpetas_requeridas = ['1_Boletas', '2_Afp', '3_5ta', '4_Convocatoria', '5_CertificadosTrabajo']
        carpetas_faltantes = []
        
        for carpeta in carpetas_requeridas:
            ruta_carpeta = os.path.join(folder_path, carpeta)
            if not os.path.exists(ruta_carpeta):
                carpetas_faltantes.append(carpeta)
        
        if carpetas_faltantes:
            self.log_message.emit(
                "warning", 
                f"⚠️ Carpetas faltantes: {', '.join(carpetas_faltantes)}. Se omitirán."
            )
        
        # Resetear labels de información
        self.step4_time_label.setText("⏱️ Tiempo: 00:00")
        self.step4_files_label.setText("📄 Archivos: 0 / 0")
        self.step4_folder_label.setText("📁 Carpeta: Escaneando...")
        
        # Deshabilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step3")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Procesando...")
        
        # Crear y configurar worker
        self.current_worker = CorePipelineStep4Worker(folder_path)
        
        # Conectar señales básicas
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.finished_signal.connect(self._on_step4_completed)
        self.current_worker.error_signal.connect(self._on_step_error)
        
        # Conectar señales enriquecidas al tab
        self.current_worker.time_update_signal.connect(self._on_step4_time_update)
        self.current_worker.file_progress_signal.connect(self._on_step4_file_progress)
        self.current_worker.folder_update_signal.connect(self._on_step4_folder_update)
        self.current_worker.overall_progress_signal.connect(self._on_step4_overall_progress)
        
        # Conectar señales al monitoring panel
        if hasattr(main_window, 'monitoring_panel'):
            # Progreso de carpetas (progress_signal)
            self.current_worker.progress_signal.connect(
                lambda current, total: main_window.monitoring_panel.folders_label.setText(
                    f"📂 Carpetas: {current}/{total}"
                )
            )
            
            # Progreso de archivos (file_progress_signal)
            self.current_worker.file_progress_signal.connect(
                lambda current, total: main_window.monitoring_panel.update_progress(current, total)
            )
            
            # Tiempo (time_update_signal)
            self.current_worker.time_update_signal.connect(
                lambda elapsed: main_window.monitoring_panel.time_label.setText(
                    f"⏱️ Tiempo: {int(elapsed//3600):02d}:{int((elapsed%3600)//60):02d}:{int(elapsed%60):02d}"
                )
            )
            
            # Progreso global (overall_progress_signal)
            self.current_worker.overall_progress_signal.connect(
                lambda progress: main_window.monitoring_panel.progress_bar.setValue(progress)
            )
            
            # Estadísticas finales (stats_signal)
            self.current_worker.stats_signal.connect(
                lambda stats: main_window.monitoring_panel.errors_label.setText(
                    f"⚠️ Errores: {stats.get('total_fallidos', 0)}"
                )
            )
        
        # Iniciar worker
        self.current_worker.start()
    
    def _execute_step5(self):
        """Ejecuta el Paso 5: Unir PDFs"""
        # Resetear contadores
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.reset()
        
        folder_path = self.step5_folder.get_path()
        
        if not folder_path:
            self.log_message.emit("error", "❌ Debe seleccionar una carpeta madre")
            return
        
        # Validar que existen subcarpetas
        subcarpetas_esperadas = ['1_Boletas', '2_Afp', '3_5ta', '4_Convocatoria', '5_CertificadosTrabajo']
        carpetas_existentes = []
        
        for carpeta in subcarpetas_esperadas:
            ruta_carpeta = os.path.join(folder_path, carpeta)
            if os.path.exists(ruta_carpeta):
                carpetas_existentes.append(carpeta)
        
        if not carpetas_existentes:
            self.log_message.emit("error", "❌ No se encontraron las subcarpetas necesarias")
            return
        
        # Deshabilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step4")
        if btn:
            btn.setEnabled(False)
            btn.setText("⏳ Procesando...")
        
        # Crear y configurar worker
        self.current_worker = CorePipelineStep5Worker(folder_path)
        
        # Conectar señales
        self.current_worker.progress_signal.connect(self.progress_updated.emit)
        self.current_worker.log_signal.connect(self.log_message.emit)
        self.current_worker.stats_signal.connect(self.stats_updated.emit)
        self.current_worker.finished_signal.connect(self._on_step5_completed)
        self.current_worker.error_signal.connect(self._on_step_error)
        
        # Iniciar worker
        self.current_worker.start()
    
    @Slot(dict)
    def _on_step1_completed(self, resultado: dict):
        """Handler cuando se completa el Paso 1"""
        # Re-habilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step0")
        if btn:
            btn.setEnabled(True)
            btn.setText("▶️ Ejecutar Paso 1")
        
        # Marcar paso como completado
        self.stepper.mark_step_completed(0)
        
        # Guardar ruta para próximos pasos
        if resultado.get('success'):
            self.last_folder_path = resultado.get('folder_path')
            
            # Auto-completar campos de pasos siguientes
            if self.last_folder_path:
                self.step2_folder.set_path(self.last_folder_path)
                self.step3_folder.set_path(self.last_folder_path)
                self.step4_folder.set_path(self.last_folder_path)
                self.step5_folder.set_path(self.last_folder_path)
            
            self.log_message.emit("success", "✅ Paso 1 completado. Puede continuar al Paso 2")
    
    @Slot(dict)
    def _on_step2_completed(self, resultado: dict):
        """Handler cuando se completa el Paso 2"""
        # Re-habilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step1")
        if btn:
            btn.setEnabled(True)
            btn.setText("▶️ Ejecutar Paso 2")
        
        # Marcar paso como completado
        self.stepper.mark_step_completed(1)
        
        if resultado.get('success'):
            self.log_message.emit("success", "✅ Paso 2 completado. Puede continuar al Paso 3")
        else:
            resumen = resultado.get('resumen', {})
            if resumen.get('pdfs_procesados', 0) > 0:
                self.log_message.emit("warning", "⚠️ Paso 2 completado con algunos errores")
    
    @Slot(dict)
    def _on_step3_completed(self, resultado: dict):
        """Handler cuando se completa el Paso 3"""
        # Re-habilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step2")
        if btn:
            btn.setEnabled(True)
            btn.setText("▶️ Ejecutar Paso 3")
        
        # Marcar paso como completado
        self.stepper.mark_step_completed(2)
        
        if resultado.get('success'):
            excel_path = resultado.get('excel_path')
            if excel_path:
                self.log_message.emit("success", f"✅ Paso 3 completado. Excel: {os.path.basename(excel_path)}")
                self.log_message.emit("info", "📋 Puede editar el Excel y continuar al Paso 4")
    
    @Slot(dict)
    def _on_step4_completed(self, resultado: dict):
        """Handler cuando se completa el Paso 4"""
        # Re-habilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step3")
        if btn:
            btn.setEnabled(True)
            btn.setText("▶️ Ejecutar Paso 4")
        
        # Limpiar label de carpeta
        self.step4_folder_label.setText("📁 Carpeta: Completado")
        
        # Actualizar monitoring panel
        main_window = self.window()
        if hasattr(main_window, 'monitoring_panel'):
            main_window.monitoring_panel.status_label.setText("✅ Proceso completado")
            main_window.monitoring_panel.progress_bar.setValue(100)
        
        # Marcar paso como completado
        self.stepper.mark_step_completed(3)
        
        # Verificar si fue exitoso
        if resultado.get('success'):
            self.log_message.emit("success", "✅ Paso 4 completado. Puede continuar al Paso 5")
        else:
            totales = resultado.get('totales', {})
            if totales.get('exitosos', 0) > 0:
                self.log_message.emit("warning", "⚠️ Paso 4 completado con algunos errores")
            else:
                self.log_message.emit("warning", "⚠️ No se renombró ningún archivo")
    
    @Slot(float)
    def _on_step4_time_update(self, elapsed_seconds: float):
        """Actualiza el label de tiempo del paso 4"""
        mins = int(elapsed_seconds // 60)
        secs = int(elapsed_seconds % 60)
        self.step4_time_label.setText(f"⏱️ Tiempo: {mins:02d}:{secs:02d}")
    
    @Slot(int, int)
    def _on_step4_file_progress(self, current: int, total: int):
        """Actualiza el label de archivos procesados del paso 4"""
        self.step4_files_label.setText(f"📄 Archivos: {current} / {total}")
    
    @Slot(str)
    def _on_step4_folder_update(self, folder_name: str):
        """Actualiza el label de carpeta actual del paso 4"""
        self.step4_folder_label.setText(f"📁 Carpeta: {folder_name}")
    
    @Slot(int)
    def _on_step4_overall_progress(self, progress_percent: int):
        """Actualiza el progreso global del paso 4 (opcional, para barra de progreso futura)"""
        # Por ahora solo lo registramos en logs si quisieras agregarlo
        pass
    
    @Slot(dict)
    def _on_step5_completed(self, resultado: dict):
        """Handler cuando se completa el Paso 5"""
        # Re-habilitar botón
        btn = self.findChild(QPushButton, "btn_execute_step4")
        if btn:
            btn.setEnabled(True)
            btn.setText("▶️ Ejecutar Paso 5")
        
        # Marcar paso como completado
        self.stepper.mark_step_completed(4)
        
        if resultado.get('success'):
            ruta_enviar = resultado.get('ruta_enviar')
            if ruta_enviar:
                self.log_message.emit("success", f"✅ Paso 5 completado. Packs en: {os.path.basename(ruta_enviar)}")
                self.log_message.emit("success", "🎉 ¡Pipeline completo finalizado!")
        else:
            if resultado.get('packs_generados', 0) > 0:
                self.log_message.emit("warning", "⚠️ Paso 5 completado con algunos errores")
            else:
                self.log_message.emit("error", "❌ No se generaron packs documentarios")
        
        # Activar iluminación intermitente al completar paso final
        if resultado.get('success') or resultado.get('packs_generados', 0) > 0:
            main_window = self.window()
            if hasattr(main_window, 'flash_window'):
                main_window.flash_window(5)
    
    @Slot(str)
    def _on_step_error(self, error_msg: str):
        """Handler cuando ocurre un error"""
        # Re-habilitar botón del paso actual
        btn = self.findChild(QPushButton, f"btn_execute_step{self.current_step}")
        if btn:
            btn.setEnabled(True)
            btn.setText(f"▶️ Ejecutar Paso {self.current_step + 1}")
        
        self.log_message.emit("error", f"❌ Error: {error_msg}")