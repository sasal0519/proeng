# -*- coding: utf-8 -*-

# Módulo de interface principal da aplicação PRO ENG
# 
# Responsabilidade: Gerenciar a janela principal da aplicação desktop, orquestrar navegação 
# entre módulos de engenharia industrial (Gantt, Flowsheet, BPMN, EAP, Canvas, W5H2, Ishikawa),
# implementar sistema de temas dinâmicos (neo_brutalist, dark, light), gerenciar ciclo de vida
# de projetos e coordenar sincronização de estado entre módulos.
#
# Componentes principais:
# - SidebarItem: Botão individual de navegação na barra lateral
# - Sidebar: Container e gerenciador de estado de navegação
# - WelcomeScreen: Tela inicial com preview de módulos e acesso rápido
# - MainApp: Janela principal que coordena toda a aplicação
# - Funções auxiliares: Geração de previews programáticos, exportação de views
#
# Inputs: Eventos do usuário (cliques, redimensionamento), carregamento de arquivos de projeto
# Outputs: Interface gráfica Qt5 totalmente funcional, arquivos exportados (PNG/PDF)

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
    # Representa um botão de módulo individual na barra lateral de navegação.
    # Implementa states visuais (normal, hover, checked), comportamento de collapse
    # e emissão de sinal quando acionado.
    
    def __init__(self, icon, text, module_id, parent=None):
        # Inicializa o item da sidebar com ícone, texto, identificador do módulo e widgets pais opcionais.
        # Define propriedades de interação visual (cursor em mão), estilos iniciais e flags de estado.
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
        # Define o modo colapsado/expandido do item e força atualização visual via _refresh().
        # Quando colapsado, exibe apenas o ícone; expandido mostra "ícone + texto".
        self.is_collapsed = collapsed
        self._refresh()

    def enterEvent(self, e):
        # Ativa flag de hover quando mouse entra no widget e dispara atualização visual.
        self._hovered = True
        self._refresh()
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Desativa flag de hover quando mouse sai do widget e dispara atualização visual.
        self._hovered = False
        self._refresh()
        super().leaveEvent(e)

    def _refresh(self):
        # Atualiza texto exibido e stylesheet baseado em estado atual (collapsed, hover, checked).
        # Aplica tema dinâmico via função T() que retorna dicionário de cores do tema ativo.
        # Lógica de cores: Se hover -> destaque (accent), se checked -> background card2, senão -> card normal.
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
    # Barra lateral que agrega múltiplos SidebarItems em layout vertical.
    # Gerencia colapso/expansão global da sidebar, emite sinal quando usuário solicita módulo.
    # Implementa padrão Observer para responder a cliques dos items.
    
    module_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        # Inicializa a sidebar com tamanho fixo (200px expandido, 60px colapsado),
        # cria lista de módulos disponíveis e constrói interface visual.
        super().__init__(parent)
        self.is_collapsed = False
        self.setFixedWidth(200)
        self._build_ui()

    def _build_ui(self):
        # Cria layout vertical contendo:
        # 1. Botão toggle (☰/✕) para colapsar/expandir
        # 2. Lista de 8 SidebarItems (Início, Gantt, Flowsheet, BPMN, EAP, Canvas, 5W2H, Ishikawa)
        # 3. Stretch para empurrar items para cima
        # Conecta sinais de clique para emitir module_requested com ID do módulo.
        t = T()
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(10, 20, 10, 20)
        self.lay.setSpacing(8)

        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle)
        self.lay.addWidget(self.btn_toggle, 0, Qt.AlignCenter)
        self.lay.addSpacing(20)

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
        # Inverte estado de colapso, ajusta largura do frame, atualiza texto do botão toggle,
        # e propaga mudança de estado para todos os items via set_collapsed().
        self.is_collapsed = not self.is_collapsed
        self.setFixedWidth(60 if self.is_collapsed else 200)
        self.btn_toggle.setText("☰" if self.is_collapsed else "✕")
        for item in self.items:
            item.set_collapsed(self.is_collapsed)

    def set_active(self, module_id):
        # Marca item como ativo (checked=True) baseado em ID de módulo.
        # Todos outros items são desmarcados. Usado para destacar navegação atual.
        for it in self.items:
            it.setChecked(it.module_id == module_id)

    def _apply_style(self):
        # Aplica estilos Qt baseados no tema atual via T().
        # Configura background do frame, borda direita e estilo específico do botão toggle.
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


# Dicionário centralizado com metadados dos módulos disponíveis.
# Cada entrada contém: nome exibível, descrição, cores para preview (color1/color2),
# ícone ASCII/emoji, e tag de categorização. Usado para gerar cards, previews e validações.
MODULE_PREVIEWS = {
    "gantt": {
        "name": "Gantt Chart",
        "desc": "Cronograma de projetos com calculo de caminho critico (CPM).",
        "color1": "#1a4a8b",
        "color2": "#0d2847",
        "icon": "GNT",
        "tag": "CRONOGRAMA",
    },
    "flowsheet": {
        "name": "PFD Flowsheet",
        "desc": "Modelagem de fluxos industriais com equipamentos e linhas de processo.",
        "color1": "#1a6b4a",
        "color2": "#0d4a33",
        "icon": "PFD",
        "tag": "PROCESSOS",
    },
    "bpmn": {
        "name": "BPMN Modeler",
        "desc": "Desenho e analise de processos de negocio com notacao BPMN.",
        "color1": "#1a3a6b",
        "color2": "#0d2647",
        "icon": "BPMN",
        "tag": "PROCESSOS",
    },
    "eap": {
        "name": "EAP / WBS",
        "desc": "Estrutura analitica do projeto com hierarquia de escopo.",
        "color1": "#6b4a1a",
        "color2": "#4a3210",
        "icon": "WBS",
        "tag": "ESCOPO",
    },
    "canvas": {
        "name": "Project Model Canvas",
        "desc": "Planejamento estrategico de iniciativas e projetos.",
        "color1": "#4a1a6b",
        "color2": "#321047",
        "icon": "PMC",
        "tag": "ESTRATEGIA",
    },
    "w5h2": {
        "name": "Plano 5W2H",
        "desc": "Plano de acao com definicao de responsabilidades e custos.",
        "color1": "#1a4a6b",
        "color2": "#0d3047",
        "icon": "5W2H",
        "tag": "ACAO",
    },
    "ishikawa": {
        "name": "Ishikawa",
        "desc": "Analise de causa raiz para melhoria continua de processos.",
        "color1": "#6b1a2a",
        "color2": "#470d18",
        "icon": "6M",
        "tag": "QUALIDADE",
    },
}


