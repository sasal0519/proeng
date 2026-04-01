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

from proeng.core.themes import T
from proeng.core.project import AppProject
from proeng.core.utils import _export_view, _c
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
        self._refresh()

    def set_collapsed(self, collapsed):
        self.is_collapsed = collapsed
        self._refresh()

    def _refresh(self):
        t = T()
        txt = (
            self.icon_char
            if self.is_collapsed
            else f"{self.icon_char}   {self.full_text}"
        )
        self.setText(txt)

        # Estilo Dinâmico Premium
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t["text_dim"]};
                border: none; border-radius: 8px;
                text-align: left; padding-left: 12px;
                font-family: 'Segoe UI'; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {t["bg_card"]}; color: {t["accent_bright"]}; }}
            QPushButton:checked {{ 
                background: {t["accent_dim"]}; color: {t["accent_bright"]}; 
                border-left: 3px solid {t["accent_bright"]}; 
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
        self.setStyleSheet(f"""
            QFrame {{ 
                background: {t["bg_card"]}; 
                border-right: 1px solid {t["accent_dim"]};
            }}
            QPushButton#toggle {{
                background: transparent; border: 1px solid {t["accent_dim"]};
                border-radius: 6px; color: {t["accent"]}; font-size: 14px;
            }}
        """)
        self.btn_toggle.setStyleSheet(
            f"background: transparent; color: {t['accent']}; font-size: 18px; border: none;"
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

    # Fundo gradient
    grad = QLinearGradient(0, 0, size.width(), size.height())
    grad.setColorAt(0, c1)
    grad.setColorAt(1, c2)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), 12, 12)
    p.fillPath(path, QBrush(grad))

    # Grid de mock
    p.setPen(QPen(QColor(255, 255, 255, 20), 1))
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

        # Preview image
        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedHeight(105)
        self._refresh_preview()
        self._preview_lbl.setScaledContents(True)
        layout.addWidget(self._preview_lbl)

        # Info area
        info_widget = QWidget()
        info_widget.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 8, 12, 10)
        info_layout.setSpacing(4)

        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont("Segoe UI", 8))
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
        # Preferência por screenshots reais de alta fidelidade
        path = f"proeng/resources/screenshots/{self.module_id}_{t['name']}.png"
        if os.path.exists(path):
            self._preview_lbl.setPixmap(QPixmap(path))
        else:
            # Fallback para o desenho programático detalhado
            px = _generate_module_preview(self.module_id, QSize(240, 105))
            self._preview_lbl.setPixmap(px)

    def _update_style(self, hovered: bool):
        t = T()
        glass_border = t.get("glass_border", "rgba(255,255,255,30)")
        border_color = t["accent_bright"] if hovered else glass_border
        bg_color = t["bg_card2"] if hovered else t["bg_card"]
        self.setStyleSheet(f"""
            QFrame#moduleCard {{
                background-color: {bg_color};
                border-radius: 12px;
                border: 1px solid {border_color};
            }}
            QWidget#cardInfo {{ background: transparent; border-radius: 0 0 12px 12px; }}
            QLabel {{ color: {t["text"]}; background: transparent; border: none; }}
        """)

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
        lay.setContentsMargins(8, 8, 8, 8)

        self.img_lbl = QLabel()
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setFixedSize(300, 170)
        lay.addWidget(self.img_lbl)

        self.title_lbl = QLabel(title)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_lbl.setStyleSheet("padding: 2px 4px;")
        lay.addWidget(self.title_lbl)

        self._refresh()

    def _refresh(self):
        t = T()
        # Tenta carregar screenshot real primeiro
        path = f"proeng/resources/screenshots/{self.module_key}_{t['name']}.png"
        if os.path.exists(path):
            self.img_lbl.setPixmap(QPixmap(path))
        else:
            # Fallback para o desenho programático se o arquivo não existir
            px = _generate_module_preview(self.module_key, QSize(300, 170))
            self.img_lbl.setPixmap(px)

        self.title_lbl.setStyleSheet(f"color: {t['text']};")
        self._style()

    def _style(self):
        t = T()
        glass_border = t.get("glass_border", "rgba(255,255,255,30)")
        border = t["accent_bright"] if self._hover else glass_border
        bg_col1 = t["bg_card2"] if self._hover else t["bg_card"]
        bg_col2 = t["bg_app"]
        self.setStyleSheet(f"""
            QFrame {{ 
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {bg_col1}, stop:1 {bg_col2}); 
                border: 1px solid {border}; 
                border-radius: 12px; 
            }}
        """)

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
        self.main_lay.setContentsMargins(15, 40, 15, 15)  # Mais respiro no topo
        self.main_lay.setSpacing(12)

        # Container de imagem proporcional (40% da largura, mantendo aspecto 1.5)
        self.frame = QFrame()
        self.frame.setFixedHeight(410)
        self.frame_lay = QVBoxLayout(self.frame)
        self.frame_lay.setContentsMargins(10, 10, 10, 10)

        self.img_lbl = QLabel()
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.frame_lay.addWidget(self.img_lbl)

        self.main_lay.addWidget(self.frame)

        # Indicadores (Dots)
        self.dots_lay = QHBoxLayout()
        self.dots_lay.setAlignment(Qt.AlignCenter)
        self.dots_lay.setSpacing(8)
        self.dots = []
        for _ in range(len(self.items_data)):
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"border-radius: 4px; background: {T()['accent_dim']};")
            self.dots.append(dot)
            self.dots_lay.addWidget(dot)
        self.main_lay.addLayout(self.dots_lay)

        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.main_lay.addWidget(self.title_lbl)

        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Segoe UI", 11))
        self.desc_lbl.setAlignment(Qt.AlignCenter)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumHeight(45)
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

        # Moldura com efeito Glass
        glass_border = t.get("glass_border", "rgba(255,255,255,40)")
        self.frame.setStyleSheet(f"""
            QFrame {{
                background: {t["bg_card"]};
                border: 1px solid {glass_border};
                border-radius: 24px;
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header Ultra-Compacto e Centralizado ───────────────────────────
        header = QWidget()
        header.setMinimumHeight(280)
        header_main_layout = QVBoxLayout(header)
        header_main_layout.setContentsMargins(0, 20, 0, 20)
        header_main_layout.setSpacing(5)
        header_main_layout.setAlignment(Qt.AlignCenter)

        self.logo_lbl = QLabel("PRO ENG")
        self.logo_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.logo_lbl.setAlignment(Qt.AlignCenter)

        self.sub_lbl = QLabel(
            "Solução integrada para modelagem e engenharia estratégica."
        )
        self.sub_lbl.setFont(QFont("Segoe UI", 10))
        self.sub_lbl.setAlignment(Qt.AlignCenter)
        self.sub_lbl.setStyleSheet("color: rgba(255,255,255,180); margin-bottom: 10px;")

        # Botões Principais (Novo / Abrir)
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(15)

        self.btn_new = QPushButton("Novo Projeto")
        self.btn_new.setFixedSize(220, 42)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_project.emit)

        self.btn_open = QPushButton("Abrir Projeto...")
        self.btn_open.setFixedSize(210, 42)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_project.emit)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_open)

        header_main_layout.addWidget(self.logo_lbl)
        header_main_layout.addWidget(self.sub_lbl)
        header_main_layout.addLayout(btn_row)
        header_main_layout.addSpacing(15)

        # Seção de Exemplos Centralizada (Compacta)
        ex_title = QLabel("PROJETOS DE EXEMPLO")
        ex_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        ex_title.setAlignment(Qt.AlignCenter)
        ex_title.setStyleSheet(
            f"color: {t['accent']}; letter-spacing: 1px; margin-bottom: 5px;"
        )
        header_main_layout.addWidget(ex_title)

        ex_row = QHBoxLayout()
        ex_row.setAlignment(Qt.AlignCenter)
        ex_row.setSpacing(6)

        self.ex_buttons = []
        examples = [
            ("Refinaria", "R"),
            ("Amônia", "A"),
            ("ETA", "E"),
            ("Caldeira", "C"),
            ("Mineração", "M"),
        ]
        for name, icon in examples:
            btn = QPushButton(f"{icon}  {name}")
            btn.setFixedSize(110, 32)
            btn.setCursor(Qt.PointingHandCursor)
            real_name = name if name != "Amônia" else "Produção de Amônia"
            if name == "ETA":
                real_name = "Tratamento de Água (ETA)"
            if name == "Caldeira":
                real_name = "Caldeira Industrial"
            if name == "Mineração":
                real_name = "Linha de Mineração"

            btn.clicked.connect(lambda _, n=real_name: self.load_example.emit(n))
            ex_row.addWidget(btn)
            self.ex_buttons.append(btn)

        header_main_layout.addLayout(ex_row)
        main_layout.addWidget(header)

        # ── Separator ───────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)

        # ── Área de Conteúdo Lado a Lado (Proporcional) ──────────────────────
        content_row = QHBoxLayout()
        content_row.setContentsMargins(60, 20, 60, 40)
        content_row.setSpacing(60)
        main_layout.addLayout(content_row, 1)

        # Esquerda: Carrossel (Aumentado para 40% da largura)
        self.carousel = ScreenshotCarousel()
        content_row.addWidget(self.carousel, 40)

        # Direita: Grid de Módulos (60%)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(0, 10, 0, 10)
        grid.setSpacing(30)
        grid.setAlignment(Qt.AlignCenter)

        label_tools = QLabel("SELECIONE UMA FERRAMENTA")
        label_tools.setFont(QFont("Segoe UI", 12, QFont.Bold))
        label_tools.setStyleSheet(
            f"color: {t['accent']}; letter-spacing: 1px;"
        )  # Usando accent principal para melhor contraste
        label_tools.setAlignment(Qt.AlignCenter)
        grid.addWidget(label_tools, 0, 0, 1, 3, Qt.AlignCenter)

        module_ids = list(MODULE_PREVIEWS.keys())
        for i, mid in enumerate(module_ids):
            card = ModuleCard(mid)
            card.clicked.connect(self.open_module.emit)
            row = (i // 3) + 1
            col = i % 3
            grid.addWidget(card, row, col, Qt.AlignCenter)

        # colunas com peso igual
        for c in range(3):
            grid.setColumnStretch(c, 1)

        scroll.setWidget(cards_container)
        # Lado Direito: Grid de Módulos (com screenshots industriais)
        content_row.addWidget(scroll, 60)

        self.refresh_theme()  # Apply all styles after widgets are created

    def refresh_theme(self):
        t = T()
        glass_border = t.get("glass_border", "rgba(255,255,255,30)")

        # Estilo do Logo e Subtítulo
        self.logo_lbl.setStyleSheet(
            f"color: {t['accent_bright']}; letter-spacing: 2px; font-weight: 800;"
        )
        self.sub_lbl.setStyleSheet(f"color: {t['text_dim']};")

        # Botões Modernos
        btn_base = f"""
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: 1px solid {glass_border};
                border-radius: 12px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {t["accent"]};
                color: white;
                border-color: {t["accent_bright"]};
            }}
        """
        self.btn_new.setStyleSheet(
            btn_base
            + f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['accent']}, stop:1 {t['accent_bright']}); color: white; border: 2px solid {t['accent']}; font-weight: 800; }}"
        )
        self.btn_open.setStyleSheet(btn_base)

        ex_style = f"""
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text_dim"]};
                border: 1px solid {glass_border};
                border-radius: 21px; /* Pill */
                font-family: 'Segoe UI'; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t["accent_dim"]};
                color: {t["accent_bright"]};
                border-color: {t["accent_bright"]};
            }}
        """
        for b in self.ex_buttons:
            b.setStyleSheet(ex_style)

        # Refresh components
        self.carousel.refresh_theme()
        # Gallery logic
        gallery = self.findChild(ScreenshotGallery)
        if gallery:
            gallery.refresh_theme()

        for card in self.findChildren(ModuleCard):
            card._refresh_preview()
            if hasattr(card, "_update_style"):
                card._update_style(False)


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
            menu_style = f"""
                QMenu {{
                    background-color: {t["bg_card"]};
                    color: {t["text"]};
                    border: 1px solid {t["accent_dim"]};
                    border-radius: 6px;
                    padding: 5px;
                }}
                QMenu::item {{
                    padding: 6px 24px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {t["accent"]};
                    color: white;
                }}
                QMenu::separator {{
                    height: 1px;
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
        from proeng.core.themes import T, set_theme

        new = "light" if T()["name"] == "dark" else "dark"
        set_theme(new)
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
        # Usamos bg_input para a base de campos de texto (melhora visibilidade no dark)
        p.setColor(QPalette.Base, QColor(t["bg_input"]))
        p.setColor(QPalette.AlternateBase, QColor(t["bg_card2"]))
        p.setColor(QPalette.Text, QColor(t["text"]))
        p.setColor(QPalette.Button, QColor(t["bg_card"]))
        p.setColor(QPalette.ButtonText, QColor(t["text"]))
        p.setColor(QPalette.Highlight, QColor(t["accent"]))
        p.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.instance().setPalette(p)

        # Stylesheet Global para Modernidade e Transparência
        glass_border = t.get("glass_border", "rgba(255,255,255,30)")
        global_style = f"""
            QMainWindow {{ background-color: {t["bg_app"]}; }}
            
            /* Campos de Texto e Listas Modernos */
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QListView, QListWidget {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: 1px solid {t["accent_dim"]};
                border-radius: 8px;
                padding: 6px;
                selection-background-color: {t["accent"]};
                selection-color: white;
            }}
            QLineEdit:focus, QTextEdit:focus, QListView:focus {{
                border: 2px solid {t["accent_bright"]};
                background-color: {t["bg_app"]};
            }}
            
            QListWidget::item, QListView::item {{
                padding: 8px;
                border-radius: 4px;
            }}
            QListWidget::item:selected, QListView::item:selected {{
                background-color: {t["accent"]};
                color: white;
            }}
            QListWidget::item:hover, QListView::item:hover {{
                background-color: {t["bg_card2"]};
            }}

            /* ScrollBars Minimalistas */
            QScrollBar:vertical {{
                border: none; background: transparent;
                width: 8px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {t["accent_dim"]};
                min-height: 30px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t["accent"]}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

            QScrollBar:horizontal {{
                border: none; background: transparent;
                height: 8px; margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: {t["accent_dim"]};
                min-width: 30px; border-radius: 4px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

            /* Tooltips Modernos */
            QToolTip {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: 1px solid {t["accent"]};
                border-radius: 4px;
                padding: 4px;
            }}

            /* Menus e ComboBoxes */
            QMenu {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: 1px solid {glass_border};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: {t["accent"]};
                color: white;
                border-radius: 4px;
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
                border: 1px solid {t["accent_dim"]};
                border-radius: 6px;
                padding: 6px 16px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {t["accent"]};
                color: white;
            }}
        """
        QApplication.instance().setStyleSheet(global_style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.showMaximized()
    sys.exit(app.exec_())
