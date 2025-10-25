from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QTextBrowser, 
    QGroupBox, QHBoxLayout, QTabWidget, QTextEdit, QFileDialog, QListWidget,
    QMessageBox
)
from PySide6.QtCore import Signal, Qt, QObject, QThread

# Importaciones de nuestro core
from app.core.gemini_client import GeminiClient
from app.core.disc_analyzer import recalculate_disc_profile

# --- Worker para análisis en segundo plano (MODIFICADO) ---
class AnalysisWorker(QObject):
    # LA SEÑAL AHORA TRANSPORTA EL RESULTADO DE LA API
    finished = Signal(int, str)  # Emite (input_id, gemini_response_json)
    error = Signal(str)

    def __init__(self, input_id, input_type, content):
        super().__init__()
        self.input_id = input_id
        self.input_type = input_type
        self.content = content
        # El worker ya no necesita acceso directo a la BD
        self.gemini_client = GeminiClient.get_instance()

    def run(self):
        """
        Ejecutado en el hilo secundario. SOLO llama a la API.
        """
        try:
            if self.input_type in ['text', 'html']:
                response, err = self.gemini_client.analyze_text_or_html(self.content)
            elif self.input_type == 'image':
                response, err = self.gemini_client.analyze_image(self.content)
            else:
                err = f"Unsupported input type: {self.input_type}"

            if err:
                self.error.emit(err)
                return

            # En lugar de escribir en la BD, emitimos el resultado
            self.finished.emit(self.input_id, response)
        except Exception as e:
            self.error.emit(f"An unexpected error occurred in the worker: {e}")