def _generate_module_preview(module_id: str, size: QSize) -> QPixmap:
    # Renderiza imagem representativa do módulo usando QPainter.
    # Desenha grade de fundo e representações esquemáticas do diagrama típico de cada módulo.
    # Tenta carregar screenshot real se existir, senão gera desenho programático.
    #
    # Cada módulo tem representação visual própria:
    # - flowsheet: Desenha tanques, trocadores, bombas e linhas de processo
    # - bpmn: Desenha raias, eventos circulares, tarefas retangulares e gateways diamantados
    # - eap: Desenha hierarquia em árvore com caixas conectadas por linhas
    # - canvas: Desenha blocos coloridos representando blocos do Business Model Canvas
    # - w5h2: Desenha matriz com linhas alternadas e colunas separadas
    # - ishikawa: Desenha espinha de peixe com linha central e ramificações
    #
    # Retorna: Objeto QPixmap contendo a imagem renderizada ou fallback em caso de erro.
    info = MODULE_PREVIEWS.get(module_id, {})
    c1 = QColor(info.get("color1", "#1a2a4a"))
    c2 = QColor(info.get("color2", "#0d1a30"))
    icon = info.get("icon", "📦")

    px = QPixmap(size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)

    p.fillRect(QRectF(0, 0, size.width(), size.height()), QBrush(c1))
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), 12, 12)
    p.fillPath(path, QBrush(c1))

    # Desenha grade de fundo subdividida em 6x5 células para efeito visual
    p.setPen(QPen(QColor("#333333"), 1))
    step_x = size.width() // 6
    step_y = size.height() // 5
    for i in range(1, 6):
        p.drawLine(i * step_x, 0, i * step_x, size.height())
    for j in range(1, 5):
        p.drawLine(0, j * step_y, size.width(), j * step_y)

    # Desenha representações específicas por módulo
    if module_id == "flowsheet":
        # Desenha tanque de armazenamento, vaso cilíndrico vertical, trocador e bomba
        p.setPen(QPen(QColor(100, 200, 255, 200), 1.5))
        p.setBrush(QBrush(QColor(40, 120, 200, 80)))

        p.drawRoundedRect(QRectF(30, 40, 40, 70), 5, 5)
        p.drawEllipse(QPointF(110, 50), 22, 22)
        p.drawArc(QRectF(95, 35, 30, 30), 0, 180 * 16)
        p.setBrush(QBrush(QColor(60, 180, 220, 90)))
        p.drawRoundedRect(QRectF(150, 70, 70, 35), 8, 8)
        p.drawEllipse(QPointF(60, 130), 15, 15)

        # Desenha linhas de tubulação conectando equipamentos
        pen_pipe = QPen(QColor(160, 220, 255, 180), 2)
        p.setPen(pen_pipe)
        p.drawLine(70, 75, 88, 50)
        p.drawLine(132, 50, 150, 85)
        p.drawLine(60, 110, 60, 115)

    elif module_id == "bpmn":
        # Desenha raia vermelha à esquerda, evento de início (circulo verde), 
        # tarefa retangular, gateway diamantado e transições
        p.setPen(QPen(QColor(150, 200, 255, 160), 1))
        p.setBrush(QBrush(QColor(40, 80, 180, 100)))
        p.drawRect(10, 10, 25, size.height() - 20)

        p.setBrush(QBrush(QColor(50, 100, 220, 80)))
        p.setPen(QPen(QColor("#41CD52"), 2))
        p.drawEllipse(QPointF(60, 50), 12, 12)
        p.setPen(QPen(QColor(200, 220, 255, 200), 1.5))
        p.drawRoundedRect(QRectF(90, 35, 60, 30), 6, 6)
        p.drawPolygon(
            QPolygonF(
                [QPointF(190, 50), QPointF(205, 65), QPointF(190, 80), QPointF(175, 65)]
            )
        )
        p.drawRoundedRect(QRectF(160, 100, 60, 30), 6, 6)

        # Desenha setas de transição entre elementos
        p.setPen(QPen(QColor(200, 220, 255, 120), 1.5))
        p.drawLine(72, 50, 90, 50)
        p.drawLine(150, 50, 175, 65)

    elif module_id == "eap":
        # Desenha estrutura hierárquica: projeto raiz no topo, dois níveis intermediários,
        # e quatro elementos de nível folha na base conectados por linhas verticais
        p.setPen(QPen(QColor(255, 180, 80, 180), 1.5))
        p.setBrush(QBrush(QColor(200, 140, 40, 90)))
        p.drawRoundedRect(95, 15, 75, 28, 4, 4)
        for x in [30, 160]:
            p.drawRoundedRect(x, 60, 65, 24, 3, 3)
            p.drawLine(132, 43, x + 32, 60)
        for x in [15, 65, 145, 195]:
            p.drawRoundedRect(x, 105, 45, 20, 2, 2)
            px_parent = 62 if x < 100 else 192
            p.drawLine(px_parent, 84, x + 22, 105)

    elif module_id == "canvas":
        # Desenha 8 blocos representando seções do Business Model Canvas
        # com cores variadas e posicionamento estratégico
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
        # Desenha matriz com 7 linhas alternadas (representando 5W2H) e coluna de cabeçalho azul
        row_h = 18
        for i in range(7):
            y = 20 + i * (row_h + 4)
            p.setPen(QPen(Qt.NoPen))
            # Alterna cores de linha (branco transparente com opacidades diferentes)
            p.setBrush(QBrush(QColor(255, 255, 255, 20 if i % 2 == 0 else 40)))
            p.drawRect(10, y, size.width() - 20, row_h)
            # Desenha separadores verticais para colunas
            p.setPen(QPen(QColor(255, 255, 255, 60), 0.5))
            for x in [30, 80, 130, 180]:
                p.drawLine(x, y, x, y + row_h)
        # Desenha cabeçalho azul
        p.setBrush(QBrush(QColor(100, 200, 255, 80)))
        p.drawRect(10, 5, size.width() - 20, 12)

    elif module_id == "ishikawa":
        # Desenha espinha de peixe: linha principal horizontal com seta no final,
        # e 3 pares de ramificações secundárias com sub-ramificações terciárias
        p.setPen(QPen(QColor(255, 100, 100, 220), 2.5))
        mid_y = size.height() // 2 + 5
        # Linha principal (coluna vertebral)
        p.drawLine(15, mid_y, size.width() - 50, mid_y)
        # Seta (cabeça do peixe)
        p.drawPolygon(
            QPolygonF(
                [
                    QPointF(size.width() - 50, mid_y),
                    QPointF(size.width() - 65, mid_y - 8),
                    QPointF(size.width() - 65, mid_y + 8),
                ]
            )
        )

        # Desenha 3 espinhas secundárias (causas primárias) com ramificações terciárias
        p.setPen(QPen(QColor(255, 150, 150, 180), 1.8))
        for x in [50, 110, 170]:
            p.drawLine(x, mid_y, x + 35, mid_y - 50)
            p.drawLine(x, mid_y, x + 35, mid_y + 50)
            p.setPen(QPen(QColor(255, 150, 150, 100), 1))
            # Sub-ramificações
            p.drawLine(x + 15, mid_y - 20, x + 35, mid_y - 20)
            p.drawLine(x + 15, mid_y + 20, x + 35, mid_y + 20)

    p.end()
    return px


