# -*- coding: utf-8 -*-
"""Utilitários globais: cores dinâmicas, pintura de nós, exportação.

Estilo: SEM gradientes, SEM transparência. Cores sólidas apenas.
"""

from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QFileDialog,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QPixmap,
)
from PyQt5.QtCore import Qt, QRectF

from proeng.core.themes import T, _ACTIVE


def _c(key):
    """Retorna uma QColor baseada na chave do tema ativo (cores sólidas apenas)."""
    try:
        val = T().get(key, "#7367F0")
        return QColor(val)
    except Exception:
        return QColor("#7367F0")


def _solid_fill(rect, hovered=False):
    """Retorna cor sólida para preenchimento (sem gradientes, sem transparência)."""
    return _c("bg_card2") if hovered else _c("bg_card")


def _is_nb(t=None):
    """Returns True — all themes now use neo-brutalist styling."""
    return True


def _nb_paint_node(
    painter,
    rect,
    hovered=False,
    pressed=False,
    border_color=None,
    bg_color=None,
    shadow=True,
    radius=None,
):
    """Paint a node with hard border, solid shadow, and flat color.

    Works for ALL themes — no gradients, no transparency.
    Hover: shadow reduces (button-press simulation).
    Pressed: element shifts down-right, shadow disappears.
    """
    t = T()

    bw = t.get("border_width", 3)
    if pressed:
        sx = t.get("shadow_offset_x", 4)
        sy = t.get("shadow_offset_y", 4)
        shadow = False
    elif hovered:
        sx = t.get("shadow_hover_offset_x", 2)
        sy = t.get("shadow_hover_offset_y", 2)
    else:
        sx = t.get("shadow_offset_x", 4)
        sy = t.get("shadow_offset_y", 4)
    rad = t.get("border_radius", 0) if radius is None else radius
    sh_col = QColor(t.get("shadow", "#000000"))
    bdr_col = QColor(border_color) if border_color else QColor(t["glass_border"])
    fill_col = QColor(bg_color) if bg_color else _solid_fill(rect, hovered)

    if pressed and shadow:
        pass
    elif shadow:
        painter.save()
        painter.setBrush(QBrush(sh_col))
        painter.setPen(QPen(Qt.NoPen))
        shadow_rect = rect.translated(sx, sy)
        painter.drawRect(shadow_rect)
        painter.restore()

    painter.save()
    if pressed:
        painter.translate(sx, sy)
    painter.setBrush(QBrush(fill_col))
    painter.setPen(QPen(bdr_col, bw))
    if rad > 0:
        painter.drawRoundedRect(rect, rad, rad)
    else:
        painter.drawRect(rect)
    painter.restore()


C_BG_APP = "transparent"
C_BG_NODE = "transparent"
C_BORDER = "rgba(0,0,0,0)"
C_TEXT_MAIN = "white"
C_TEXT = "white"
C_PLACEHOLDER = "grey"
C_BTN_ADD = "#22C55E"
C_BTN_DEL = "#EF4444"
C_LINE = "#7367F0"
C_BTN_SIB = "#0EA5E9"
C_BG_ROOT = "#5E50EF"
C_BORDER_ROOT = "white"


def _export_view(view, fmt, parent=None):
    t = T()
    scene = view.scene()
    rect = scene.itemsBoundingRect().adjusted(-150, -150, 150, 150)
    if rect.isEmpty():
        QMessageBox.warning(parent, "Nada para exportar", "A cena está vazia.")
        return

    if fmt == "png":
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PNG", "diagrama.png", "Imagem PNG (*.png)"
        )
        if not path:
            return
        scale = 3
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
        QMessageBox.information(parent, "PNG Exportado", f"Arquivo salvo em:\n{path}")

    elif fmt == "pdf":
        try:
            from PyQt5.QtPrintSupport import QPrinter

            HAS_PRINT = True
        except ImportError:
            HAS_PRINT = False

        if not HAS_PRINT:
            QMessageBox.warning(
                parent,
                "Módulo ausente",
                "QPrintSupport não encontrado.\nExecute: pip install PyQt5 --upgrade",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PDF", "diagrama.pdf", "PDF (*.pdf)"
        )
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

        target_rect = QRectF(0, 0, printer.width(), printer.height())
        scene.render(
            p, target=target_rect, source=rect, aspectRatioMode=Qt.KeepAspectRatio
        )
        p.end()
        QMessageBox.information(parent, "PDF Exportado", f"Arquivo salvo em:\n{path}")


W5H2_TYPES = {
    "ROOT": {"t": "PLANO DE ACAO", "c": "#E03535"},
    "WHAT": {"t": "O QUE? (Acao)", "c": "#3498DB"},
    "WHY": {"t": "POR QUE? (Justificativa)", "c": "#F1C40F"},
    "WHO": {"t": "QUEM? (Responsavel)", "c": "#9B59B6"},
    "WHERE": {"t": "ONDE? (Local)", "c": "#2ECC71"},
    "WHEN": {"t": "QUANDO? (Prazo)", "c": "#E67E22"},
    "HOW": {"t": "COMO? (Metodo/Etapas)", "c": "#1ABC9C"},
    "COST": {"t": "QUANTO? (Custo/Orcamento)", "c": "#E74C3C"},
}
