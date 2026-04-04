# -*- coding: utf-8 -*-
"""Barra de navegação e botão de alternância de tema."""

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QFont,
)
from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    pyqtSignal,
)

from proeng.core.themes import T, THEMES, set_theme, cycle_theme
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar


def _draw_icon_sun(p, x, y, size, col):
    pen = QPen(QColor(col), 2, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    cx, cy = x + size / 2, y + size / 2
    r = size * 0.22
    p.drawEllipse(QPointF(cx, cy), r, r)
    import math

    for a in range(0, 360, 45):
        rad = math.radians(a)
        p.drawLine(
            QPointF(cx + (r + 2) * math.cos(rad), cy + (r + 2) * math.sin(rad)),
            QPointF(cx + (r + 6) * math.cos(rad), cy + (r + 6) * math.sin(rad)),
        )


def _draw_icon_moon(p, x, y, size, col):
    pen = QPen(QColor(col), 2, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    cx, cy = x + size / 2, y + size / 2
    r = size * 0.32
    p.drawEllipse(QPointF(cx, cy), r, r)
    t = T()
    p.setBrush(QColor(t["bg_app"]))
    p.setPen(QPen(Qt.NoPen))
    p.drawEllipse(QPointF(cx + 3, cy - 2), r * 0.8, r * 0.8)


def _draw_icon_nb(p, x, y, size, col):
    pen = QPen(QColor(col), 2.5, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    m = 3
    p.drawRect(QRectF(x + m, y + m, size - m * 2, size - m * 2))
    p.drawLine(QPointF(x + m, y + m), QPointF(x + size - m, y + size - m))


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
        self.theme_changed.emit()
        self.update()

    def event(self, e):
        from PyQt5.QtCore import QEvent

        if e.type() == QEvent.HoverEnter:
            self._hov = True
            self.update()
        elif e.type() == QEvent.HoverLeave:
            self._hov = False
            self.update()
        return super().event(e)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)

        if self._hov:
            p.translate(3, 3)

        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if not self._hov:
            p.save()
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(
                QRectF(r.left() + sx * 0.5, r.top() + sy * 0.5, r.width(), r.height())
            )
            p.restore()

        p.setBrush(QColor(t["bg_card"]))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        p.setBrush(QColor(t["accent"] if self._hov else t["accent_bright"]))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), r.width(), 4))

        theme_name = t["name"]
        icon_col = t["text"]
        if theme_name == "dark":
            _draw_icon_sun(p, r.left() + 10, r.top() + 9, 18, icon_col)
        elif theme_name == "light":
            _draw_icon_moon(p, r.left() + 10, r.top() + 9, 18, icon_col)
        else:
            _draw_icon_nb(p, r.left() + 10, r.top() + 9, 18, icon_col)

        label_map = {"dark": "DARK", "light": "LIGHT", "neo_brutalist": "NEO"}
        label = label_map.get(theme_name, "TEMA")
        ff = t.get("font_family", "'Inter', sans-serif")
        p.setFont(QFont(ff, 9, QFont.Bold))
        p.setPen(QColor(t["text"]))
        lbl_r = QRectF(r.left() + 34, r.top(), r.width() - 40, r.height())
        p.drawText(lbl_r, Qt.AlignVCenter | Qt.AlignLeft, label)
        p.end()


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
        lay.setContentsMargins(14, 8, 0, 8)
        lay.setSpacing(10)

        self._btn_back = QPushButton("Inicio")
        self._btn_back.clicked.connect(self._go_home)
        lay.addWidget(self._btn_back)

        sep = QWidget()
        sep.setFixedSize(1, 24)
        lay.addWidget(sep)

        self._btn_file = QPushButton("Arquivo")
        self._btn_modules = QPushButton("Modulos")
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

        sep2 = QWidget()
        sep2.setFixedSize(1, 24)
        lay.addWidget(sep2)

        self._toggle = ThemeToggle()
        if toggle_theme_fn:
            self._toggle.theme_changed.connect(toggle_theme_fn)
        self._toggle.theme_changed.connect(self._apply_style)
        self._toggle.theme_changed.connect(self.update)
        lay.addWidget(self._toggle)

        lay.addSpacing(10)

        self._win_ctrls = QWidget()
        ctrl_lay = QHBoxLayout(self._win_ctrls)
        ctrl_lay.setContentsMargins(0, 0, 0, 0)
        ctrl_lay.setSpacing(0)

        self._btn_min = QPushButton("-")
        self._btn_max = QPushButton("[]")
        self._btn_close = QPushButton("X")

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
        bw = t.get("border_width", 3)
        bdr = t["glass_border"]
        ff = t.get("font_family", "'Inter', sans-serif")

        self.setStyleSheet(f"""
            QWidget {{
                background: {t["toolbar_bg"]};
                border-bottom: {bw}px solid {bdr};
            }}
        """)

        sep_style = f"background: {bdr};"
        for child in self.findChildren(QWidget):
            if child.objectName() == "" and child.sizeHint().width() == 1:
                child.setStyleSheet(sep_style)

        btn_style = f"""
            QPushButton {{
                background: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {bdr};
                border-radius: 0px;
                padding-left: 20px; padding-right: 20px;
                font-family: {ff}; font-size: 13px; font-weight: 900;
            }}
            QPushButton:hover {{
                background: {t["accent"]};
                color: #FFFFFF;
                border-color: {bdr};
            }}
            QPushButton::menu-indicator {{ image: none; }}
        """
        self._btn_back.setStyleSheet(btn_style)
        self._btn_file.setStyleSheet(btn_style)
        self._btn_modules.setStyleSheet(btn_style)
        self._btn_help.setStyleSheet(btn_style)

        self._brand.setStyleSheet(f"""
            QLabel {{
                color: {t["text"]};
                font-family: {ff};
                font-size: 16px;
                font-weight: 900;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 5px 10px;
                letter-spacing: 1px;
            }}
        """)
        self._lbl.setStyleSheet(f"""
            QLabel {{
                color: {t["text"]};
                font-family: {ff};
                font-size: 12px;
                font-weight: bold;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 5px;
            }}
        """)

        win_btn_style = f"""
            QPushButton {{
                background: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {bdr};
                border-radius: 0px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {t.get("btn_close_h", "#e81123")};
                color: #FFFFFF;
            }}
        """
        self._btn_min.setStyleSheet(win_btn_style)
        self._btn_max.setStyleSheet(win_btn_style)
        self._btn_close.setStyleSheet(win_btn_style)

    def _min_window(self):
        win = self.window()
        if win:
            win.showMinimized()

    def _max_window(self):
        win = self.window()
        if win:
            if win.isMaximized():
                win.showNormal()
                self._btn_max.setText("[]")
            else:
                win.showMaximized()
                self._btn_max.setText("[ ]")

    def _close_window(self):
        win = self.window()
        if win:
            win.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._moving = True
            self._start_pos = event.globalPos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._moving and event.buttons() & Qt.LeftButton:
            win = self.window()
            if win.isMaximized():
                pass
            diff = event.globalPos() - self._start_pos
            win.move(win.pos() + diff)
            self._start_pos = event.globalPos()
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._moving = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        bw = t.get("border_width", 3)
        y = self.height() - bw
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawLine(0, y, self.width(), y)
        p.end()
        super().paintEvent(event)
