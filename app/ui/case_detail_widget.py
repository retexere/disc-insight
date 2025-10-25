from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QTextBrowser, 
    QGroupBox, QHBoxLayout, QTabWidget, QTextEdit, QFileDialog, QListWidget,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt

class CaseDetailWidget(QWidget):
    back_to_list_requested = Signal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_case_id = None
        self.selected_image_paths = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- Botón para volver ---
        top_layout = QHBoxLayout()
        back_button = QPushButton("← Volver a la lista")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        top_layout.addWidget(back_button)
        top_layout.addStretch()

        # --- Sección de Datos Básicos ---
        details_group = QGroupBox("Detalles del Caso")
        form_layout = QFormLayout()
        self.name_label = QLabel("N/A")
        self.alias_label = QLabel("N/A")
        self.tags_label = QLabel("N/A")
        self.notes_browser = QTextBrowser()
        self.notes_browser.setMaximumHeight(100)
        form_layout.addRow("Nombre:", self.name_label)
        form_layout.addRow("Alias:", self.alias_label)
        form_layout.addRow("Etiquetas:", self.tags_label)
        form_layout.addRow("Notas:", self.notes_browser)
        details_group.setLayout(form_layout)
        
        # --- SECCIÓN DE INPUTS (LA PARTE NUEVA) ---
        inputs_group = QGroupBox("Añadir y Ver Inputs")
        inputs_layout = QVBoxLayout()

        # Pestañas para los diferentes tipos de input
        self.tab_widget = QTabWidget()
        
        # Pestaña de Texto
        text_tab = QWidget()
        text_layout = QVBoxLayout(text_tab)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Pega o escribe aquí cualquier texto relevante...")
        save_text_button = QPushButton("Guardar Texto")
        save_text_button.clicked.connect(self.save_text_input)
        text_layout.addWidget(self.text_input)
        text_layout.addWidget(save_text_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Pestaña de Imagen
        image_tab = QWidget()
        image_layout = QVBoxLayout(image_tab)
        select_images_button = QPushButton("Seleccionar Imágenes...")
        select_images_button.clicked.connect(self.select_image_files)
        self.image_path_label = QLabel("Ninguna imagen seleccionada.")
        self.image_path_label.setWordWrap(True)
        save_images_button = QPushButton("Guardar Imágenes")
        save_images_button.clicked.connect(self.save_image_inputs)
        image_layout.addWidget(select_images_button)
        image_layout.addWidget(self.image_path_label)
        image_layout.addStretch()
        image_layout.addWidget(save_images_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Pestaña de HTML
        html_tab = QWidget()
        html_layout = QVBoxLayout(html_tab)
        self.html_input = QTextEdit()
        self.html_input.setPlaceholderText("Pega aquí el código fuente HTML (ej: perfil de LinkedIn)...")
        save_html_button = QPushButton("Guardar HTML")
        save_html_button.clicked.connect(self.save_html_input)
        html_layout.addWidget(self.html_input)
        html_layout.addWidget(save_html_button, alignment=Qt.AlignmentFlag.AlignRight)

        self.tab_widget.addTab(text_tab, "Texto Plano")
        self.tab_widget.addTab(image_tab, "Imágenes")
        self.tab_widget.addTab(html_tab, "HTML")

        inputs_layout.addWidget(self.tab_widget)
        
        # Lista para mostrar el historial de inputs
        inputs_layout.addWidget(QLabel("Historial de Inputs:"))
        self.inputs_list_widget = QListWidget()
        self.inputs_list_widget.setMaximumHeight(150)
        inputs_layout.addWidget(self.inputs_list_widget)

        inputs_group.setLayout(inputs_layout)
        
        # --- Placeholders para el resto ---
        disc_chart_placeholder = QGroupBox("Gráfico DISC")
        strategies_placeholder = QGroupBox("Estrategias")

        # Añadir todo al layout principal
        main_layout.addLayout(top_layout)
        main_layout.addWidget(details_group)
        main_layout.addWidget(inputs_group) # <-- Añadimos el nuevo grupo
        main_layout.addWidget(disc_chart_placeholder)
        main_layout.addWidget(strategies_placeholder)
        main_layout.addStretch()

    def load_case_data(self, case_id: int):
        self.current_case_id = case_id
        case_data = self.db_manager.get_case_by_id(case_id)
        
        if case_data:
            self.name_label.setText(case_data.get("name", "N/A"))
            self.alias_label.setText(case_data.get("alias", "N/A"))
            self.tags_label.setText(case_data.get("tags", "N/A"))
            self.notes_browser.setPlainText(case_data.get("notes", "N/A"))
            self.refresh_inputs_list() # Cargar el historial de inputs
        else:
            # Limpiar
            self.name_label.setText("Error: Caso no encontrado")
            # ... (limpiar otros campos)

    def refresh_inputs_list(self):
        """Carga y muestra el historial de inputs para el caso actual."""
        self.inputs_list_widget.clear()
        if self.current_case_id is None:
            return
            
        inputs = self.db_manager.get_inputs_for_case(self.current_case_id)
        for item in inputs:
            # Mostramos un resumen del input
            content_preview = (item['content'][:70] + '...') if len(item['content']) > 70 else item['content']
            display_text = f"[{item['created_at']}] {item['input_type'].upper()}: {content_preview}"
            self.inputs_list_widget.addItem(display_text)

    def save_text_input(self):
        content = self.text_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Entrada Vacía", "El campo de texto no puede estar vacío.")
            return
        
        self.db_manager.create_input(self.current_case_id, 'text', content)
        QMessageBox.information(self, "Éxito", "Input de texto guardado correctamente.")
        self.text_input.clear()
        self.refresh_inputs_list()

    def select_image_files(self):
        # Permite seleccionar múltiples archivos de imagen
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Imágenes", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if files:
            self.selected_image_paths = files
            self.image_path_label.setText(f"{len(files)} imágenes seleccionadas:\n" + "\n".join(files))
        else:
            self.selected_image_paths = []
            self.image_path_label.setText("Ninguna imagen seleccionada.")
            
    def save_image_inputs(self):
        if not self.selected_image_paths:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona al menos una imagen.")
            return

        for path in self.selected_image_paths:
            self.db_manager.create_input(self.current_case_id, 'image', path)
            
        QMessageBox.information(self, "Éxito", f"{len(self.selected_image_paths)} inputs de imagen guardados.")
        self.selected_image_paths = []
        self.image_path_label.setText("Ninguna imagen seleccionada.")
        self.refresh_inputs_list()
        
    def save_html_input(self):
        content = self.html_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Entrada Vacía", "El campo de HTML no puede estar vacío.")
            return
            
        self.db_manager.create_input(self.current_case_id, 'html', content)
        QMessageBox.information(self, "Éxito", "Input de HTML guardado correctamente.")
        self.html_input.clear()
        self.refresh_inputs_list()
