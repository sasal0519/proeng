# -*- coding: utf-8 -*-
"""Janela principal da aplicação PRO ENG - Formato Workspace/Project."""

import sys
import os

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QMenuBar,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
    QLabel,
    QSplitter,
    QGraphicsView,
    QSizePolicy,
    QScrollArea,
    QGridLayout,
    QFrame,
    QGraphicsOpacityEffect,
)
from PyQt5.QtGui import (
    QIcon,
    QFont,
    QColor,
    QPalette,
    QBrush,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QPainterPath,
    QRadialGradient,
    QPolygonF,
)
from PyQt5.QtCore import (
    Qt,
    QSize,
    QRectF,
    QPointF,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QTimer,
    QSequentialAnimationGroup,
    QPauseAnimation,
)

from proeng.core.themes import T, cycle_theme
from proeng.core.project import AppProject
from proeng.core.utils import _export_view, _c, _is_nb
from proeng.core.base_module import BaseModule


class SidebarItem(QPushButton):
    def __init__(self, icon, text, module_id, parent=None):
        super().__init__(parent)
        self.module_id = module_id
        self.full_text = text
        self.icon_char = icon
        self.is_collapsed = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(40)
        self._hovered = False
        self._refresh()

    def set_collapsed(self, collapsed):
        self.is_collapsed = collapsed
        self._refresh()

    def enterEvent(self, e):
        self._hovered = True
        self._refresh()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._refresh()
        super().leaveEvent(e)

    def _refresh(self):
        t = T()
        txt = (
            self.icon_char
            if self.is_collapsed
            else f"{self.icon_char}   {self.full_text}"
        )
        self.setText(txt)

        bw = t.get("border_width", 3)
        ff = t.get("font_family", "'Inter', 'Segoe UI', 'Arial', sans-serif")
        if self._hovered:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["accent"]}; color: #FFFFFF;
                    border: {bw}px solid {t["glass_border"]}; border-radius: 0px;
                    text-align: left; padding-left: 12px;
                    font-family: {ff}; font-size: 11px; font-weight: 900;
                }}
            """)
        elif self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["bg_card2"]}; color: {t["accent"]};
                    border: {bw}px solid {t["glass_border"]}; border-radius: 0px;
                    text-align: left; padding-left: 12px;
                    font-family: {ff}; font-size: 11px; font-weight: 900;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {t["bg_card"]}; color: {t["text"]};
                    border: {bw}px solid {t["glass_border"]}; border-radius: 0px;
                    text-align: left; padding-left: 12px;
                    font-family: {ff}; font-size: 11px; font-weight: 900;
                }}
            """)


class Sidebar(QFrame):
    module_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = False
        self.setFixedWidth(200)
        self._build_ui()

    def _build_ui(self):
        t = T()
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 20, 10, 20)
        self.lay.setSpacing(8)

        # Botão Toggle
        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle)
        self.lay.addWidget(self.btn_toggle, 0, Qt.AlignCenter)
        self.lay.addSpacing(20)

        # Itens
        self.items = []
        modules = [
            ("🏠", "Início", "welcome"),
            ("📊", "Gantt", "gantt"),
            ("🏭", "Flowsheet", "flowsheet"),
            ("🔀", "BPMN", "bpmn"),
            ("📋", "EAP", "eap"),
            ("📝", "Canvas", "canvas"),
            ("🎯", "5W2H", "w5h2"),
            ("🐟", "Ishikawa", "ishikawa"),
        ]

        self.group = []
        for icon, name, mid in modules:
            btn = SidebarItem(icon, name, mid)
            btn.clicked.connect(lambda _, m=mid: self.module_requested.emit(m))
            self.lay.addWidget(btn)
            self.items.append(btn)
            self.group.append(btn)

        self.lay.addStretch()
        self._apply_style()

    def toggle(self):
        self.is_collapsed = not self.is_collapsed
        self.setFixedWidth(60 if self.is_collapsed else 200)
        self.btn_toggle.setText("☰" if self.is_collapsed else "✕")
        for item in self.items:
            item.set_collapsed(self.is_collapsed)

    def set_active(self, module_id):
        for it in self.items:
            it.setChecked(it.module_id == module_id)

    def _apply_style(self):
        t = T()
        bw = t.get("border_width", 3)
        bdr = t["glass_border"]
        self.setStyleSheet(f"""
            QFrame {{ 
                background: {t["bg_card"]}; 
                border-right: {bw + 1}px solid {bdr};
            }}
        """)
        self.btn_toggle.setStyleSheet(
            f"background: {t['accent']}; color: #FFFFFF; font-size: 18px; font-weight: 900; border: {bw}px solid {bdr}; border-radius: 0px;"
        )


from proeng.modules.flowsheet import _FlowsheetModule
from proeng.modules.gantt import _GanttModule
from proeng.modules.eap import _EAPModule
from proeng.modules.bpmn import _BPMNModule
from proeng.modules.canvas import _CanvasModule
from proeng.modules.ishikawa import _IshikawaModule
from proeng.modules.w5h2 import _W5H2Module


# ─────────────────────────────────────────────────────────────────────────────
#  WELCOME SCREEN
# ─────────────────────────────────────────────────────────────────────────────

MODULE_PREVIEWS = {
    "gantt": {
        "name": "Gantt Chart",
        "desc": "Cronograma de projetos com calculo de caminho critico (CPM).",
        "color1": "#1a4a8b",
        "color2": "#0d2847",
        "icon": "GNT",
    },
    "flowsheet": {
        "name": "PFD Flowsheet",
        "desc": "Modelagem de fluxos industriais com equipamentos e linhas de processo.",
        "color1": "#1a6b4a",
        "color2": "#0d4a33",
        "icon": "PFD",
    },
    "bpmn": {
        "name": "BPMN Modeler",
        "desc": "Desenho e analise de processos de negocio com notacao BPMN.",
        "color1": "#1a3a6b",
        "color2": "#0d2647",
        "icon": "BPMN",
    },
    "eap": {
        "name": "EAP / WBS",
        "desc": "Estrutura analitica do projeto com hierarquia de escopo.",
        "color1": "#6b4a1a",
        "color2": "#4a3210",
        "icon": "WBS",
    },
    "canvas": {
        "name": "Project Model Canvas",
        "desc": "Planejamento estrategico de iniciativas e projetos.",
        "color1": "#4a1a6b",
        "color2": "#321047",
        "icon": "PMC",
    },
    "w5h2": {
        "name": "Plano 5W2H",
        "desc": "Plano de acao com definicao de responsabilidades e custos.",
        "color1": "#1a4a6b",
        "color2": "#0d3047",
        "icon": "5W2H",
    },
    "ishikawa": {
        "name": "Ishikawa",
        "desc": "Analise de causa raiz para melhoria continua de processos.",
        "color1": "#6b1a2a",
        "color2": "#470d18",
        "icon": "6M",
    },
}


