# -*- coding: utf-8 -*-
"""Toolbar unificada e helper de ocultação da toolbar interna."""
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

from proeng.core.themes import T
from proeng.core.utils import _export_view

#   TOOLBAR UNIFICADA (usada por todos os módulos)
# ═══════════════════════════════════════════════════════════════════

def _make_toolbar(title_text, view_getter, zoom_in_fn, zoom_out_fn, reset_fn, parent, help_text=None):
    t = T()
    toolbar = QWidget()
    toolbar.setFixedHeight(48)
    toolbar.setStyleSheet(f"""
        QWidget {{
            background: {t["toolbar_bg"]};
            border-bottom: 1px solid {t["accent_dim"]};
        }}
    """)
    lay = QHBoxLayout(toolbar)
    lay.setContentsMargins(14, 4, 14, 4)
    lay.setSpacing(6)

    lbl = QLabel(title_text)
    lbl.setStyleSheet(f"""
        color: {t["accent_bright"]}; font-family: 'Segoe UI';
        font-size: 12px; font-weight: bold;
        background: transparent; border: none;
        padding: 0;
    """)
    # Elide if too long
    lbl.setMaximumWidth(480)
    lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    lay.addWidget(lbl)
    lay.addStretch()

    sep = QWidget(); sep.setFixedSize(1, 26)
    sep.setStyleSheet(f"background: {t['toolbar_sep']};")
    lay.addWidget(sep)

    btn_s = f"""
        QPushButton {{
            background: {t["toolbar_btn"]};
            color: {t["text"]};
            border: 1px solid {t["accent_dim"]};
            border-radius: 6px; padding: 5px 12px;
            font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;
            min-width: 36px;
        }}
        QPushButton:hover {{
            background: {t["toolbar_btn_h"]};
            border-color: {t["accent_bright"]}; color: {t["accent_bright"]};
        }}
        QPushButton:pressed {{ background: {t["accent"]}; color: white; }}
    """
    for txt, fn in [("🔍−", zoom_out_fn), ("🔍+", zoom_in_fn), ("⟳", reset_fn)]:
        b = QPushButton(txt); b.setStyleSheet(btn_s); b.clicked.connect(fn)
        lay.addWidget(b)

    sep2 = QWidget(); sep2.setFixedSize(1, 26)
    sep2.setStyleSheet(f"background: {t['toolbar_sep']};")
    lay.addWidget(sep2)

    exp_s = f"""
        QPushButton {{
            background: {t["toolbar_btn"]};
            color: {t["accent"]};
            border: 1px solid {t["accent_dim"]};
            border-radius: 6px; padding: 5px 12px;
            font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;
        }}
        QPushButton:hover {{
            background: {t["accent"]}; color: white;
            border-color: {t["accent_bright"]};
        }}
    """
    for txt, key in [("⬇ PNG", "png"), ("⬇ PDF", "pdf")]:
        b = QPushButton(txt); b.setStyleSheet(exp_s)
        b.setToolTip(f"Exportar como {key.upper()}")
        b.clicked.connect(lambda _, k=key: _export_view(view_getter(), k, parent))
        lay.addWidget(b)

    if help_text:
        sep_h = QWidget(); sep_h.setFixedSize(1, 26)
        sep_h.setStyleSheet(f"background: {t['toolbar_sep']};")
        lay.addWidget(sep_h)
        btn_h = QPushButton("❓ Ajuda")
        has_help_s = f"""
            QPushButton {{
                background: {t["toolbar_bg"]}; color: {t["text"]};
                border: 1px solid {t["accent"]}; border-radius: 6px; padding: 5px 12px;
                font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {t["accent"]}; color: white; }}
        """
        btn_h.setStyleSheet(has_help_s)
        btn_h.clicked.connect(lambda: QMessageBox.information(parent, "Ajuda: " + title_text.split("—")[0].strip(), help_text))
        lay.addWidget(btn_h)

    return toolbar


def _hide_inner_toolbar(widget):
    """Oculta a toolbar interna de um módulo widget.

    Procura o primeiro filho QWidget de altura fixa compatível com toolbar
    (entre 40 e 60 px) e o esconde, para evitar barra duplicada quando o
    módulo é embutido no layout principal com _make_toolbar.
    """
    for child in widget.children():
        if isinstance(child, QWidget):
            h = child.height()
            fh = child.maximumHeight()
            # Toolbar típica tem altura fixa entre 40‑60 px
            if 40 <= fh <= 60:
                child.hide()
                return
            # Fallback: verifica _toolbar_fs (FlowsheetWidget) ou _toolbar (outros)
    for attr in ("_toolbar_fs", "_toolbar", "_tb"):
        tb = getattr(widget, attr, None)
        if tb is not None and isinstance(tb, QWidget):
            tb.hide()
            return
