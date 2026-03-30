# -*- coding: utf-8 -*-
"""Barra de navegação e botão de alternância de tema."""
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

from proeng.core.themes import T, THEMES, _ACTIVE, set_theme
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar


class ThemeToggle(QPushButton):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedSize(86, 32)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._hov = False
        self.clicked.connect(self._toggle)

    def _toggle(self):
        new = "light" if T()["name"] == "dark" else "dark"
        set_theme(new)
        self.theme_changed.emit()
        self.update()

    def event(self, e):
        from PyQt5.QtCore import QEvent
        if e.type() == QEvent.HoverEnter:  self._hov = True;  self.update()
        elif e.type() == QEvent.HoverLeave: self._hov = False; self.update()
        return super().event(e)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        p.setBrush(QBrush(QColor(t["bg_card2"] if self._hov else t["bg_card"])))
        p.setPen(QPen(QColor(t["accent"]), 1.2))
        p.drawRoundedRect(r, 8, 8)
        is_dark = (t["name"] == "dark")
        icon = "☀️" if is_dark else "🌙"
        label = " Claro" if is_dark else " Escuro"
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(QColor(t["accent_bright"]))
        p.drawText(r, Qt.AlignCenter, icon + label)
        p.end()


# ═══════════════════════════════════════════════════════════════════
#   NAVBAR
# ═══════════════════════════════════════════════════════════════════

class NavBar(QWidget):
    def __init__(self, go_home_fn, toggle_theme_fn):
        super().__init__()
        self.setFixedHeight(48)
        self._go_home = go_home_fn
        self._setup(toggle_theme_fn)

    def _apply_style(self):
        t = T()
        self.setStyleSheet(f"""
            QWidget {{
                background: {t["toolbar_bg"]};
                border-bottom: 1px solid {t["accent_dim"]};
            }}
        """)
        self._btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {t["toolbar_btn"]};
                color: {t["text_dim"]};
                border: 1px solid {t["accent_dim"]};
                border-radius: 7px; padding: 5px 16px;
                font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {t["toolbar_btn_h"]};
                color: {t["accent_bright"]};
                border-color: {t["accent_bright"]};
            }}
        """)
        self._brand.setStyleSheet(f"""
            color: {t["accent_bright"]}; font-family: 'Consolas';
            font-size: 13px; font-weight: bold;
            background: transparent; border: none;
        """)
        self._lbl.setStyleSheet(f"""
            color: {t["accent_dim"]}; font-family: 'Segoe UI';
            font-size: 11px; background: transparent; border: none;
        """)

    def _setup(self, toggle_theme_fn):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        self._btn_back = QPushButton("◀  Menu")
        self._btn_back.clicked.connect(self._go_home)
        lay.addWidget(self._btn_back)

        sep = QWidget(); sep.setFixedSize(1, 24)
        sep.setStyleSheet("background: rgba(128,128,128,0.3);")
        lay.addWidget(sep)

        self._brand = QLabel("Pro Eng Tools")
        lay.addWidget(self._brand)
        lay.addStretch()

        self._lbl = QLabel("")
        lay.addWidget(self._lbl)

        sep2 = QWidget(); sep2.setFixedSize(1, 24)
        sep2.setStyleSheet("background: rgba(128,128,128,0.3);")
        lay.addWidget(sep2)

        self._toggle = ThemeToggle()
        self._toggle.theme_changed.connect(self._apply_style)
        self._toggle.theme_changed.connect(self.update)
        lay.addWidget(self._toggle)

        self._apply_style()

    def set_module(self, title):
        self._lbl.setText(title)

    def paintEvent(self, event):
        super().paintEvent(event)
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        y = self.height() - 1
        g = QLinearGradient(0, y, self.width(), y)
        g.setColorAt(0.0,  QColor(0, 0, 0, 0))
        g.setColorAt(0.3,  QColor(t["accent_bright"]))
        g.setColorAt(0.7,  QColor(t["accent_bright"]))
        g.setColorAt(1.0,  QColor(0, 0, 0, 0))
        p.setPen(QPen(QBrush(g), 1))
        p.drawLine(0, y, self.width(), y)
        p.end()


# ═══════════════════════════════════════════════════════════════════
#   TELA DE SELEÇÃO

