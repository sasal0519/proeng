# -*- coding: utf-8 -*-
"""Sistema de temas — Dark Industrial e Light Blue."""
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


#   SISTEMA DE TEMAS  ·  Dark Industrial  vs  Light Blue
# ═══════════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "name":          "dark",
        # Fundo principal mais sóbrio e neutro
        "bg_app":        "#050816",     # Azul petróleo quase preto
        # Cartões com glass leve, porém menos “fantasia”
        "bg_card":       "rgba(15, 23, 42, 210)",   # Slate escuro
        "bg_card2":      "rgba(30, 64, 175, 220)",  # Azul mais forte no hover
        "bg_input":      "#020617",     # Fundo quase preto para inputs
        "glass_border":  "rgba(148, 163, 184, 80)",
        # Paleta de acento mais corporativa (azul petróleo)
        "accent":        "#2563EB",     # Blue 600
        "accent_bright": "#38BDF8",     # Sky 400
        "accent_dim":    "rgba(37, 99, 235, 110)",
        # Tipografia
        "text":          "#E5E7EB",     # Gray-200
        "text_dim":      "#9CA3AF",     # Gray-400
        "text_muted":    "#6B7280",     # Gray-500
        # Linhas e elementos estruturais
        "line":          "#38BDF8",
        "line_eap":      "#4B5563",
        # Botões de ação
        "btn_add":       "#22C55E",
        "btn_sib":       "#0EA5E9",
        "btn_del":       "#EF4444",
        # Nós de diagramas
        "node_bg":       "rgba(15, 23, 42, 230)",
        "node_border":   "rgba(148, 163, 184, 180)",
        "node_text":     "#F9FAFB",
        # Barra superior mais discreta
        "toolbar_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(5,8,22,255),stop:1 rgba(15,23,42,255))",
        "toolbar_sep":   "rgba(148,163,184,60)",
        "toolbar_btn":   "rgba(15,23,42,255)",
        "toolbar_btn_h": "rgba(30,64,175,255)",
        # Assinaturas/suporte
        "sig_bg_l":      "rgba(5,8,22,0)",
        "sig_bg_r":      "rgba(15,23,42,230)",
        "sig_border":    "rgba(148,163,184,80)",
        "sig_text":      "rgba(229,231,235,200)",
        # Controles de janela
        "btn_close_h":   "#EF4444",
        "btn_win_h":     "rgba(148,163,184,60)",
    },
    "light": {
        "name":          "light",
        # Fundo claro levemente acinzentado (menos brilho)
        "bg_app":        "#F3F4F6",     # Gray-100
        "bg_card":       "rgba(255,255,255, 245)",  # Branco com leve transparência
        "bg_card2":      "rgba(226, 232, 240, 255)",# Gray-200 no hover
        "bg_input":      "#FFFFFF",
        "glass_border":  "rgba(148,163,184,70)",
        # Acento azul profissional
        "accent":        "#2563EB",     # Blue 600
        "accent_bright": "#1D4ED8",     # Blue 700
        "accent_dim":    "rgba(37, 99, 235, 80)",
        # Tipografia
        "text":          "#111827",     # Gray-900
        "text_dim":      "#4B5563",     # Gray-600
        "text_muted":    "#6B7280",     # Gray-500
        # Linhas
        "line":          "#2563EB",
        "line_eap":      "#CBD5F5",     # Azul bem claro para linhas estruturais
        # Botões
        "btn_add":       "#16A34A",
        "btn_sib":       "#2563EB",
        "btn_del":       "#DC2626",
        # Nós
        "node_bg":       "#FFFFFF",
        "node_border":   "#E5E7EB",
        "node_text":     "#111827",
        # Barra superior
        "toolbar_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(243,244,246,255),stop:1 rgba(229,231,235,255))",
        "toolbar_sep":   "rgba(148,163,184,60)",
        "toolbar_btn":   "rgba(255,255,255,255)",
        "toolbar_btn_h": "rgba(219,234,254,255)",
        # Assinaturas/suporte
        "sig_bg_l":      "rgba(255,255,255,0)",
        "sig_bg_r":      "rgba(243,244,246,245)",
        "sig_border":    "rgba(148,163,184,70)",
        "sig_text":      "rgba(17,24,39,190)",
        # Controles de janela
        "btn_close_h":   "#EF4444",
        "btn_win_h":     "rgba(148,163,184,60)",
    },
}

# Tema ativo (mutável em runtime)
_ACTIVE = {"theme": THEMES["dark"]}

def T():
    """Retorna o dicionário do tema ativo."""
    return _ACTIVE["theme"]

def set_theme(name: str):
    _ACTIVE["theme"] = THEMES[name]


# ═══════════════════════════════════════════════════════════════════
#   EXPORTAÇÃO PDF / PNG
# ═══════════════════════════════════════════════════════════════════

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

W5H2_TYPES = {
    "ROOT":  {"t": "PLANO DE AÇÃO", "c": "#E03535"},
    "WHAT":  {"t": "O QUÊ? (Ação)", "c": "#3498DB"},
    "WHY":   {"t": "POR QUÊ? (Justificativa)", "c": "#F1C40F"},
    "WHO":   {"t": "QUEM? (Responsável)", "c": "#9B59B6"},
    "WHERE": {"t": "ONDE? (Local)", "c": "#2ECC71"},
    "WHEN":  {"t": "QUANDO? (Prazo)", "c": "#E67E22"},
    "HOW":   {"t": "COMO? (Método/Etapas)", "c": "#1ABC9C"},
    "COST":  {"t": "QUANTO? (Custo/Orçamento)", "c": "#E74C3C"}
}


