from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF, QFont
from PySide6.QtCore import Qt, QPointF

class DiscChartWidget(QWidget):
    """
    Un widget personalizado para dibujar un gráfico de radar del perfil DISC.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.disc_data = {'d': 0, 'i': 0, 's': 0, 'c': 0}

    def update_data(self, d: float, i: float, s: float, c: float):
        """Actualiza los datos del gráfico y solicita un redibujado."""
        self.disc_data = {'d': d, 'i': i, 's': s, 'c': c}
        self.update() # Llama a paintEvent

    def paintEvent(self, event):
        """El método principal de dibujado."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        center = QPointF(width / 2, height / 2)
        radius = min(width, height) * 0.35 # Radio principal del gráfico

        # --- 1. Dibujar el fondo del radar (ejes y niveles) ---
        self.draw_radar_background(painter, center, radius)

        # --- 2. Dibujar el polígono de datos ---
        self.draw_data_polygon(painter, center, radius)

        # --- 3. Dibujar las etiquetas (D, I, S, C) ---
        self.draw_labels(painter, center, radius)

        painter.end()

    def draw_radar_background(self, painter, center, radius):
        """Dibuja los ejes y las líneas de nivel."""
        pen = QPen(QColor(200, 200, 200), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Ejes
        painter.drawLine(center + QPointF(0, -radius), center + QPointF(0, radius))
        painter.drawLine(center + QPointF(-radius, 0), center + QPointF(radius, 0))

        # Niveles (cuadrados concéntricos rotados)
        for i in range(1, 5): # 25%, 50%, 75%, 100%
            level_radius = radius * (i / 4.0)
            points = [
                center + QPointF(0, -level_radius),
                center + QPointF(level_radius, 0),
                center + QPointF(0, level_radius),
                center + QPointF(-level_radius, 0),
            ]
            painter.drawPolygon(QPolygonF(points))

    def draw_data_polygon(self, painter, center, radius):
        """Dibuja el polígono que representa los valores DISC."""
        if not self.disc_data:
            return

        # Calcular las coordenadas de cada punto basado en su valor (0-100)
        d_point = center + QPointF(0, -radius * (self.disc_data['d'] / 100.0))
        i_point = center + QPointF(radius * (self.disc_data['i'] / 100.0), 0)
        s_point = center + QPointF(0, radius * (self.disc_data['s'] / 100.0))
        c_point = center + QPointF(-radius * (self.disc_data['c'] / 100.0), 0)
        
        polygon = QPolygonF([d_point, i_point, s_point, c_point])

        # Relleno semi-transparente
        brush = QBrush(QColor(85, 172, 238, 100), Qt.BrushStyle.SolidPattern)
        painter.setBrush(brush)
        # Borde sólido
        pen = QPen(QColor(85, 172, 238), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        painter.drawPolygon(polygon)

    def draw_labels(self, painter, center, radius):
        """Dibuja las etiquetas D, I, S, C en los ejes."""
        painter.setPen(QColor(50, 50, 50))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        
        label_offset = 20 # Distancia desde el borde del gráfico

        # Rectángulos de texto para alineación
        painter.drawText(QPointF(center.x() - 8, center.y() - radius - 5), "D")
        painter.drawText(QPointF(center.x() + radius + 5, center.y() + 8), "I")
        painter.drawText(QPointF(center.x() - 5, center.y() + radius + label_offset), "S")
        painter.drawText(QPointF(center.x() - radius - label_offset, center.y() + 8), "C")
