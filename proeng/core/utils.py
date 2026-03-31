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

from proeng.core.themes import T, _ACTIVE

# ==========================================
# FUNÇÕES DE COR DINÂMICAS
# ==========================================

def _c(key):
    """Retorna uma QColor baseada na chave do tema ativo, suportando formatos hex e rgba."""
    try:
        val = T().get(key, "#7367F0")
        if val.startswith("rgba"):
            # Parse rgba(r, g, b, a)
            parts = val.replace("rgba(", "").replace(")", "").split(",")
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            a = int(parts[3])
            return QColor(r, g, b, a)
        return QColor(val)
    except Exception:
        return QColor("#7367F0")

def _glass_grad(rect, hovered=False):
    """Gera um gradiente linear de alta fidelidade (Efeito Glass) para preenchimentos borderless."""
    t = T()
    grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    
    if t["name"] == "dark":
        # Dark Mode: Slate-800 Glass -> Deep Slate-950
        c1 = _c("bg_card") if not hovered else _c("bg_card2")
        c2 = _c("bg_app")
        grad.setColorAt(0, c1)
        grad.setColorAt(0.4, c1) # Mantém brilho no topo
        grad.setColorAt(1, c2)
    else:
        # Light Mode: 'Frost' effect (Slate-50 to White)
        # Mais opacidade no topo para definição borderless
        c1 = QColor(241, 245, 249, 230) if not hovered else QColor(226, 232, 240, 255)
        c2 = QColor(255, 255, 255, 200)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        
    return grad

# PROXY LEGACY CONSTANTS (Mapeadas dinamicamente para o motor de temas T())
C_BG_APP      = "transparent" # Fundo via StyleSheet
C_BG_NODE     = "transparent" 
C_BORDER      = "rgba(0,0,0,0)"
C_TEXT_MAIN   = "white"
C_TEXT        = "white"
C_PLACEHOLDER = "grey"
C_BTN_ADD     = "#22C55E"
C_BTN_DEL     = "#EF4444"
C_LINE        = "#7367F0"
C_BTN_SIB     = "#0EA5E9"
C_BG_ROOT     = "#5E50EF"
C_BORDER_ROOT = "white"

# Note: many Flowsheet components now use T() directly, 
# but these constants prevent crashes on legacy imports.


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
        scale = 3  # Maior escala para mais resolução 
        target_w = max(1, int(rect.width() * scale))
        target_h = max(1, int(rect.height() * scale))
        img = QPixmap(target_w, target_h)
        img.fill(QColor(t["bg_app"]))
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        
        target_rect = QRectF(0, 0, target_w, target_h)
        scene.render(p, target=target_rect, source=rect)
        p.end()
        img.save(path, "PNG")
        QMessageBox.information(parent, "✅ PNG Exportado", f"Arquivo salvo em:\n{path}")

    elif fmt == "pdf":
        try:
            from PyQt5.QtPrintSupport import QPrinter
            HAS_PRINT = True
        except ImportError:
            HAS_PRINT = False
            
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
        p.setRenderHint(QPainter.TextAntialiasing)
        
        # Mapeia a cena para o tamanho inteiro da folha A3 mantendo proporção 
        target_rect = QRectF(0, 0, printer.width(), printer.height())
        scene.render(p, target=target_rect, source=rect, aspectRatioMode=Qt.KeepAspectRatio)
        p.end()
        QMessageBox.information(parent, "✅ PDF Exportado", f"Arquivo salvo em:\n{path}")


# ==========================================
#   MÓDULO 5W2H (ACTION PLAN AUTO-LAYOUT)
# ==========================================

W5H2_TYPES = {
    "ROOT":    {"t": "🎯 Objetivo",  "c": "#5E50EF"}, # Soft Indigo
    "WHAT":    {"t": "🤔 O Que?",      "c": "#FF9F43"}, # Soft Orange
    "WHY":     {"t": "❓ Por Que?",    "c": "#EA5455"}, # Soft Red
    "WHO":     {"t": "👤 Quem?",       "c": "#28C76F"}, # Soft Green
    "WHERE":   {"t": "📍 Onde?",      "c": "#00CFE8"}, # Soft Cyan
    "WHEN":    {"t": "📅 Quando?",     "c": "#D4A017"}, # Goldenrod
    "HOW":     {"t": "🛠 Como?",       "c": "#82868b"}, # Gray Slate
    "COST":    {"t": "💰 Quanto?",     "c": "#B33939"}  # Darker Red
}


