# -*- coding: utf-8 -*-
"""Módulo PM Canvas — Project Model Canvas (Finocchio)."""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QGraphicsPathItem,
    QMenu,
    QListView,
    QLineEdit,
    QLabel,
    QStackedWidget,
    QTextEdit,
    QGraphicsRectItem,
    QInputDialog,
    QFileDialog,
    QSizePolicy,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QPalette,
    QCursor,
    QPolygonF,
    QFont,
    QFontMetrics,
    QIcon,
    QPixmap,
    QPainterPath,
    QDrag,
)
from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QMimeData,
    QByteArray,
    QDataStream,
    QIODevice,
    QSize,
    QPoint,
    QTimer,
    pyqtSignal,
    QObject,
    QSizeF,
)

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.utils import _export_view, _c, _solid_fill, _nb_paint_node, _is_nb
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule

import math as _math


class CanvasSignals(QObject):
    add_block = pyqtSignal(str)
    delete_block = pyqtSignal(str)
    edit_block = pyqtSignal(str)
    commit_block = pyqtSignal(str, str)


class CanvasFloatingEditor(QWidget):
    """Editor flutuante multi-linha para o PM Canvas."""

    committed = pyqtSignal(str, str)

    def __init__(self, parent_view):
        from PyQt5.QtWidgets import QTextEdit

        super().__init__(parent_view)
        self._target_id = None
        self._original = ""
        self._done = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        from PyQt5.QtWidgets import QTextEdit as _QTE

        self._edit = _QTE(self)
        layout.addWidget(self._edit)
        self._edit.installEventFilter(self)
        self._apply_style()
        self.hide()

    def _apply_style(self):
        try:
            t = T()
            bg = t["bg_card2"]
            fg = t["text"]
            bdr = t["accent_bright"]
        except Exception:
            bg, fg, bdr = t["bg_card2"], t["text"], t["accent_bright"]
        self._edit.setStyleSheet(f"""
            QTextEdit {{
                background: {bg};
                color: {fg};
                border: 2px solid {bdr};
                border-radius: 6px;
                font-family: 'Segoe UI';
                font-size: 11pt;
                padding: 6px;
            }}
        """)

    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent

        if obj is self._edit and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not (event.modifiers() & Qt.ShiftModifier):
                    self._commit()
                    return True
            elif event.key() == Qt.Key_Escape:
                self._commit(self._original)
                return True
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        self._commit()
        super().focusOutEvent(event)

    def open(self, target_id, current_text, scene_rect, view):
        self._apply_style()
        self._target_id = target_id
        self._original = current_text
        self._done = False
        rect_in_view = view.mapFromScene(scene_rect).boundingRect()
        self.setGeometry(rect_in_view)
        self._edit.setPlainText(current_text)
        self._edit.selectAll()
        self.show()
        self.raise_()
        self._edit.setFocus()

    def _commit(self, text=None):
        if self._done:
            return
        self._done = True
        self.hide()
        result = (text if text is not None else self._edit.toPlainText()).strip()
        self.committed.emit(self._target_id, result)