class CaseDetailWidget(QWidget):
    back_to_list_requested = Signal()
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.main_window = parent
        self.current_case_id = None
        self.selected_image_paths = []
        # Es mejor crear un nuevo QThread cada vez para evitar problemas de estado
        self.analysis_thread = None 
        self.init_ui()

    # --- on_analysis_finished (MODIFICADO) ---
    def on_analysis_finished(self, input_id, gemini_response):
        """
        Este slot se ejecuta en el HILO PRINCIPAL al recibir la señal 'finished'.
        Aquí es seguro interactuar con la BD y la UI.
        """
        print(f"Analysis for input {input_id} finished. Updating database in main thread.")

        # 1. Actualizar la base de datos (¡Ahora en el hilo correcto!)
        self.db_manager.update_input_with_gemini_response(input_id, gemini_response)

        # 2. Recalcular el perfil completo del caso
        recalculate_disc_profile(self.current_case_id)
        
        # 3. Informar al usuario y actualizar la UI
        QMessageBox.information(self, "Éxito", "Input analizado y guardado.\nPerfil DISC actualizado.")
        self.refresh_inputs_list()
        self.set_ui_enabled(True)
        self.main_window.statusBar().showMessage("Análisis completado. Perfil actualizado.", 5000)
        
        # Limpiar el hilo
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.quit()
            self.analysis_thread.wait()

    # --- run_analysis (MODIFICADO) ---
    def run_analysis(self, input_id, input_type, content):
        self.set_ui_enabled(False)
        self.main_window.statusBar().showMessage(f"Analizando input ({input_type.upper()})... por favor espere.")
        
        # Creamos un nuevo hilo y worker para cada análisis
        self.analysis_thread = QThread()
        self.worker = AnalysisWorker(input_id, input_type, content)
        self.worker.moveToThread(self.analysis_thread)

        self.analysis_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_analysis_finished) # Conectado al nuevo slot
        self.worker.error.connect(self.on_analysis_error)
        
        # Limpieza
        self.worker.finished.connect(self.analysis_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)

        self.analysis_thread.start()

    # --- El resto del archivo es idéntico al anterior, lo incluyo por completitud ---
    
    def on_analysis_error(self, error_message):
        QMessageBox.critical(self, "Error de Análisis", f"Ocurrió un error:\n{error_message}")
        self.refresh_inputs_list()
        self.set_ui_enabled(True)
        self.main_window.statusBar().showMessage("Error durante el análisis.", 5000)
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.quit()
            self.analysis_thread.wait()

    def set_ui_enabled(self, enabled: bool):
        self.save_text_button.setEnabled(enabled)
        self.save_images_button.setEnabled(enabled)
        self.save_html_button.setEnabled(enabled)

    def save_text_input(self):
        content = self.text_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Entrada Vacía", "El campo de texto no puede estar vacío.")
            return
        input_id = self.db_manager.create_input(self.current_case_id, 'text', content)
        if input_id:
            self.text_input.clear()
            self.run_analysis(input_id, 'text', content)

    def save_image_inputs(self):
        if not self.selected_image_paths:
            QMessageBox.warning(self, "Sin Selección", "Por favor, selecciona al menos una imagen.")
            return
        paths_to_process = self.selected_image_paths[:]
        self.selected_image_paths = []
        self.image_path_label.setText("Ninguna imagen seleccionada.")
        for path in paths_to_process:
            input_id = self.db_manager.create_input(self.current_case_id, 'image', path)
            if input_id:
                self.run_analysis(input_id, 'image', path)

    def save_html_input(self):
        content = self.html_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Entrada Vacía", "El campo de HTML no puede estar vacío.")
            return
        input_id = self.db_manager.create_input(self.current_case_id, 'html', content)
        if input_id:
            self.html_input.clear()
            self.run_analysis(input_id, 'html', content)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        back_button = QPushButton("← Volver a la lista")
        back_button.clicked.connect(self.back_to_list_requested.emit)
        top_layout.addWidget(back_button)
        top_layout.addStretch()
        details_group = QGroupBox("Detalles del Caso")
        form_layout = QFormLayout()
        self.name_label = QLabel("N/A")
        self.alias_label = QLabel("N/A")
        self.tags_label = QLabel("N/A")
        self.notes_browser = QTextBrowser(); self.notes_browser.setMaximumHeight(100)
        form_layout.addRow("Nombre:", self.name_label); form_layout.addRow("Alias:", self.alias_label); form_layout.addRow("Etiquetas:", self.tags_label); form_layout.addRow("Notas:", self.notes_browser)
        details_group.setLayout(form_layout)
        inputs_group = QGroupBox("Añadir y Ver Inputs")
        inputs_layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        text_tab = QWidget(); text_layout = QVBoxLayout(text_tab)
        self.text_input = QTextEdit(); self.text_input.setPlaceholderText("Pega o escribe aquí cualquier texto relevante...")
        self.save_text_button = QPushButton("Guardar y Analizar Texto"); self.save_text_button.clicked.connect(self.save_text_input)
        text_layout.addWidget(self.text_input); text_layout.addWidget(self.save_text_button, alignment=Qt.AlignmentFlag.AlignRight)
        image_tab = QWidget(); image_layout = QVBoxLayout(image_tab)
        select_images_button = QPushButton("Seleccionar Imágenes..."); select_images_button.clicked.connect(self.select_image_files)
        self.image_path_label = QLabel("Ninguna imagen seleccionada."); self.image_path_label.setWordWrap(True)
        self.save_images_button = QPushButton("Guardar y Analizar Imágenes"); self.save_images_button.clicked.connect(self.save_image_inputs)
        image_layout.addWidget(select_images_button); image_layout.addWidget(self.image_path_label); image_layout.addStretch(); image_layout.addWidget(self.save_images_button, alignment=Qt.AlignmentFlag.AlignRight)
        html_tab = QWidget(); html_layout = QVBoxLayout(html_tab)
        self.html_input = QTextEdit(); self.html_input.setPlaceholderText("Pega aquí el código fuente HTML...")
        self.save_html_button = QPushButton("Guardar y Analizar HTML"); self.save_html_button.clicked.connect(self.save_html_input)
        html_layout.addWidget(self.html_input); html_layout.addWidget(self.save_html_button, alignment=Qt.AlignmentFlag.AlignRight)
        self.tab_widget.addTab(text_tab, "Texto Plano"); self.tab_widget.addTab(image_tab, "Imágenes"); self.tab_widget.addTab(html_tab, "HTML")
        inputs_layout.addWidget(self.tab_widget); inputs_layout.addWidget(QLabel("Historial de Inputs:"))
        self.inputs_list_widget = QListWidget(); self.inputs_list_widget.setMaximumHeight(150)
        inputs_layout.addWidget(self.inputs_list_widget)
        inputs_group.setLayout(inputs_layout)
        disc_chart_placeholder = QGroupBox("Gráfico DISC")
        strategies_placeholder = QGroupBox("Estrategias")
        main_layout.addLayout(top_layout); main_layout.addWidget(details_group); main_layout.addWidget(inputs_group); main_layout.addWidget(disc_chart_placeholder); main_layout.addWidget(strategies_placeholder); main_layout.addStretch()

    def load_case_data(self, case_id: int):
        self.current_case_id = case_id; case_data = self.db_manager.get_case_by_id(case_id)
        if case_data: self.name_label.setText(case_data.get("name", "N/A")); self.alias_label.setText(case_data.get("alias", "N/A")); self.tags_label.setText(case_data.get("tags", "N/A")); self.notes_browser.setPlainText(case_data.get("notes", "N/A")); self.refresh_inputs_list()
        else: self.name_label.setText("Error: Caso no encontrado")

    def refresh_inputs_list(self):
        self.inputs_list_widget.clear();
        if self.current_case_id is None: return
        inputs = self.db_manager.get_inputs_for_case(self.current_case_id)
        for item in inputs: status = "✓ Analizado" if item['gemini_raw_response'] else "⌛ Pendiente"; content_preview = (item['content'][:60] + '...') if len(item['content']) > 60 else item['content']; display_text = f"[{item['created_at'][11:19]}] {item['input_type'].upper()} - {status}: {content_preview}"; self.inputs_list_widget.addItem(display_text)
            
    def select_image_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleccionar Imágenes", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if files: self.selected_image_paths = files; self.image_path_label.setText(f"{len(files)} imágenes seleccionadas:\n" + "\n".join(files))
        else: self.selected_image_paths = []; self.image_path_label.setText("Ninguna imagen seleccionada.")
