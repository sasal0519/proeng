# -*- coding: utf-8 -*-
"""Utilitários globais: cores estáticas, _export_view."""
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

from proeng.core.themes import T, _ACTIVE, W5H2_TYPES

# ==========================================
# CORES DINÂMICAS — lidas em tempo real do tema ativo
# (definidas após THEMES, mas usadas via funções abaixo)
# ==========================================

# Placeholders estáticos usados ANTES do sistema de temas carregar
# (serão sobrescritos pelas funções dinâmicas de cor)
C_BG_APP       = "#0D0D0D"
C_BG_NODE      = "#1A0A0A"
C_BG_ROOT      = "#2A0F0F"
C_BORDER       = "#CC2222"
C_BORDER_ROOT  = "#E03535"
C_BORDER_EMPTY = "#8B2020"
C_TEXT_WBS     = "#CC2222"
C_TEXT_MAIN    = "#FAE8E8"
C_TEXT         = "#FAE8E8"
C_PLACEHOLDER  = "#8B2020"
C_BTN_ADD      = "#1A5C1A"
C_BTN_SIB      = "#1A3A6B"
C_BTN_DEL      = "#8B1515"
C_LINE         = "#E03535"
C_LINE_EAP     = "#8B2020"

# Funções de cor dinâmicas (usam T() após o sistema de temas estar carregado)
# São chamadas dentro dos métodos paint() para pegar a cor do tema atual
def _c(key):
    try: return _ACTIVE["theme"][key]
    except: return "#CC2222"  # fallback


# ==========================================
# ==========================================
#   MÓDULO FLOWSHEET (PFD)
# ==========================================
# ==========================================


def _export_view(view, fmt, parent=None):
    t = T()
    scene = view.scene()
    rect  = scene.itemsBoundingRect().adjusted(-150, -150, 150, 150)
    if rect.isEmpty():
        QMessageBox.warning(parent, "Nada para exportar", "A cena está vazia.")
        return

    if fmt == "png":
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PNG", "diagrama.png", "Imagem PNG (*.png)")
        if not path:
            return
        scale = 2
        img = QPixmap(max(1, int(rect.width()*scale)), max(1, int(rect.height()*scale)))
        img.fill(QColor(t["bg_app"]))
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(scale, scale)
        scene.render(p, source=rect)
        p.end()
        img.save(path, "PNG")
        QMessageBox.information(parent, "✅ PNG Exportado", f"Arquivo salvo em:\n{path}")

    elif fmt == "pdf":
        if not HAS_PRINT:
            QMessageBox.warning(parent, "Módulo ausente",
                "QPrintSupport não encontrado.\n"
                "Execute: pip install PyQt5 --upgrade")
            return
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PDF", "diagrama.pdf", "PDF (*.pdf)")
        if not path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.A3)
        printer.setOrientation(QPrinter.Landscape)
        p = QPainter(printer)
        p.setRenderHint(QPainter.Antialiasing)
        scene.render(p, source=rect)
        p.end()
        QMessageBox.information(parent, "✅ PDF Exportado", f"Arquivo salvo em:\n{path}")


# ==========================================
#   MÓDULO 5W2H (ACTION PLAN AUTO-LAYOUT)
# ==========================================


