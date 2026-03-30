# -*- coding: utf-8 -*-
"""Módulo PFD Flowsheet — Diagrama de processo industrial."""
import sys
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QListWidget, QListWidgetItem, QSplitter, QGraphicsPathItem, QMenu,
    QListView, QLineEdit, QLabel, QStackedWidget, QTextEdit,
    QGraphicsRectItem, QInputDialog, QFileDialog, QSizePolicy, QGraphicsEllipseItem, QToolBox,
    QGraphicsSimpleTextItem
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QPalette, QCursor, QPolygonF,
    QFont, QFontMetrics, QIcon, QPixmap, QPainterPath, QDrag, QLinearGradient
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QMimeData, QByteArray, QDataStream,
    QIODevice, QSize, QPoint, QTimer, pyqtSignal, QObject, QSizeF
)

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.utils import (_export_view, C_BG_APP, C_BG_NODE,
    C_BORDER, C_TEXT_MAIN, C_TEXT, C_PLACEHOLDER, C_BTN_ADD, C_BTN_DEL, C_LINE,
    C_BTN_SIB, C_BG_ROOT, C_BORDER_ROOT, W5H2_TYPES)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar


def draw_equipment(painter, symbol_type, size, is_icon=False, theme=None):
    s = size / 2
    if theme is None:
        try: theme = T()
        except: theme = THEMES["dark"]
    pen_color = theme["text"] if is_icon else theme["accent"]
    _bg_node  = theme["bg_card"]

    default_pen = QPen(QColor(pen_color), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(default_pen)
    painter.setBrush(QBrush(QColor(_bg_node)))

    # Alias handling for backwards compatibility
    aliases = {
        "Bomba Centrífuga": "Bomba",
        "Trocador Casco-Tubo": "Trocador",
        "Reator CSTR": "Reator",
        "Tanque Aberto": "Tanque",
        "Vaso Vertical": "Vaso",
        "Tanque Misturador": "Misturador",
        "Secador Rotativo": "Secador",
        "Válvula Globo": "Válvula",
        "Separador Bifásico": "Separador Bifásico",
        "PSV (Alívio)": "PSV",
        "Válvula de Bloqueio": "Válvula",
        "Forno": "Forno", "Fornalha": "Forno", "Lavagem": "Lavadora",
        "Peneira": "Peneira", "Filtro": "Filtro"
    }
    st = aliases.get(symbol_type, symbol_type)

    if st == "Vaso":
        painter.drawRoundedRect(QRectF(-s*0.8, -s, s*1.6, s*2), s*0.6, s*0.6)
    elif st == "Vaso Horizontal":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3, s*1.2), s*0.6, s*0.6)
    elif st == "Tanque":
        painter.drawRect(QRectF(-s*0.8, -s*0.5, s*1.6, s*1.5))
        painter.drawArc(QRectF(-s*0.8, -s*1.0, s*1.6, s*1.0), 0, 180 * 16)
    elif st == "Tanque Fechado":
        painter.drawRect(QRectF(-s*0.8, -s, s*1.6, s*2))
        painter.drawArc(QRectF(-s*0.8, -s*1.2, s*1.6, s*0.8), 0, 180 * 16)
        painter.drawArc(QRectF(-s*0.8, s*0.6, s*1.6, s*0.8), 180*16, 180 * 16)
    elif st == "Esfera de Gás":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.6, s*0.8), QPointF(-s*0.8, s*1.5))
        painter.drawLine(QPointF(s*0.6, s*0.8), QPointF(s*0.8, s*1.5))
    elif st == "Silo":
        painter.drawRect(QRectF(-s*0.8, -s*1.5, s*1.6, s*2))
        poly = QPolygonF([QPointF(-s*0.8, s*0.5), QPointF(s*0.8, s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Separador Bifásico":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3.0, s*1.2), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.5, 0), QPointF(s*1.5, 0))
    elif st == "Separador Trifásico":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3.0, s*1.2), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.5, -s*0.2), QPointF(s*1.5, -s*0.2))
        painter.drawLine(QPointF(-s*1.5, s*0.2), QPointF(s*1.5, s*0.2))
    elif st == "Bomba":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        poly = QPolygonF([QPointF(-s*0.3, -s*0.7), QPointF(s*0.3, -s*0.7), QPointF(0, -s*1.4)])
        painter.setBrush(QBrush(QColor(pen_color)))
        painter.drawPolygon(poly)
    elif st == "Bomba Volumétrica":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawEllipse(QRectF(-s*0.4, -s*0.4, s*0.8, s*0.8))
        painter.drawLine(QPointF(0, -s*0.8), QPointF(0, s*0.8))
    elif st == "Compressor":
        poly = QPolygonF([QPointF(-s*0.8, s*0.8), QPointF(s*0.8, s*0.4),
                          QPointF(s*0.8, -s*0.4), QPointF(-s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif st == "Soprador":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.6, s*1.2, s*1.2))
        painter.drawRect(QRectF(s*0.2, -s*0.6, s*0.5, s*0.5))
    elif st == "Exaustor":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawLine(QPointF(-s*0.6, 0), QPointF(s*0.6, 0))
        painter.drawLine(QPointF(0, -s*0.6), QPointF(0, s*0.6))
    elif st == "Turbina":
        poly = QPolygonF([QPointF(s*0.8, s*0.8), QPointF(-s*0.8, s*0.4),
                          QPointF(-s*0.8, -s*0.4), QPointF(s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif st == "Ejetor":
        poly = QPolygonF([QPointF(-s, -s*0.3), QPointF(-s*0.2, -s*0.1), QPointF(s, -s*0.3),
                          QPointF(s, s*0.3), QPointF(-s*0.2, s*0.1), QPointF(-s, s*0.3)])
        painter.drawPolygon(poly)
    elif st == "Trocador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, 0), QPointF(-s*0.5, -s*0.5))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(0, s*0.5))
        painter.drawLine(QPointF(0, s*0.5), QPointF(s*0.5, -s*0.5))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(s, 0))
    elif st == "Trocador de Placas":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        for i in [-0.8, -0.4, 0, 0.4, 0.8]:
            painter.drawLine(QPointF(s*i, -s*0.8), QPointF(s*i, s*0.8))
    elif st == "Permutador a Ar":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(s*0.5, -s*1.2))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(-s*0.5, -s*1.2))
        painter.drawEllipse(QRectF(-s*0.6, -s*1.3, s*1.2, s*0.8))
    elif st == "Resfriador de Topo":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawLine(QPointF(-s*0.8, -s*0.8), QPointF(s*0.8, s*0.8))
    elif st == "Fornalha":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s*1.5))
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(0, -s*1.5), QPointF(s, -s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, s*0.2))
        painter.drawLine(QPointF(s*0.6, s*0.2), QPointF(-s*0.6, -0.2))
    elif st == "Caldeira":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.8, s*3.0, s*1.6), s*0.4, s*0.4)
        for i in [-0.4, 0, 0.4]:
            painter.drawLine(QPointF(-s*1.5, s*i), QPointF(s*1.5, s*i))
    elif st == "Torre de Resfriamento":
        poly = QPolygonF([QPointF(-s, s*1.5), QPointF(s, s*1.5),
                          QPointF(s*0.6, -s*1.2), QPointF(-s*0.6, -s*1.2)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.4, -s*1.4), QPointF(s*0.4, -s*1.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, -s*1.4))
    elif st == "Evaporador":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*1.5, s*1.2, s*2), s*0.6, s*0.6)
        painter.drawRect(QRectF(-s*0.6, s*0.5, s*1.2, s*1.0))
    elif st == "Aquecedor Elétrico":
        painter.drawRect(QRectF(-s*0.6, -s, s*1.2, s*2))
        poly = QPolygonF([QPointF(-s*0.4, 0), QPointF(0, -s*0.6), QPointF(s*0.4, 0), QPointF(0, s*0.6)])
        painter.drawPolygon(poly)
    elif st == "Reator":
        painter.drawRoundedRect(QRectF(-s*0.8, -s*1.2, s*1.6, s*2.4), s*0.4, s*0.4)
        painter.drawRect(QRectF(-s*0.25, -s*1.6, s*0.5, s*0.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, s*0.6))
        painter.drawLine(QPointF(-s*0.4, s*0.2), QPointF(s*0.4, s*0.6))
        painter.drawLine(QPointF(s*0.4, s*0.2), QPointF(-s*0.4, s*0.6))
    elif st == "Reator Tubular (PFR)":
        painter.drawRect(QRectF(-s*1.6, -s*0.5, s*3.2, s))
        for i in [-1.0, -0.5, 0, 0.5, 1.0]:
            painter.drawEllipse(QRectF(s*i - s*0.2, -s*0.4, s*0.4, s*0.8))
    elif st == "Misturador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.6, -s*0.6), QPointF(s*0.6, s*0.6))
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, -s*0.6))
    elif st == "Moinho":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawEllipse(QRectF(-s*0.8, -s*0.4, s*0.8, s*0.8))
        painter.drawEllipse(QRectF(0, -s*0.4, s*0.8, s*0.8))
    elif st == "Britador":
        poly = QPolygonF([QPointF(-s*0.8, -s), QPointF(s*0.8, -s), QPointF(s*0.4, s*0.8), QPointF(-s*0.4, s*0.8)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, -s), QPointF(0, s*0.8))
    elif st == "Torre de Destilação" or st == "Coluna de Absorção":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        for i in [-1.5, -0.75, 0, 0.75, 1.5]:
            painter.drawLine(QPointF(-s*0.6, s*i), QPointF(s*0.6, s*i))
        if st == "Coluna de Absorção":
            painter.drawLine(QPointF(-s*0.6, -s*1.5), QPointF(s*0.6, s*1.5))
            painter.drawLine(QPointF(s*0.6, -s*1.5), QPointF(-s*0.6, s*1.5))
    elif st == "Secador":
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.6, s*2.4, s*1.2), s*0.2, s*0.2)
        painter.drawLine(QPointF(-s*1.2, 0), QPointF(s*1.2, 0))
    elif st == "Filtro Prensa":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        for i in [-0.6, 0, 0.6]:
            painter.drawLine(QPointF(s*i, -s*0.8), QPointF(s*i, s*0.8))
    elif st == "Filtro Rotativo":
        painter.drawEllipse(QRectF(-s*1.2, -s*1.2, s*2.4, s*2.4))
        painter.drawRect(QRectF(-s*1.5, s*0.4, s*3, s*0.8))
    elif st == "Filtro":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s, 0), QPointF(s, 0))
        painter.setPen(default_pen)
    elif st == "Ciclone":
        painter.drawRect(QRectF(-s*0.6, -s*1.5, s*1.2, s))
        poly = QPolygonF([QPointF(-s*0.6, -s*0.5), QPointF(s*0.6, -s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Hidrociclone":
        painter.drawRect(QRectF(-s*0.4, -s*1.5, s*0.8, s))
        poly = QPolygonF([QPointF(-s*0.4, -s*0.5), QPointF(s*0.4, -s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Centrífuga":
        painter.drawEllipse(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        painter.drawLine(QPointF(-s*1.2, 0), QPointF(s*1.2, 0))
    elif st == "Clarificador":
        painter.drawRect(QRectF(-s*1.5, -s*0.5, s*3, s))
        poly = QPolygonF([QPointF(-s*1.5, s*0.5), QPointF(s*1.5, s*0.5), QPointF(s*0.5, s*1.5), QPointF(-s*0.5, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Peneira Vibratória" or st == "Peneira":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s*1.2, -s*0.4), QPointF(s*1.2, s*0.4))
        painter.setPen(default_pen)
    elif st == "Válvula":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
    elif st == "Válvula Borboleta":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawEllipse(QRectF(-s*0.2, -s*0.2, s*0.4, s*0.4))
    elif st == "Válvula de Controle":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, 0), QPointF(0, -s*1.2))
        painter.drawEllipse(QRectF(-s*0.6, -s*1.8, s*1.2, s*0.6))
    elif st == "Válvula de Retenção":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, -s*0.5), QPointF(0, s*0.5))
    elif st == "PSV":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, 0), QPointF(0, -s))
        painter.drawLine(QPointF(-s*0.4, -s*0.6), QPointF(s*0.4, -s*0.6))
    elif st == "Flare":
        painter.drawRect(QRectF(-s*0.2, -s*1.5, s*0.4, s*3))
        if not is_icon: painter.setBrush(QBrush(QColor("#E06622")))
        poly = QPolygonF([QPointF(-s*0.5, -s*1.5), QPointF(s*0.5, -s*1.5), QPointF(0, -s*2.5)])
        painter.drawPolygon(poly)
    elif st == "Chaminé":
        poly = QPolygonF([QPointF(-s*0.4, -s*2), QPointF(s*0.4, -s*2), QPointF(s*0.8, s*2), QPointF(-s*0.8, s*2)])
        painter.drawPolygon(poly)
    elif symbol_type == "Forno":
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6), 10, 10)
        # Serpentina/Fogo
        path = QPainterPath()
        path.moveTo(-s*0.8, s*0.2)
        for i in range(5):
            path.lineTo(-s*0.6 + i*s*0.3, -s*0.2 if i%2==0 else s*0.2)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        
    elif symbol_type == "Lavadora":
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.drawRoundedRect(QRectF(-s*0.7, -s*1.3, s*1.4, s*2.6), 15, 15)
        # Mesh interna
        for i in range(4):
            painter.drawLine(-s*0.5, -s + i*s*0.6, s*0.5, -s + i*s*0.6)
            
    elif symbol_type == "Box":
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.setPen(QPen(QColor(theme["accent"]), 2.5))
        # Desenha uma seta larga (bloco de entrada/saída)
        if symbol_type == "Entrada":
            poly = QPolygonF([QPointF(-s*1.5, -s*0.7), QPointF(s*0.8, -s*0.7), 
                              QPointF(s*1.5, 0), QPointF(s*0.8, s*0.7), QPointF(-s*1.5, s*0.7)])
        else: # Saída
            poly = QPolygonF([QPointF(-s*1.5, 0), QPointF(-s*0.8, -s*0.7), 
                              QPointF(s*1.5, -s*0.7), QPointF(s*1.5, s*0.7), QPointF(-s*0.8, s*0.7)])
        painter.drawPolygon(poly)
        # Texto interno (A ou B simplificado ou o próprio nome)
        font = painter.font()
        font.setBold(True); painter.setFont(font)
        txt = "A" if symbol_type == "Entrada" else "B"
        painter.drawText(QRectF(-s*1.5, -s*0.7, s*2.5, s*1.4), Qt.AlignCenter, txt)

    else:
        # Fallback para garantir visibilidade se o símbolo não for reconhecido
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.setPen(QPen(QColor(theme["accent"]), 2, Qt.DashLine))
        painter.drawRect(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, -s), QPointF(s, s))
        painter.drawLine(QPointF(-s, s), QPointF(s, -s))


class ConnectorPort(QGraphicsEllipseItem):
    def __init__(self, node, port_id):
        super().__init__(-5, -5, 10, 10, node)
        self.node = node
        self.port_id = port_id
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(0, 150, 255)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setZValue(10)
        self.setVisible(False)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(0, 255, 255)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 150, 255)))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            view = self.scene().views()[0]
            if hasattr(view, 'start_connection'):
                view.start_connection(self)
                event.accept()
                return
        super().mousePressEvent(event)