def _generate_module_preview(module_id: str, size: QSize) -> QPixmap:
    """Gera uma imagem representativa do módulo via QPainter."""
    info = MODULE_PREVIEWS.get(module_id, {})
    c1 = QColor(info.get("color1", "#1a2a4a"))
    c2 = QColor(info.get("color2", "#0d1a30"))
    icon = info.get("icon", "📦")

    px = QPixmap(size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    # Fundo solido
    p.fillRect(QRectF(0, 0, size.width(), size.height()), QBrush(c1))
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), 12, 12)
    p.fillPath(path, QBrush(c1))

    # Grid de mock
    p.setPen(QPen(QColor("#333333"), 1))
    step_x = size.width() // 6
    step_y = size.height() // 5
    for i in range(1, 6):
        p.drawLine(i * step_x, 0, i * step_x, size.height())
    for j in range(1, 5):
        p.drawLine(0, j * step_y, size.width(), j * step_y)

    # Mock shapes dependendo do módulo — Desenhos Premium
    if module_id == "flowsheet":
        # Equipamentos industriais: Bombas, Trocadores e Tanques
        p.setPen(QPen(QColor(100, 200, 255, 200), 1.5))
        p.setBrush(QBrush(QColor(40, 120, 200, 80)))

        # Tanque (Cilindro vertical)
        p.drawRoundedRect(QRectF(30, 40, 40, 70), 5, 5)
        # Trocador (Círculo com espiral)
        p.drawEllipse(QPointF(110, 50), 22, 22)
        p.drawArc(QRectF(95, 35, 30, 30), 0, 180 * 16)
        # Separador (Horizontal)
        p.setBrush(QBrush(QColor(60, 180, 220, 90)))
        p.drawRoundedRect(QRectF(150, 70, 70, 35), 8, 8)
        # Bomba (Círculo pequeno)
        p.drawEllipse(QPointF(60, 130), 15, 15)

        # Tubulações com gradiente
        pen_pipe = QPen(QColor(160, 220, 255, 180), 2)
        p.setPen(pen_pipe)
        p.drawLine(70, 75, 88, 50)  # Tanque -> Trocador
        p.drawLine(132, 50, 150, 85)  # Trocador -> Separador
        p.drawLine(60, 110, 60, 115)  # Tanque -> Bomba

    elif module_id == "bpmn":
        # Raias e Fluxos
        p.setPen(QPen(QColor(150, 200, 255, 160), 1))
        # Cabeçalho da Raia
        p.setBrush(QBrush(QColor(40, 80, 180, 100)))
        p.drawRect(10, 10, 25, size.height() - 20)

        # Atividades e Gateways
        p.setBrush(QBrush(QColor(50, 100, 220, 80)))
        # Evento Início (Verde)
        p.setPen(QPen(QColor("#41CD52"), 2))
        p.drawEllipse(QPointF(60, 50), 12, 12)
        # Tarefa 1
        p.setPen(QPen(QColor(200, 220, 255, 200), 1.5))
        p.drawRoundedRect(QRectF(90, 35, 60, 30), 6, 6)
        # Gateway (Diamond)
        p.drawPolygon(
            QPolygonF(
                [QPointF(190, 50), QPointF(205, 65), QPointF(190, 80), QPointF(175, 65)]
            )
        )
        # Tarefa 2 (Baixo)
        p.drawRoundedRect(QRectF(160, 100, 60, 30), 6, 6)

        # Conexões
        p.setPen(QPen(QColor(200, 220, 255, 120), 1.5))
        p.drawLine(72, 50, 90, 50)
        p.drawLine(150, 50, 175, 65)

    elif module_id == "eap":
        # Árvore Hierárquica Estritamente Profissional
        p.setPen(QPen(QColor(255, 180, 80, 180), 1.5))
        p.setBrush(QBrush(QColor(200, 140, 40, 90)))
        # Nível 1
        p.drawRoundedRect(95, 15, 75, 28, 4, 4)
        # Nível 2
        for x in [30, 160]:
            p.drawRoundedRect(x, 60, 65, 24, 3, 3)
            p.drawLine(132, 43, x + 32, 60)
        # Nível 3
        for x in [15, 65, 145, 195]:
            p.drawRoundedRect(x, 105, 45, 20, 2, 2)
            px_parent = 62 if x < 100 else 192
            p.drawLine(px_parent, 84, x + 22, 105)

    elif module_id == "canvas":
        # Blocos do Canvas com Cores Significativas
        colors = ["#1a3a6b", "#1a6b4a", "#6b4a1a", "#4a1a6b", "#6b1a2a"]
        blocks = [
            (10, 10, 45, 100, 0),
            (60, 10, 45, 45, 1),
            (110, 10, 45, 100, 2),
            (60, 65, 45, 45, 3),
            (160, 10, 45, 100, 4),
            (210, 10, 45, 45, 0),
            (10, 120, 110, 45, 1),
            (130, 120, 120, 45, 2),
        ]
        for rx, ry, rw, rh, ci in blocks:
            p.setPen(QPen(QColor(colors[ci]).lighter(), 1))
            p.setBrush(QBrush(QColor(colors[ci])))
            p.setOpacity(0.6)
            p.drawRoundedRect(QRectF(rx, ry, rw, rh), 4, 4)
        p.setOpacity(1.0)

    elif module_id == "w5h2":
        # Matriz Alternada
        row_h = 18
        for i in range(7):
            y = 20 + i * (row_h + 4)
            p.setPen(QPen(Qt.NoPen))
            p.setBrush(QBrush(QColor(255, 255, 255, 20 if i % 2 == 0 else 40)))
            p.drawRect(10, y, size.width() - 20, row_h)
            # Simular colunas
            p.setPen(QPen(QColor(255, 255, 255, 60), 0.5))
            for x in [30, 80, 130, 180]:
                p.drawLine(x, y, x, y + row_h)
        # Cabeçalho
        p.setBrush(QBrush(QColor(100, 200, 255, 80)))
        p.drawRect(10, 5, size.width() - 20, 12)

    elif module_id == "ishikawa":
        # Diagrama de Espinha Completo
        p.setPen(QPen(QColor(255, 100, 100, 220), 2.5))
        mid_y = size.height() // 2 + 5
        p.drawLine(15, mid_y, size.width() - 50, mid_y)
        # Cabeça seta
        p.drawPolygon(
            QPolygonF(
                [
                    QPointF(size.width() - 50, mid_y),
                    QPointF(size.width() - 65, mid_y - 8),
                    QPointF(size.width() - 65, mid_y + 8),
                ]
            )
        )

        # Espinhas principais
        p.setPen(QPen(QColor(255, 150, 150, 180), 1.8))
        for x in [50, 110, 170]:
            # Topo
            p.drawLine(x, mid_y, x + 35, mid_y - 50)
            # Fundo
            p.drawLine(x, mid_y, x + 35, mid_y + 50)
            # Sub-causas (tiny lines)
            p.setPen(QPen(QColor(255, 150, 150, 100), 1))
            p.drawLine(x + 15, mid_y - 20, x + 35, mid_y - 20)
            p.drawLine(x + 15, mid_y + 20, x + 35, mid_y + 20)

    p.end()
    return px

    p.end()
    return px


class ModuleCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, parent=None):
        super().__init__(parent)
        info = MODULE_PREVIEWS[module_id]
        self.module_id = module_id
        self.setMinimumSize(240, 220)
        self.setMaximumWidth(240)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("moduleCard")
        self._hovered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedHeight(105)
        self._refresh_preview()
        self._preview_lbl.setScaledContents(True)
        layout.addWidget(self._preview_lbl)

        info_widget = QWidget()
        info_widget.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(16, 12, 16, 14)
        info_layout.setSpacing(6)

        ff = t_font = T().get("font_family", "'Inter', 'Segoe UI', 'Arial', sans-serif")
        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont(ff.replace("'", ""), 11, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont(ff.replace("'", ""), 9))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(46)
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        info_layout.addWidget(desc_lbl)
        info_layout.addStretch(1)

        info_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(info_widget)
        self._update_style(False)

    def _refresh_preview(self):
        t = T()
        path = f"proeng/resources/screenshots/{self.module_id}_{t['name']}.png"
        if os.path.exists(path):
            self._preview_lbl.setPixmap(QPixmap(path))
        else:
            px = _generate_module_preview(self.module_id, QSize(240, 105))
            self._preview_lbl.setPixmap(px)

    def _update_style(self, hovered: bool):
        t = T()
        bw = t.get("border_width", 3)
        border_color = t["glass_border"]
        bg_color = t["bg_card2"] if hovered else t["bg_card"]
        ff = t.get("font_family", "'Segoe UI', 'Arial', sans-serif")

        self.setStyleSheet(f"""
            QFrame#moduleCard {{
                background-color: {bg_color};
                border-radius: 0px;
                border: {bw}px solid {border_color};
            }}
            QWidget#cardInfo {{ background: transparent; }}
            QLabel {{ color: {t["text"]}; background: transparent; border: none; font-family: {ff}; font-weight: bold; }}
        """)
        self.update()

    def paintEvent(self, event):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)

        if self._hovered:
            p.translate(4, 4)

        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if not self._hovered:
            p.save()
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(
                QRectF(r.left() + sx * 0.5, r.top() + sy * 0.5, r.width(), r.height())
            )
            p.restore()

        p.setBrush(QColor(t["bg_card2"] if self._hovered else t["bg_card"]))
        p.setPen(QPen(QColor("#000000"), bw))
        p.drawRect(r)
        p.end()
        super().paintEvent(event)

    def enterEvent(self, e):
        self._hovered = True
        self._update_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._update_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


# ─────────────────────────────────────────────────────────────────────────────
#  GALERIA DE EXEMPLOS
# ─────────────────────────────────────────────────────────────────────────────