class ModuleCard(QFrame):
    # Card de apresentação de módulo na tela de boas-vindas.
    # Exibe imagem de preview, nome, descrição em layout vertical.
    # Implementa interatividade com efeito hover (sombra, translação) e emissão de sinal ao clique.
    
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, parent=None):
        # Inicializa card com tamanho fixo (240x220), carrega dados do módulo via MODULE_PREVIEWS,
        # cria layout vertical com preview, título e descrição, aplica estilo inicial.
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

        # Widget de preview com altura fixa
        self._preview_lbl = QLabel()
        self._preview_lbl.setFixedHeight(105)
        self._refresh_preview()
        self._preview_lbl.setScaledContents(True)
        layout.addWidget(self._preview_lbl)

        # Widget de informações (título, descrição)
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
        # Atualiza imagem de preview do card.
        # Prioridade: 1) Screenshot real do arquivo, 2) Preview programático via _generate_module_preview.
        t = T()
        path = f"proeng/resources/screenshots/{self.module_id}_{t['name']}.png"
        if os.path.exists(path):
            self._preview_lbl.setPixmap(QPixmap(path))
        else:
            px = _generate_module_preview(self.module_id, QSize(240, 105))
            self._preview_lbl.setPixmap(px)

    def _update_style(self, hovered: bool):
        # Aplica stylesheet baseado em estado de hover.
        # Quando hover=True, background becomes bg_card2; caso contrário usa bg_card.
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
        # Customiza rendering do card com sombra decorativa e borda.
        # Quando hover, translaciona 4px para cima/esquerda para efeito de levantamento.
        # Desenha sombra offset nos cantos quando não hover, depois retângulo de background.
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
        # Ativa estado hover e dispara atualização visual.
        self._hovered = True
        self._update_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Desativa estado hover e dispara atualização visual.
        self._hovered = False
        self._update_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        # Ao clique do botão esquerdo do mouse, emite sinal clicked com ID do módulo.
        # Permite que MainApp saiba qual módulo foi selecionado.
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


class GalleryItem(QFrame):
    # Item individual exibido na galeria de exemplos na tela de boas-vindas.
    # Semelhante ao ModuleCard mas com dimensões maiores e destinado a screenshot real.
    # Implementa hover com efeito visual de translação e sombra.
    
    def __init__(self, title, module_key, parent=None):
        # Inicializa item com tamanho fixo (320x220), carrega screenshot,
        # cria layout com imagem (290x155) e label de título (10px, negrito, centrado).
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
        # Carrega imagem de preview do módulo.
        # Prioridade: 1) Screenshot real, 2) Gerador programático.
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
        # Aplica stylesheet baseado no tema e estado hover.
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
        # Customiza rendering com sombra offset quando não hover.
        # Aplica translação pequena quando hover para efeito de levantamento.
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
        # Ativa estado hover e dispara atualização visual.
        self._hover = True
        self._style()
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Desativa estado hover e dispara atualização visual.
        self._hover = False
        self._style()
        super().leaveEvent(e)


class ScreenshotGallery(QScrollArea):
    # Área de scroll horizontal exibindo 6 GalleryItems em sequência.
    # Frame = NoFrame para aspecto mais limpo, scroll horizontal sempre visível, vertical desativada.
    
    def __init__(self, parent=None):
        # Inicializa área de scroll com altura fixa (250px), cria container com layout horizontal,
        # popula com 6 GalleryItems (PFD Flowsheet, EAP/WBS, BPMN, Canvas, Ishikawa, 5W2H).
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
        # Propaga atualização de tema para todos os GalleryItems.
        # Cada item recarrega screenshot e aplica estilos novos.
        for it in self.items:
            it._refresh()


