from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, 
    QTextBrowser, QGroupBox, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt

class CaseDetailWidget(QWidget):
    """
    Widget para mostrar toda la información de un caso seleccionado,
    incluyendo datos básicos, inputs, gráfico DISC y estrategias.
    """
    # Señal que se emitirá cuando el usuario quiera volver a la lista de casos
    back_to_list_requested = Signal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_case_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Botón para volver ---
        top_layout = QHBoxLayout()
        back_button = QPushButton("← Volver a la lista")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        top_layout.addWidget(back_button)
        top_layout.addStretch() # Empuja el botón a la izquierda

        # --- Sección de Datos Básicos ---
        details_group = QGroupBox("Detalles del Caso")
        form_layout = QFormLayout()
        
        self.name_label = QLabel("N/A")
        self.alias_label = QLabel("N/A")
        self.tags_label = QLabel("N/A")
        self.notes_browser = QTextBrowser() # Usamos QTextBrowser para mostrar texto con saltos de línea
        self.notes_browser.setReadOnly(True)
        self.notes_browser.setMaximumHeight(100) # Limitar altura

        form_layout.addRow("Nombre:", self.name_label)
        form_layout.addRow("Alias:", self.alias_label)
        form_layout.addRow("Etiquetas:", self.tags_label)
        form_layout.addRow("Notas:", self.notes_browser)
        
        details_group.setLayout(form_layout)
        
        # --- Placeholders para futuras secciones ---
        disc_chart_placeholder = QGroupBox("Gráfico DISC")
        inputs_placeholder = QGroupBox("Inputs (Texto, Imágenes, HTML)")
        strategies_placeholder = QGroupBox("Estrategias")

        main_layout.addLayout(top_layout)
        main_layout.addWidget(details_group)
        main_layout.addWidget(disc_chart_placeholder)
        main_layout.addWidget(inputs_placeholder)
        main_layout.addWidget(strategies_placeholder)
        main_layout.addStretch() # Empuja todo hacia arriba

    def load_case_data(self, case_id: int):
        """Carga y muestra los datos del caso con el ID proporcionado."""
        self.current_case_id = case_id
        case_data = self.db_manager.get_case_by_id(case_id)
        
        if case_data:
            self.name_label.setText(case_data.get("name", "N/A"))
            self.alias_label.setText(case_data.get("alias", "N/A"))
            self.tags_label.setText(case_data.get("tags", "N/A"))
            self.notes_browser.setPlainText(case_data.get("notes", "N/A"))
        else:
            # Limpiar los campos si el caso no se encuentra
            self.name_label.setText("Error: Caso no encontrado")
            self.alias_label.setText("")
            self.tags_label.setText("")
            self.notes_browser.setPlainText("")
