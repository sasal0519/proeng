# -*- coding: utf-8 -*-
"""Janela principal da aplicação ProEng - Formato Workspace/Project."""
import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QStackedWidget,
    QMenuBar, QAction, QFileDialog, QMessageBox, QLabel, QSplitter,
    QGraphicsView, QSizePolicy, QScrollArea, QGridLayout, QFrame,
    QGraphicsOpacityEffect
)
from PyQt5.QtGui import (
    QIcon, QFont, QColor, QPalette, QBrush, QLinearGradient,
    QPainter, QPen, QPixmap, QPainterPath, QRadialGradient, QPolygonF
)
from PyQt5.QtCore import (
    Qt, QSize, QRectF, QPointF, pyqtSignal, QPropertyAnimation, 
    QEasingCurve, QTimer, QSequentialAnimationGroup, QPauseAnimation
)

from proeng.core.themes import T
from proeng.core.project import AppProject
from proeng.core.utils   import _export_view

from proeng.modules.flowsheet import _FlowsheetModule
from proeng.modules.eap       import _EAPModule
from proeng.modules.bpmn      import _BPMNModule
from proeng.modules.canvas    import _CanvasModule
from proeng.modules.ishikawa  import _IshikawaModule
from proeng.modules.w5h2      import _W5H2Module


# ─────────────────────────────────────────────────────────────────────────────
#  WELCOME SCREEN
# ─────────────────────────────────────────────────────────────────────────────

