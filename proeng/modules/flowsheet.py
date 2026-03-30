# -*- coding: utf-8 -*-
"""Módulo PFD Flowsheet — Diagrama de processo industrial."""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QListWidget, QListWidgetItem, QSplitter, QGraphicsPathItem, QMenu,
    QListView, QLineEdit, QLabel, QStackedWidget, QTextEdit,
    QGraphicsRectItem, QInputDialog, QFileDialog, QSizePolicy
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

    if symbol_type == "Vaso":
        painter.drawRoundedRect(QRectF(-s*0.8, -s, s*1.6, s*2), s*0.6, s*0.6)
    elif symbol_type == "Tanque":
        painter.drawRect(QRectF(-s*0.8, -s*0.5, s*1.6, s*1.5))
        painter.drawArc(QRectF(-s*0.8, -s*1.0, s*1.6, s*1.0), 0, 180 * 16)
    elif symbol_type == "Bomba":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        poly = QPolygonF([QPointF(-s*0.3, -s*0.7), QPointF(s*0.3, -s*0.7), QPointF(0, -s*1.4)])
        painter.setBrush(QBrush(QColor(pen_color)))
        painter.drawPolygon(poly)
    elif symbol_type == "Compressor":
        poly = QPolygonF([QPointF(-s*0.8, s*0.8), QPointF(s*0.8, s*0.4),
                          QPointF(s*0.8, -s*0.4), QPointF(-s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif symbol_type == "Soprador":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.6, s*1.2, s*1.2))
        painter.drawRect(QRectF(s*0.2, -s*0.6, s*0.5, s*0.5))
    elif symbol_type == "Turbina":
        poly = QPolygonF([QPointF(s*0.8, s*0.8), QPointF(-s*0.8, s*0.4),
                          QPointF(-s*0.8, -s*0.4), QPointF(s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif symbol_type == "Trocador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, 0), QPointF(-s*0.5, -s*0.5))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(0, s*0.5))
        painter.drawLine(QPointF(0, s*0.5), QPointF(s*0.5, -s*0.5))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(s, 0))
    elif symbol_type == "Fornalha":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s*1.5))
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(0, -s*1.5), QPointF(s, -s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, s*0.2))
        painter.drawLine(QPointF(s*0.6, s*0.2), QPointF(-s*0.6, -0.2))
    elif symbol_type == "Reator":
        painter.drawRoundedRect(QRectF(-s*0.8, -s*1.2, s*1.6, s*2.4), s*0.4, s*0.4)
        painter.drawRect(QRectF(-s*0.25, -s*1.6, s*0.5, s*0.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, s*0.6))
        painter.drawLine(QPointF(-s*0.4, s*0.2), QPointF(s*0.4, s*0.6))
        painter.drawLine(QPointF(s*0.4, s*0.2), QPointF(-s*0.4, s*0.6))
    elif symbol_type == "Misturador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.6, -s*0.6), QPointF(s*0.6, s*0.6))
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, -s*0.6))
    elif symbol_type == "Filtro":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s, 0), QPointF(s, 0))
        painter.setPen(default_pen)
    elif symbol_type == "Ciclone":
        painter.drawRect(QRectF(-s*0.6, -s*1.5, s*1.2, s))
        poly = QPolygonF([QPointF(-s*0.6, -s*0.5), QPointF(s*0.6, -s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif symbol_type == "Torre de Destilação":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        for i in [-1.5, -0.75, 0, 0.75, 1.5]:
            painter.drawLine(QPointF(-s*0.6, s*i), QPointF(s*0.6, s*i))
    elif symbol_type == "Torre de Resfriamento":
        poly = QPolygonF([QPointF(-s, s*1.5), QPointF(s, s*1.5),
                          QPointF(s*0.6, -s*1.2), QPointF(-s*0.6, -s*1.2)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.4, -s*1.4), QPointF(s*0.4, -s*1.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, -s*1.4))
    elif symbol_type == "Flare":
        painter.drawRect(QRectF(-s*0.2, -s*1.5, s*0.4, s*3))
        if not is_icon:
            painter.setBrush(QBrush(QColor("#E06622")))
        poly = QPolygonF([QPointF(-s*0.5, -s*1.5), QPointF(s*0.5, -s*1.5), QPointF(0, -s*2.5)])
        painter.drawPolygon(poly)
    elif symbol_type == "Válvula":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
    elif symbol_type == "Secador":
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.6, s*2.4, s*1.2), s*0.2, s*0.2)
        painter.drawLine(QPointF(-s*1.2, 0), QPointF(s*1.2, 0))
    elif symbol_type == "Evaporador":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*1.5, s*1.2, s*2), s*0.6, s*0.6)
        painter.drawRect(QRectF(-s*0.6, s*0.5, s*1.2, s*1.0))
    elif symbol_type == "Permutador a Ar":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(s*0.5, -s*1.2))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(-s*0.5, -s*1.2))
        painter.drawEllipse(QRectF(-s*0.6, -s*1.3, s*1.2, s*0.8))
    elif symbol_type == "Separador Bifásico":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3.0, s*1.2), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.5, 0), QPointF(s*1.5, 0))
    elif symbol_type == "Ejetor":
        poly = QPolygonF([QPointF(-s, -s*0.3), QPointF(-s*0.2, -s*0.1), QPointF(s, -s*0.3),
                          QPointF(s, s*0.3), QPointF(-s*0.2, s*0.1), QPointF(-s, s*0.3)])
        painter.drawPolygon(poly)
    elif symbol_type == "Moinho":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawEllipse(QRectF(-s*0.8, -s*0.4, s*0.8, s*0.8))
        painter.drawEllipse(QRectF(0, -s*0.4, s*0.8, s*0.8))
    elif symbol_type == "Peneira":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s*1.2, -s*0.4), QPointF(s*1.2, s*0.4))
        painter.setPen(default_pen)
    elif symbol_type == "Caldeira":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.8, s*3.0, s*1.6), s*0.4, s*0.4)
        for i in [-0.4, 0, 0.4]:
            painter.drawLine(QPointF(-s*1.5, s*i), QPointF(s*1.5, s*i))
    elif symbol_type == "Coluna de Absorção":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        painter.drawLine(QPointF(-s*0.6, -s*1.5), QPointF(s*0.6, s*1.5))
        painter.drawLine(QPointF(s*0.6, -s*1.5), QPointF(-s*0.6, s*1.5))
    elif symbol_type == "Filtro Prensa":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        for i in [-0.6, 0, 0.6]:
            painter.drawLine(QPointF(s*i, -s*0.8), QPointF(s*i, s*0.8))