class GalleryItem(QFrame):
    def __init__(self, title, module_key, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 220)
        self._hover = False
        self.module_key = module_key
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        self.img_lbl = QLabel()
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setFixedSize(290, 155)
        lay.addWidget(self.img_lbl)

        ff = T().get("font_family", "'Inter', 'Segoe UI', 'Arial', sans-serif")
        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setFont(QFont(ff.replace("'", ""), 10, QFont.Bold))
        self.title_lbl.setStyleSheet("padding: 4px;")
        lay.addWidget(self.title_lbl)

        self._refresh()

    def _refresh(self):
        t = T()
        path = f"proeng/resources/screenshots/{self.module_key}_{t['name']}.png"
        if os.path.exists(path):
            self.img_lbl.setPixmap(QPixmap(path))
        else:
            px = _generate_module_preview(self.module_key, QSize(290, 155))
            self.img_lbl.setPixmap(px)

        self.title_lbl.setStyleSheet(
            f"color: {t['text']}; font-family: {t.get('font_family', "'Segoe UI', 'Arial', sans-serif")};"
        )
        self._style()

    def _style(self):
        t = T()
        bw = t.get("border_width", 3)
        border_color = "#000000"
        bg_color = t["bg_card2"] if self._hover else t["bg_card"]

        self.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border: {bw}px solid {border_color};
                border-radius: 0px;
            }}
        """)
        self.update()

    def paintEvent(self, event):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)

        if self._hover:
            p.translate(4, 4)

        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if not self._hover:
            p.save()
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(
                QRectF(r.left() + sx * 0.5, r.top() + sy * 0.5, r.width(), r.height())
            )
            p.restore()

        p.setBrush(QColor(t["bg_card2"] if self._hover else t["bg_card"]))
        p.setPen(QPen(QColor("#000000"), bw))
        p.drawRect(r)
        p.end()
        super().paintEvent(event)

    def enterEvent(self, e):
        self._hover = True
        self._style()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self._style()
        super().leaveEvent(e)


class ScreenshotGallery(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFixedHeight(250)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.layout_h = QHBoxLayout(container)
        self.layout_h.setContentsMargins(10, 0, 10, 0)
        self.layout_h.setSpacing(16)

        items_data = [
            ("PFD Flowsheet", "flowsheet"),
            ("EAP / WBS", "eap"),
            ("BPMN Modeler", "bpmn"),
            ("Project Model Canvas", "canvas"),
            ("Ishikawa", "ishikawa"),
            ("Plano 5W2H", "w5h2"),
        ]
        self.items = []
        for title, key in items_data:
            it = GalleryItem(title, key)
            self.items.append(it)
            self.layout_h.addWidget(it)

        self.setWidget(container)

    def refresh_theme(self):
        for it in self.items:
            it._refresh()


# ─────────────────────────────────────────────────────────────────────────────
#  CARROSSEL DE EXEMPLOS (LADO ESQUERDO)
# ─────────────────────────────────────────────────────────────────────────────


class ScreenshotCarousel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(450)  # Aumentado conforme solicitado
        self.current_idx = 0
        self.items_data = [
            (
                "PFD Flowsheet",
                "flowsheet",
                "Ferramenta para diagramas de processo com tubulacoes e equipamentos industriais.",
            ),
            (
                "EAP / WBS",
                "eap",
                "Organizacao hierarquica do escopo e pacotes de trabalho do projeto.",
            ),
            (
                "BPMN Modeler",
                "bpmn",
                "Modelagem de processos de negocio com eventos, tarefas e gateways.",
            ),
            (
                "Project Model Canvas",
                "canvas",
                "Planejamento estrategico visual com blocos de decisao e entrega.",
            ),
            (
                "Ishikawa",
                "ishikawa",
                "Analise de causa raiz para falhas e oportunidades de melhoria.",
            ),
            (
                "Plano 5W2H",
                "w5h2",
                "Plano de acao orientado a execucao, prazo, responsavel e custo.",
            ),
        ]

        self._build_ui()

        # Sistema de Animação de Fade
        self.opacity_effect = QGraphicsOpacityEffect(self.img_lbl)
        self.img_lbl.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_with_fade)
        self.timer.start(3000)  # Ajustado para 3 segundos

    def _build_ui(self):
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(10, 20, 10, 10)
        self.main_lay.setSpacing(8)

        # Container de imagem proporcional
        self.frame = QFrame()
        self.frame.setFixedHeight(280)
        self.frame_lay = QVBoxLayout(self.frame)
        self.frame_lay.setContentsMargins(8, 8, 8, 8)

        self.img_lbl = QLabel()
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.frame_lay.addWidget(self.img_lbl)

        self.main_lay.addWidget(self.frame)

        # Indicadores (Dots)
        self.dots_lay = QHBoxLayout()
        self.dots_lay.setAlignment(Qt.AlignCenter)
        self.dots_lay.setSpacing(6)
        self.dots = []
        for _ in range(len(self.items_data)):
            dot = QFrame()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"border-radius: 3px; background: {T()['accent_dim']};")
            self.dots.append(dot)
            self.dots_lay.addWidget(dot)
        self.main_lay.addLayout(self.dots_lay)

        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.main_lay.addWidget(self.title_lbl)

        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Arial", 8))
        self.desc_lbl.setAlignment(Qt.AlignCenter)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumHeight(30)
        self.main_lay.addWidget(self.desc_lbl)

        self._refresh()

    def _refresh(self):
        t = T()
        title, key, desc = self.items_data[self.current_idx]

        # Somente no Carrossel: tenta carregar os screenshots reais
        path = f"proeng/resources/screenshots/{key}_{t['name']}.png"
        if os.path.exists(path):
            self.img_lbl.setPixmap(QPixmap(path))
        else:
            # Fallback para o desenho programático se o arquivo não existir
            px = _generate_module_preview(key, QSize(450, 300))
            self.img_lbl.setPixmap(px)

        self.title_lbl.setText(title)
        self.desc_lbl.setText(desc)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignCenter)

        # Estilização Premium
        self.title_lbl.setStyleSheet(
            f"color: {t['accent_bright']}; text-transform: uppercase; letter-spacing: 1px;"
        )
        self.desc_lbl.setStyleSheet(
            f"color: {t['text_dim']}; font-style: italic; padding: 0 10px;"
        )

        # Moldura com borda solida
        bw = t.get("border_width", 3)
        self.frame.setStyleSheet(f"""
            QFrame {{
                background: {t["bg_card"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
            }}
        """)

        # Atualizar Dots
        for i, dot in enumerate(self.dots):
            if i == self.current_idx:
                dot.setStyleSheet(
                    f"border-radius: 4px; background: {t['accent_bright']}; width: 20px;"
                )
                dot.setFixedWidth(24)
            else:
                dot.setStyleSheet(f"border-radius: 4px; background: {t['accent_dim']};")
                dot.setFixedWidth(8)

    def _next_with_fade(self):
        # Fade Out -> Change Pixmap -> Fade In
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.1)
        self.fade_anim.finished.connect(self._change_and_fade_in)
        self.fade_anim.start()

    def _change_and_fade_in(self):
        try:
            self.fade_anim.finished.disconnect(self._change_and_fade_in)
        except:
            pass
        self.current_idx = (self.current_idx + 1) % len(self.items_data)
        self._refresh()
        self.fade_anim.setStartValue(0.1)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def refresh_theme(self):
        self._refresh()


class BrutalistModuleCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, block_color: str, parent=None):
        super().__init__(parent)
        info = MODULE_PREVIEWS[module_id]
        self.module_id = module_id
        self.block_color = block_color
        self.setMinimumSize(220, 180)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("brutCard")
        self._hovered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        color_strip = QFrame()
        color_strip.setFixedHeight(14)
        color_strip.setObjectName("colorStrip")
        color_strip.setStyleSheet(f"background: {block_color}; border: none;")
        layout.addWidget(color_strip)

        info_widget = QWidget()
        info_widget.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(14, 14, 14, 14)
        info_layout.setSpacing(6)

        icon_lbl = QLabel(info["icon"])
        icon_lbl.setFont(QFont("Courier New", 22, QFont.Bold))
        icon_lbl.setStyleSheet("color: #000000; background: transparent; border: none;")
        info_layout.addWidget(icon_lbl)

        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont("Courier New", 11, QFont.Bold))
        title_lbl.setStyleSheet(
            "color: #000000; background: transparent; border: none;"
        )
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont("Courier New", 8))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #333333; background: transparent; border: none;")
        desc_lbl.setMinimumHeight(40)
        info_layout.addWidget(desc_lbl)
        info_layout.addStretch(1)

        layout.addWidget(info_widget)
        self._update_style(False)

    def _update_style(self, hovered: bool):
        offset = 10 if hovered else 8
        self.setStyleSheet(f"""
            QFrame#brutCard {{
                background-color: #FFFFFF;
                border: 4px solid #000000;
                border-radius: 0px;
            }}
            QWidget#cardInfo {{ background: transparent; }}
        """)
        self.setGraphicsEffect(None)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(offset)
        shadow.setYOffset(offset)
        shadow.setColor(QColor("#000000"))
        self.setGraphicsEffect(shadow)

    def enterEvent(self, e):
        self._hovered = True
        self._update_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._update_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


class BrutalistQuickAccess(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("quickAccess")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("ACESSO RAPIDO")
        title.setFont(QFont("Courier New", 14, QFont.Bold))
        title.setStyleSheet("color: #000000; background: transparent; border: none;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #000000; border: none; max-height: 3px;")
        layout.addWidget(sep)

        self.btn_new = QPushButton("+  NOVO PROJETO")
        self.btn_new.setFixedHeight(48)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setFont(QFont("Courier New", 12, QFont.Bold))

        self.btn_open = QPushButton(">  ABRIR PROJETO")
        self.btn_open.setFixedHeight(48)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setFont(QFont("Courier New", 12, QFont.Bold))

        layout.addWidget(self.btn_new)
        layout.addWidget(self.btn_open)
        layout.addStretch()

        self._style()

    def _style(self):
        self.setStyleSheet(f"""
            QFrame#quickAccess {{
                background: #FFD600;
                border: 4px solid #000000;
            }}
            QPushButton {{
                background: #FFFFFF;
                color: #000000;
                border: 3px solid #000000;
                border-radius: 0px;
                font-weight: bold;
                font-family: 'Courier New';
            }}
            QPushButton:hover {{
                background: #000000;
                color: #FFD600;
            }}
        """)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(8)
        shadow.setYOffset(8)
        shadow.setColor(QColor("#000000"))
        self.setGraphicsEffect(shadow)


class BrutalistProfileBlock(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("profileBlock")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("STATUS")
        title.setFont(QFont("Courier New", 14, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF; background: transparent; border: none;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #FFFFFF; border: none; max-height: 3px;")
        layout.addWidget(sep)

        self.status_lbl = QLabel("PRONTO")
        self.status_lbl.setFont(QFont("Courier New", 20, QFont.Bold))
        self.status_lbl.setStyleSheet(
            "color: #FFFFFF; background: transparent; border: none;"
        )
        layout.addWidget(self.status_lbl)

        self.info_lbl = QLabel("Nenhum projeto aberto")
        self.info_lbl.setFont(QFont("Courier New", 9))
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setStyleSheet(
            "color: #E0E0E0; background: transparent; border: none;"
        )
        layout.addWidget(self.info_lbl)
        layout.addStretch()

        self._style()

    def _style(self):
        self.setStyleSheet(f"""
            QFrame#profileBlock {{
                background: #1565C0;
                border: 4px solid #000000;
            }}
        """)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(8)
        shadow.setYOffset(8)
        shadow.setColor(QColor("#000000"))
        self.setGraphicsEffect(shadow)

    def update_status(self, project_name):
        if project_name:
            self.status_lbl.setText("ATIVO")
            self.info_lbl.setText(project_name)
        else:
            self.status_lbl.setText("PRONTO")
            self.info_lbl.setText("Nenhum projeto aberto")


class BrutalistExampleBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("exampleBar")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        title = QLabel("PROJETOS EXEMPLO")
        title.setFont(QFont("Courier New", 11, QFont.Bold))
        title.setStyleSheet("color: #000000; background: transparent; border: none;")
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.ex_buttons = []
        examples = [
            ("R", "Refinaria"),
            ("A", "Amonia"),
            ("E", "ETA"),
            ("C", "Caldeira"),
            ("M", "Mineracao"),
        ]
        for letter, name in examples:
            btn = QPushButton(f"[{letter}] {name}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Courier New", 9, QFont.Bold))
            btn.setFixedHeight(36)
            real_name = {
                "Refinaria": "Refinaria",
                "Amonia": "Producao de Amonia",
                "ETA": "Tratamento de Agua (ETA)",
                "Caldeira": "Caldeira Industrial",
                "Mineracao": "Linha de Mineracao",
            }[name]
            btn.clicked.connect(lambda _, n=real_name: None)
            btn_row.addWidget(btn)
            self.ex_buttons.append(btn)

        layout.addLayout(btn_row)
        self._style()

    def _style(self):
        self.setStyleSheet(f"""
            QFrame#exampleBar {{
                background: #FFFFFF;
                border: 4px solid #000000;
            }}
            QPushButton {{
                background: #F5F0E8;
                color: #000000;
                border: 3px solid #000000;
                border-radius: 0px;
                font-weight: bold;
                font-family: 'Courier New';
            }}
            QPushButton:hover {{
                background: #E65100;
                color: #FFFFFF;
            }}
        """)
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(6)
        shadow.setYOffset(6)
        shadow.setColor(QColor("#000000"))
        self.setGraphicsEffect(shadow)


class WelcomeScreen(QWidget):
    open_module = pyqtSignal(str)
    new_project = pyqtSignal()
    open_project = pyqtSignal()
    load_example = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        t = T()
        is_nb = t["name"] == "neo_brutalist"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════════════
        # HEADER - Logo e botões principais
        header = QWidget()
        header.setMinimumHeight(120)
        header_main_layout = QVBoxLayout(header)
        header_main_layout.setContentsMargins(20, 15, 20, 15)
        header_main_layout.setSpacing(6)
        header_main_layout.setAlignment(Qt.AlignCenter)

        # Logo
        self.logo_lbl = QLabel("PRO ENG")
        self.logo_lbl.setFont(QFont("Arial", 22, QFont.Black))
        self.logo_lbl.setAlignment(Qt.AlignCenter)

        # Subtítulo
        self.sub_lbl = QLabel("Engenharia Estrategica")
        self.sub_lbl.setFont(QFont("Arial", 8, QFont.Bold))
        self.sub_lbl.setAlignment(Qt.AlignCenter)

        # Botões principais
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(10)

        self.btn_new = QPushButton("NOVO")
        self.btn_new.setFixedSize(100, 32)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_new.clicked.connect(self.new_project.emit)

        self.btn_open = QPushButton("ABRIR")
        self.btn_open.setFixedSize(100, 32)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setFont(QFont("Arial", 10, QFont.Bold))
        self.btn_open.clicked.connect(self.open_project.emit)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_open)

        header_main_layout.addWidget(self.logo_lbl)
        header_main_layout.addWidget(self.sub_lbl)
        header_main_layout.addLayout(btn_row)
        main_layout.addWidget(header)

        # ═══════════════════════════════════════════════════════════════════
        # CONTEÚDO PRINCIPAL
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(20, 15, 20, 15)
        content_layout.setSpacing(20)

        # ESQUERDA: Carrossel
        self.carousel = ScreenshotCarousel()
        content_layout.addWidget(self.carousel, 45)

        # DIREITA: Grid de Módulos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setSpacing(15)
        grid.setAlignment(Qt.AlignCenter)

        label_tools = QLabel("FERRAMENTAS")
        label_tools.setFont(QFont("Arial", 10, QFont.Bold))
        label_tools.setAlignment(Qt.AlignCenter)
        grid.addWidget(label_tools, 0, 0, 1, 3, Qt.AlignCenter)

        module_ids = list(MODULE_PREVIEWS.keys())
        block_colors = [
            "#2E7D32",
            "#1565C0",
            "#C62828",
            "#E65100",
            "#6A1B9A",
            "#00838F",
        ]

        for i, mid in enumerate(module_ids):
            card = ModuleCardNB(mid, block_colors[i % len(block_colors)])
            card.clicked.connect(self.open_module.emit)
            row = (i // 3) + 1
            col = i % 3
            grid.addWidget(card, row, col)

        for c in range(3):
            grid.setColumnStretch(c, 1)

        scroll.setWidget(cards_container)
        content_layout.addWidget(scroll, 55)

        main_layout.addWidget(content_container, 1)

        self.refresh_theme()

    def _create_block(self, bg_color, title_text, title_height):
        block = QFrame()
        block.setFrameShape(QFrame.NoFrame)
        block.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 4px solid #000000;
            }}
        """)

        if title_text:
            lay = QVBoxLayout(block)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(0)

            title = QLabel(title_text)
            title.setFixedHeight(title_height)
            title.setFont(QFont("Arial", 11, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            title.setStyleSheet("""
                background-color: #000000;
                color: #FFFFFF;
                letter-spacing: 2px;
            """)
            lay.addWidget(title)

            content = QWidget()
            lay.addWidget(content)

            block._content_layout = QVBoxLayout(content)
            block._content_layout.setContentsMargins(15, 15, 15, 15)
            block._content_layout.setSpacing(10)

            return block
        return block

    def refresh_theme(self):
        t = T()
        is_nb = t["name"] == "neo_brutalist"

        if is_nb:
            self.setStyleSheet(f"background-color: {t['bg_app']};")

            # Estilo Logo
            ff = t.get("font_family", "Arial, sans-serif")
            self.logo_lbl.setStyleSheet(
                f"color: #000000; font-size: 22px; font-family: {ff}; font-weight: 900;"
            )
            self.sub_lbl.setStyleSheet(
                f"color: #333333; font-size: 8px; font-family: {ff}; font-weight: bold;"
            )

            # Botões principais
            self.btn_new.setStyleSheet("""
                QPushButton {
                    background-color: #FF5722;
                    color: #FFFFFF;
                    border: 3px solid #000000;
                    border-radius: 0px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-family: Arial;
                }
                QPushButton:hover {
                    background-color: #E64A19;
                    border: 3px solid #000000;
                }
            """)

            self.btn_open.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 3px solid #000000;
                    border-radius: 0px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-family: Arial;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                    border: 3px solid #000000;
                }
            """)

            # Atualizar cards de módulos
            for card in self.findChildren(ModuleCardNB):
                card._update_style()

            # Atualizar carousel
            if hasattr(self, "carousel"):
                self.carousel.refresh_theme()
        else:
            # Estilo para outros temas (glassmorphism)
            glass_border = t.get("glass_border", "#CCCCCC")
            self.setStyleSheet(f"background-color: {t['bg_app']};")

            self.logo_lbl.setStyleSheet(
                f"color: {t['text']}; font-size: 24px; font-family: Segoe UI; font-weight: bold;"
            )
            self.sub_lbl.setStyleSheet(f"color: {t['text_dim']};")

            self.btn_new.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t["accent"]};
                    color: white;
                    border: 2px solid {glass_border};
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {t["accent_bright"]};
                }}
            """)

            self.btn_open.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t["bg_card"]};
                    color: {t["text"]};
                    border: 2px solid {glass_border};
                    border-radius: 6px;
                    padding: 12px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {t["bg_card2"]};
                }}
            """)


class ModuleCardNB(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, accent_color: str, parent=None):
        super().__init__(parent)
        info = MODULE_PREVIEWS[module_id]
        self.module_id = module_id
        self.accent_color = accent_color
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumSize(180, 160)
        self.setMaximumWidth(200)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Área de ícone
        icon_area = QWidget()
        icon_area.setFixedHeight(60)
        icon_area.setStyleSheet(
            f"background-color: {accent_color}; border-bottom: 4px solid #000000;"
        )
        icon_lay = QVBoxLayout(icon_area)
        icon_lay.setContentsMargins(10, 10, 10, 10)

        icon_lbl = QLabel(info.get("icon", "📊"))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 28px;")
        icon_lay.addWidget(icon_lbl)

        lay.addWidget(icon_area)

        # Info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(6)

        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont("Arial", 8))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(36)
        info_layout.addWidget(desc_lbl)

        lay.addWidget(info_widget)
        self._update_style()

    def _update_style(self):
        t = T()
        is_nb = t["name"] == "neo_brutalist"

        if is_nb:
            if self._hovered:
                self.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF;
                        border: 4px solid #000000;
                    }
                    QLabel { color: #000000; background: transparent; }
                """)
            else:
                self.setStyleSheet("""
                    QFrame {
                        background-color: #FFFFFF;
                        border: 4px solid #000000;
                    }
                    QLabel { color: #000000; background: transparent; }
                """)
        else:
            border_col = t.get("glass_border", "#CCCCCC")
            bg = t["bg_card2"] if self._hovered else t["bg_card"]
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: 2px solid {border_col};
                    border-radius: 8px;
                }}
                QLabel {{ color: {t["text"]}; background: transparent; }}
            """)

    def enterEvent(self, e):
        self._hovered = True
        self._update_style()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._update_style()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────────────────


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = AppProject()
        self.setWindowTitle("PRO ENG - Início")
        self.setGeometry(80, 60, 1440, 880)

        # Frameless Window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # Using themes.py colors

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_palette()

        # Layout Principal (Vertical)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Import e Adição da NavBar (Barra Superior)
        from proeng.ui.nav_bar import NavBar

        self.nav_bar = NavBar(
            lambda: self._navigate_to_module("welcome"),
            self._toggle_theme_action,
            self._on_module_help,
        )
        self.nav_bar.example_requested.connect(self._on_load_example)
        main_layout.addWidget(self.nav_bar)

        self._stack = QStackedWidget()
        self._modules = {}

        # Welcome screen (índice 0)
        self._welcome = WelcomeScreen()
        self._welcome.new_project.connect(self._new_project)
        self._welcome.open_project.connect(self._open_project)
        self._welcome.open_module.connect(self._navigate_to_module)
        self._welcome.load_example.connect(self._on_load_example)
        self._stack.addWidget(self._welcome)

        main_layout.addWidget(self._stack, 1)

        # Barra de Status
        self.statusBar().setStyleSheet(
            f"background: {T()['bg_app']}; color: {T()['text_muted']}; border-top: 1px solid {T()['accent_dim']};"
        )
        self.statusBar().showMessage("Pronto")

        # MenuBar (Integrated inside the layout if screen is small? For now keep it hidden or move it)
        menubar = self.menuBar()
        menubar.hide()  # We can access actions via shortcuts or module-specific UI
        self._create_menu()
        self.showMaximized()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # ═══════════════════════════════════════════════════════════════════
    #   NAVEGAÇÃO
    # ═══════════════════════════════════════════════════════════════════

    def _navigate_to_module(self, module_id: str):
        """Navega para um módulo específico pelo ID."""
        if module_id == "welcome":
            self._stack.setCurrentIndex(0)
            self.setWindowTitle("PRO ENG - Início")
            return

        if module_id not in self._modules:
            # Lazy Loading do módulo
            mod_class = {
                "gantt": _GanttModule,
                "flowsheet": _FlowsheetModule,
                "eap": _EAPModule,
                "bpmn": _BPMNModule,
                "canvas": _CanvasModule,
                "ishikawa": _IshikawaModule,
                "w5h2": _W5H2Module,
            }.get(module_id)

            if mod_class:
                mod_widget = mod_class()
                self._modules[module_id] = mod_widget
                self._stack.addWidget(mod_widget)

        if module_id in self._modules:
            idx = self._stack.indexOf(self._modules[module_id])
            self._stack.setCurrentIndex(idx)
            title = MODULE_PREVIEWS.get(module_id, {}).get("name", "Módulo")
            self.setWindowTitle(f"PRO ENG - {title}")

    def _on_load_example(self, example_name):
        """Manipula o sinal da NavBar para carregar um projeto de exemplo."""
        ans = QMessageBox.question(
            self,
            "Carregar Exemplo",
            f"Isso irá apagar seu desenho atual para carregar o exemplo '{example_name}'.\n\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        # 1. Garante que estamos no flowsheet
        self._navigate_to_module("flowsheet")

        # 2. Obtém o widget do flowsheet e carrega
        fw = self._modules.get("flowsheet")
        if fw and hasattr(fw, "_inner"):
            fw._inner.load_example(example_name)

    # ═══════════════════════════════════════════════════════════════════
    #   BARRA DE MENUS
    # ═══════════════════════════════════════════════════════════════════
    def _create_menu(self):
        try:
            t = T()
            bw = t.get("border_width", 3)
            menu_style = f"""
                QMenu {{
                    background-color: {t["bg_card"]};
                    color: {t["text"]};
                    border: {bw}px solid {t["glass_border"]};
                    border-radius: 0px;
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 6px 24px;
                    border-radius: 0px;
                }}
                QMenu::item:selected {{
                    background-color: {t["accent"]};
                    color: white;
                }}
                QMenu::separator {{
                    height: 2px;
                    background: {t["glass_border"]};
                    margin: 4px 8px;
                }}
            """
        except:
            menu_style = ""

        # --- MENU ARQUIVO ---
        file_menu = QMenu(self)
        file_menu.setStyleSheet(menu_style)

        new_act = QAction("Novo Projeto", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("Abrir Projeto...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        file_menu.addSeparator()

        save_act = QAction("Salvar", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        save_as_act = QAction("Salvar como...", self)
        save_as_act.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        # Submenu Exportar
        export_menu = file_menu.addMenu("Exportar / Imprimir")
        export_menu.setStyleSheet(menu_style)

        png_act = QAction("Imagem (PNG)", self)
        png_act.triggered.connect(lambda: self._on_export("png"))
        export_menu.addAction(png_act)

        pdf_act = QAction("Documento (PDF)", self)
        pdf_act.setShortcut("Ctrl+P")
        pdf_act.triggered.connect(lambda: self._on_export("pdf"))
        export_menu.addAction(pdf_act)

        file_menu.addSeparator()

        home_act = QAction("Ir para Início", self)
        home_act.triggered.connect(lambda: self._navigate_to_module("welcome"))
        file_menu.addAction(home_act)

        file_menu.addSeparator()

        exit_act = QAction("Sair", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        self.nav_bar._btn_file.setMenu(file_menu)

        # --- MENU MÓDULOS ---
        modules_menu = QMenu(self)
        modules_menu.setStyleSheet(menu_style)
        modules_info = [
            ("welcome", "Início"),
            ("flowsheet", "PFD Flowsheet"),
            ("bpmn", "BPMN Modeler"),
            ("eap", "Gerador EAP"),
            ("canvas", "PM Canvas"),
            ("w5h2", "Plano 5W2H"),
            ("ishikawa", "Ishikawa"),
        ]
        for mid, label in modules_info:
            act = QAction(label, self)
            act.triggered.connect(lambda _, m=mid: self._navigate_to_module(m))
            modules_menu.addAction(act)

        self.nav_bar._btn_modules.setMenu(modules_menu)

        # Adicionamos ações fantasmas no menubar escondido para manter os atalhos globais (Ctrl+S, etc)
        # O Qt gerencia atalhos melhor se estiverem em um QMenuBar ou QAction adicionado à janela
        self.addActions([new_act, open_act, save_act, pdf_act])

    # ═══════════════════════════════════════════════════════════════════
    #   AÇÕES DE MÓDULO (EXPORT, ZOOM, HELP)
    # ═══════════════════════════════════════════════════════════════════

    def _on_export(self, fmt):
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.warning(
                self,
                "Ação Inválida",
                "Por favor, abra uma ferramenta para exportar seu trabalho.",
            )
            return

        # Tenta obter a view para exportação
        view = None
        # Preferencialmente via BaseModule
        if isinstance(mod, BaseModule):
            view = mod.get_view()
        # Compatibilidade com módulos antigos/embutidos
        if view is None and hasattr(mod, "get_view"):
            try:
                view = mod.get_view()
            except Exception:
                view = None
        if view is None and hasattr(mod, "_inner") and hasattr(mod._inner, "view"):
            view = mod._inner.view
        if view is None and hasattr(mod, "_inner") and hasattr(mod._inner, "canvas"):
            view = mod._inner.canvas

        if view:
            _export_view(view, fmt, self)
        else:
            QMessageBox.warning(
                self, "Exportar", "Este módulo não suporta exportação direta."
            )

    def _on_zoom_action(self, action):
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            return

        # Tenta executar métodos de zoom no módulo ou no seu widget interno
        target = mod
        if not hasattr(target, "zoom_in") and hasattr(mod, "_inner"):
            target = mod._inner

        try:
            if action == "in":
                if hasattr(target, "zoom_in"):
                    target.zoom_in()
            elif action == "out":
                if hasattr(target, "zoom_out"):
                    target.zoom_out()
            elif action == "reset":
                if hasattr(target, "reset_zoom"):
                    target.reset_zoom()
        except:
            pass

    def _on_module_help(self):
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.information(
                self,
                "Ajuda: Início",
                "Bem-vindo ao PRO ENG!\n\nSelecione um dos módulos à direita ou "
                "pelo menu 'Módulos' para iniciar seu projeto.",
            )
            return

        help_txt = getattr(
            mod, "help_text", "Guia rápido não disponível para este módulo."
        )
        title = self.windowTitle().replace("PRO ENG - ", "")
        QMessageBox.information(self, f"Guia: {title}", help_txt)

    # ═══════════════════════════════════════════════════════════════════
    #   SINCRONIZAÇÃO DE PROJETO
    # ═══════════════════════════════════════════════════════════════════

    def _sync_all_to_project(self):
        for m_id, widget in self._modules.items():
            if hasattr(widget, "get_state"):
                self.project.update_module_state(m_id, widget.get_state())

    def _sync_project_to_all(self):
        for m_id, widget in self._modules.items():
            if hasattr(widget, "set_state"):
                widget.set_state(self.project.get_module_state(m_id))

    def _new_project(self):
        ans = QMessageBox.question(
            self,
            "Novo Projeto",
            "Sua área de trabalho atual será apagada. Deseja continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self.project = AppProject()
            self.setWindowTitle("PRO ENG  - Sem Título")
            for widget in self._modules.values():
                if hasattr(widget, "set_state"):
                    widget.set_state({})
            # Volta para a Welcome
            self._navigate_to_module("welcome")

    def _save_project(self):
        self._sync_all_to_project()
        if not self.project.has_file:
            self._save_project_as()
        else:
            try:
                self.project.save(self.project.filename)
                self.statusBar().showMessage(
                    f"✅ Projeto Salvo: {os.path.basename(self.project.filename)}", 3000
                )
                self.setWindowTitle(
                    f"PRO ENG  - {os.path.basename(self.project.filename)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _save_project_as(self):
        self._sync_all_to_project()
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Projeto Como", "", "Projeto PRO ENG (*.proeng)"
        )
        if path:
            if not path.endswith(".proeng"):
                path += ".proeng"
            try:
                self.project.save(path)
                self.statusBar().showMessage(
                    f"✅ Projeto Salvo: {os.path.basename(path)}", 3000
                )
                self.setWindowTitle(f"PRO ENG  - {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto", "", "Projeto PRO ENG (*.proeng)"
        )
        if path:
            try:
                self.project.load(path)
                modules_info = [
                    ("welcome", "🏠", "Início"),
                    ("flowsheet", "🏭", "PFD Flowsheet"),
                    ("bpmn", "🔀", "BPMN Modeler"),
                    ("eap", "📋", "Gerador EAP"),
                    ("canvas", "📝", "PM Canvas"),
                    ("w5h2", "🎯", "Plano 5W2H"),
                    ("ishikawa", "🐟", "Ishikawa"),
                ]
                for mid, _icon, _label in modules_info:
                    if mid != "welcome":
                        self._get_or_create_module(mid)
                self._sync_project_to_all()
                self.setWindowTitle(f"PRO ENG - {os.path.basename(path)}")
                self.statusBar().showMessage("✅ Projeto Carregado com Sucesso!", 3000)
                # Navega para o Flowsheet automaticamente
                self._navigate_to_module("flowsheet")
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro ao Abrir", f"Erro carregando o arquivo: {str(e)}"
                )

    # ═══════════════════════════════════════════════════════════════════
    #   CONTROLE DE UI
    # ═══════════════════════════════════════════════════════════════════

    def _get_or_create_module(self, module_name):
        if module_name == "welcome":
            self._stack.setCurrentWidget(self._welcome)
            return self._welcome

        builders = {
            "gantt": _GanttModule,
            "flowsheet": _FlowsheetModule,
            "eap": _EAPModule,
            "bpmn": _BPMNModule,
            "canvas": _CanvasModule,
            "ishikawa": _IshikawaModule,
            "w5h2": _W5H2Module,
        }
        if module_name not in self._modules:
            w = builders[module_name]()
            w.setStyleSheet(f"background: {T()['bg_app']};")
            self._stack.addWidget(w)
            self._modules[module_name] = w

            if hasattr(w, "set_state") and self.project.get_module_state(module_name):
                w.set_state(self.project.get_module_state(module_name))

        return self._modules[module_name]

    def _toggle_theme_action(self):
        from proeng.core.themes import T, cycle_theme

        cycle_theme()
        self._on_theme_toggle_refresh()

    def _on_theme_toggle_refresh(self):
        self._setup_palette()
        t = T()

        # Welcome
        if hasattr(self._welcome, "refresh_theme"):
            self._welcome.refresh_theme()

        # NavBar
        if hasattr(self, "nav_bar"):
            self.nav_bar._apply_style()

        # Modules
        for mod in self._modules.values():
            mod.setStyleSheet(f"background:{t['bg_app']};")
            # Refresh the module itself
            if hasattr(mod, "refresh_theme"):
                try:
                    mod.refresh_theme()
                except:
                    pass

            # Refresh all children
            for w in mod.findChildren(QWidget):
                if hasattr(w, "refresh_theme"):
                    try:
                        w.refresh_theme()
                    except:
                        pass

            # Special case for Graphics Views
            for gv in mod.findChildren(QGraphicsView):
                try:
                    gv.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                    if gv.scene():
                        gv.scene().update()
                except:
                    pass

            # Special case for ListWidgets
            for sp in mod.findChildren(QListWidget):
                if hasattr(sp, "_apply_palette_style"):
                    try:
                        sp._apply_palette_style()
                    except:
                        pass

    def _setup_palette(self):
        t = T()
        p = QPalette()
        p.setColor(QPalette.Window, QColor(t["bg_app"]))
        p.setColor(QPalette.WindowText, QColor(t["text"]))
        p.setColor(QPalette.Base, QColor(t["bg_input"]))
        p.setColor(QPalette.AlternateBase, QColor(t["bg_card2"]))
        p.setColor(QPalette.Text, QColor(t["text"]))
        p.setColor(QPalette.Button, QColor(t["bg_card"]))
        p.setColor(QPalette.ButtonText, QColor(t["text"]))
        p.setColor(QPalette.Highlight, QColor(t["accent"]))
        if _is_nb(t):
            p.setColor(QPalette.HighlightedText, QColor(t["text"]))
        else:
            p.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.instance().setPalette(p)

        # Stylesheet Global — Neo-Brutalist (sem gradientes, sem transparencia)
        glass_border = t.get("glass_border", "#CCCCCC")
        is_nb = _is_nb(t)
        bw = t.get("border_width", 3)
        br = t.get("border_radius", 0)
        shadow = t.get("shadow", "#000000")
        sx = t.get("shadow_offset_x", 4)
        sy = t.get("shadow_offset_y", 4)
        global_style = f"""
            QMainWindow {{ background-color: {t["bg_app"]}; }}
            
            /* Campos de Texto e Listas */
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QListView, QListWidget {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 8px;
                selection-background-color: {t["accent"]};
                selection-color: white;
            }}
            QLineEdit:focus, QTextEdit:focus, QListView:focus {{
                border: {bw + 1}px solid {t["accent_bright"]};
                background-color: {t["bg_app"]};
            }}
            
            QListWidget::item, QListView::item {{
                padding: 8px;
                border-radius: {br}px;
            }}
            QListWidget::item:selected, QListView::item:selected {{
                background-color: {t["accent"]};
                color: white;
            }}
            QListWidget::item:hover, QListView::item:hover {{
                background-color: {t["bg_card2"]};
            }}

            /* ScrollBars */
            QScrollBar:vertical {{
                border: {bw}px solid {t["glass_border"]};
                background: {t["bg_card"]};
                width: {12 + bw * 2}px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {t["accent"]};
                min-height: 30px;
                border-radius: {br}px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t["accent_bright"]}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

            QScrollBar:horizontal {{
                border: {bw}px solid {t["glass_border"]};
                background: {t["bg_card"]};
                height: {12 + bw * 2}px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {t["accent"]};
                min-width: 30px;
                border-radius: {br}px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

            /* Tooltips */
            QToolTip {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 6px;
            }}

            /* Menus e ComboBoxes */
            QMenu {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: {t["accent"]};
                color: white;
                border-radius: {br}px;
            }}
            
            QMessageBox {{
                background-color: {t["bg_app"]};
            }}
            QMessageBox QLabel {{
                color: {t["text"]};
            }}
            QMessageBox QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 8px 20px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {t["accent"]};
                color: white;
            }}

            /* QComboBox */
            QComboBox {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 6px;
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                selection-background-color: {t["accent"]};
                selection-color: white;
            }}

            /* QTableWidget */
            QTableWidget {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                gridline-color: {t["glass_border"]};
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
            QHeaderView::section {{
                background-color: {t["bg_card2"]};
                color: {t["text"]};
                border: 1px solid {t["glass_border"]};
                padding: 6px;
                font-weight: bold;
            }}

            /* QDateEdit */
            QDateEdit {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 6px;
            }}

            /* QCheckBox */
            QCheckBox {{
                color: {t["text"]};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                background: {t["bg_input"]};
            }}
            QCheckBox::indicator:checked {{
                background: {t["accent"]};
                border-color: {t["glass_border"]};
            }}

            /* QPushButton — Neo-Brutalist with hover/press microinteraction */
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 8px 16px;
                font-weight: bold;
                font-family: {t.get("font_family", "'Inter', sans-serif")};
            }}
            QPushButton:hover {{
                background-color: {t["accent"]};
                color: #FFFFFF;
                border-color: {t["glass_border"]};
            }}
            QPushButton:pressed {{
                background-color: {t["accent_bright"]};
                color: #FFFFFF;
            }}

            /* QSplitter */
            QSplitter::handle {{
                background-color: {t["glass_border"]};
            }}
            QSplitter::handle:horizontal {{
                width: {bw}px;
            }}
            QSplitter::handle:vertical {{
                height: {bw}px;
            }}

            /* QSlider */
            QSlider::groove:horizontal {{
                border: {bw}px solid {t["glass_border"]};
                background: {t["bg_card"]};
                height: 8px;
                border-radius: {br}px;
            }}
            QSlider::handle:horizontal {{
                background: {t["accent"]};
                border: {bw}px solid {t["glass_border"]};
                width: 18px;
                margin: -6px 0;
                border-radius: {br}px;
            }}
            QSlider::groove:vertical {{
                border: {bw}px solid {t["glass_border"]};
                background: {t["bg_card"]};
                width: 8px;
                border-radius: {br}px;
            }}
            QSlider::handle:vertical {{
                background: {t["accent"]};
                border: {bw}px solid {t["glass_border"]};
                height: 18px;
                margin: 0 -6px;
                border-radius: {br}px;
            }}

            /* QDialog */
            QDialog {{
                background-color: {t["bg_app"]};
                color: {t["text"]};
            }}

            /* QTabWidget */
            QTabWidget::pane {{
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
            }}
            QTabBar::tab {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: {br}px;
                padding: 8px 16px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {t["accent"]};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {t["bg_card2"]};
            }}
        """
        QApplication.instance().setStyleSheet(global_style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.showMaximized()
    sys.exit(app.exec_())