MODULE_PREVIEWS = {
    "flowsheet": {
        "name": "🏭 PFD Flowsheet",
        "desc": "Diagramas de fluxo de processo com tubulações e equipamentos inteligentes.",
        "color1": "#1a6b4a",
        "color2": "#0d4a33",
        "icon": "🏭",
    },
    "bpmn": {
        "name": "🔀 BPMN Modeler",
        "desc": "Modelagem e otimização de fluxos de processos de negócio.",
        "color1": "#1a3a6b",
        "color2": "#0d2647",
        "icon": "🔀",
    },
    "eap": {
        "name": "📋 Gerador EAP",
        "desc": "Estrutura Analítica do projeto para organização funcional do escopo.",
        "color1": "#6b4a1a",
        "color2": "#4a3210",
        "icon": "📋",
    },
    "canvas": {
        "name": "📝 PM Canvas",
        "desc": "Planejamento estratégico de modelos de negócio e projetos.",
        "color1": "#4a1a6b",
        "color2": "#321047",
        "icon": "📝",
    },
    "w5h2": {
        "name": "🎯 Plano 5W2H",
        "desc": "Planos de ação estruturados para execução rápida e controle.",
        "color1": "#1a4a6b",
        "color2": "#0d3047",
        "icon": "🎯",
    },
    "ishikawa": {
        "name": "🐟 Ishikawa",
        "desc": "Análise de causa raiz para resolução estruturada de problemas.",
        "color1": "#6b1a2a",
        "color2": "#470d18",
        "icon": "🐟",
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
        p.drawLine(70, 75, 88, 50)     # Tanque -> Trocador
        p.drawLine(132, 50, 150, 85)   # Trocador -> Separador
        p.drawLine(60, 110, 60, 115)   # Tanque -> Bomba

    elif module_id == "bpmn":
        # Raias e Fluxos 
        p.setPen(QPen(QColor(150, 200, 255, 160), 1))
        # Cabeçalho da Raia
        p.setBrush(QBrush(QColor(40, 80, 180, 100)))
        p.drawRect(10, 10, 25, size.height()-20)
        
        # Atividades e Gateways
        p.setBrush(QBrush(QColor(50, 100, 220, 80)))
        # Evento Início (Verde)
        p.setPen(QPen(QColor("#41CD52"), 2))
        p.drawEllipse(QPointF(60, 50), 12, 12)
        # Tarefa 1
        p.setPen(QPen(QColor(200, 220, 255, 200), 1.5))
        p.drawRoundedRect(QRectF(90, 35, 60, 30), 6, 6)
        # Gateway (Diamond)
        p.drawPolygon(QPolygonF([QPointF(190, 50), QPointF(205, 65), QPointF(190, 80), QPointF(175, 65)]))
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
            (10, 10, 45, 100, 0), (60, 10, 45, 45, 1), (110, 10, 45, 100, 2),
            (60, 65, 45, 45, 3), (160, 10, 45, 100, 4), (210, 10, 45, 45, 0),
            (10, 120, 110, 45, 1), (130, 120, 120, 45, 2)
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
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, 20 if i%2==0 else 40)))
            p.drawRect(10, y, size.width() - 20, row_h)
            # Simular colunas
            p.setPen(QPen(QColor(255, 255, 255, 60), 0.5))
            for x in [30, 80, 130, 180]:
                p.drawLine(x, y, x, y + row_h)
        # Cabeçalho
        p.setBrush(QBrush(QColor(100, 200, 255, 80)))
        p.drawRect(10, 5, size.width()-20, 12)

    elif module_id == "ishikawa":
        # Diagrama de Espinha Completo
        p.setPen(QPen(QColor(255, 100, 100, 220), 2.5))
        mid_y = size.height() // 2 + 5
        p.drawLine(15, mid_y, size.width() - 50, mid_y)
        # Cabeça seta
        p.drawPolygon(QPolygonF([QPointF(size.width()-50, mid_y), QPointF(size.width()-65, mid_y-8), QPointF(size.width()-65, mid_y+8)]))
        
        # Espinhas principais
        p.setPen(QPen(QColor(255, 150, 150, 180), 1.8))
        for x in [50, 110, 170]:
            # Topo
            p.drawLine(x, mid_y, x + 35, mid_y - 50)
            # Fundo
            p.drawLine(x, mid_y, x + 35, mid_y + 50)
            # Sub-causas (tiny lines)
            p.setPen(QPen(QColor(255, 150, 150, 100), 1))
            p.drawLine(x+15, mid_y-20, x+35, mid_y-20)
            p.drawLine(x+15, mid_y+20, x+35, mid_y+20)

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
        self.setMinimumSize(265, 265)
        self.setMaximumWidth(265)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("moduleCard")
        self._hovered = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Preview image
        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedHeight(125)
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
        desc_lbl.setMinimumHeight(55)
        desc_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        info_layout.addWidget(desc_lbl)
        info_layout.addStretch(1)

        info_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(info_widget)
        self._update_style(False)

    def _refresh_preview(self):
        # Ignora screenshots e usa os desenhos gerados (mockups) para a grade
        px = _generate_module_preview(self.module_id, QSize(265, 125))
        self._preview_lbl.setPixmap(px)

    def _update_style(self, hovered: bool):
        t = T()
        border_color = t["accent_bright"] if hovered else t["accent_dim"]
        shadow = f"border: 2px solid {border_color};" if hovered else f"border: 1px solid {t['accent_dim']};"
        self.setStyleSheet(f"""
            QFrame#moduleCard {{
                background: {t['bg_card']};
                border-radius: 12px;
                {shadow}
            }}
            QWidget#cardInfo {{ background: {t['bg_card']}; border-radius: 0 0 12px 12px; }}
            QLabel {{ color: {t['text']}; background: transparent; border: none; }}
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
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
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
        border = t["accent"] if self._hover else t["accent_dim"]
        bg = t["bg_card2"] if self._hover else t["bg_card"]
        self.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 10px; }}")

    def enterEvent(self, e): self._hover = True; self._style(); super().enterEvent(e)
    def leaveEvent(self, e): self._hover = False; self._style(); super().leaveEvent(e)

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
            ("🏭 PFD Flowsheet", "flowsheet"),
            ("📋 Gerador EAP", "eap"),
            ("🔀 BPMN Modeler", "bpmn"),
            ("📝 PM Canvas", "canvas"),
            ("🐟 Ishikawa", "ishikawa"),
            ("🎯 Plano 5W2H", "w5h2"),
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
        self.setMinimumWidth(450) # Aumentado conforme solicitado
        self.current_idx = 0
        self.items_data = [
            ("🏭 PFD Flowsheet", "flowsheet", "Ferramenta avançada para diagramas de processo com tubulações inteligentes."),
            ("📋 Gerador EAP", "eap", "Organização hierárquica e visual de todo o escopo do projeto."),
            ("🔀 BPMN Modeler", "bpmn", "Modelagem profissional de processos para otimização operacional."),
            ("📝 PM Canvas", "canvas", "Visão estratégica de modelos de negócio e novos projetos planejados."),
            ("🐟 Ishikawa", "ishikawa", "Análise estruturada para identificação e solução de falhas industriais."),
            ("🎯 Plano 5W2H", "w5h2", "Matriz ágil de execução para garantir o cumprimento de metas e prazos."),
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
        self.timer.start(3000) # Ajustado para 3 segundos

    def _build_ui(self):
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(15, 40, 15, 15) # Mais respiro no topo
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
            dot.setStyleSheet("border-radius: 4px; background: gray;")
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
        
        # Estilização Premium
        self.title_lbl.setStyleSheet(f"color: {t['accent_bright']}; text-transform: uppercase; letter-spacing: 1px;")
        self.desc_lbl.setStyleSheet(f"color: {t['text_dim']}; font-style: italic;")
        
        # Moldura com efeito Glow
        self.frame.setStyleSheet(f"""
            QFrame {{
                background: {t['bg_card']};
                border: 2px solid {t['accent']};
                border-radius: 20px;
            }}
        """)
        
        # Atualizar Dots
        for i, dot in enumerate(self.dots):
            if i == self.current_idx:
                dot.setStyleSheet(f"border-radius: 4px; background: {t['accent_bright']}; width: 20px;")
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
        try: self.fade_anim.finished.disconnect(self._change_and_fade_in)
        except: pass
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        t = T()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────────────
        header = QWidget()
        header.setMinimumHeight(200)
        header.setMaximumHeight(220)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(40, 30, 40, 20)
        header_layout.setAlignment(Qt.AlignCenter)

        logo_lbl = QLabel("⚙️ ProEng Suite • Industrial")
        logo_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        logo_lbl.setAlignment(Qt.AlignCenter)

        sub_lbl = QLabel("Solução integrada para modelagem, engenharia de processos e gestão ágil")
        sub_lbl.setFont(QFont("Segoe UI", 13))
        sub_lbl.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(16)

        self.btn_new = QPushButton("  ✨ Novo Projeto")
        self.btn_new.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.btn_new.setMinimumSize(240, 52)
        self.btn_new.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.clicked.connect(self.new_project.emit)

        self.btn_open = QPushButton("  📂 Abrir Projeto...")
        self.btn_open.setFont(QFont("Segoe UI", 13))
        self.btn_open.setMinimumSize(210, 52)
        self.btn_open.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.clicked.connect(self.open_project.emit)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_open)

        header_layout.addWidget(logo_lbl)
        header_layout.addWidget(sub_lbl)
        header_layout.addSpacing(16)
        header_layout.addLayout(btn_row)

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

        label_tools = QLabel("🛠  SELECIONE UMA FERRAMENTA")
        label_tools.setFont(QFont("Segoe UI", 12, QFont.Bold))
        label_tools.setStyleSheet(f"color: {t['accent_bright']}; letter-spacing: 1px;")
        label_tools.setAlignment(Qt.AlignLeft)
        grid.addWidget(label_tools, 0, 0, 1, 3)

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
        content_row.addWidget(scroll, 60)

        self._style()

    def _style(self):
        t = T()
        self.setStyleSheet(f"""
            WelcomeScreen {{
                background-color: {t['bg_app']};
            }}
        """)
        # Header gradient via paintEvent override is overkill; use QWidget hack
        header = self.findChild(QWidget)
        # Style buttons
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent']}, stop:1 {t['accent_bright']});
                color: #FFFFFF;
                border-radius: 10px;
                border: none;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {t['accent_bright']}, stop:1 {t['accent']});
            }}
            QPushButton:pressed {{ opacity: 0.8; }}
        """)
        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background: {t['bg_card']};
                color: {t['text']};
                border: 2px solid {t['accent_dim']};
                border-radius: 10px;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                border-color: {t['accent']};
                color: {t['accent_bright']};
            }}
        """)

    def refresh_theme(self):
        self._style()
        self.carousel.refresh_theme()
        for card in self.findChildren(ModuleCard):
            card._refresh_preview()
            card._update_style(False)


# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR RETRÁTIL
# ─────────────────────────────────────────────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project = AppProject()
        self.setWindowTitle("ProEng - Início")
        self.setGeometry(80, 60, 1440, 880)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_palette()

        # Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Pilha de Telas
        self._stack = QStackedWidget()
        self._modules = {}

        # Welcome screen (índice 0)
        self._welcome = WelcomeScreen()
        self._welcome.new_project.connect(self._new_project)
        self._welcome.open_project.connect(self._open_project)
        self._welcome.open_module.connect(self._navigate_to_module)
        self._stack.addWidget(self._welcome)

        main_layout.addWidget(self._stack, 1)

        # MenuBar
        self._create_menu()

    def resizeEvent(self, event):
        super().resizeEvent(event)

    # ═══════════════════════════════════════════════════════════════════
    #   NAVEGAÇÃO
    # ═══════════════════════════════════════════════════════════════════

    def _navigate_to_module(self, module_id: str):
        """Navega para um módulo específico pelo ID."""
        if module_id == "welcome":
            self._stack.setCurrentIndex(0)
            self.setWindowTitle("ProEng - Início")
            return

        if module_id not in self._modules:
            # Lazy Loading do módulo
            mod_class = {
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
            self.setWindowTitle(f"ProEng - {title}")

    # ═══════════════════════════════════════════════════════════════════
    #   BARRA DE MENUS
    # ═══════════════════════════════════════════════════════════════════
    def _create_menu(self):
        menubar = self.menuBar()
        menubar.clear()
        try:
            t = T()
            menubar.setStyleSheet(
                f"QMenuBar {{ background-color: {t['bg_card']}; color: {t['text']};"
                f" padding: 4px; border-bottom: 1px solid {t['accent_dim']}; }}"
                f"QMenu {{ background-color: {t['bg_card']}; color: {t['text']};"
                f" border: 1px solid {t['accent_dim']}; }}"
                f"QMenu::item:selected {{ background-color: {t['accent']}; color: #fff; }}"
            )
        except:
            pass

        file_menu = menubar.addMenu("📁 Arquivo")

        new_act = QAction("✨ Novo Projeto", self)
        new_act.setShortcut("Ctrl+N")
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("📂 Abrir Projeto...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        file_menu.addSeparator()

        save_act = QAction("💾 Salvar", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        save_as_act = QAction("💾 Salvar como...", self)
        save_as_act.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        # Submenu Exportar
        export_menu = file_menu.addMenu("⬇ Exportar / Imprimir")
        
        png_act = QAction("🖼 Imagem (PNG)", self)
        png_act.triggered.connect(lambda: self._on_export("png"))
        export_menu.addAction(png_act)
        
        pdf_act = QAction("📄 Documento (PDF)", self)
        pdf_act.setShortcut("Ctrl+P") # Padrão para Impressão
        pdf_act.triggered.connect(lambda: self._on_export("pdf"))
        export_menu.addAction(pdf_act)

        file_menu.addSeparator()

        home_act = QAction("🏠 Ir para Início", self)
        home_act.triggered.connect(lambda: self._navigate_to_module("welcome"))
        file_menu.addAction(home_act)

        file_menu.addSeparator()

        exit_act = QAction("🚪 Sair", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Módulos Menu
        modules_menu = menubar.addMenu("🛠 Módulos")
        modules_info = [
            ("welcome",   "🏠", "Início"),
            ("flowsheet", "🏭", "PFD Flowsheet"),
            ("bpmn",      "🔀", "BPMN Modeler"),
            ("eap",       "📋", "Gerador EAP"),
            ("canvas",    "📝", "PM Canvas"),
            ("w5h2",      "🎯", "Plano 5W2H"),
            ("ishikawa",  "🐟", "Ishikawa"),
        ]
        for mid, icon, label in modules_info:
            act = QAction(f"{icon}  {label}", self)
            act.triggered.connect(lambda _, m=mid: self._navigate_to_module(m))
            modules_menu.addAction(act)

        view_menu = menubar.addMenu("👁 Exibir")

        theme_act = QAction("🌗 Alternar Tema (Escuro/Claro)", self)
        theme_act.triggered.connect(self._toggle_theme_action)
        view_menu.addAction(theme_act)

        view_menu.addSeparator()

        zi_act = QAction("🔍+ Zoom In", self)
        zi_act.setShortcut("Ctrl++")
        zi_act.triggered.connect(lambda: self._on_zoom_action("in"))
        view_menu.addAction(zi_act)

        zo_act = QAction("🔍− Zoom Out", self)
        zo_act.setShortcut("Ctrl+-")
        zo_act.triggered.connect(lambda: self._on_zoom_action("out"))
        view_menu.addAction(zo_act)

        zr_act = QAction("⟳ Resetar Zoom", self)
        zr_act.setShortcut("Ctrl+0")
        zr_act.triggered.connect(lambda: self._on_zoom_action("reset"))
        view_menu.addAction(zr_act)

        # Ajuda Menu
        help_menu = menubar.addMenu("❓ Ajuda")
        
        guide_act = QAction("📖 Guia do Módulo Atual", self)
        guide_act.setShortcut("F1")
        guide_act.triggered.connect(self._on_module_help)
        help_menu.addAction(guide_act)

        about_act = QAction("ℹ Sobre o ProEng", self)
        about_act.triggered.connect(lambda: QMessageBox.about(self, "Sobre ProEng", "ProEng Suite v2.0\nSistema Integrado de Engenharia Industrial\n© 2026"))
        help_menu.addAction(about_act)

    # ═══════════════════════════════════════════════════════════════════
    #   AÇÕES DE MÓDULO (EXPORT, ZOOM, HELP)
    # ═══════════════════════════════════════════════════════════════════

    def _on_export(self, fmt):
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.warning(self, "Ação Inválida", "Por favor, abra uma ferramenta para exportar seu trabalho.")
            return
        
        # Tenta obter a view para exportação
        view = None
        if hasattr(mod, "get_view"):
            view = mod.get_view()
        elif hasattr(mod, "_inner") and hasattr(mod._inner, "view"):
            view = mod._inner.view
        elif hasattr(mod, "_inner") and hasattr(mod._inner, "canvas"):
            view = mod._inner.canvas

        if view:
            _export_view(view, fmt, self)
        else:
            QMessageBox.warning(self, "Exportar", "Este módulo não suporta exportação direta.")

    def _on_zoom_action(self, action):
        mod = self._stack.currentWidget()
        if mod == self._welcome: return
        
        # Tenta executar métodos de zoom no módulo ou no seu widget interno
        target = mod
        if not hasattr(target, "zoom_in") and hasattr(mod, "_inner"):
            target = mod._inner
            
        try:
            if action == "in":
                if hasattr(target, "zoom_in"): target.zoom_in()
            elif action == "out":
                if hasattr(target, "zoom_out"): target.zoom_out()
            elif action == "reset":
                if hasattr(target, "reset_zoom"): target.reset_zoom()
        except:
            pass

    def _on_module_help(self):
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.information(self, "Ajuda: Início", 
                "Bem-vindo ao ProEng!\n\nSelecione um dos módulos à direita ou "
                "pelo menu 'Módulos' para iniciar seu projeto.")
            return
            
        help_txt = getattr(mod, "help_text", "Guia rápido não disponível para este módulo.")
        title = self.windowTitle().replace("ProEng - ", "")
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
            self, "Novo Projeto",
            "Sua área de trabalho atual será apagada. Deseja continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.project = AppProject()
            self.setWindowTitle("ProEng  - Sem Título")
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
                self.statusBar().showMessage(f"✅ Projeto Salvo: {os.path.basename(self.project.filename)}", 3000)
                self.setWindowTitle(f"ProEng  - {os.path.basename(self.project.filename)}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _save_project_as(self):
        self._sync_all_to_project()
        path, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto Como", "", "Projeto ProEng (*.proeng)")
        if path:
            if not path.endswith(".proeng"):
                path += ".proeng"
            try:
                self.project.save(path)
                self.statusBar().showMessage(f"✅ Projeto Salvo: {os.path.basename(path)}", 3000)
                self.setWindowTitle(f"ProEng  - {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Projeto", "", "Projeto ProEng (*.proeng)")
        if path:
            try:
                self.project.load(path)
                modules_info = [
                    ("welcome",   "🏠", "Início"),
                    ("flowsheet", "🏭", "PFD Flowsheet"),
                    ("bpmn",      "🔀", "BPMN Modeler"),
                    ("eap",       "📋", "Gerador EAP"),
                    ("canvas",    "📝", "PM Canvas"),
                    ("w5h2",      "🎯", "Plano 5W2H"),
                    ("ishikawa",  "🐟", "Ishikawa"),
                ]
                for mid, _icon, _label in modules_info:
                    if mid != "welcome":
                        self._get_or_create_module(mid)
                self._sync_project_to_all()
                self.setWindowTitle(f"ProEng - {os.path.basename(path)}")
                self.statusBar().showMessage("✅ Projeto Carregado com Sucesso!", 3000)
                # Navega para o Flowsheet automaticamente
                self._navigate_to_module("flowsheet")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Abrir", f"Erro carregando o arquivo: {str(e)}")

    # ═══════════════════════════════════════════════════════════════════
    #   CONTROLE DE UI
    # ═══════════════════════════════════════════════════════════════════

    def _get_or_create_module(self, module_name):
        if module_name == "welcome":
            self._stack.setCurrentWidget(self._welcome)
            return self._welcome

        builders = {
            "flowsheet": _FlowsheetModule,
            "eap":       _EAPModule,
            "bpmn":      _BPMNModule,
            "canvas":    _CanvasModule,
            "ishikawa":  _IshikawaModule,
            "w5h2":      _W5H2Module,
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
        from proeng.core.themes import THEMES, _ACTIVE
        name = "light" if _ACTIVE["theme"]["name"] == "dark" else "dark"
        _ACTIVE["theme"] = THEMES[name]
        self._on_theme_toggle_refresh()

    def _on_theme_toggle_refresh(self):
        self._setup_palette()
        t = T()

        self._create_menu()

        # Welcome
        if hasattr(self._welcome, "refresh_theme"):
            self._welcome.refresh_theme()

        from PyQt5.QtWidgets import QListWidget
        for mod in self._modules.values():
            mod.setStyleSheet(f"background:{t['bg_app']};")
            for w in mod.findChildren(QWidget):
                if hasattr(w, "refresh_theme"):
                    try:
                        w.refresh_theme()
                    except Exception:
                        pass
            for gv in mod.findChildren(QGraphicsView):
                try:
                    gv.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                    if gv.scene():
                        gv.scene().update()
                except Exception:
                    pass
            for sp in mod.findChildren(QListWidget):
                if hasattr(sp, "_apply_palette_style"):
                    try:
                        sp._apply_palette_style()
                    except Exception:
                        pass
        self._setup_palette()

    def _setup_palette(self):
        t = T()
        p = QPalette()
        p.setColor(QPalette.Window,          QColor(t["bg_app"]))
        p.setColor(QPalette.WindowText,      QColor(t["text"]))
        p.setColor(QPalette.Base,            QColor(t["bg_card"]))
        p.setColor(QPalette.AlternateBase,   QColor(t["bg_card2"]))
        p.setColor(QPalette.Text,            QColor(t["text"]))
        p.setColor(QPalette.Button,          QColor(t["bg_card"]))
        p.setColor(QPalette.ButtonText,      QColor(t["text"]))
        p.setColor(QPalette.Highlight,       QColor(t["accent"]))
        p.setColor(QPalette.HighlightedText, QColor(t["bg_app"]))
        QApplication.instance().setPalette(p)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