class Edge(QGraphicsPathItem):
    def __init__(self, source_node, dest_node, source_port="right", dest_port="left"):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.source_port = source_port
        self.dest_port = dest_port
        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        try: lc = T()["line"]
        except: lc = C_LINE
        pen = QPen(QColor(lc), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
        self.setZValue(-1)
        self.is_utility = False
        self.pipe_name = ""
        
        # Rótulo de texto para a tubulação
        self.label_item = QGraphicsSimpleTextItem(self)
        self.label_item.setBrush(QBrush(QColor("white")))
        self.label_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.label_item.setFlag(QGraphicsItem.ItemIgnoresTransformations, False)
        self.label_item.setVisible(False)
        
        self.adjust()

    def get_port_normal(self, port_id):
        # Normaliza IDs como 'left_1', 'left_2' para 'left'
        side = port_id.split('_')[0]
        if side == "top": return (0, -1)
        if side == "bottom": return (0, 1)
        if side == "left": return (-1, 0)
        if side == "right": return (1, 0)
        return (0, 0)

    def get_port_position(self, node, port_id):
        if hasattr(node, 'ports') and port_id in node.ports:
            return node.mapToScene(node.ports[port_id].pos())
        return node.sceneBoundingRect().center()

    def adjust(self):
        if not self.source_node or not self.dest_node:
            return
        
        p1 = self.get_port_position(self.source_node, self.source_port)
        p2 = self.get_port_position(self.dest_node, self.dest_port)
        
        path = QPainterPath()
        path.moveTo(p1)
        
        d1 = self.get_port_normal(self.source_port)
        d2 = self.get_port_normal(self.dest_port)
        
        p1_out = QPointF(p1.x() + d1[0]*20, p1.y() + d1[1]*20)
        p1_out = QPointF(p1.x() + d1[0]*25, p1.y() + d1[1]*25)
        p2_in  = QPointF(p2.x() + d2[0]*25, p2.y() + d2[1]*25)
        
        path.lineTo(p1_out)
        
        # Lógica ortogonal aprimorada:
        # Se a porta é vertical (top/bottom), queremos sair vertical e depois seguir horizontal
        if d1[1] != 0: # Vertical port
            # Vai até a altura de saída, depois horizontal até o X do destino, depois vertical final
            path.lineTo(p1_out.x(), p1_out.y()) # Já está lá
            path.lineTo(p2_in.x(), p1_out.y()) 
            path.lineTo(p2_in.x(), p2_in.y())
        else: # Horizontal port
            # Vai até o X de saída, depois vertical até o Y do destino, depois horizontal final
            path.lineTo(p1_out.x(), p2_in.y())
            path.lineTo(p2_in.x(), p2_in.y())
            
        path.lineTo(p2)
        self.setPath(path)
        
        # Posiciona o rótulo NO MEIO DE UM SEGMENTO DA TUBULAÇÃO (colado ao pipe)
        if self.pipe_name:
            # Estratégia: Sempre buscar o meio do componente horizontal mais estável
            if d1[1] != 0: # Porta Vertical (Top/Bottom)
                # Segmento horizontal entre o elbow (p1_out.x) e o destino (p2_in.x)
                mid_x = (p1_out.x() + p2_in.x()) / 2
                mid_y = p1_out.y()
            else: # Porta Horizontal (Left/Right)
                # Segmento horizontal principal. Queremos evitar o curto segmento de 25px inicial.
                dist_x = p2_in.x() - p1_out.x()
                if abs(dist_x) > 10:
                    mid_x = p1_out.x() + dist_x * 0.5
                else:
                    mid_x = p1_out.x()
                mid_y = p2_in.y()

            # Ajuste de margem: se estiver colado no X inicial (p1), empurra um pouco
            if abs(mid_x - p1.x()) < 40:
                mid_x = p1.x() + (40 if p2.x() > p1.x() else -40)

            # Posicionamento final: RENTE e ACIMA (não centralizado no Y)
            label_h = self.label_item.boundingRect().height()
            self.label_item.setPos(mid_x - self.label_item.boundingRect().width()/2, 
                                   mid_y - label_h - 2)
            self.label_item.setVisible(True)
        else:
            self.label_item.setVisible(False)
            
        # Calcula direção da seta no destino (p2)
        # O último segmento é de p2_in para p2
        # d2 é o vetor normal da porta de destino
        # Então a seta aponta de fora para dentro da porta
        dx = p2.x() - p2_in.x()
        dy = p2.y() - p2_in.y()
        self._arrow_dir = math.atan2(dy, dx)
        self._dest_pos = p2

    def contextMenuEvent(self, event):
        menu = QMenu()
        try:
            t = T()
            menu.setStyleSheet(f"""
                QMenu {{ background-color: {t["bg_card"]}; color: {t["text"]}; border: 1px solid {t["accent"]};
                        font-family: 'Segoe UI'; font-size: 12px; font-weight: bold; }}
                QMenu::item {{ padding: 7px 28px; }}
                QMenu::item:selected {{ background-color: {t["accent"]}; color: #FFFFFF; }}
            """)
        except Exception:
            pass
        del_action = menu.addAction("🗑 Excluir Tubulação")
        menu.addSeparator()
        name_action = menu.addAction("🏷️ Renomear Tubulação")
        dash_action = menu.addAction("🏁 Linha de Utilidade (Tracejada)")
        dash_action.setCheckable(True)
        dash_action.setChecked(self.is_utility)
        
        action = menu.exec_(event.screenPos())
        if action == del_action:
            if self in self.source_node.edges:
                self.source_node.edges.remove(self)
            if self in self.dest_node.edges:
                self.dest_node.edges.remove(self)
            self.scene().removeItem(self)
        elif action == name_action:
            from PyQt5.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(None, "Nomear Tubulação", "Digite o nome da seção:", QLineEdit.Normal, self.pipe_name)
            if ok:
                self.pipe_name = text
                self.label_item.setText(text)
                self.adjust()
        elif action == dash_action:
            self.is_utility = action.isChecked()
            self.adjust()

    def paint(self, painter, option, widget=None):
        try: t = T()
        except: t = {"line": C_LINE, "accent_bright": "#00E5FF"}
        
        lc = t.get("line", C_LINE)
        style = Qt.DashLine if self.is_utility else Qt.SolidLine
        
        if self.isSelected():
            painter.setPen(QPen(QColor(t.get("accent_bright", "#00E5FF")), 3, style, Qt.RoundCap, Qt.RoundJoin))
        else:
            painter.setPen(QPen(QColor(lc), 2.5, style, Qt.RoundCap, Qt.RoundJoin))
            
        # Desenha o caminho (a linha em si)
        painter.drawPath(self.path())
        
        # Desenha a seta no final
        if hasattr(self, '_dest_pos'):
            # Usa a mesma cor da linha
            color = QColor(lc) if not self.isSelected() else QColor(t.get("accent_bright", "#00E5FF"))
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            
            # Matriz de rotação para a seta (mais aguda/afiada como na imagem)
            arrow_size = 14
            angle = self._arrow_dir
            
            p1 = self._dest_pos
            # Três pontos do triângulo (mais 'sharp')
            pt1 = p1
            pt2 = QPointF(p1.x() - arrow_size * math.cos(angle - 0.3), 
                         p1.y() - arrow_size * math.sin(angle - 0.3))
            pt3 = QPointF(p1.x() - arrow_size * math.cos(angle + 0.3), 
                         p1.y() - arrow_size * math.sin(angle + 0.3))
            
            painter.drawPolygon(QPolygonF([pt1, pt2, pt3]))


class ProcessNode(QGraphicsItem):
    def __init__(self, symbol_type):
        super().__init__()
        self.symbol_type = symbol_type
        self.edges = []
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.SizeAllCursor))
        self.size = 50
        self.ports = {}
        for side in ["top", "bottom", "left", "right"]:
            for i in range(1, 4):
                pid = f"{side}_{i}"
                self.ports[pid] = ConnectorPort(self, pid)
                
        self.update_ports()
        self.setToolTip(f"Equipamento: {self.symbol_type}")

        # Label flutuante nativa para hover (Z-order alto)
        self._hover_bg = QGraphicsRectItem(self)
        self._hover_bg.setBrush(QBrush(QColor(20, 20, 20, 230)))
        self._hover_bg.setPen(QPen(QColor(T()["accent"]), 1))
        
        self._hover_text = QGraphicsSimpleTextItem(self.symbol_type, self)
        self._hover_text.setBrush(QBrush(QColor("white")))
        self._hover_text.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        # Ajusta tamanho do fundo baseado no texto
        tw = self._hover_text.boundingRect().width()
        th = self._hover_text.boundingRect().height()
        self._hover_bg.setRect(-5, -5, tw + 10, th + 10)
        
        # Posiciona acima do item
        r = self.boundingRect()
        ly = r.top() - th - 15
        lx = r.center().x() - tw/2
        self._hover_bg.setPos(lx, ly)
        self._hover_text.setPos(lx, ly)
        
        self._hover_bg.setZValue(100)
        self._hover_text.setZValue(101)
        self._hover_bg.setVisible(False)
        self._hover_text.setVisible(False)

        # Importante: rótulos não devem processar eventos de mouse nem hover
        self._hover_bg.setAcceptHoverEvents(False)
        self._hover_text.setAcceptHoverEvents(False)
        self._hover_bg.setAcceptedMouseButtons(Qt.NoButton)
        self._hover_text.setAcceptedMouseButtons(Qt.NoButton)

    def hoverEnterEvent(self, event):
        for port in self.ports.values():
            port.setVisible(True)
        # Força o recálculo da área para garantir que o rótulo seja redesenhado
        self.prepareGeometryChange()
        r = self.boundingRect()
        tw = self._hover_text.boundingRect().width()
        th = self._hover_text.boundingRect().height()
        lx, ly = r.center().x() - tw/2, r.top() + 5
        self._hover_bg.setPos(lx, ly)
        self._hover_text.setPos(lx, ly)
        self._hover_bg.setVisible(True)
        self._hover_text.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        for port in self.ports.values():
            port.setVisible(False)
        self._hover_bg.setVisible(False)
        self._hover_text.setVisible(False)
        super().hoverLeaveEvent(event)

    def update_ports(self):
        # As portas devem ficar rentes ao desenho do equipamento, ignorando a margem de hover
        s = self.size / 2
        st = self._get_alias()
        
        # Calcula o retângulo real do desenho (baseado na lógica do boundingRect)
        m = 0 # Sem margem interna para as portas
        if st in ["Torre de Destilação", "Coluna de Absorção", "Flare", "Chaminé"]:
            r = QRectF(-s*0.8 - m, -s*2.7 - m, s*1.6 + m*2, s*5.4 + m*2)
        elif st in ["Separador Bifásico", "Separador Trifásico", "Caldeira", "Vaso Horizontal", "Clarificador"]:
            r = QRectF(-s*1.8 - m, -s - m, self.size*1.8 + m*2, self.size + m*2)
        elif st in ["Secador", "Peneira", "Peneira Vibratória", "Filtro Prensa", "Trocador de Placas", "Filtro Rotativo"]:
            r = QRectF(-s*1.5 - m, -s*1.2 - m, self.size*1.5 + m*2, self.size*1.2 + m*2)
        elif st in ["Reator", "Reator Tubular (PFR)", "Ciclone", "Hidrociclone", "Torre de Resfriamento", "Silo"]:
            r = QRectF(-s*1.8 - m, -s*1.8 - m, self.size*1.8 + m*2, self.size*1.8 + m*2)
        elif st in ["Evaporador", "Aquecedor Elétrico"]:
            r = QRectF(-s - m, -s*1.6 - m, self.size + m*2, self.size*1.6 + m*2)
        else:
            r = QRectF(-s - m, -s - m, self.size + m*2, self.size + m*2)

        if hasattr(self, 'ports'):
            # Distribui 3 portas por lado (25%, 50%, 75%)
            for i in range(1, 4):
                frac = i * 0.25
                self.ports[f"top_{i}"].setPos(r.left() + r.width() * frac, r.top())
                self.ports[f"bottom_{i}"].setPos(r.left() + r.width() * frac, r.bottom())
                self.ports[f"left_{i}"].setPos(r.left(), r.top() + r.height() * frac)
                self.ports[f"right_{i}"].setPos(r.right(), r.top() + r.height() * frac)

    def _get_alias(self):
        aliases = {"Bomba Centrífuga": "Bomba", "Trocador Casco-Tubo": "Trocador",
                   "Reator CSTR": "Reator", "Tanque Aberto": "Tanque", "Vaso Vertical": "Vaso",
                   "Tanque Misturador": "Misturador", "Secador Rotativo": "Secador",
                   "Válvula Globo": "Válvula", "Válvula de Bloqueio": "Válvula", "PSV (Alívio)": "PSV"}
        return aliases.get(self.symbol_type, self.symbol_type)

    def add_edge(self, edge):
        self.edges.append(edge)

    def set_size(self, new_size):
        self.prepareGeometryChange()
        self.size = max(20, min(new_size, 300))
        self.update_ports()
        for edge in self.edges:
            edge.adjust()
        self.update()

    def delete_node(self):
        for edge in list(self.edges):
            self.scene().removeItem(edge)
            if edge in edge.source_node.edges:
                edge.source_node.edges.remove(edge)
            if edge in edge.dest_node.edges:
                edge.dest_node.edges.remove(edge)
        self.scene().removeItem(self)

    def contextMenuEvent(self, event):
        t_m = T()
        menu = QMenu()
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {t_m["bg_card"]}; color: {t_m["text"]}; border: 1px solid {t_m["accent"]};
                    font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }}
            QMenu::item {{ padding: 8px 30px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: #FFFFFF; }}
        """)
        grow_action   = menu.addAction("➕ Aumentar Tamanho")
        shrink_action = menu.addAction("➖ Diminuir Tamanho")
        menu.addSeparator()
        del_action = menu.addAction("🗑 Excluir Equipamento")
        action = menu.exec_(event.screenPos())
        if action == grow_action:
            self.set_size(self.size + 10)
        elif action == shrink_action:
            self.set_size(self.size - 10)
        elif action == del_action:
            self.delete_node()

    def get_closest_port(self, target_pos):
        rect = self.sceneBoundingRect()
        ports = [
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(),  rect.center().y()),
            QPointF(rect.right(), rect.center().y())
        ]
        return min(ports, key=lambda p: (p.x() - target_pos.x())**2 + (p.y() - target_pos.y())**2)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.adjust()
        return super().itemChange(change, value)

    def boundingRect(self):
        m = 5
        label_h = 40 
        s = self.size / 2
        st = self._get_alias()

        if st in ["Torre de Destilação", "Coluna de Absorção", "Flare", "Chaminé"]:
            base = QRectF(-s*0.8 - m, -s*2.7 - m, s*1.6 + m*2, s*5.4 + m*2)
        elif st in ["Separador Bifásico", "Separador Trifásico", "Caldeira", "Vaso Horizontal", "Clarificador"]:
            base = QRectF(-s*1.8 - m, -s - m, self.size*1.8 + m*2, self.size + m*2)
        elif st in ["Secador", "Peneira", "Peneira Vibratória", "Filtro Prensa", "Trocador de Placas", "Filtro Rotativo"]:
            base = QRectF(-s*1.5 - m, -s*1.2 - m, self.size*1.5 + m*2, self.size*1.2 + m*2)
        elif st in ["Reator", "Reator Tubular (PFR)", "Ciclone", "Hidrociclone", "Torre de Resfriamento", "Silo"]:
            base = QRectF(-s*1.8 - m, -s*1.8 - m, self.size*1.8 + m*2, self.size*1.8 + m*2)
        elif st in ["Evaporador", "Aquecedor Elétrico"]:
            base = QRectF(-s - m, -s*1.6 - m, self.size + m*2, self.size*1.6 + m*2)
        else:
            base = QRectF(-s - m, -s - m, self.size + m*2, self.size + m*2)
            
        return base.adjusted(-s*2, -label_h - 20, s*2, s*2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setPen(QPen(QColor(t["accent_bright"]), 2, Qt.DotLine))
            # Desenha apenas o retângulo do equipamento (sem o label_h de 40px)
            painter.drawRect(self.boundingRect().adjusted(0, 40, 0, 0))
        draw_equipment(painter, self.symbol_type, self.size, is_icon=False, theme=t)


class TerminalNode(QGraphicsItem):
    """Nodo especial para Entradas e Saídas dinâmicas."""
    def __init__(self, terminal_type="Entrada", terminal_name=""):
        super().__init__()
        self.terminal_type = terminal_type
        self.edges = []
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.size = 20
        # No terminal, teremos apenas uma porta que fica na base da seta
        self.ports = {"terminal": ConnectorPort(self, "terminal")}
        self.ports["terminal"].setPos(0, 0)
        
        # O Nome agora será exibido na tubulação (Edge), não no TerminalNode
        self.label = QGraphicsSimpleTextItem(self)
        self.label.setVisible(False)

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def get_port_normal(self, port_id):
        # Terminais não têm 'dobra' técnica, a linha vai direto ao ponto
        return (0, 0)

    def update_label_pos(self):
        pass # Rótulo agora fica na tubulação (Edge)

    def boundingRect(self):
        return QRectF(-10, -10, 20, 20)

    def paint(self, painter, option, widget=None):
        # O terminal agora é um âncora invisível. 
        # A seta é desenhada pela própria Edge (tubulação) no seu ponto final.
        pass

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for edge in self.edges:
                edge.adjust()
        return super().itemChange(change, value)

    def add_edge(self, edge):
        self.edges.append(edge)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.addAction("🗑 Excluir Terminal", self.delete_terminal)
        menu.exec_(event.screenPos())

    def delete_terminal(self):
        for edge in list(self.edges):
            self.scene().removeItem(edge)
            if edge in edge.source_node.edges: edge.source_node.edges.remove(edge)
            if edge in edge.dest_node.edges: edge.dest_node.edges.remove(edge)
        self.scene().removeItem(self)


class SymbolListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragOnly)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWordWrap(True)
        self.setGridSize(QSize(125, 110))
        self.setIconSize(QSize(40, 40))
        self.setSpacing(5)
        self.setTextElideMode(Qt.ElideNone)
        self.setAcceptDrops(False) # A lista não aceita drops, só exporta
        self.setMouseTracking(True)
        self.itemEntered.connect(self._on_item_entered)
        
        # Label de hover flutuante (estilo premium)
        self._hover_label = QLabel(self)
        self._hover_label.hide()
        self._hover_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._hover_label.setStyleSheet("""
            background-color: rgba(20, 20, 20, 230);
            color: white;
            border: 1px solid #00E5FF;
            border-radius: 4px;
            padding: 4px 8px;
            font-family: 'Segoe UI';
            font-size: 11px;
            font-weight: bold;
        """)

    def _on_item_entered(self, item):
        if item:
            self._hover_label.setText(item.text())
            self._hover_label.adjustSize()
            self._hover_label.show()
        else:
            self._hover_label.hide()

    def leaveEvent(self, event):
        self._hover_label.hide()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        item = self.itemAt(event.pos())
        if item:
            self._hover_label.setText(item.text())
            self._hover_label.adjustSize()
            # Posiciona um pouco à direita e abaixo do cursor
            self._hover_label.move(event.pos().x() + 15, event.pos().y() + 15)
            self._hover_label.show()
            self._hover_label.raise_()
        else:
            self._hover_label.hide()

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item: return
        item_data = QByteArray()
        data_stream = QDataStream(item_data, QIODevice.WriteOnly)
        data_stream.writeQString(item.text())
        mime_data = QMimeData()
        mime_data.setData('application/x-pfd-item', item_data)
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        pixmap = item.icon().pixmap(40, 40)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
        drag.exec_(Qt.CopyAction)

class SymbolPalette(QToolBox):
    def __init__(self):
        super().__init__()
        self._apply_palette_style()
        self.categories = {
            "Geral": [
                "Filtro", "Peneira", "Separador Bifásico"
            ],
            "Armazenamento": [
                "Tanque Aberto", "Tanque Fechado", "Vaso Vertical", "Vaso Horizontal",
                "Esfera de Gás", "Silo"
            ],
            "Movimentação": [
                "Bomba Centrífuga", "Bomba Volumétrica", "Compressor", "Soprador",
                "Exaustor", "Turbina", "Ejetor"
            ],
            "Troca Térmica": [
                "Trocador Casco-Tubo", "Trocador de Placas", "Forno",
                "Resfriador de Topo", "Fornalha", "Caldeira", "Torre de Resfriamento",
                "Evaporador", "Aquecedor Elétrico"
            ],
            "Transformação": [
                "Reator CSTR", "Reator Tubular (PFR)", "Lavagem", "Tanque Misturador", "Moinho", "Britador"
            ],
            "Separação": [
                "Torre de Destilação", "Coluna de Absorção", "Secador Rotativo",
                "Filtro Prensa", "Filtro Rotativo", "Filtro", "Ciclone", "Hidrociclone",
                "Centrífuga", "Clarificador", "Peneira Vibratória"
            ],
            "Controles": [
                "Válvula Globo", "Válvula Borboleta", "Válvula de Controle",
                "Válvula de Retenção", "PSV (Alívio)", "Flare", "Chaminé"
            ]
        }
        
        self.lists = []
        for cat, symbols in self.categories.items():
            list_widget = SymbolListWidget()
            self._apply_list_style(list_widget)
            for sym in symbols:
                item = QListWidgetItem(self._create_icon(sym), sym)
                item.setTextAlignment(Qt.AlignCenter)
                list_widget.addItem(item)
            self.addItem(list_widget, cat)
            self.lists.append(list_widget)

    def _apply_palette_style(self):
        try: t = T()
        except: return
        self.setStyleSheet(f"""
            QToolBox::tab {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border-bottom: 1px solid {t["accent_dim"]};
                font-family: 'Segoe UI', Arial; font-weight: bold; font-size: 13px;
                padding-left: 10px;
            }}
            QToolBox::tab:selected {{
                color: {t["accent"]}; border-bottom: 2px solid {t["accent"]};
            }}
        """)

    def _apply_list_style(self, list_widget):
        try: t = T()
        except: return
        list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {t["bg_app"]}; color: {t["text"]};
                border: none; outline: 0; padding: 6px;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                border-radius: 10px; padding: 10px;
                font-family: 'Segoe UI', Arial; font-size: 9px; font-weight: bold;
                color: {t["text"]};
            }}
            QListWidget::item:hover {{
                background-color: {t["bg_card"]};
                border: 1px solid {t["accent_dim"]};
            }}
            QListWidget::item:selected {{
                background-color: {t["accent"]};
                color: #FFFFFF; border: 1px solid {t["accent"]};
            }}
            QScrollBar:vertical {{ background: {t["bg_app"]}; width: 6px; }}
            QScrollBar::handle:vertical {{ background: {t["accent_dim"]}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

    def _create_icon(self, symbol_type):
        pixmap = QPixmap(50, 50)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(25, 25)
        sym_size = 28
        try: th = T()
        except: th = THEMES["dark"]
        draw_equipment(painter, symbol_type, size=sym_size, is_icon=True, theme=th)
        painter.end()
        return QIcon(pixmap)


class FlowsheetCanvas(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        try: self.setBackgroundBrush(QBrush(QColor(T()["bg_app"])))
        except: self.setBackgroundBrush(QBrush(QColor(C_BG_APP)))
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.mode = "Move"
        self.temp_line = None
        self.start_item = None
        self.zoom_level = 1.0
        
        # Debounce contra duplicados
        self._last_drop_time = 0
        self._last_drop_pos = QPoint(-999, -999)

    def zoom_in(self):  self._scale_view(1.15)
    def zoom_out(self): self._scale_view(1 / 1.15)
    def reset_zoom(self):
        self.resetTransform()
        self.zoom_level = 1.0

    def _scale_view(self, factor):
        novo_zoom = self.zoom_level * factor
        if novo_zoom < 0.2 or novo_zoom > 5.0:
            return
        self.zoom_level = novo_zoom
        self.scale(factor, factor)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('application/x-pfd-item'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('application/x-pfd-item'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat('application/x-pfd-item'):
            import time
            curr_time = time.time()
            if curr_time - self._last_drop_time < 0.1 and self._last_drop_pos == event.pos():
                return
            self._last_drop_time = curr_time
            self._last_drop_pos = event.pos()

            item_data = event.mimeData().data('application/x-pfd-item')
            stream = QDataStream(item_data, QIODevice.ReadOnly)
            symbol_type = stream.readQString()
            
            if not symbol_type: return

            node = ProcessNode(symbol_type)
            node.setZValue(10)
            
            pos = self.mapToScene(event.pos())
            node.setPos(pos)
            self.scene().addItem(node)
            
            # Notifica mudança total para garantir visibilidade
            self.scene().update()
            self.viewport().update()
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            items_under_click = self.items(event.pos())
            for item in items_under_click:
                if isinstance(item, ConnectorPort):
                    self.mode = "PortConnect"
                    self.start_port = item
                    pos = item.scenePos()
                    path = QPainterPath()
                    path.moveTo(pos)
                    try: lc = T()["accent"]
                    except: lc = C_LINE
                    self.temp_line = self.scene().addPath(path, QPen(QColor(lc), 2, Qt.DashLine))
                    # Mostrar todas as portas do Canvas
                    for gi in self.scene().items():
                        if isinstance(gi, ProcessNode):
                            for p in gi.ports.values():
                                p.setVisible(True)
                    event.accept()
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == "PortConnect" and self.temp_line:
            p1 = self.start_port.scenePos()
            p2 = self.mapToScene(event.pos())
            target_port = None
            
            items_under_mouse = self.items(event.pos())
            for item in items_under_mouse:
                if isinstance(item, ConnectorPort) and item.node != self.start_port.node:
                    target_port = item
                    p2 = item.scenePos()
                    break
                    
            path = QPainterPath()
            path.moveTo(p1)
            
            d1 = self.start_port.node.get_port_normal(self.start_port.port_id) if hasattr(self.start_port.node, 'get_port_normal') else (0,0)
            if d1 == (0,0):
                d1 = Edge(self.start_port.node, self.start_port.node).get_port_normal(self.start_port.port_id)
                
            p1_out = QPointF(p1.x() + d1[0]*20, p1.y() + d1[1]*20)
            
            if target_port:
                d2 = Edge(self.start_port.node, target_port.node).get_port_normal(target_port.port_id)
                p2_in = QPointF(p2.x() + d2[0]*20, p2.y() + d2[1]*20)
            else:
                p2_in = p2
                
            path.lineTo(p1_out)
            
            if d1[0] != 0:
                path.lineTo(p1_out.x(), p2_in.y())
                path.lineTo(p2_in.x(), p2_in.y())
            else:
                path.lineTo(p2_in.x(), p1_out.y())
                path.lineTo(p2_in.x(), p2_in.y())
                
            path.lineTo(p2)
            self.temp_line.setPath(path)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mode == "PortConnect" and self.temp_line:
            target_port = None
            items_under_release = self.items(event.pos())
            for item in items_under_release:
                if isinstance(item, ConnectorPort) and item.node != self.start_port.node:
                    target_port = item
                    break
                    
            if target_port:
                edge = Edge(self.start_port.node, target_port.node, self.start_port.port_id, target_port.port_id)
                self.scene().addItem(edge)
                # Opção de nomear tubulação ao conectar equipamentos de forma proativa
                if not isinstance(target_port.node, TerminalNode):
                    from PyQt5.QtWidgets import QInputDialog
                    name, ok = QInputDialog.getText(None, "Nomear Tubulação", "Opcional: Nome da seção:", QLineEdit.Normal, "")
                    if ok and name:
                        edge.pipe_name = name
                        edge.label_item.setText(name)
                        edge.adjust()
            else:
                # Arrastado para o vazio -> Cria Terminal
                from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox, QDialogButtonBox
                
                dialog = QDialog()
                dialog.setWindowTitle("Configurar Terminal de Fluxo")
                d_layout = QFormLayout(dialog)
                
                type_combo = QComboBox()
                type_combo.addItems(["Entrada", "Saída"])
                # Lógica inteligente: se começou numa porta 'left', sugere 'Entrada', se for 'right', 'Saída'
                if "left" in self.start_port.port_id: type_combo.setCurrentText("Entrada")
                elif "right" in self.start_port.port_id: type_combo.setCurrentText("Saída")
                
                name_edit = QLineEdit()
                name_edit.setPlaceholderText("Ex: Vapor, Feed A...")
                
                d_layout.addRow("Tipo:", type_combo)
                d_layout.addRow("Nome:", name_edit)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                d_layout.addRow(buttons)
                
                if dialog.exec_() == QDialog.Accepted:
                    t_type = type_combo.currentText()
                    t_name = name_edit.text() or t_type
                    
                    term = TerminalNode(t_type, t_name)
                    pos = self.mapToScene(event.pos())
                    term.setPos(pos)
                    self.scene().addItem(term)
                    
                    # Conecta automaticamente
                    if t_type == "Entrada":
                        edge = Edge(term, self.start_port.node, "terminal", self.start_port.port_id)
                    else:
                        edge = Edge(self.start_port.node, term, self.start_port.port_id, "terminal")
                    
                    # O NOME AGORA FICA NA TUBULAÇÃO (EDGE)
                    edge.pipe_name = t_name
                    edge.label_item.setText(t_name)
                    edge.adjust()
                    self.scene().addItem(edge)

            self.scene().removeItem(self.temp_line)
            self.temp_line = None
            self.start_port = None
            self.mode = "Move"
            
            # Ocultar as portas do Canvas após drag
            for gi in self.scene().items():
                if isinstance(gi, ProcessNode):
                    for p in gi.ports.values():
                        p.setVisible(False)
            return
        super().mouseReleaseEvent(event)


class FlowsheetWidget(QWidget):
    """Widget completo do Flowsheet (PFD) para embutir no app principal."""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar — todas as referências de cor são dinâmicas
        self._toolbar_fs = QWidget()
        self._toolbar_fs.setFixedHeight(50)
        tb_layout = QHBoxLayout(self._toolbar_fs)
        tb_layout.setContentsMargins(8, 0, 8, 0)
        tb_layout.setSpacing(6)
        toolbar = self._toolbar_fs

        self.btn_toggle_palette = QPushButton("☰ Equipamentos")
        self.btn_toggle_palette.setCheckable(True)
        self.btn_toggle_palette.setChecked(True)
        self.btn_toggle_palette.clicked.connect(self.toggle_palette)
        tb_layout.addWidget(self.btn_toggle_palette)

        sep0 = QWidget(); sep0.setFixedSize(2, 26)
        tb_layout.addWidget(sep0)

        self.btn_move = QPushButton("🖐 Mover")
        self.btn_conn = QPushButton("🔗 Tubulação")
        for btn in [self.btn_move, self.btn_conn]:
            btn.setCheckable(True)
            tb_layout.addWidget(btn)

        self.btn_move.setChecked(True)
        self.btn_move.clicked.connect(lambda: self.set_mode("Move"))
        self.btn_conn.clicked.connect(lambda: self.set_mode("Connect"))

        sep1 = QWidget(); sep1.setFixedSize(2, 26)
        tb_layout.addWidget(sep1)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)
        self.canvas = FlowsheetCanvas(self.scene)

        zoom_style = f"""
            QPushButton {{ background-color: {C_BG_APP}; color: {C_TEXT}; border: 1px solid #8B2020;
                           border-radius: 4px; padding: 4px 14px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {C_BORDER}; }}
        """
        for lbl, fn in [("🔍−", self.canvas.zoom_out), ("🔍+", self.canvas.zoom_in), ("⟳ 100%", self.canvas.reset_zoom)]:
            btn_zoom = QPushButton(lbl)
            btn_zoom.setStyleSheet(zoom_style)
            btn_zoom.clicked.connect(fn)
            tb_layout.addWidget(btn_zoom)

        tb_layout.addStretch()

        sep2 = QWidget(); sep2.setFixedSize(2, 26)
        tb_layout.addWidget(sep2)

        for lbl, fn in [("📄 PDF", lambda: self._export_scene("pdf")),
                         ("🖼 PNG", lambda: self._export_scene("png"))]:
            btn_exp = QPushButton(lbl)
            btn_exp.clicked.connect(fn)
            tb_layout.addWidget(btn_exp)

        self._tb_layout_fs = tb_layout
        layout.addWidget(toolbar)
        self.refresh_theme()

        self.splitter = QSplitter(Qt.Horizontal)
        self.palette_widget = SymbolPalette()
        self.splitter.addWidget(self.palette_widget)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([280, 1000])
        layout.addWidget(self.splitter)

        # Nome do Processo (Overlay no topo-esquerdo do Canvas)
        self.process_name_input = QLineEdit(self.canvas)
        self.process_name_input.setPlaceholderText("Nome do Processo...")
        self.process_name_input.setFixedWidth(250)
        self.process_name_input.move(15, 15)
        self.process_name_input.setObjectName("process_name")
        self._apply_process_name_style()

    def _apply_process_name_style(self):
        t = T()
        self.process_name_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(20, 20, 20, 180);
                color: {t["accent"]};
                border: 2px solid {t["accent_dim"]};
                border-radius: 8px;
                padding: 8px 12px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
            }}
            QLineEdit:focus {{
                border: 2px solid {t["accent"]};
                background-color: rgba(30, 30, 30, 220);
            }}
        """)

    def refresh_theme(self):
        t = T()
        self._toolbar_fs.setStyleSheet(f"""
            QWidget {{ background: {t["toolbar_bg"]}; border-bottom: 2px solid {t["accent"]}; }}
        """)
        btn_s = f"""
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["text"]};
                border: 1px solid {t["accent_dim"]}; border-radius: 5px;
                padding: 6px 14px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:checked {{ background: {t["accent"]}; color: white; border-color: {t["accent_bright"]}; }}
            QPushButton:hover {{ background: {t["toolbar_btn_h"]}; border-color: {t["accent"]}; color: {t["accent_bright"]}; }}
        """
        exp_s = f"""
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["accent"]};
                border: 1px solid {t["accent_dim"]}; border-radius: 5px;
                padding: 5px 12px; font-weight: bold; font-size: 11px;
            }}
            QPushButton:hover {{ background: {t["accent"]}; color: white; }}
        """
        for btn in [self.btn_toggle_palette, self.btn_move, self.btn_conn]:
            btn.setStyleSheet(btn_s)
        # Apply export style to last 2 buttons
        lay = self._tb_layout_fs
        for i in range(lay.count()):
            w = lay.itemAt(i).widget()
            if w and isinstance(w, QPushButton) and w not in [self.btn_toggle_palette, self.btn_move, self.btn_conn]:
                w.setStyleSheet(exp_s)
        # Refresh canvas bg
        try:
            self.canvas.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
        except Exception:
            pass
        if hasattr(self, 'palette_widget'):
            self.palette_widget._apply_palette_style()
        if hasattr(self, 'process_name_input'):
            self._apply_process_name_style()

    def toggle_palette(self):
        is_visible = self.btn_toggle_palette.isChecked()
        self.palette_widget.setVisible(is_visible)
        if is_visible:
            self.splitter.setSizes([240, self.width() - 240])

    def set_mode(self, mode):
        self.canvas.mode = mode
        if mode == "Move":
            self.btn_move.setChecked(True)
            self.btn_conn.setChecked(False)
            self.canvas.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self.btn_conn.setChecked(True)
            self.btn_move.setChecked(False)
            self.canvas.setCursor(QCursor(Qt.CrossCursor))

    def _export_scene(self, fmt):
        _export_view(self.canvas, fmt, self)