def draw_canvas_icon(painter, icon_name, rect):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(_c("text")), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    if icon_name == "just":
        painter.drawEllipse(QRectF(x, y + h * 0.2, w * 0.6, h * 0.5))
        painter.drawEllipse(QRectF(x + w * 0.4, y + h * 0.1, w * 0.6, h * 0.5))
        painter.drawLine(
            QPointF(x + w * 0.1, y + h * 0.6), QPointF(x - w * 0.1, y + h * 0.9)
        )
    elif icon_name == "obj":
        painter.drawEllipse(QRectF(x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.8))
        painter.drawEllipse(QRectF(x + w * 0.3, y + h * 0.3, w * 0.4, h * 0.4))
        painter.drawLine(
            QPointF(x + w * 0.5, y + h * 0.5), QPointF(x + w * 1.1, y - h * 0.1)
        )
        painter.drawPolygon(
            QPolygonF(
                [
                    QPointF(x + w * 1.1, y - h * 0.1),
                    QPointF(x + w * 0.9, y - h * 0.1),
                    QPointF(x + w * 1.1, y + h * 0.1),
                ]
            )
        )
    elif icon_name == "ben":
        painter.setBrush(QBrush(QColor(_c("text"))))
        painter.drawRect(QRectF(x + w * 0.1, y + h * 0.6, w * 0.2, h * 0.4))
        painter.drawRect(QRectF(x + w * 0.4, y + h * 0.3, w * 0.2, h * 0.7))
        painter.drawRect(QRectF(x + w * 0.7, y, w * 0.2, h * 1.0))
        painter.drawLine(QPointF(x, y + h * 0.8), QPointF(x + w, y + h * 0.2))
    elif icon_name == "prod":
        painter.drawRect(QRectF(x + w * 0.2, y + h * 0.4, w * 0.6, h * 0.6))
        painter.drawLine(QPointF(x + w * 0.2, y + h * 0.4), QPointF(x, y + h * 0.1))
        painter.drawLine(QPointF(x + w * 0.8, y + h * 0.4), QPointF(x + w, y + h * 0.1))
    elif icon_name == "req":
        painter.drawRect(QRectF(x + w * 0.2, y, w * 0.6, h))
        painter.drawLine(
            QPointF(x + w * 0.3, y + h * 0.3), QPointF(x + w * 0.7, y + h * 0.3)
        )
        painter.drawLine(
            QPointF(x + w * 0.3, y + h * 0.5), QPointF(x + w * 0.7, y + h * 0.5)
        )
        painter.drawLine(
            QPointF(x + w * 0.3, y + h * 0.7), QPointF(x + w * 0.5, y + h * 0.7)
        )
    elif icon_name == "stk":
        painter.drawEllipse(QRectF(x, y, w * 0.3, h * 0.3))
        painter.drawArc(QRectF(x - w * 0.1, y + h * 0.3, w * 0.5, h * 0.4), 0, 180 * 16)
        painter.drawRect(QRectF(x + w * 0.4, y + h * 0.2, w * 0.3, h * 0.8))
    elif icon_name == "eqp":
        painter.drawEllipse(QRectF(x + w * 0.1, y + h * 0.1, w * 0.3, h * 0.3))
        painter.drawArc(QRectF(x, y + h * 0.4, w * 0.5, h * 0.4), 0, 180 * 16)
        painter.drawEllipse(QRectF(x + w * 0.6, y + h * 0.1, w * 0.3, h * 0.3))
        painter.drawArc(QRectF(x + w * 0.5, y + h * 0.4, w * 0.5, h * 0.4), 0, 180 * 16)
    elif icon_name == "prem":
        painter.drawEllipse(QRectF(x, y + h * 0.4, w * 0.4, h * 0.4))
        painter.drawEllipse(QRectF(x + w * 0.2, y + h * 0.2, w * 0.5, h * 0.5))
        painter.drawEllipse(QRectF(x + w * 0.6, y + h * 0.4, w * 0.4, h * 0.4))
        painter.drawLine(
            QPointF(x + w * 0.2, y + h * 0.8), QPointF(x + w * 0.8, y + h * 0.8)
        )
    elif icon_name == "ent":
        painter.drawRect(QRectF(x, y + h * 0.4, w * 0.25, h * 0.3))
        painter.drawRect(QRectF(x + w * 0.35, y + h * 0.4, w * 0.25, h * 0.3))
        painter.drawRect(QRectF(x + w * 0.7, y + h * 0.4, w * 0.25, h * 0.3))
    elif icon_name == "rest":
        painter.drawEllipse(rect)
        painter.drawLine(
            QPointF(x + w * 0.15, y + h * 0.15), QPointF(x + w * 0.85, y + h * 0.85)
        )
    elif icon_name == "risc":
        painter.drawEllipse(QRectF(x + w * 0.1, y + h * 0.2, w * 0.8, h * 0.8))
        painter.drawRect(QRectF(x + w * 0.4, y, w * 0.2, h * 0.2))
        painter.drawLine(QPointF(x + w * 0.5, y), QPointF(x + w * 0.7, y - h * 0.2))
    elif icon_name == "tmp":
        painter.setBrush(QBrush(QColor(_c("text"))))
        painter.drawEllipse(QRectF(x, y + h * 0.4, w * 0.15, h * 0.15))
        painter.drawEllipse(QRectF(x + w * 0.4, y + h * 0.4, w * 0.15, h * 0.15))
        painter.drawEllipse(QRectF(x + w * 0.8, y + h * 0.4, w * 0.15, h * 0.15))
        painter.drawLine(
            QPointF(x + w * 0.15, y + h * 0.47), QPointF(x + w * 0.4, y + h * 0.47)
        )
        painter.drawLine(
            QPointF(x + w * 0.55, y + h * 0.47), QPointF(x + w * 0.8, y + h * 0.47)
        )
    elif icon_name == "cst":
        t = T()
        painter.setFont(QFont(t.get("font_family", "Segoe UI"), int(h * 0.8), QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, "$$$")
    painter.restore()


class CanvasSectionFixed(QGraphicsItem):
    def __init__(self, sec_id, rect, title, subtitle, icon, signals, zoom):
        super().__init__()
        self.sec_id = sec_id
        self.w, self.h = rect.width(), rect.height()
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.signals = signals
        self.zoom = zoom
        self.setPos(rect.topLeft())
        self.setZValue(-20)
        self.hovered = False
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.boundingRect()

        if _is_nb(t):
            _nb_paint_node(painter, r, self.hovered)
        else:
            painter.setBrush(QBrush(_solid_fill(r, self.hovered)))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(r, 12, 12)

        if _is_nb(t):
            bw = t.get("border_width", 3)
            strip_h = max(6, int(6 * self.zoom))
            painter.save()
            painter.setBrush(
                QBrush(
                    QColor(t["accent_bright"]) if self.hovered else QColor(t["accent"])
                )
            )
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(bw, bw, self.w - bw * 2, strip_h))
            painter.restore()
        else:
            # ── Accent strip topo (CLIPPED to round container) ────────────────────────
            painter.save()
            clip_path = QPainterPath()
            clip_path.addRoundedRect(r, 12, 12)
            painter.setClipPath(clip_path)

            strip_h = max(3, int(4 * self.zoom))
            painter.setBrush(QBrush(QColor(t["accent_bright"])))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(0, 0, self.w, strip_h))
            painter.restore()
            # ──────────────────────────────────────────────────────────────────────────

        # Ícone
        icon_size = 42 * self.zoom
        ic_r = QRectF(12 * self.zoom, 14 * self.zoom, icon_size, icon_size)
        painter.save()
        draw_canvas_icon(painter, self.icon, ic_r)
        painter.restore()

        # Título — bound height to avoid overflow + padding
        ff = t.get("font_family", "Segoe UI")
        title_font = QFont(ff, max(7, int(12 * self.zoom)), QFont.Bold)
        painter.setPen(QColor(t["text"]))
        painter.setFont(title_font)
        title_x = 68 * self.zoom
        title_w = self.w - title_x - 14 * self.zoom
        title_rect = QRectF(title_x, 14 * self.zoom, title_w, self.h * 0.45)
        painter.drawText(
            title_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.title
        )

        if self.subtitle:
            fm_t = QFontMetrics(title_font)
            tb = fm_t.boundingRect(
                0, 0, int(title_w), 1000, Qt.AlignLeft | Qt.TextWordWrap, self.title
            )
            sub_font = QFont(ff, max(6, int(10 * self.zoom)), QFont.Bold)
            painter.setPen(_c("accent"))
            painter.setFont(sub_font)
            sub_y = title_rect.top() + tb.height() + 4 * self.zoom
            sub_rect = QRectF(title_x, sub_y, title_w, self.h - sub_y - 8 * self.zoom)
            painter.drawText(
                sub_rect, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.subtitle
            )

        # Botão "+"
        btn_s = min(55 * self.zoom, self.h * 0.35, self.w * 0.2)
        btn_rect = QRectF(self.w / 2 - btn_s / 2, self.h / 2 - btn_s / 2, btn_s, btn_s)
        if self.hovered:
            if _is_nb(t):
                painter.setBrush(QBrush(QColor(t["accent"])))
                painter.setPen(QPen(QColor("#000000"), 3))
                painter.drawRect(btn_rect)
            else:
                painter.setBrush(QBrush(QColor(t["accent"])))
                painter.setPen(QPen(QColor(t["text"]), 1.5))
                painter.drawRoundedRect(btn_rect, 10, 10)
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont(ff, max(12, int(28 * self.zoom)), QFont.Bold))
            painter.drawText(btn_rect, Qt.AlignCenter, "+")
        else:
            painter.setBrush(QBrush(QColor(128, 128, 128, 30)))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(btn_rect, 10, 10)
            painter.setPen(QColor(t["accent"]))
            painter.setFont(QFont(ff, max(12, int(28 * self.zoom)), QFont.Bold))
            painter.drawText(btn_rect, Qt.AlignCenter, "+")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            btn_s = 60 * self.zoom
            btn_rect = QRectF(
                self.w / 2 - btn_s / 2, self.h / 2 - btn_s / 2, btn_s, btn_s
            )
            if btn_rect.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.add_block.emit(self.sec_id))
                event.accept()
                return
        super().mousePressEvent(event)


