import sys
from PySide6.QtWidgets import QApplication

# Importamos nuestra ventana principal
from app.main_window import MainWindow

if __name__ == "__main__":
    # 1. Crear la instancia de la aplicación
    # QApplication es el objeto central que gestiona el flujo de la GUI
    app = QApplication(sys.argv)

    # 2. Crear y mostrar la ventana principal
    main_win = MainWindow()
    main_win.show()

    # 3. Iniciar el bucle de eventos de la aplicación
    # app.exec() inicia el bucle que procesa eventos (clics, teclado, etc.)
    # sys.exit asegura una salida limpia
    sys.exit(app.exec())
