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
        self.setFixedSize(120, 38)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._hov = False
        self.clicked.connect(self._toggle)

    def _toggle(self):
        # We only emit the signal; the central MainApp will handle the theme switch
        # and tell everyone (including this button's parent) to refresh.
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
        p.setRenderHint(QPainter.Antialiasing, False)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        
        # Visual clean: botão quadrado, sem preenchimento.
        p.setBrush(Qt.NoBrush)
        border_color = QColor(t["accent_bright"] if self._hov else t.get("glass_border", "rgba(255,255,255,40)"))
        p.setPen(QPen(border_color, 1.0))
        p.drawRect(r)
        
        is_dark = (t["name"] == "dark")
        label = "CLARO" if is_dark else "ESCURO"
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.setPen(QColor(t["text"]))
        p.drawText(r, Qt.AlignCenter, label)
        p.end()


# ═══════════════════════════════════════════════════════════════════
#   NAVBAR
# ═══════════════════════════════════════════════════════════════════

class NavBar(QWidget):
    example_requested = pyqtSignal(str)

    def __init__(self, go_home_fn, toggle_theme_fn, help_fn=None):
        super().__init__()
        self.setFixedHeight(64)
        self._go_home = go_home_fn
        self._help_fn = help_fn
        self._setup(toggle_theme_fn)

    def _setup(self, toggle_theme_fn):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 0, 8) # No margin right for window controls
        lay.setSpacing(10)

        self._btn_back = QPushButton("Inicio")
        self._btn_back.clicked.connect(self._go_home)
        lay.addWidget(self._btn_back)

        sep = QWidget(); sep.setFixedSize(1, 24)
        sep.setStyleSheet("background: rgba(128,128,128,0.3);")
        lay.addWidget(sep)

        # Botões de Menu (Reposicionados à esquerda)
        self._btn_file = QPushButton("Arquivo")
        self._btn_modules = QPushButton("Módulos")
        self._btn_help = QPushButton("Ajuda")
        if self._help_fn:
            self._btn_help.clicked.connect(self._help_fn)
        for btn in [self._btn_file, self._btn_modules, self._btn_help]:
            lay.addWidget(btn)

        self._brand = QLabel("PRO ENG | ENGINEERING WORKSPACE")
        lay.addWidget(self._brand)
        lay.addStretch()

        self._lbl = QLabel("")
        lay.addWidget(self._lbl)

        sep2 = QWidget(); sep2.setFixedSize(1, 24)
        sep2.setStyleSheet("background: rgba(128,128,128,0.3);")
        lay.addWidget(sep2)

        self._toggle = ThemeToggle()
        if toggle_theme_fn:
            self._toggle.theme_changed.connect(toggle_theme_fn)
        self._toggle.theme_changed.connect(self._apply_style)
        self._toggle.theme_changed.connect(self.update)
        lay.addWidget(self._toggle)
        
        lay.addSpacing(10)
        
        # Window Controls
        self._win_ctrls = QWidget()
        ctrl_lay = QHBoxLayout(self._win_ctrls)
        ctrl_lay.setContentsMargins(0, 0, 0, 0)
        ctrl_lay.setSpacing(0)
        
        self._btn_min = QPushButton("−") # Unicode Minus for Minimize
        self._btn_max = QPushButton("□") # Unicode Square for Maximize
        self._btn_close = QPushButton("✕") # Unicode X for Close
        
        for btn in [self._btn_min, self._btn_max, self._btn_close]:
            btn.setFixedSize(50, 40)
            btn.setFlat(True)
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            ctrl_lay.addWidget(btn)
            
        self._btn_min.clicked.connect(self._min_window)
        self._btn_max.clicked.connect(self._max_window)
        self._btn_close.clicked.connect(self._close_window)
        
        lay.addWidget(self._win_ctrls)

        self._apply_style()
        self._moving = False

    def _apply_style(self):
        t = T()
        self.setStyleSheet(f"""
            QWidget {{
                background: {t["toolbar_bg"]};
                border-bottom: 1px solid {t.get('glass_border', 'rgba(255,255,255,20)')};
            }}
        """)
        self._btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t["text"]};
                border: none;
                border-radius: 0px; 
                padding-left: 20px; padding-right: 20px;
                height: 42px;
                font-family: 'Segoe UI'; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: transparent;
                color: {t["accent_bright"]};
            }}
        """)
        self._brand.setStyleSheet(f"""
            color: {t["accent_bright"]}; font-family: 'Segoe UI';
            font-size: 14px; font-weight: 700;
            background: transparent; border: none; letter-spacing: 1px;
        """)
        self._lbl.setStyleSheet(f"""
            color: {t["text_dim"]}; font-family: 'Segoe UI';
            font-size: 12px; font-weight: 600; background: transparent; border: none;
        """)

        menu_btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {t["text"]};
                border: none;
                border-radius: 0px;
                padding-left: 20px; padding-right: 20px;
                height: 42px;
                font-family: 'Segoe UI';
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: transparent;
                color: {t["accent_bright"]};
            }}
            QPushButton::menu-indicator {{ image: none; }}
        """
        self._btn_file.setStyleSheet(menu_btn_style)
        self._btn_modules.setStyleSheet(menu_btn_style)
        self._btn_help.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t["text"]};
                border: none;
                border-radius: 0px;
                padding-left: 20px; padding-right: 20px;
                height: 42px;
                font-family: 'Segoe UI';
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: transparent;
                color: {t["accent_bright"]};
            }}
        """)
        
        win_btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {t["text"]};
                border: none;
                border-radius: 0;
            }}
            QPushButton:hover {{
                background: {t.get("btn_win_h", "rgba(255,255,255,20)")};
            }}
        """
        self._btn_min.setStyleSheet(win_btn_style)
        self._btn_max.setStyleSheet(win_btn_style)
        self._btn_close.setStyleSheet(win_btn_style + f"QPushButton:hover {{ background: {t.get('btn_close_h', '#e81123')}; color: white; }}")

    def _min_window(self):
        win = self.window()
        if win: win.showMinimized()

    def _max_window(self):
        win = self.window()
        if win:
            if win.isMaximized():
                win.showNormal()
                self._btn_max.setText("□")
            else:
                win.showMaximized()
                self._btn_max.setText("❐") # Restore icon

    def _close_window(self):
        win = self.window()
        if win: win.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._moving = True
            self._start_pos = event.globalPos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._moving and event.buttons() & Qt.LeftButton:
            win = self.window()
            if win.isMaximized():
                # Optional: Handle un-maximize on drag like Windows
                pass
            diff = event.globalPos() - self._start_pos
            win.move(win.pos() + diff)
            self._start_pos = event.globalPos()
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._moving = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        # Subtle accent line at the bottom
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        y = self.height() - 1
        g = QLinearGradient(0, y, self.width(), y)
        g.setColorAt(0.0,  QColor(t['accent_bright']).lighter(150))
        g.setColorAt(0.2,  QColor(t["accent_bright"]))
        g.setColorAt(0.8,  QColor(t["accent_bright"]))
        g.setColorAt(1.0,  QColor(t['accent_bright']).lighter(150))
        # Reduce opacity for the line
        pen = QPen(QBrush(g), 0.8)
        p.setOpacity(0.4)
        p.setPen(pen)
        p.drawLine(0, y, self.width(), y)
        p.end()
        super().paintEvent(event)


# ═══════════════════════════════════════════════════════════════════
#   TELA DE SELEÇÃO

