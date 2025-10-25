from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QLabel, QMessageBox, QGroupBox
)

class SettingsDialog(QDialog):
    """
    Diálogo para configurar los parámetros de la aplicación,
    como la API Key de Gemini y los pesos de los inputs.
    """
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager

        self.setWindowTitle("Configuración")
        self.setMinimumWidth(500)

        # --- Widgets del formulario ---
        # Sección de Gemini
        self.gemini_api_key_input = QLineEdit()
        self.gemini_api_key_input.setEchoMode(QLineEdit.EchoMode.Password) # Ocultar la clave

        # Sección de Pesos
        self.weight_text_input = QLineEdit()
        self.weight_html_input = QLineEdit()
        self.weight_image_input = QLineEdit()

        # --- Layouts ---
        main_layout = QVBoxLayout(self)
        
        gemini_group = QGroupBox("Configuración de Gemini API")
        gemini_layout = QFormLayout(gemini_group)
        gemini_layout.addRow(QLabel("API Key:"), self.gemini_api_key_input)
        
        weights_group = QGroupBox("Ponderación de Inputs para Análisis DISC")
        weights_layout = QFormLayout(weights_group)
        weights_layout.addRow(QLabel("Peso para Texto:"), self.weight_text_input)
        weights_layout.addRow(QLabel("Peso para HTML:"), self.weight_html_input)
        weights_layout.addRow(QLabel("Peso para Imágenes:"), self.weight_image_input)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(gemini_group)
        main_layout.addWidget(weights_group)
        main_layout.addWidget(button_box)

        # Cargar los valores actuales de la base de datos
        self.load_settings()

    def load_settings(self):
        """Carga la configuración desde la BD y la muestra en los campos."""
        self.gemini_api_key_input.setText(self.db_manager.get_setting('gemini_api_key') or "")
        self.weight_text_input.setText(self.db_manager.get_setting('weight_text') or "0.2")
        self.weight_html_input.setText(self.db_manager.get_setting('weight_html') or "0.5")
        self.weight_image_input.setText(self.db_manager.get_setting('weight_image') or "0.3")

    def save_settings(self):
        """Guarda la configuración de los campos en la BD."""
        try:
            # Validar que los pesos sean números
            float(self.weight_text_input.text())
            float(self.weight_html_input.text())
            float(self.weight_image_input.text())
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Los pesos deben ser números válidos.")
            return

        # Guardar cada valor
        self.db_manager.update_setting('gemini_api_key', self.gemini_api_key_input.text())
        self.db_manager.update_setting('weight_text', self.weight_text_input.text())
        self.db_manager.update_setting('weight_html', self.weight_html_input.text())
        self.db_manager.update_setting('weight_image', self.weight_image_input.text())
        
        QMessageBox.information(self, "Éxito", "Configuración guardada correctamente.")
        self.accept()
