from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit, 
    QPushButton, QAbstractItemView, QDialog
)
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal
from typing import List, Dict, Any

# Importamos nuestro nuevo formulario
from app.ui.case_form_dialog import CaseFormDialog

# ... (El código de CaseTableModel no cambia, lo omito por brevedad) ...
class CaseTableModel(QAbstractTableModel):
    def __init__(self, data: List[Dict[str, Any]]):
        super().__init__()
        self._data = data
        self._headers = ["ID", "Nombre", "Alias", "Etiquetas", "Última Modificación"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        row_data = self._data[index.row()]
        column = index.column()
        if column == 0: return str(row_data.get("id", ""))
        if column == 1: return row_data.get("name", "")
        if column == 2: return row_data.get("alias", "")
        if column == 3: return row_data.get("tags", "")
        if column == 4: return row_data.get("updated_at", "")
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None

class CaseListWidget(QWidget):
    case_selected = Signal(int)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        self.init_ui()
        self.load_cases()

    def init_ui(self):
        """Configura el layout y los widgets internos."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        controls_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre, alias o etiqueta...")
        
        self.new_case_button = QPushButton("Nuevo Caso")
        # --- CONEXIÓN DE LA SEÑAL ---
        self.new_case_button.clicked.connect(self.open_new_case_dialog)
        
        # ---------------------------

        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(self.new_case_button)

        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setStretchLastSection(True)

        # Conectar la señal de doble clic de la tabla a nuestro manejador
        self.table_view.doubleClicked.connect(self.handle_row_double_clicked)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.table_view)

    def load_cases(self):
        """Obtiene los casos de la base de datos y actualiza la tabla."""
        print("Cargando casos desde la base de datos...")
        cases_data = self.db_manager.get_all_cases()
        
        self.model = CaseTableModel(cases_data)
        self.table_view.setModel(self.model)
        
        self.table_view.resizeColumnsToContents()
        print(f"Se cargaron {len(cases_data)} casos.")
        
    def open_new_case_dialog(self):
        """
        Abre el diálogo para crear un nuevo caso y actualiza la lista si se guarda.
        """
        # Creamos una instancia de nuestro diálogo, pasándole el gestor de BD
        dialog = CaseFormDialog(self.db_manager, parent=self)
        
        # .exec() abre el diálogo de forma modal (bloquea la ventana principal)
        # y devuelve un valor cuando se cierra.
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Si el usuario hizo clic en "Save" y los datos se guardaron,
            # recargamos la lista de casos para mostrar el nuevo registro.
            print("Nuevo caso guardado. Actualizando la lista...")
            self.load_cases()

    def handle_row_double_clicked(self, index: QModelIndex):
        """
        Se ejecuta cuando el usuario hace doble clic en una fila.
        Obtiene el ID del caso y emite la señal 'case_selected'.
        """
        if not index.isValid():
            return
            
        # El modelo interno tiene los datos originales
        row = index.row()
        case_data = self.model._data[row]
        case_id = case_data['id']
        
        print(f"Caso seleccionado con ID: {case_id}")
        self.case_selected.emit(case_id)
