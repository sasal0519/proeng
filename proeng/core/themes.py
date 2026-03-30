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
        "bg_app":        "#161922",     # Grafite profundo azulado
        "bg_card":       "#222636",     # Slate azulado suave
        "bg_card2":      "#2F3349",     # Slate médio para hover
        "accent":        "#7367F0",     # Indigo moderno (menos agressivo que vermelho)
        "accent_bright": "#9E95F5",     # Indigo brilhante
        "accent_dim":    "#484481",     # Indigo desbotado / Bordas
        "text":          "#D0D2D6",     # Off-white suave
        "text_dim":      "#B4B7BD",     # Slate claro
        "text_muted":    "#676D7D",     # Slate escuro
        "line":          "#7367F0",
        "line_eap":      "#484481",
        "btn_add":       "#28C76F",     # Verde esmeralda moderno
        "btn_sib":       "#00CFE8",     # Ciano vibrante
        "btn_del":       "#EA5455",     # Coral suave para deleção
        "node_bg":       "#161922",
        "node_border":   "#484481",
        "node_text":     "#D0D2D6",
        "toolbar_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #161922,stop:0.5 #222636,stop:1 #161922)",
        "toolbar_sep":   "rgba(115,103,240,0.25)",
        "toolbar_btn":   "rgba(34,38,54,0.95)",
        "toolbar_btn_h": "rgba(115,103,240,0.15)",
        "sig_bg_l":      "rgba(22,25,34,0)",
        "sig_bg_r":      "rgba(47,51,73,225)",
        "sig_border":    "rgba(115,103,240,50)",
        "sig_text":      "rgba(180,183,189,180)",
    },
    "light": {
        # ── Paleta Azul Celeste & Branco Moderno ─────────────────────
        "name":          "light",
        # Superfícies
        "bg_app":        "#F4F8FF",     # fundo geral — azul muito pálido
        "bg_card":       "#FFFFFF",     # card puro branco
        "bg_card2":      "#E6EFFF",     # card hover / selecionado
        # Accent azul saturado (mais vibrante que antes)
        "accent":        "#1A62CC",     # azul primário
        "accent_bright": "#2575E8",     # azul brilhante / hover
        "accent_dim":    "#93B8E8",     # azul desbotado / borda suave
        # Texto
        "text":          "#0D1A2E",     # quase preto-azulado
        "text_dim":      "#4A6A94",     # azul médio
        "text_muted":    "#A8BDD8",     # azul apagado
        # Linhas do diagrama
        "line":          "#2575E8",
        "line_eap":      "#93B8E8",
        # Botões de ação nos nós
        "btn_add":       "#166B30",
        "btn_sib":       "#1A3A8B",
        "btn_del":       "#C0392B",
        # Node canvas (flowsheet)
        "node_bg":       "#EBF3FF",
        "node_border":   "#93B8E8",
        "node_text":     "#0D1A2E",
        # Toolbar
        "toolbar_bg":    "qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #E6EFFF,stop:0.5 #F4F8FF,stop:1 #E6EFFF)",
        "toolbar_sep":   "rgba(26,98,204,0.25)",
        "toolbar_btn":   "rgba(255,255,255,0.97)",
        "toolbar_btn_h": "rgba(26,98,204,0.10)",
        # Assinatura
        "sig_bg_l":      "rgba(180,210,255,0)",
        "sig_bg_r":      "rgba(220,235,255,235)",
        "sig_border":    "rgba(26,98,204,55)",
        "sig_text":      "rgba(26,80,160,205)",
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