class ScreenshotCarousel(QWidget):
    # Carrossel automático que cicla entre 6 módulos com animação de fade.
    # Exibe imagem, título, descrição e indicadores visuais (dots) para navegação.
    # Timer dispara transição a cada 3 segundos com animação de opacidade.
    
    def __init__(self, parent=None):
        # Inicializa com lista de 6 módulos, cria UI, configura animação de fade (400ms),
        # inicia timer de 3 segundos para acionar próximo item.
        super().__init__(parent)
        self.setMinimumWidth(450)
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

        # Configura efeito de opacidade e animação de transição suave
        self.opacity_effect = QGraphicsOpacityEffect(self.img_lbl)
        self.img_lbl.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Timer que dispara transição automática
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_with_fade)
        self.timer.start(3000)

    def _build_ui(self):
        # Cria layout vertical contendo:
        # 1. Frame com imagem escalada (280px altura)
        # 2. Linha de indicadores (dots) centrados
        # 3. Título (Arial 10px negrito, centrado, maiúscula)
        # 4. Descrição (Arial 8px, centrada, itálica, altura mínima 30px)
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(10, 20, 10, 10)
        self.main_lay.setSpacing(8)

        self.frame = QFrame()
        self.frame.setFixedHeight(280)
        self.frame_lay = QVBoxLayout(self.frame)
        self.frame_lay.setContentsMargins(8, 8, 8, 8)

        self.img_lbl = QLabel()
        self.img_lbl.setScaledContents(True)
        self.img_lbl.setAlignment(Qt.AlignCenter)
        self.frame_lay.addWidget(self.img_lbl)

        self.main_lay.addWidget(self.frame)

        # Cria linha de indicadores (dots)
        self.dots_lay = QHBoxLayout()
        self.dots_lay.setAlignment(Qt.AlignCenter)
        self.dots_lay.setSpacing(6)
        self.dots = []
        for _ in range(len(self.items_data)):
            dot = QFrame()
            dot.setFixedSize(8, 8)
            dot.setStyleSheet(f"background: {T()['accent_dim']};")
            self.dots.append(dot)
            self.dots_lay.addWidget(dot)
        self.main_lay.addLayout(self.dots_lay)

        # Cria título
        self.title_lbl = QLabel()
        self.title_lbl.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setWordWrap(True)
        self.main_lay.addWidget(self.title_lbl)

        # Cria descrição
        self.desc_lbl = QLabel()
        self.desc_lbl.setFont(QFont("Arial", 8))
        self.desc_lbl.setAlignment(Qt.AlignCenter)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setMinimumHeight(30)
        self.main_lay.addWidget(self.desc_lbl)

        self._refresh()

    def _refresh(self):
        # Atualiza conteúdo visual baseado no índice atual.
        # Carrega imagem, atualiza título/descrição, aplica estilos do tema,
        # destaca o dot correspondente ao índice.
        t = T()
        title, key, desc = self.items_data[self.current_idx]
        is_nb = t["name"] == "neo_brutalist"
        is_dark = t["name"] == "dark"
        bw = t.get("border_width", 3)

        path = f"proeng/resources/screenshots/{key}_{t['name']}.png"
        if os.path.exists(path):
            self.img_lbl.setPixmap(QPixmap(path))
        else:
            px = _generate_module_preview(key, QSize(450, 300))
            self.img_lbl.setPixmap(px)

        self.title_lbl.setText(title)
        self.desc_lbl.setText(desc)
        self.desc_lbl.setWordWrap(True)
        self.desc_lbl.setAlignment(Qt.AlignCenter)

        # Aplica estilos diferentes conforme tema
        if is_nb:
            self.title_lbl.setStyleSheet(
                f"color: {t['accent']}; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; background: transparent;"
            )
            self.desc_lbl.setStyleSheet(
                f"color: {t['text_dim']}; font-style: italic; padding: 0 10px; background: transparent;"
            )
        elif is_dark:
            self.title_lbl.setStyleSheet(
                f"color: {t['accent_bright']}; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; background: transparent;"
            )
            self.desc_lbl.setStyleSheet(
                f"color: {t['text_dim']}; font-style: italic; padding: 0 10px; background: transparent;"
            )
        else:
            self.title_lbl.setStyleSheet(
                f"color: {t['accent']}; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; background: transparent;"
            )
            self.desc_lbl.setStyleSheet(
                f"color: {t['text_dim']}; font-style: italic; padding: 0 10px; background: transparent;"
            )

        # Aplica estilo ao frame contendo imagem
        self.frame.setStyleSheet(f"""
            QFrame {{
                background: {t["bg_card"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
            }}
        """)

        # Atualiza dots: dot atual fica maior e mais visível
        for i, dot in enumerate(self.dots):
            if i == self.current_idx:
                dot.setStyleSheet(
                    f"border-radius: 0px; background: {t['accent']}; width: 24px;"
                )
                dot.setFixedWidth(24)
            else:
                dot.setStyleSheet(f"border-radius: 0px; background: {t['accent_dim']};")
                dot.setFixedWidth(8)

    def _next_with_fade(self):
        # Inicia animação de fade out (1.0 -> 0.1) e conecta callback para mudar item.
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.1)
        self.fade_anim.finished.connect(self._change_and_fade_in)
        self.fade_anim.start()

    def _change_and_fade_in(self):
        # Callback executado após fade out completo.
        # Incrementa índice com wrap-around, executa refresh, inicia fade in (0.1 -> 1.0).
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
        # Propaga atualização de tema para o carrossel.
        self._refresh()