class _FlowsheetModule(QWidget):
    def __init__(self):
        super().__init__()
        self._inner = FlowsheetWidget()
        # Oculta toolbar interna original
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Clique com Botão Direito no fundo para adicionar Equipamentos PFD.\n"
            "• Para conectar tubulações, passe o mouse sobre o equipamento e arraste a tubulação "
            "a partir das Portas Azuis (Estilo DWSIM).\n"
            "• Clique com Botão Direito na tubulação inserida para excluir.\n"
            "• Use as ferramentas de Zoom no menu 'Exibir' ou atalhos Ctrl +/-."
        )
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(self._inner)





    def get_state(self):
        from proeng.modules.flowsheet import ProcessNode, Edge
        nodes = []
        node_ids = {}
        idx = 1
        for item in self._inner.scene.items():
            if isinstance(item, ProcessNode):
                nodes.append({
                    "id": idx,
                    "type": item.symbol_type,
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y(),
                    "size": item.size
                })
                node_ids[id(item)] = idx
                idx += 1
            elif isinstance(item, TerminalNode):
                nodes.append({
                    "id": idx,
                    "is_terminal": True,
                    "t_type": item.terminal_type,
                    "t_name": item.terminal_name,
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y()
                })
                node_ids[id(item)] = idx
                idx += 1
        
        edges = []
        for item in self._inner.scene.items():
            if isinstance(item, Edge):
                src_id = node_ids.get(id(item.source_node))
                tgt_id = node_ids.get(id(item.dest_node))
                if src_id and tgt_id:
                    edges.append({
                        "source": src_id,
                        "target": tgt_id,
                        "source_port": getattr(item, 'source_port', 'right'),
                        "dest_port": getattr(item, 'dest_port', 'left'),
                        "name": getattr(item, 'pipe_name', ""),
                        "is_utility": getattr(item, 'is_utility', False)
                    })
        return {
            "name": self._inner.process_name_input.text(),
            "nodes": nodes, 
            "edges": edges
        }

    def set_state(self, state):
        if not state: return
        self._inner.process_name_input.setText(state.get("name", ""))
        self._inner.scene.clear()
        
        from proeng.modules.flowsheet import ProcessNode, Edge
        node_map = {}
        for n_data in state.get("nodes", []):
            if n_data.get("is_terminal"):
                node = TerminalNode(n_data["t_type"], n_data["t_name"])
            else:
                node = ProcessNode(n_data["type"])
                node.set_size(n_data.get("size", 50))
            
            node.setPos(n_data["x"], n_data["y"])
            self._inner.scene.addItem(node)
            node_map[n_data["id"]] = node
            
            
        for e_data in state.get("edges", []):
            src = node_map.get(e_data["source"])
            tgt = node_map.get(e_data["target"])
            sp = e_data.get("source_port", "right_2") # Default para a porta central
            dp = e_data.get("dest_port", "left_2")
            
            # Backward compatibility: mapeia nomes antigos para os novos nomes centrais
            compat = {"top": "top_2", "bottom": "bottom_2", "left": "left_2", "right": "right_2"}
            sp = compat.get(sp, sp)
            dp = compat.get(dp, dp)
            
            if src and tgt:
                edge = Edge(src, tgt, sp, dp)
                edge.pipe_name = e_data.get("name", "")
                if edge.pipe_name:
                    edge.label_item.setText(edge.pipe_name)
                edge.is_utility = e_data.get("is_utility", False)
                edge.adjust()
                self._inner.scene.addItem(edge)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _FlowsheetModule()
    w.setWindowTitle("PFD Flowsheet — ProEng")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())