class Edge(QGraphicsPathItem):
    def __init__(self, source_node, dest_node):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        try: lc = T()["line"]
        except: lc = C_LINE
        pen = QPen(QColor(lc), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
        self.setZValue(-1)
        self.adjust()

    def adjust(self):
        if not self.source_node or not self.dest_node:
            return
        c1 = self.source_node.pos()
        c2 = self.dest_node.pos()
        p1 = self.source_node.get_closest_port(c2)
        p2 = self.dest_node.get_closest_port(c1)
        path = QPainterPath()
        path.moveTo(p1)
        rect1 = self.source_node.sceneBoundingRect()
        is_p1_horizontal = (abs(p1.y() - rect1.center().y()) < 5)
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2
        if is_p1_horizontal:
            path.lineTo(mid_x, p1.y())
            path.lineTo(mid_x, p2.y())
        else:
            path.lineTo(p1.x(), mid_y)
            path.lineTo(p2.x(), mid_y)
        path.lineTo(p2)
        self.setPath(path)

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
        action = menu.exec_(event.screenPos())
        if action == del_action:
            if self in self.source_node.edges:
                self.source_node.edges.remove(self)
            if self in self.dest_node.edges:
                self.dest_node.edges.remove(self)
            self.scene().removeItem(self)

    def paint(self, painter, option, widget=None):
        try: lc = T()["line"]
        except: lc = C_LINE
        if self.isSelected():
            painter.setPen(QPen(QColor(T()["accent_bright"]), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        else:
            painter.setPen(QPen(QColor(lc), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        super().paint(painter, option, widget)


class ProcessNode(QGraphicsItem):
    def __init__(self, symbol_type):
        super().__init__()
        self.symbol_type = symbol_type
        self.edges = []
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(QCursor(Qt.SizeAllCursor))
        self.size = 50

    def add_edge(self, edge):
        self.edges.append(edge)

    def set_size(self, new_size):
        self.prepareGeometryChange()
        self.size = max(20, min(new_size, 300))
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
        s = self.size / 2
        if self.symbol_type in ["Torre de Destilação", "Coluna de Absorção"]:
            return QRectF(-s - m, -s*2.5 - m, self.size + m*2, self.size*2.5 + m*2)
        elif self.symbol_type in ["Separador Bifásico", "Caldeira"]:
            return QRectF(-s*1.5 - m, -s - m, self.size*1.5 + m*2, self.size + m*2)
        elif self.symbol_type in ["Secador", "Peneira", "Filtro Prensa"]:
            return QRectF(-s*1.2 - m, -s - m, self.size*1.2 + m*2, self.size + m*2)
        elif self.symbol_type == "Reator":
            return QRectF(-s - m, -s*1.6 - m, self.size + m*2, self.size*1.4 + m*2)
        elif self.symbol_type == "Fornalha":
            return QRectF(-s - m, -s*1.5 - m, self.size + m*2, self.size*1.25 + m*2)
        elif self.symbol_type == "Ciclone":
            return QRectF(-s - m, -s*1.5 - m, self.size + m*2, self.size*1.5 + m*2)
        elif self.symbol_type == "Torre de Resfriamento":
            return QRectF(-s - m, -s*1.7 - m, self.size + m*2, self.size*1.6 + m*2)
        elif self.symbol_type == "Flare":
            return QRectF(-s - m, -s*2.5 - m, self.size + m*2, self.size*2 + m*2)
        return QRectF(-s - m, -s - m, self.size + m*2, self.size + m*2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setPen(QPen(QColor(t["accent_bright"]), 2, Qt.DotLine))
            painter.drawRect(self.boundingRect())
        draw_equipment(painter, self.symbol_type, self.size, is_icon=False, theme=t)


class SymbolPalette(QListWidget):
    def __init__(self):
        super().__init__()
        self.setDragDropMode(QListWidget.DragOnly)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setWordWrap(True)
        self.setGridSize(QSize(90, 80))
        self.setIconSize(QSize(36, 36))
        self.setSpacing(4)
        self._apply_palette_style()

    def _apply_palette_style(self):
        try: t = T()
        except: return
        hover_bg = QColor(t["bg_card2"]).name()
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {t["bg_app"]}; color: {t["text"]};
                border: none; outline: 0; padding: 8px;
            }}
            QListWidget::item {{
                background-color: {t["bg_card"]};
                border: 1px solid {t["accent_dim"]};
                border-radius: 6px; padding: 4px;
                font-family: 'Segoe UI', Arial; font-size: 10px; font-weight: bold;
                color: {t["text"]};
            }}
            QListWidget::item:hover {{
                background-color: {t["bg_card2"]};
                border: 1px solid {t["accent"]};
            }}
            QListWidget::item:selected {{
                background-color: {t["accent"]};
                color: #FFFFFF; border: 1px solid {t["accent_bright"]};
            }}
            QScrollBar:vertical {{ background: {t["bg_app"]}; width: 6px; }}
            QScrollBar::handle:vertical {{ background: {t["accent_dim"]}; border-radius: 3px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)
        symbols = [
            "Vaso", "Tanque", "Separador Bifásico", "Bomba", "Compressor", "Soprador", "Turbina",
            "Ejetor", "Trocador", "Permutador a Ar", "Fornalha", "Caldeira", "Reator", "Misturador",
            "Moinho", "Filtro", "Filtro Prensa", "Peneira", "Ciclone", "Secador", "Evaporador",
            "Torre de Destilação", "Coluna de Absorção", "Torre de Resfriamento", "Flare", "Válvula"
        ]
        for sym in symbols:
            item = QListWidgetItem(self._create_icon(sym), sym)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            self.addItem(item)

    def _create_icon(self, symbol_type):
        pixmap = QPixmap(50, 50)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(25, 25)
        sym_size = 28
        if symbol_type in ["Torre de Destilação", "Coluna de Absorção", "Flare"]:
            sym_size = 14
        elif symbol_type in ["Reator", "Fornalha", "Ciclone", "Torre de Resfriamento",
                              "Evaporador", "Separador Bifásico", "Caldeira"]:
            sym_size = 18
        try: th = T()
        except: th = THEMES["dark"]
        draw_equipment(painter, symbol_type, size=sym_size, is_icon=True, theme=th)
        painter.end()
        return QIcon(pixmap)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return
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


class FlowsheetCanvas(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.Antialiasing)
        try: self.setBackgroundBrush(QBrush(QColor(T()["bg_app"])))
        except: self.setBackgroundBrush(QBrush(QColor(C_BG_APP)))
        self.setAcceptDrops(True)
        self.mode = "Move"
        self.temp_line = None
        self.start_item = None
        self.zoom_level = 1.0

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
            item_data = event.mimeData().data('application/x-pfd-item')
            stream = QDataStream(item_data, QIODevice.ReadOnly)
            symbol_type = stream.readQString()
            node = ProcessNode(symbol_type)
            pos = self.mapToScene(event.pos())
            node.setPos(pos)
            self.scene().addItem(node)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        if self.mode == "Connect" and event.button() == Qt.LeftButton:
            items_under_click = self.items(event.pos())
            for item in items_under_click:
                if isinstance(item, ProcessNode):
                    self.start_item = item
                    pos = self.mapToScene(event.pos())
                    path = QPainterPath()
                    path.moveTo(pos)
                    try: lc = T()["accent"]
                    except: lc = C_LINE
                    self.temp_line = self.scene().addPath(path, QPen(QColor(lc), 2, Qt.DashLine))
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == "Connect" and self.temp_line:
            target_node = None
            items_under_mouse = self.items(event.pos())
            for item in items_under_mouse:
                if isinstance(item, ProcessNode) and item != self.start_item:
                    target_node = item
                    break
            p2_raw = self.mapToScene(event.pos())
            if target_node:
                c2 = target_node.sceneBoundingRect().center()
                p2 = target_node.get_closest_port(self.start_item.sceneBoundingRect().center())
            else:
                c2, p2 = p2_raw, p2_raw
            p1 = self.start_item.get_closest_port(c2)
            path = QPainterPath()
            path.moveTo(p1)
            rect1 = self.start_item.sceneBoundingRect()
            is_p1_horizontal = (abs(p1.y() - rect1.center().y()) < 5)
            mid_x = (p1.x() + p2.x()) / 2
            mid_y = (p1.y() + p2.y()) / 2
            if is_p1_horizontal:
                path.lineTo(mid_x, p1.y())
                path.lineTo(mid_x, p2.y())
            else:
                path.lineTo(p1.x(), mid_y)
                path.lineTo(p2.x(), mid_y)
            path.lineTo(p2)
            self.temp_line.setPath(path)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mode == "Connect" and self.temp_line:
            target_node = None
            items_under_release = self.items(event.pos())
            for item in items_under_release:
                if isinstance(item, ProcessNode) and item != self.start_item:
                    target_node = item
                    break
            if target_node:
                edge = Edge(self.start_item, target_node)
                self.scene().addItem(edge)
            self.scene().removeItem(self.temp_line)
            self.temp_line = None
            self.start_item = None
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
        self.splitter.setSizes([240, 1060])
        layout.addWidget(self.splitter)

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
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        tb = _make_toolbar("🏭  PFD Flowsheet — Diagrama de Processo Industrial",
                           lambda: self._inner.canvas,
                           self._inner.canvas.zoom_in,
                           self._inner.canvas.zoom_out,
                           self._inner.canvas.reset_zoom, self)
        layout.addWidget(tb)
        layout.addWidget(self._inner)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _FlowsheetModule()
    w.setWindowTitle("PFD Flowsheet — ProEng")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())

