from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QLabel, QMessageBox
)

class CaseFormDialog(QDialog):
    """
    Un diálogo para crear o editar un caso.
    Contiene un formulario con los campos necesarios.
    """
    def __init__(self, db_manager, case_data=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.case_data = case_data  # Si es None, es un caso nuevo. Si no, es para editar.

        self.setWindowTitle("Nuevo Caso" if self.case_data is None else "Editar Caso")
        self.setMinimumWidth(400)

        # Crear los widgets del formulario
        self.name_input = QLineEdit()
        self.alias_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Separados por comas (ej: ventas, prospecto)")
        self.notes_input = QTextEdit()
        self.notes_input.setAcceptRichText(False) # Forzar texto plano

        # Configurar el layout
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("Nombre (*):"), self.name_input)
        form_layout.addRow(QLabel("Alias:"), self.alias_input)
        form_layout.addRow(QLabel("Etiquetas:"), self.tags_input)
        form_layout.addRow(QLabel("Notas:"), self.notes_input)

        # Botones de Aceptar/Cancelar
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept) # Conecta el botón "Save" a la ranura accept
        button_box.rejected.connect(self.reject) # Conecta el botón "Cancel" a la ranura reject

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        
        # Si estamos editando, rellenar los campos con los datos existentes
        if self.case_data:
            self.populate_form()

    def populate_form(self):
        """Rellena el formulario con los datos de un caso existente."""
        self.name_input.setText(self.case_data.get("name", ""))
        self.alias_input.setText(self.case_data.get("alias", ""))
        self.tags_input.setText(self.case_data.get("tags", ""))
        self.notes_input.setPlainText(self.case_data.get("notes", ""))

    def accept(self):
        """
        Se ejecuta al hacer clic en 'Save'. Valida los datos y los guarda en la BD.
        """
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Campo Requerido", "El campo 'Nombre' no puede estar vacío.")
            return # No cierra el diálogo si la validación falla

        alias = self.alias_input.text().strip()
        tags = self.tags_input.text().strip()
        notes = self.notes_input.toPlainText().strip()

        if self.case_data is None:
            # Crear nuevo caso
            self.db_manager.create_case(name, alias, tags, notes)
        else:
            # Actualizar caso existente (no se usará en este paso, pero está listo)
            case_id = self.case_data['id']
            self.db_manager.update_case(case_id, name, alias, tags, notes)
        
        super().accept() # Cierra el diálogo y devuelve QDialog.Accepted
