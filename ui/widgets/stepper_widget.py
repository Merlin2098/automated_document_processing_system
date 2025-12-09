"""
Stepper Widget - Widget visual de pasos con estado
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QCursor


class StepCircle(QWidget):
    """Círculo individual de un paso"""
    
    clicked = Signal(int)  # Emite el índice del paso cuando se hace clic
    
    def __init__(self, number: int, index: int, theme_manager, parent=None):
        super().__init__(parent)
        self.number = number
        self.index = index
        self.theme_manager = theme_manager
        self.state = "pending"  # pending, active, completed
        
        self.setFixedSize(40, 40)
        self.setCursor(QCursor(Qt.PointingHandCursor))  # Cursor de manita
    
    def set_state(self, state: str):
        """Establece el estado del círculo"""
        self.state = state
        self.update()
    
    def mousePressEvent(self, event):
        """Maneja el clic en el círculo"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
    
    def paintEvent(self, event):
        """Dibuja el círculo"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Obtener colores usando el nuevo sistema
        primary = self.theme_manager.get_color('primary')
        surface = self.theme_manager.get_color('surface')
        border = self.theme_manager.get_color('border')
        text_secondary = self.theme_manager.get_color('text.secondary')
        
        # Determinar colores según estado
        if self.state == "active":
            bg_color = QColor(primary)
            border_color = QColor(primary)
            text_color = QColor('#FFFFFF')
        elif self.state == "completed":
            bg_color = QColor(primary)
            border_color = QColor(primary)
            text_color = QColor('#FFFFFF')
        else:  # pending
            bg_color = QColor(surface)
            border_color = QColor(border)
            text_color = QColor(text_secondary)
        
        # Dibujar círculo
        painter.setBrush(bg_color)
        painter.setPen(QPen(border_color, 3))
        painter.drawEllipse(0, 0, 40, 40)
        
        # Dibujar número
        painter.setPen(text_color)
        painter.setFont(painter.font())
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, 40, 40, Qt.AlignCenter, str(self.number))


class StepperWidget(QWidget):
    """Widget de stepper completo"""
    
    step_clicked = Signal(int)  # Emite el índice del paso clickeado
    
    def __init__(self, steps: list, theme_manager, parent=None):
        super().__init__(parent)
        self.steps = steps
        self.theme_manager = theme_manager
        self.step_circles = []
        self.step_labels = []
        self.active_step = 0
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Layout horizontal para los pasos
        steps_layout = QHBoxLayout()
        steps_layout.setSpacing(20)
        
        for i, step_text in enumerate(self.steps):
            # Layout vertical para cada paso
            step_layout = QVBoxLayout()
            step_layout.setAlignment(Qt.AlignCenter)
            step_layout.setSpacing(8)
            
            # Círculo
            circle = StepCircle(i + 1, i, self.theme_manager)
            circle.clicked.connect(self._on_step_circle_clicked)  # Conectar señal del círculo
            self.step_circles.append(circle)
            step_layout.addWidget(circle, alignment=Qt.AlignCenter)
            
            # Label
            label = QLabel(step_text)
            label.setProperty("labelStyle", "secondary")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setFixedWidth(80)
            self.step_labels.append(label)
            step_layout.addWidget(label, alignment=Qt.AlignCenter)
            
            steps_layout.addLayout(step_layout)
            
            # Agregar línea conectora (excepto después del último)
            if i < len(self.steps) - 1:
                steps_layout.addStretch(1)
        
        main_layout.addLayout(steps_layout)
    
    def _on_step_circle_clicked(self, step_index: int):
        """Maneja el clic en un círculo de paso"""
        self.step_clicked.emit(step_index)
    
    def set_active_step(self, step_index: int):
        """Establece el paso activo"""
        self.active_step = step_index
        
        for i, circle in enumerate(self.step_circles):
            if i < step_index:
                circle.set_state("completed")
            elif i == step_index:
                circle.set_state("active")
            else:
                circle.set_state("pending")
        
        # Actualizar labels usando el nuevo sistema de colores
        primary = self.theme_manager.get_color('primary')
        text_primary = self.theme_manager.get_color('text.primary')
        text_secondary = self.theme_manager.get_color('text.secondary')
        
        for i, label in enumerate(self.step_labels):
            if i == step_index:
                label.setStyleSheet(f"color: {primary}; font-weight: 600;")
            elif i < step_index:
                label.setStyleSheet(f"color: {text_primary};")
            else:
                label.setStyleSheet(f"color: {text_secondary};")
    
    def mark_step_completed(self, step_index: int):
        """Marca un paso como completado"""
        if step_index < len(self.step_circles):
            self.step_circles[step_index].set_state("completed")
    
    def reset(self):
        """Reinicia todos los pasos a pendiente"""
        self.set_active_step(0)