class BrutalistModuleCard(QFrame):
    # Card de módulo com estilo Neo-Brutalist: faixa de cor sólida no topo,
    # efeito de sombra rígida (sem blur), bordas pretas 4px, texto em Courier New.
    
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, block_color: str, parent=None):
        # Inicializa card brutlista com ID do módulo, cor de destaque,
        # layout: faixa colorida (14px) + widget de informações (ícone, título, descrição).
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

        # Faixa colorida superior
        color_strip = QFrame()
        color_strip.setFixedHeight(14)
        color_strip.setObjectName("colorStrip")
        color_strip.setStyleSheet(f"background: {block_color}; border: none;")
        layout.addWidget(color_strip)

        # Widget de informações
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
        # Aplica estilo brutlista com offset de sombra aumentado quando hover.
        # Sombra: 8px (normal) ou 10px (hover), sem blur radius, cor preta #000000.
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
        # Ativa estado hover e aumenta offset de sombra.
        self._hovered = True
        self._update_style(True)
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Desativa estado hover e reduz offset de sombra.
        self._hovered = False
        self._update_style(False)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        # Ao clique esquerdo, emite sinal com ID do módulo.
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


class BrutalistQuickAccess(QFrame):
    # Bloco de ações rápidas (Novo Projeto, Abrir Projeto) em estilo Neo-Brutalist.
    # Background amarelo (#FFD600), botões brancos com hover invertido (fundo preto, texto amarelo).
    
    def __init__(self, parent=None):
        # Inicializa com layout vertical contendo título "ACESSO RAPIDO", separador,
        # e dois botões de ação fixos (48px altura).
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
        # Aplica stylesheet Neo-Brutalist: frame amarelo com borda preta 4px,
        # botões brancos com texto preto, hover inverte cores.
        # Sombra offset rígida: 8px X e Y, sem blur, cor preta.
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
    # Bloco de status/perfil em estilo Neo-Brutalist.
    # Background azul marítimo (#1565C0), texto branco, exibe status (PRONTO/ATIVO) e nome do projeto.
    
    def __init__(self, parent=None):
        # Inicializa com layout vertical contendo título "STATUS", separador branco,
        # label de status (20px, negrito), label de informação (9px, dimmed).
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
        # Aplica stylesheet Neo-Brutalist: background azul (#1565C0), borda preta 4px,
        # sombra offset rígida 8px, sem blur.
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
        # Atualiza status baseado em nome do projeto passado como parâmetro.
        # Se project_name não vazio: status="ATIVO", info mostra nome.
        # Caso contrário: status="PRONTO", info mostra "Nenhum projeto aberto".
        if project_name:
            self.status_lbl.setText("ATIVO")
            self.info_lbl.setText(project_name)
        else:
            self.status_lbl.setText("PRONTO")
            self.info_lbl.setText("Nenhum projeto aberto")


