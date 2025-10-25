import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QStackedWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from app.core.database_manager import DatabaseManager
from app.ui.case_list_widget import CaseListWidget
from app.ui.case_detail_widget import CaseDetailWidget
from app.ui.settings_dialog import SettingsDialog # Importar el nuevo diálogo

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager.get_instance()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("DISC Insight (PoC)")
        self.setGeometry(100, 100, 900, 700)
        self.create_menu()

        # --- GESTIÓN DE VISTAS CON QStackedWidget ---
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Crear instancias de nuestras dos vistas principales
        self.case_list_widget = CaseListWidget(self.db_manager)
        self.case_detail_widget = CaseDetailWidget(self.db_manager, self)

        # Añadir las vistas al stacked widget
        self.stacked_widget.addWidget(self.case_list_widget)
        self.stacked_widget.addWidget(self.case_detail_widget)

        # --- CONEXIÓN DE SEÑALES Y SLOTS ---
        # 1. Cuando se selecciona un caso en la lista, mostrar la vista de detalle
        self.case_list_widget.case_selected.connect(self.show_case_detail)
        
        # 2. Cuando se pide volver desde la vista de detalle, mostrar la lista
        self.case_detail_widget.back_to_list_requested.connect(self.show_case_list)

        self.statusBar().showMessage("Aplicación lista. Mostrando lista de casos.")
        
        # Iniciar mostrando la lista de casos
        self.show_case_list()

    def create_menu(self):
        """Crea la barra de menú principal de la aplicación."""
        menu_bar = self.menuBar()
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("&Archivo")
        
        settings_action = QAction("Configuración...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_settings_dialog(self):
        """Abre el diálogo de configuración."""
        dialog = SettingsDialog(self.db_manager, self)
        dialog.exec()
        # Después de cerrar el diálogo, es buena idea re-configurar el cliente Gemini
        # por si el usuario cambió la API Key.
        from app.core.gemini_client import GeminiClient
        GeminiClient.get_instance().configure_client()

    def show_case_list(self):
        """Activa y muestra la vista de la lista de casos."""
        self.stacked_widget.setCurrentWidget(self.case_list_widget)
        self.statusBar().showMessage("Mostrando lista de casos.")

    def show_case_detail(self, case_id: int):
        """Activa y muestra la vista de detalle para un caso específico."""
        self.case_detail_widget.load_case_data(case_id)
        self.stacked_widget.setCurrentWidget(self.case_detail_widget)
        self.statusBar().showMessage(f"Viendo detalles del caso ID: {case_id}")

    def closeEvent(self, event):
        print("Cerrando la aplicación...")
        self.db_manager.close()
        event.accept()
