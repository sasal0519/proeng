# -*- coding: utf-8 -*-

"""
PRO ENG - Tela de Boas-Vindas (Welcome Screen)

Tela inicial exibida ao abrir a aplicacao, contendo:
- Logo e subtotal
- Botoes Novo/Abrir projeto
- Grid de cards de modulos disponiveis

Depende de: MODULE_PREVIEWS, T (themes), ModuleCardNB
Emite sinais para o MainApp gerenciar navegacao.
"""

import os

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QScrollArea,
    QFrame,
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, pyqtSignal

from proeng.core.themes import T
from proeng.ui.main_app import MODULE_PREVIEWS


class ModuleCardNB(QFrame):
    """Card de módulo com estilo neo-brutalist.
    
    Exibe um card clicável representando um módulo de engenharia.
    Mostra ícone do módulo, título e descrição com elementos visuais
    neo-brutalist (bordas duras, sombras afiadas, tipografia em negrito).
    
    Suporta estados de hover e press para feedback interativo.
    Emite sinal clicked quando usuário clica no card.
    
    Attributes:
        clicked (pyqtSignal): Emitido com module_id quando card é clicado.
    """

    clicked = pyqtSignal(str)

    def __init__(self, module_id: str, accent_color: str, parent=None, index: int = 0):
        super().__init__(parent)
        info = MODULE_PREVIEWS[module_id]
        self.module_id = module_id
        self.accent_color = accent_color
        self._hovered = False
        self._pressed = False
        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumSize(225, 255)
        self.setMaximumWidth(280)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        icon_area = QWidget()
        icon_area.setFixedHeight(90)
        icon_area.setObjectName("iconArea")
        icon_lay = QVBoxLayout(icon_area)
        icon_lay.setContentsMargins(12, 12, 12, 12)

        self.icon_lbl = QLabel(info.get("icon", ""))
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        self.icon_lbl.setStyleSheet("font-size: 44px; background: transparent;")
        icon_lay.addWidget(self.icon_lbl)

        lay.addWidget(icon_area)

        info_widget = QWidget()
        info_widget.setObjectName("cardInfo")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(12, 14, 12, 12)
        info_layout.setSpacing(6)

        title_lbl = QLabel(info["name"])
        title_lbl.setFont(QFont("Arial", 14, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setWordWrap(True)
        title_lbl.setObjectName("cardTitle")
        info_layout.addWidget(title_lbl)

        desc_lbl = QLabel(info["desc"])
        desc_lbl.setFont(QFont("Arial", 11))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumHeight(60)
        desc_lbl.setObjectName("cardDesc")
        info_layout.addWidget(desc_lbl)

        lay.addWidget(info_widget)
        self._update_style()

    def _update_style(self):
        t = T()
        bw = t.get("border_width", 4)
        br = t.get("border_radius", 0)

        # Icon area
        icon_area = self.findChild(QWidget, "iconArea")
        if icon_area:
            icon_area.setStyleSheet(
                f"background-color: {self.accent_color}; "
                f"border-bottom: {bw}px solid #000000; "
                f"border-radius: {br}px; "
            )

        # Text labels
        title_lbl = self.findChild(QLabel, "cardTitle")
        desc_lbl = self.findChild(QLabel, "cardDesc")
        if title_lbl:
            title_lbl.setStyleSheet(
                f"color: {t['text']}; background: transparent; "
                f"font-weight: 900; letter-spacing: 1px;"
            )
        if desc_lbl:
            desc_lbl.setStyleSheet(
                f"color: {t['text_dim']}; background: transparent; font-size: 12px;"
            )

        # Card frame
        if self._hovered:
            bg = "#FFFFFF"
        else:
            bg = t["bg_card"]

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: {bw}px solid {t['glass_border']};
                border-radius: {br}px;
            }}
        """)

        self._apply_shadow(t)

    def _apply_shadow(self, t):
        if self._pressed or self._hovered:
            offset = 0
        else:
            offset = t.get("shadow_offset_x", 8)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(0)
        shadow.setXOffset(offset)
        shadow.setYOffset(offset)
        shadow.setColor(QColor(t["shadow"]))
        self.setGraphicsEffect(shadow)

    def enterEvent(self, e):
        self._hovered = True
        self._update_style()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hovered = False
        self._pressed = False
        self._update_style()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressed = True
            self._update_style()
            self.clicked.emit(self.module_id)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._pressed = False
            self._update_style()
        super().mouseReleaseEvent(e)


class WelcomeScreen(QWidget):
    """Tela de boas-vindas exibida no início da aplicação.
    
    Mostra o logo PRO ENG, botões de ação (Novo/Abrir projeto)
    e grid de módulos de engenharia disponíveis.
    
    Emite sinais para permitir MainApp coordenar navegação de módulo
    e gerenciamento de projeto a partir desta tela.
    
    Suporta propagação de tema via método refresh_theme().
    
    Attributes:
        open_module (pyqtSignal): Emitido com module_id quando card é clicado.
        new_project (pyqtSignal): Emitido quando botão "Novo Projeto" é clicado.
        open_project (pyqtSignal): Emitido quando botão "Abrir Projeto" é clicado.
        load_example (pyqtSignal): Emitido com example_id quando exemplo é carregado.
    """

    open_module = pyqtSignal(str)
    new_project = pyqtSignal()
    open_project = pyqtSignal()
    load_example = pyqtSignal(str)

    def __init__(self, parent=None):
        """Inicializa a tela de boas-vindas.
        
        Args:
            parent: Widget pai opcional.
        """
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -- Header --
        header = QWidget()
        header.setMinimumHeight(200)
        header_main_layout = QVBoxLayout(header)
        header_main_layout.setContentsMargins(0, 0, 0, 0)
        header_main_layout.setSpacing(0)

        top_strip = QFrame()
        top_strip.setFixedHeight(8)
        top_strip.setObjectName("headerStrip")
        header_main_layout.addWidget(top_strip)

        header_content = QWidget()
        header_content_layout = QVBoxLayout(header_content)
        header_content_layout.setContentsMargins(20, 16, 20, 16)
        header_content_layout.setSpacing(12)
        header_content_layout.setAlignment(Qt.AlignCenter)

        self.logo_lbl = QLabel("PRO ENG")
        self.logo_lbl.setFont(QFont("Arial", 48, QFont.Black))
        self.logo_lbl.setAlignment(Qt.AlignCenter)

        self.sub_lbl = QLabel("ENGENHARIA ESTRATEGICA")
        self.sub_lbl.setFont(QFont("Arial", 19, QFont.Bold))
        self.sub_lbl.setAlignment(Qt.AlignCenter)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(20)
        btn_row.setContentsMargins(0, 12, 0, 0)

        self.btn_new = QPushButton("NOVO")
        self.btn_new.setFixedSize(160, 48)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setFont(QFont("Arial", 15, QFont.Bold))
        self.btn_new.clicked.connect(self.new_project.emit)

        self.btn_open = QPushButton("ABRIR")
        self.btn_open.setFixedSize(160, 48)
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_open.setFont(QFont("Arial", 15, QFont.Bold))
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

        # -- Content --
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)

        section_title = QLabel("FERRAMENTAS DISPONIVEIS")
        section_title.setFont(QFont("Arial", 22, QFont.Black))
        section_title.setAlignment(Qt.AlignCenter)
        section_title.setObjectName("sectionTitle")
        content_layout.addWidget(section_title)
        self.section_title = section_title

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(28)
        grid.setAlignment(Qt.AlignCenter)

        module_ids = list(MODULE_PREVIEWS.keys())
        block_colors = [
            T().get("block_green", "#00C853"),
            T().get("block_blue", "#2979FF"),
            T().get("block_red", "#FF1744"),
            T().get("block_orange", "#FF6D00"),
            T().get("block_purple", "#AA00FF"),
            T().get("block_yellow", "#FFD600"),
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

    def refresh_theme(self):
        """Reaplica todos os estilos com base no tema ativo.
        
        Chamado após mudança de tema para atualizar cores, bordas, fontes
        e outras propriedades visuais. Itera entre todos widgets filhos
        e aplica entradas stylesheet do dicionário de tema ativo.
        """
        t = T()
        ff = t.get("font_family", "Arial, sans-serif")
        bw = t.get("border_width", 4)
        br = t.get("border_radius", 0)

        # Header / separator strips
        if hasattr(self, "layout"):
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item:
                    w = item.widget()
                    if isinstance(w, QFrame) and w.objectName() in ("headerStrip", "sepStrip"):
                        if w.objectName() == "headerStrip":
                            w.setStyleSheet(
                                f"background-color: {t['accent']}; border: none; border-radius: 0px;"
                            )
                        else:
                            w.setStyleSheet(
                                f"background-color: {t['glass_border']}; border: none; border-radius: 0px;"
                            )
                        break

        self.setStyleSheet(f"background-color: {t['bg_app']}; border-radius: 0px;")

        # Logo
        self.logo_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {t['text']};
                font-size: 56px;
                font-family: {ff};
                font-weight: 900;
                background: transparent;
                border: none;
                letter-spacing: 2px;
                text-transform: uppercase;
            }}
            """
        )

        # Subtitle
        self.sub_lbl.setStyleSheet(
            f"""
            QLabel {{
                color: {t['accent']};
                font-size: 18px;
                font-family: {ff};
                font-weight: 900;
                background: transparent;
                border: none;
                letter-spacing: 3px;
                text-transform: uppercase;
            }}
            """
        )

        # Buttons
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background-color: {t["accent"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
                padding: 8px 16px;
                font-weight: 900;
                font-family: {ff};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {t["accent_bright"]};
                color: #FFFFFF;
                padding: 10px 14px;
            }}
            QPushButton:pressed {{
                background-color: {t["glass_border"]};
                color: {t["accent_bright"]};
                padding: 10px 14px;
            }}
        """)

        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {t["glass_border"]};
                border-radius: 0px;
                padding: 8px 16px;
                font-weight: 900;
                font-family: {ff};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {t["bg_card2"]};
                border-color: {t["accent"]};
                padding: 10px 14px;
            }}
            QPushButton:pressed {{
                background-color: {t["glass_border"]};
                color: {t["accent"]};
                padding: 10px 14px;
            }}
        """)

        # Section title
        if hasattr(self, "section_title"):
            self.section_title.setStyleSheet(
                f"""
                QLabel {{
                    color: {t['text']};
                    background: transparent;
                    border: {bw}px solid {t['glass_border']};
                    border-radius: {br}px;
                    padding: 10px 20px;
                    font-weight: 900;
                    font-family: {ff};
                    font-size: 14px;
                    text-transform: uppercase;
                    letter-spacing: 2px;
                }}
                """
            )

        # Cards
        for card in self.findChildren(ModuleCardNB):
            card._update_style()