class BrutalistExampleBar(QFrame):
    # Barra de projetos exemplares em estilo Neo-Brutalist.
    # Background branco, botões com cores de hover laranja (#E65100).
    # Contém 5 botões de exemplo: Refinaria, Amônia, ETA, Caldeira, Mineração.
    
    def __init__(self, parent=None):
        # Inicializa com layout vertical contendo título, linha de 5 botões exemplo.
        # Cada botão inicializa com descrição da localização.
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
        # Aplica stylesheet Neo-Brutalist: frame branco com borda preta 4px,
        # botões com background bege (#F5F0E8), hover laranja (#E65100) com texto branco,
        # sombra offset rígida 6px.
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
    # Tela inicial da aplicação exibindo logo "PRO ENG", botões de ação (Novo/Abrir),
    # grid de 8 ModuleCardNB em 5 colunas, e seção de título.
    # Implementa padrão Composite para gerenciar múltiplos cards e componentes.
    
    open_module = pyqtSignal(str)
    new_project = pyqtSignal()
    open_project = pyqtSignal()
    load_example = pyqtSignal(str)

    def __init__(self, parent=None):
        # Inicializa a tela de boas-vindas e constrói interface via _build_ui().
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        # Constrói layout vertical contendo:
        # 1. Header: Logo "PRO ENG" (28px), subtítulo, botões Novo/Abrir
        # 2. Strip separador decorativo
        # 3. ScrollArea com grid 5 colunas de ModuleCardNB
        # Aplica tema ao final via refresh_theme().
        t = T()
        is_nb = t["name"] == "neo_brutalist"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QWidget()
        header.setMinimumHeight(140)
        header_main_layout = QVBoxLayout(header)
        header_main_layout.setContentsMargins(0, 0, 0, 0)
        header_main_layout.setSpacing(0)

        top_strip = QFrame()
        top_strip.setFixedHeight(8)
        top_strip.setObjectName("headerStrip")
        header_main_layout.addWidget(top_strip)

        header_content = QWidget()
        header_content_layout = QVBoxLayout(header_content)
        header_content_layout.setContentsMargins(20, 12, 20, 12)
        header_content_layout.setSpacing(4)
        header_content_layout.setAlignment(Qt.AlignCenter)

        self.logo_lbl = QLabel("PRO ENG")
        self.logo_lbl.setFont(QFont("Arial", 28, QFont.Black))
        self.logo_lbl.setAlignment(Qt.AlignCenter)

        self.sub_lbl = QLabel("ENGENHARIA ESTRATEGICA")
        self.sub_lbl.setFont(QFont("Arial", 9, QFont.Bold))
        self.sub_lbl.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(12)
        btn_row.setContentsMargins(0, 8, 0, 0)

        self.btn_new = QPushButton("NOVO")
        self.btn_new.setFixedSize(120, 36)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_new.clicked.connect(self.new_project.emit)

        self.btn_open = QPushButton("ABRIR")
        self.btn_open.setFixedSize(120, 36)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_open.clicked.connect(self.open_project.emit)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_open)

        header_content_layout.addWidget(self.logo_lbl)
        header_content_layout.addWidget(self.sub_lbl)
        header_content_layout.addLayout(btn_row)
        header_main_layout.addWidget(header_content)

        main_layout.addWidget(header)

        sep_strip = QFrame()
        sep_strip.setFixedHeight(4)
        sep_strip.setObjectName("sepStrip")
        main_layout.addWidget(sep_strip)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(16)

        section_title = QLabel("FERRAMENTAS DISPONIVEIS")
        section_title.setFont(QFont("Arial", 14, QFont.Black))
        section_title.setAlignment(Qt.AlignCenter)
        section_title.setObjectName("sectionTitle")
        content_layout.addWidget(section_title)
        self.section_title = section_title

        # Cria área de scroll com grid de cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(24)
        grid.setAlignment(Qt.AlignCenter)

        # Cria cards em grid 5 colunas
        module_ids = list(MODULE_PREVIEWS.keys())
        block_colors = [
            t.get("block_green", "#00C853"),
            t.get("block_blue", "#2979FF"),
            t.get("block_red", "#FF1744"),
            t.get("block_orange", "#FF6D00"),
            t.get("block_purple", "#AA00FF"),
            t.get("block_yellow", "#FFD600"),
        ]

        cols = 5
        self.module_cards = []
        for i, mid in enumerate(module_ids):
            card = ModuleCardNB(mid, block_colors[i % len(block_colors)], index=i)
            card.clicked.connect(self.open_module.emit)
            row = i // cols
            col = i % cols
            grid.addWidget(card, row, col)
            self.module_cards.append(card)

        for c in range(cols):
            grid.setColumnStretch(c, 1)

        scroll.setWidget(cards_container)
        content_layout.addWidget(scroll, 1)

        main_layout.addWidget(content_container, 1)

        self.refresh_theme()

    def _create_block(self, bg_color, title_text, title_height):
        # Factory method para criar blocos decorativos com customização de título.
        # Retorna QFrame com styling específico e (opcionalmente) título.
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
        # Atualiza toda a interface quando tema é alterado via cycle_theme().
        # Propaga atualização para: header strips, buttons, section title, cards.
        t = T()
        is_nb = t["name"] == "neo_brutalist"
        is_dark = t["name"] == "dark"
        is_light = t["name"] == "light"

        if hasattr(self, "header"):
            header = self.layout().itemAt(0).widget()
            if header:
                strip = header.findChild(QFrame, "headerStrip")
                if strip:
                    strip.setStyleSheet(
                        f"background-color: {t['accent']}; border: none;"
                    )

        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item:
                w = item.widget()
                if isinstance(w, QFrame) and w.objectName() == "sepStrip":
                    w.setStyleSheet(
                        f"background-color: {t['glass_border']}; border: none;"
                    )
                    break

        self.setStyleSheet(f"background-color: {t['bg_app']};")

        ff = t.get("font_family", "Arial, sans-serif")
        bw = t.get("border_width", 3)

        if is_nb:
            self.logo_lbl.setStyleSheet(
                f"color: #000000; font-size: 28px; font-family: {ff}; font-weight: 900;"
            )
            self.sub_lbl.setStyleSheet(
                f"color: {t['accent']}; font-size: 9px; font-family: {ff}; font-weight: bold; letter-spacing: 3px;"
            )
        elif is_dark:
            self.logo_lbl.setStyleSheet(
                f"color: {t['text']}; font-size: 28px; font-family: {ff}; font-weight: 900;"
            )
            self.sub_lbl.setStyleSheet(
                f"color: {t['accent_bright']}; font-size: 9px; font-family: {ff}; font-weight: bold; letter-spacing: 3px;"
            )
        else:
            self.logo_lbl.setStyleSheet(
                f"color: {t['text']}; font-size: 28px; font-family: {ff}; font-weight: 900;"
            )
            self.sub_lbl.setStyleSheet(
                f"color: {t['accent']}; font-size: 9px; font-family: {ff}; font-weight: bold; letter-spacing: 3px;"
            )

        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {t["accent"]};
                color: #FFFFFF;
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
                padding: 6px 12px;
                font-weight: bold;
                font-family: Arial;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {t["accent_bright"]};
            }}
            QPushButton:pressed {{
                background-color: {t["accent_dim"]};
            }}
        """)

        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
                padding: 6px 12px;
                font-weight: bold;
                font-family: Arial;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {t["bg_card2"]};
            }}
            QPushButton:pressed {{
                background-color: {t["accent_dim"]};
                color: #FFFFFF;
            }}
        """)

        for card in self.findChildren(ModuleCardNB):
            card._update_style()

        if hasattr(self, "section_title"):
            if is_nb:
                self.section_title.setStyleSheet(
                    f"color: {t['text']}; background: transparent; border: {bw}px solid {t['glass_border']}; padding: 8px; font-weight: 900;"
                )
            elif is_dark:
                self.section_title.setStyleSheet(
                    f"color: {t['accent_bright']}; background: {t['bg_card']}; border: {bw}px solid {t['glass_border']}; padding: 8px; font-weight: 900;"
                )
            else:
                self.section_title.setStyleSheet(
                    f"color: {t['accent']}; background: {t['bg_card']}; border: {bw}px solid #000000; padding: 8px; font-weight: 900;"
                )