class CanvasBlockSolid(QGraphicsItem):
    def __init__(self, pid, text, signals, zoom):
        super().__init__()
        self.pid = pid
        self.text = text
        self.signals = signals
        self.zoom = zoom
        self.hovered = False
        self._font_text = QFont(T().get("font_family", "Segoe UI"), int(12 * zoom), QFont.Bold)
        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(10)

    def _calc_size(self):
        self.base_w = 190 * self.zoom
        base_h = 110 * self.zoom
        pad_x = 18 * self.zoom
        pad_y = 30 * self.zoom  # room for del button top + breathing room
        if not self.text:
            self.w, self.h = self.base_w, base_h
        else:
            fm = QFontMetrics(self._font_text)
            text_rect = fm.boundingRect(
                0,
                0,
                int(self.base_w - pad_x),
                10000,
                Qt.AlignCenter | Qt.TextWordWrap,
                self.text,
            )
            self.w = self.base_w
            self.h = max(base_h, text_rect.height() + pad_y)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, painter, option, widget=None):
        r = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()

        # Body background block with universal glass engine
        painter.setBrush(QBrush(_solid_fill(r, self.hovered)))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(r, 10, 10)

        # ── Accent strip lateral (CLIPPED) ────────────────────────────────────────
        if self.hovered:
            painter.save()
            clip_path = QPainterPath()
            clip_path.addRoundedRect(r, 10, 10)
            painter.setClipPath(clip_path)

            painter.setBrush(QBrush(QColor(t["accent_bright"])))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(0, 0, max(3, int(4 * self.zoom)), self.h))
            painter.restore()

        if not self.text:
            painter.setFont(QFont("Segoe UI", max(7, int(10 * self.zoom))))
            painter.setPen(QColor(t["text_muted"]))
            painter.drawText(r, Qt.AlignCenter, "Duplo clique\npara editar")
        else:
            painter.setFont(self._font_text)
            painter.setPen(QColor(t["text"]))
            # Precise alignment and wrapping for task blocks
            # Increase padding to avoid rounded corners and give breathing room
            px, py = 16 * self.zoom, 12 * self.zoom
            inner = r.adjusted(px, py, -px, -py - 14 * self.zoom)
            painter.drawText(
                inner, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, self.text
            )

        if self.hovered:
            del_s = 20 * self.zoom
            del_rect = QRectF(
                self.w - del_s - 4 * self.zoom, 4 * self.zoom, del_s, del_s
            )
            painter.setBrush(QBrush(QColor(t["btn_del"])))
            painter.setPen(QPen(QColor("#FF6666"), 1))
            painter.drawRoundedRect(del_rect, 4, 4)
            painter.setPen(QColor("#FFF"))
            painter.setFont(QFont("Consolas", max(9, int(13 * self.zoom)), QFont.Bold))
            painter.drawText(del_rect, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            del_s = 22 * self.zoom
            del_rect = QRectF(
                self.w - del_s - 5 * self.zoom, 5 * self.zoom, del_s, del_s
            )
            if del_rect.contains(event.pos()) and self.hovered:
                QTimer.singleShot(0, lambda: self.signals.delete_block.emit(self.pid))
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_block.emit(self.pid))


class PMCanvasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = CanvasSignals()
        self.signals.add_block.connect(self._on_add_block)
        self.signals.delete_block.connect(self._on_delete_block)
        self.signals.edit_block.connect(self._on_edit_block)
        self.signals.commit_block.connect(self._on_commit_block)

        self.zoom_level = 0.6
        self.next_pid = 1

        self.sections_data = [
            {"id": "just", "t": "JUSTIFICATIVAS", "st": "Passado", "i": "just"},
            {"id": "obj", "t": "OBJ SMART", "st": "", "i": "obj"},
            {"id": "ben", "t": "BENEFÍCIOS", "st": "Futuro", "i": "ben"},
            {"id": "prod", "t": "PRODUTO", "st": "", "i": "prod"},
            {"id": "req", "t": "REQUISITOS", "st": "", "i": "req"},
            {
                "id": "stk",
                "t": "STAKEHOLDERS\nEXTERNOS",
                "st": "& Fatores externos",
                "i": "stk",
            },
            {"id": "eqp", "t": "EQUIPE", "st": "", "i": "eqp"},
            {"id": "prem", "t": "PREMISSAS", "st": "", "i": "prem"},
            {"id": "ent", "t": "GRUPO DE\nENTREGAS", "st": "", "i": "ent"},
            {"id": "rest", "t": "RESTRIÇÕES", "st": "", "i": "rest"},
            {"id": "risc", "t": "RISCOS", "st": "", "i": "risc"},
            {"id": "tmp", "t": "LINHA DO TEMPO", "st": "", "i": "tmp"},
            {"id": "cst", "t": "CUSTOS", "st": "", "i": "cst"},
        ]
        self.sections = {s["id"]: [] for s in self.sections_data}
        self.blocks_items = {}

        self._setup_ui()
        self._float_editor = CanvasFloatingEditor(self.view)
        self._float_editor.committed.connect(self.signals.commit_block.emit)
        self.update_zoom(0.6)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        try:
            self.view.setBackgroundBrush(QBrush(_c("bg_app")))
        except:
            self.view.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        self.view.scale(self.zoom_level, self.zoom_level)
        layout.addWidget(self.view)

    def refresh_theme(self):
        if hasattr(self, "view"):
            try:
                self.view.setBackgroundBrush(QBrush(_c("bg_app")))
                self.view.viewport().update()
            except Exception:
                pass

        if hasattr(self, "_float_editor"):
            self._float_editor._apply_style()

        self._draw_board()

    def zoom_in(self):
        self.update_zoom(self.zoom_level * 1.15)

    def zoom_out(self):
        self.update_zoom(self.zoom_level / 1.15)

    def reset_zoom(self):
        self.update_zoom(0.6)

    def update_zoom(self, z):
        self.zoom_level = max(0.2, min(z, 3.0))
        self._draw_board()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()

    def _draw_board(self):
        self.scene.clear()
        self.blocks_items.clear()
        z = self.zoom_level
        cw = 450 * z
        ch = 120 * z

        grid_geo = {
            "just": (0, 0, cw, ch * 3.5),
            "obj": (0, ch * 3.5, cw, ch * 2.5),
            "ben": (0, ch * 6.0, cw, ch * 4.0),
            "prod": (cw, 0, cw, ch * 3.5),
            "req": (cw, ch * 3.5, cw, ch * 6.5),
            "stk": (cw * 2, 0, cw, ch * 4.0),
            "eqp": (cw * 2, ch * 4.0, cw, ch * 4.5),
            "prem": (cw * 3, 0, cw, ch * 4.0),
            "ent": (cw * 3, ch * 4.0, cw, ch * 4.5),
            "rest": (cw * 2, ch * 8.5, cw * 2, ch * 1.5),
            "risc": (cw * 4, 0, cw, ch * 4.0),
            "tmp": (cw * 4, ch * 4.0, cw, ch * 4.5),
            "cst": (cw * 4, ch * 8.5, cw, ch * 1.5),
        }
        sec_info = {s["id"]: s for s in self.sections_data}

        # Cabeçalhos GP / PITCH com gradiente
        t_style = T()
        for txt, xp in [("GRUPO", 10 * z), ("PITCH", cw * 2 + 10 * z)]:
            ti = self.scene.addText(txt)
            ti.setDefaultTextColor(QColor(t_style["accent"]))
            ti.setFont(QFont("Consolas", int(24 * z), QFont.Bold))
            ti.setPos(xp, -65 * z)

        for sid, geo in grid_geo.items():
            s = sec_info[sid]
            rect = QRectF(geo[0], geo[1], geo[2], geo[3])
            sec_item = CanvasSectionFixed(
                sid, rect, s["t"], s["st"], s["i"], self.signals, z
            )
            self.scene.addItem(sec_item)

            pad_x, pad_y = 20 * z, 100 * z
            curr_px, curr_py = pad_x, pad_y
            block_positions = []

            for pdata in self.sections[sid]:
                pid = pdata["id"]
                p_item = CanvasBlockSolid(pid, pdata["text"], self.signals, z)
                if curr_px + p_item.w > rect.width() and curr_px > pad_x:
                    curr_px = pad_x
                    curr_py += p_item.h + 15 * z
                block_positions.append((p_item, curr_px, curr_py))
                curr_px += p_item.w + 15 * z

            if len(block_positions) > 1:
                pen_conn = QPen(
                    QColor(_c("accent")),
                    max(2, int(4 * z)),
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin,
                )
                for i in range(len(block_positions) - 1):
                    p_item1, px1, py1 = block_positions[i]
                    p_item2, px2, py2 = block_positions[i + 1]
                    c1 = QPointF(
                        rect.x() + px1 + p_item1.w / 2, rect.y() + py1 + p_item1.h / 2
                    )
                    c2 = QPointF(
                        rect.x() + px2 + p_item2.w / 2, rect.y() + py2 + p_item2.h / 2
                    )
                    self.scene.addLine(
                        c1.x(), c1.y(), c2.x(), c2.y(), pen_conn
                    ).setZValue(5)
                    angle = _math.atan2(c2.y() - c1.y(), c2.x() - c1.x())
                    arrow_size = 14 * z
                    mid_p = QPointF((c1.x() + c2.x()) / 2, (c1.y() + c2.y()) / 2)
                    ap1 = QPointF(
                        mid_p.x() - arrow_size * _math.cos(angle - _math.pi / 6),
                        mid_p.y() - arrow_size * _math.sin(angle - _math.pi / 6),
                    )
                    ap2 = QPointF(
                        mid_p.x() - arrow_size * _math.cos(angle + _math.pi / 6),
                        mid_p.y() - arrow_size * _math.sin(angle + _math.pi / 6),
                    )
                    self.scene.addPolygon(
                        QPolygonF([mid_p, ap1, ap2]),
                        QPen(Qt.NoPen),
                        QBrush(QColor(_c("accent"))),
                    ).setZValue(6)

            for p_item, px, py in block_positions:
                p_item.setPos(rect.x() + px, rect.y() + py)
                self.scene.addItem(p_item)
                self.blocks_items[p_item.pid] = p_item

        # Título rodapé
        ti = self.scene.addText("Project Model Canvas")
        ti.setDefaultTextColor(QColor(_c("text")))
        ti.setFont(QFont("Consolas", int(20 * z), QFont.Bold))
        ti.setPos(cw * 5 - ti.boundingRect().width() - 20 * z, ch * 10 + 10 * z)

        self.scene.setSceneRect(
            -100 * z, -100 * z, cw * 5 + 200 * z, ch * 10.5 + 200 * z
        )

    def _on_add_block(self, sec_id):
        pid = f"b_{self.next_pid}"
        self.next_pid += 1
        self.sections[sec_id].append({"id": pid, "text": ""})
        self._draw_board()
        QTimer.singleShot(60, lambda: self._on_edit_block(pid))

    def _on_delete_block(self, pid):
        for sec_id, blocks in self.sections.items():
            for i, b in enumerate(blocks):
                if b["id"] == pid:
                    del blocks[i]
                    self._draw_board()
                    return

    def _on_edit_block(self, pid):
        if pid in self.blocks_items:
            p_item = self.blocks_items[pid]
            self._float_editor.open(
                pid, p_item.text, p_item.sceneBoundingRect(), self.view
            )

    def _on_commit_block(self, pid, text):
        for sec_id, blocks in self.sections.items():
            for b in blocks:
                if b["id"] == pid:
                    b["text"] = text
                    self._draw_board()
                    return

    def _export_scene(self, fmt):
        _export_view(self.view, fmt, self)


