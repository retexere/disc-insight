import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QStackedWidget, QScrollArea
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from app.core.database_manager import DatabaseManager
from app.ui.case_list_widget import CaseListWidget
from app.ui.case_detail_widget import CaseDetailWidget
from app.ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager.get_instance()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("DISC Insight (PoC)")
        self.setGeometry(100, 100, 900, 700)
        self.create_menu()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Crear instancia de la lista de casos (sin cambios)
        self.case_list_widget = CaseListWidget(self.db_manager)
        
        # --- IMPLEMENTACIÓN DEL SCROLL AREA ---
        # 1. Crear la instancia de nuestro widget de detalle
        self.case_detail_widget = CaseDetailWidget(self.db_manager, self)

        # 2. Crear un QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True) # ¡Muy importante! Permite que el widget interior se redimensione
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Opcional: desactiva el scroll horizontal
        
        # 3. Asignar nuestro widget de detalle como el contenido del QScrollArea
        scroll_area.setWidget(self.case_detail_widget)
        # ----------------------------------------

        # Añadir las vistas al stacked widget
        self.stacked_widget.addWidget(self.case_list_widget)
        # En lugar de añadir el widget de detalle directamente, añadimos el scroll_area que lo contiene
        self.stacked_widget.addWidget(scroll_area) 

        # Conexiones (sin cambios)
        self.case_list_widget.case_selected.connect(self.show_case_detail)
        self.case_detail_widget.back_to_list_requested.connect(self.show_case_list)

        self.statusBar().showMessage("Aplicación lista. Mostrando lista de casos.")
        
        self.show_case_list()

    def show_case_detail(self, case_id: int):
        """Activa y muestra la vista de detalle para un caso específico."""
        self.case_detail_widget.load_case_data(case_id)
        # IMPORTANTE: al cambiar de vista, apuntamos al scroll_area, no al widget de detalle
        self.stacked_widget.setCurrentIndex(1) # O setCurrentWidget(scroll_area)
        self.statusBar().showMessage(f"Viendo detalles del caso ID: {case_id}")

    # ... (El resto de la clase MainWindow no necesita cambios) ...
    def create_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        settings_action = QAction("Configuración...", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.db_manager, self)
        dialog.exec()
        from app.core.gemini_client import GeminiClient
        GeminiClient.get_instance().configure_client()

    def show_case_list(self):
        self.stacked_widget.setCurrentIndex(0) # O setCurrentWidget(self.case_list_widget)
        self.statusBar().showMessage("Mostrando lista de casos.")

    def closeEvent(self, event):
        print("Cerrando la aplicación...")
        self.db_manager.close()
        event.accept()
