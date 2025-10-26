from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QComboBox, 
    QDialogButtonBox, QGroupBox, QListWidget, QPushButton, QHBoxLayout,
    QMessageBox, QListWidgetItem
)
from PySide6.QtCore import QObject, Signal, QThread, Qt

from app.core.gemini_client import GeminiClient
from app.core.database_manager import DatabaseManager

class SuggestionWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, context):
        super().__init__()
        self.context = context
        self.gemini_client = GeminiClient.get_instance()

    def run(self):
        suggestion, err = self.gemini_client.suggest_strategy_improvement(self.context)
        if err:
            self.error.emit(err)
        else:
            self.finished.emit(suggestion)

class StrategyEditorDialog(QDialog):
    def __init__(self, db_manager, case_data, strategy_id=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.case_data = case_data
        self.strategy_id = strategy_id
        self.strategy_data = self.db_manager.conn.execute("SELECT * FROM strategies WHERE id = ?", (self.strategy_id,)).fetchone() if self.strategy_id else None

        self.setWindowTitle("Editar Estrategia" if self.strategy_id else "Nueva Estrategia")
        self.setMinimumSize(600, 700)

        # --- UI Elements ---
        main_layout = QVBoxLayout(self)
        form_group = QGroupBox("Detalles de la Estrategia")
        form_layout = QFormLayout(form_group)
        self.title_input = QLineEdit()
        self.objective_input = QTextEdit()
        self.objective_input.setMaximumHeight(80)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "paused", "completed"])
        form_layout.addRow("Título:", self.title_input)
        form_layout.addRow("Objetivo:", self.objective_input)
        form_layout.addRow("Descripción/Plan:", self.description_input)
        form_layout.addRow("Estado:", self.status_combo)

        events_group = QGroupBox("Historial y Notas")
        events_layout = QVBoxLayout(events_group)
        self.events_list = QListWidget()
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(60)
        self.note_input.setPlaceholderText("Añadir una nueva nota o resultado...")
        buttons_layout = QHBoxLayout()
        self.add_note_button = QPushButton("Añadir Nota")
        self.suggest_button = QPushButton("🤖 Sugerir Mejoras (IA)")
        buttons_layout.addWidget(self.add_note_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.suggest_button)
        events_layout.addWidget(self.events_list)
        events_layout.addWidget(self.note_input)
        events_layout.addLayout(buttons_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)

        main_layout.addWidget(form_group)
        main_layout.addWidget(events_group)
        main_layout.addWidget(button_box)

        # --- Connections ---
        self.add_note_button.clicked.connect(self.add_user_note)
        self.suggest_button.clicked.connect(self.get_suggestion)
        button_box.accepted.connect(self.save_strategy)
        button_box.rejected.connect(self.reject)

        if self.strategy_id:
            self.load_strategy_data()
        else: # Disable event tracking for new strategies until they are saved
            events_group.setEnabled(False)

    def load_strategy_data(self):
        if not self.strategy_data: return
        self.title_input.setText(self.strategy_data['title'])
        self.objective_input.setPlainText(self.strategy_data['objective'])
        self.description_input.setPlainText(self.strategy_data['description'])
        self.status_combo.setCurrentText(self.strategy_data['status'])
        self.refresh_events_list()

    def refresh_events_list(self):
        self.events_list.clear()
        events = self.db_manager.get_events_for_strategy(self.strategy_id)
        for event in events:
            item_text = f"[{event['created_at'][5:16]}] {event['content']}"
            item = QListWidgetItem(item_text)
            if event['event_type'] == 'gemini_suggestion':
                item.setForeground(Qt.GlobalColor.blue)
            self.events_list.addItem(item)
        self.events_list.scrollToBottom()

    def add_user_note(self):
        note_text = self.note_input.toPlainText().strip()
        if not note_text: return
        self.db_manager.create_strategy_event(self.strategy_id, 'user_note', note_text)
        self.note_input.clear()
        self.refresh_events_list()

    def get_suggestion(self):
        self.suggest_button.setEnabled(False)
        self.suggest_button.setText("Pensando...")

        # Build context for Gemini
        latest_eval = self.db_manager.get_latest_evaluation_for_case(self.case_data['id'])
        disc_profile = f"D={latest_eval['disc_d']:.0f}, I={latest_eval['disc_i']:.0f}, S={latest_eval['disc_s']:.0f}, C={latest_eval['disc_c']:.0f}" if latest_eval else "No disponible"
        
        events = self.db_manager.get_events_for_strategy(self.strategy_id)
        recent_history = "\n".join([f"- {e['content']}" for e in events[-3:]]) # Last 3 events

        context = f"""
        Perfil DISC de la Persona: {disc_profile}
        Objetivo de la Estrategia: {self.objective_input.toPlainText()}
        Resultados Recientes:
        {recent_history if recent_history else "Sin interacciones registradas."}
        """

        # Run in background thread
        self.thread = QThread()
        self.worker = SuggestionWorker(context)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_suggestion_finished)
        self.worker.error.connect(self.on_suggestion_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_suggestion_finished(self, suggestion):
        self.db_manager.create_strategy_event(self.strategy_id, 'gemini_suggestion', f"Sugerencia IA: {suggestion}")
        self.refresh_events_list()
        self.suggest_button.setEnabled(True)
        self.suggest_button.setText("🤖 Sugerir Mejoras (IA)")

    def on_suggestion_error(self, err_msg):
        QMessageBox.critical(self, "Error de IA", err_msg)
        self.suggest_button.setEnabled(True)
        self.suggest_button.setText("🤖 Sugerir Mejoras (IA)")

    def save_strategy(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Campo Requerido", "El título no puede estar vacío.")
            return

        if self.strategy_id:
            self.db_manager.update_strategy(
                self.strategy_id, title, self.objective_input.toPlainText(),
                self.description_input.toPlainText(), self.status_combo.currentText()
            )
        else:
            self.db_manager.create_strategy(
                self.case_data['id'], title, self.objective_input.toPlainText(),
                self.description_input.toPlainText(), self.status_combo.currentText()
            )
        self.accept()