class _CanvasModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = PMCanvasWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "PROJECT MODEL CANVAS — Guia Rapido\n\n"
            "O Project Model Canvas e uma ferramenta visual de "
            "planejamento estrategico que organiza as principais "
            "dimensoes de um projeto em um unico quadro: justificativa, "
            "objetivos, beneficios, produto, requisitos, stakeholders, "
            "equipe, premissas, restricoes, riscos, entregas, custos "
            "e cronograma.\n\n"
            "COMO USAR:\n"
            "• Clique no botao (+) no centro de cada secao para "
            "adicionar um novo post-it com sua anotacao.\n"
            "• Clique duas vezes em qualquer post-it para editar "
            "o texto existente.\n"
            "• Para excluir um post-it, passe o mouse sobre ele "
            "e clique no botao (-) que aparece.\n\n"
            "ESTRUTURA DO CANVAS:\n"
            "• O quadro e dividido em blocos tematicos que cobrem "
            "todos os aspectos essenciais do planejamento.\n"
            "• Cada bloco aceita multiplos post-its para detalhar "
            "as informacoes relevantes.\n\n"
            "NAVEGACAO:\n"
            "• Use Ctrl + Scroll do mouse ou Ctrl +/- para zoom.\n"
            "• Arraste o fundo para navegar pelo canvas."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def reset_zoom(self):
        self._inner.reset_zoom()

    def zoom_in(self):
        self._inner.zoom_in()

    def zoom_out(self):
        self._inner.zoom_out()

        # ═══════════════════════════════════════════════════════════════════

    def get_state(self):
        return {
            "schema": "canvas.v1",
            "sections": self._inner.sections,
            "next_pid": self._inner.next_pid,
        }

    def set_state(self, state):
        if not state:
            return
        secs = state.get("sections", {})
        if secs:
            self._inner.sections = secs
        else:
            self._inner.sections = {s["id"]: [] for s in self._inner.sections_data}
        self._inner.next_pid = state.get("next_pid", 1)
        self._inner._draw_board()

    def refresh_theme(self):
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        return getattr(self._inner, "view", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _CanvasModule()
    w.setWindowTitle("PM Canvas — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())