class ModuleCardNB(QFrame):
    # Card de módulo alternativo com área de ícone colorida.
    # Layout: ícone colorido (70px altura) + informações (título, descrição).
    # Implementa hover com efeito de sombra e translação.
    
    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, accent_color: str, parent=None, index: int = 0):
        # Inicializa card com layout vertical: área de ícone (cor destaque) + info widget.
        # Tamanho: mínimo 200x160, máximo 240px largura.
        super().__init__(parent)
        info = MODULE_PREVIEWS[module_id]
        self.module_id = module_id
        self.accent_color = accent_color
        self._hovered = False
        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumSize(200, 160)
        self.setMaximumWidth(240)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Widget de ícone (área superior colorida)
        icon_area = QWidget()
        icon_area.setFixedHeight(70)
        icon_area.setObjectName("iconArea")
        icon_lay = QVBoxLayout(icon_area)
        icon_lay.setContentsMargins(12, 12, 12, 12)

        self.icon_lbl = QLabel(info.get("icon", "📊"))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 32px; background: transparent;")
        icon_lay.addWidget(self.icon_lbl)

        lay.addWidget(icon_area)

        # Widget de informações (título, descrição)
        info_widget = QWidget()
        info_widget.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 10, 12, 12)
        info_layout.setSpacing(4)

        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont("Arial", 11, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setObjectName("cardTitle")
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont("Arial", 8))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(32)
        desc_lbl.setObjectName("cardDesc")
        info_layout.addWidget(desc_lbl)

        lay.addWidget(info_widget)
        self._update_style()

    def _update_style(self):
        # Aplica estilos diferentes conforme tema (nb, dark, light).
        # Configura: cor background área ícone, border, cores de texto, efeito sombra.
        t = T()
        is_nb = t["name"] == "neo_brutalist"
        is_dark = t["name"] == "dark"
        bw = t.get("border_width", 3)

        icon_area = self.findChild(QWidget, "iconArea")
        if icon_area:
            if is_nb:
                icon_area.setStyleSheet(
                    f"background-color: {self.accent_color}; border-bottom: {bw}px solid #000000;"
                )
            elif is_dark:
                icon_area.setStyleSheet(
                    f"background-color: {self.accent_color}; border-bottom: {bw}px solid {t['glass_border']};"
                )
            else:
                icon_area.setStyleSheet(
                    f"background-color: {self.accent_color}; border-bottom: {bw}px solid #000000;"
                )

        title_lbl = self.findChild(QLabel, "cardTitle")
        desc_lbl = self.findChild(QLabel, "cardDesc")
        if title_lbl:
            title_lbl.setStyleSheet(f"color: {t['text']}; background: transparent;")
        if desc_lbl:
            desc_lbl.setStyleSheet(f"color: {t['text_dim']}; background: transparent;")

        if is_nb:
            bg = "#FFFFFF"
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: {bw}px solid #000000;
                }}
            """)
        elif is_dark:
            bg = t["bg_card2"] if self._hovered else t["bg_card"]
            border_col = t["glass_border"]
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: {bw}px solid {border_col};
                }}
            """)
        else:
            bg = t["bg_card"]
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg};
                    border: {bw}px solid #000000;
                }}
            """)

        self._apply_shadow(t)

    def _apply_shadow(self, t):
        # Aplica efeito de sombra com offset variável conforme hover.
        # Sem blur radius (efeito mais brutlista), cor do shadow do tema.
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        from PyQt5.QtGui import QColor

        if self._hovered:
            offset = t.get("shadow_hover_offset_x", 4)
        else:
            offset = t.get("shadow_offset_x", 8)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(offset)
        shadow.setYOffset(offset)
        shadow.setColor(QColor(t["shadow"]))
        self.setGraphicsEffect(shadow)

    def enterEvent(self, e):
        # Ativa estado hover e atualiza estilos.
        self._hovered = True
        self._update_style()
        super().enterEvent(e)

    def leaveEvent(self, e):
        # Desativa estado hover e atualiza estilos.
        self._hovered = False
        self._update_style()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        # Ao clique esquerdo, emite sinal com ID do módulo.
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)


class MainApp(QMainWindow):
    # Janela principal orquestradora da aplicação.
    # Responsabilidades:
    # - Navegação entre modules via QStackedWidget e lazy loading
    # - Gerenciamento de projeto (novo, abrir, salvar)
    # - Sincronização de estado entre módulos
    # - Aplicação de temas (neo_brutalist, dark, light)
    # - Menu bar, barra de status, toolbar
    # - Exportação de views para PNG/PDF
    # 
    # Implementa padrão Facade para simplificar acesso aos módulos.
    # Implementa padrão Observer para sinais de navegação.
    # Implementa padrão Factory para criação lazy de módulos.
    
    def __init__(self):
        # Inicializa aplicação principal:
        # 1. Configura janela: título, geometria, flags frameless
        # 2. Carrega ícone
        # 3. Configura paleta e stylesheet global
        # 4. Cria NavBar e stacked widget para navegação
        # 5. Cria WelcomeScreen como tela inicial
        # 6. Configura menu bar (apesar de oculta)
        # 7. Exibe maximizado
        super().__init__()
        self.project = AppProject()
        self.setWindowTitle("PRO ENG - Início")
        self.setGeometry(80, 60, 1440, 880)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_palette()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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

        self._welcome = WelcomeScreen()
        self._welcome.new_project.connect(self._new_project)
        self._welcome.open_project.connect(self._open_project)
        self._welcome.open_module.connect(self._navigate_to_module)
        self._welcome.load_example.connect(self._on_load_example)
        self._stack.addWidget(self._welcome)

        main_layout.addWidget(self._stack, 1)

        self.statusBar().setStyleSheet(
            f"background: {T()['bg_app']}; color: {T()['text_muted']}; border-top: 1px solid {T()['accent_dim']};"
        )
        self.statusBar().showMessage("Pronto")

        menubar = self.menuBar()
        menubar.hide()
        self._create_menu()
        self.showMaximized()

    def resizeEvent(self, event):
        # Evento fired quando janela é redimensionada.
        # Propaga para parent class, permitindo que componentes internos se adaptem.
        super().resizeEvent(event)

    def _navigate_to_module(self, module_id: str):
        # Navega para módulo especificado por ID usando lazy loading.
        # Se "welcome", retorna para tela inicial.
        # Caso contrário, cria módulo se não existe, adiciona ao stack, define como ativo.
        # Atualiza título da janela com nome do módulo.
        if module_id == "welcome":
            self._stack.setCurrentIndex(0)
            self.setWindowTitle("PRO ENG - Início")
            return

        if module_id not in self._modules:
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
        # Manipula solicitação de carregar projeto exemplo.
        # Exibe confirmation dialog, se confirmado navega para flowsheet
        # e tenta carregar dados do exemplo via load_example() do módulo.
        ans = QMessageBox.question(
            self,
            "Carregar Exemplo",
            f"Isso irá apagar seu desenho atual para carregar o exemplo '{example_name}'.\n\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return

        self._navigate_to_module("flowsheet")

        fw = self._modules.get("flowsheet")
        if fw and hasattr(fw, "_inner"):
            fw._inner.load_example(example_name)

    def _create_menu(self):
        # Cria menu bar com menus File e Modules.
        # Menu File: Novo, Abrir, Salvar, Salvar como, Exportar (PNG/PDF), Ir para Início, Sair
        # Menu Modules: Acesso direto a todos os 7 módulos
        # Aplicação de tema: estilos qt para menus adaptam-se ao tema ativo.
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

        self.addActions([new_act, open_act, save_act, pdf_act])

    def _on_export(self, fmt):
        # Exporta view do módulo atual para PNG ou PDF.
        # Tentativas de obter view em ordem: BaseModule.get_view(), método direto,
        # atributo _inner.view, atributo _inner.canvas.
        # Se falhar, exibe mensagem de erro.
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.warning(
                self,
                "Ação Inválida",
                "Por favor, abra uma ferramenta para exportar seu trabalho.",
            )
            return

        view = None
        if isinstance(mod, BaseModule):
            view = mod.get_view()
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
        # Executa ação de zoom no módulo atual.
        # Ação pode ser: "in", "out", "reset"
        # Tenta primeiro no widget atual, depois no _inner se existir.
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            return

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
        # Exibe diálogo QMessageBox com ajuda para módulo atual.
        # Se WelcomeScreen, mostra ajuda genérica.
        # Caso contrário, extrai help_text do módulo.
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

    def _sync_all_to_project(self):
        # Sincroniza estado de todos os módulos para AppProject.
        # Itera por dicionário de módulos, chama get_state() se disponível,
        # e atualiza project via update_module_state().
        for m_id, widget in self._modules.items():
            if hasattr(widget, "get_state"):
                self.project.update_module_state(m_id, widget.get_state())

    def _sync_project_to_all(self):
        # Sincroniza estado do AppProject para todos os módulos.
        # Itera por dicionário de módulos, chama set_state() com dados do projeto.
        for m_id, widget in self._modules.items():
            if hasattr(widget, "set_state"):
                widget.set_state(self.project.get_module_state(m_id))

    def _new_project(self):
        # Cria novo projeto: confirma com usuário, instancia novo AppProject,
        # limpa estados de módulos, navega para WelcomeScreen.
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
            self._navigate_to_module("welcome")

    def _save_project(self):
        # Salva projeto atual no arquivo existente.
        # Se não tem arquivo, redireciona para _save_project_as().
        # Caso contrário, sincroniza estado, salva, atualiza título e barra de status.
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
        # Salva projeto com novo nome via QFileDialog.getSaveFileName().
        # Adiciona extensão .proeng se necessária, sincroniza estados antes de salvar.
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
        # Abre projeto existente via QFileDialog.getOpenFileName().
        # Carrega arquivo, cria todos os módulos via lazy loading,
        # sincroniza estados do projeto para módulos, navega para flowsheet,
        # exibe mensagem de sucesso.
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
                self._navigate_to_module("flowsheet")
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro ao Abrir", f"Erro carregando o arquivo: {str(e)}"
                )

    def _get_or_create_module(self, module_name):
        # Factory method: obtém módulo existente ou cria novo (lazy loading).
        # Se "welcome", retorna _welcome.
        # Caso contrário, cria novo widget via builders dict, adiciona ao stack,
        # aplica stylesheet bg_app, sincroniza estado do projeto se disponível.
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
        # Alterna entre temas disponíveis via cycle_theme().
        # Dispara atualização completa da UI via _on_theme_toggle_refresh().
        from proeng.core.themes import T, cycle_theme

        cycle_theme()
        self._on_theme_toggle_refresh()

    def _on_theme_toggle_refresh(self):
        # Atualiza toda a UI após mudança de tema.
        # Propaga atualização para: WelcomeScreen, NavBar, todos os módulos,
        # views gráficas, widgets listados. Executa refresh_theme() se disponível.
        self._setup_palette()
        t = T()

        if hasattr(self._welcome, "refresh_theme"):
            self._welcome.refresh_theme()

        if hasattr(self, "nav_bar"):
            self.nav_bar._apply_style()

        for mod in self._modules.values():
            mod.setStyleSheet(f"background:{t['bg_app']};")
            if hasattr(mod, "refresh_theme"):
                try:
                    mod.refresh_theme()
                except:
                    pass

            for w in mod.findChildren(QWidget):
                if hasattr(w, "refresh_theme"):
                    try:
                        w.refresh_theme()
                    except:
                        pass

            for gv in mod.findChildren(QGraphicsView):
                try:
                    gv.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                    if gv.scene():
                        gv.scene().update()
                except:
                    pass

            for sp in mod.findChildren(QListWidget):
                if hasattr(sp, "_apply_palette_style"):
                    try:
                        sp._apply_palette_style()
                    except:
                        pass

    def _setup_palette(self):
        # Configura QPalette global com cores do tema atual e stylesheet global abrangente.
        # Define paleta do sistema (Window, Text, Button, Highlight, etc).
        # Depois aplica stylesheet Qt com estilos para: lineEdits, scrollbars, tooltips,
        # menus, comboboxes, tables, checkboxes, buttons, sliders, dialogs, tabs.
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
    # Ponto de entrada da aplicação.
    # Lógica:
    # 1. Cria instância QApplication (gerenciador do ciclo de eventos Qt)
    # 2. Define estilo Fusion como base (cross-platform)
    # 3. Cria instância MainApp (janela principal)
    # 4. Exibe janela maximizada
    # 5. Inicia loop de eventos (app.exec_())
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.showMaximized()
    sys.exit(app.exec_())
