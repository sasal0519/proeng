# -*- coding: utf-8 -*-
"""
PRO ENG - Janela Principal da Aplicacao (Workspace/Project)

Arquivo central da interface grafica que gerencia todos os modulos da suite
de engenharia industrial.

Responsabilidades:
    - Construcao da janela principal (QMainWindow)
    - Navegacao entre modulos via QStackedWidget com lazy loading
    - Gerenciamento de projetos (criar, abrir, salvar, exportar)
    - Sistema de temas e paleta de cores globais
    - Menu de aplicacao e atalhos de teclado

Dependencias externas:
    - proeng.core.themes: T(), cycle_theme()
    - proeng.core.project: AppProject
    - proeng.core.base_module: BaseModule
    - proeng.ui.nav_bar: NavBar
    - proeng.ui.welcome: WelcomeScreen
    - proeng.modules.*: Modulos de engenharia (Gantt, Flowsheet, BPMN, etc.)

Exports publicos:
    - MODULE_PREVIEWS: Dict com metadados de visualizacao dos modulos
    - MODULE_COLORS: Dict com cores especificas por modulo
    - MainApp: Classe da janela principal

Inputs: Nenhum (aplicacao desktop standalone)
Outputs: QMainWindow com todos os modulos integrados

Data de criacao: 2024
Ultima refatoracao: 2026-04-06
Versao: 1.0.0
"""

import os
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFileDialog,
    QMessageBox,
    QLabel,
    QFrame,
    QGraphicsView,
    QSizePolicy,
    QListWidget,
    QAction,
    QMenu,
)
from PyQt5.QtGui import (
    QIcon,
    QFont,
    QColor,
    QPalette,
    QBrush,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer

from proeng.core.themes import T, cycle_theme
from proeng.core.project import AppProject
from proeng.core.utils import _export_view, _is_nb
from proeng.core.base_module import BaseModule

# Module imports (lazy loading factory)
from proeng.modules.flowsheet import _FlowsheetModule
from proeng.modules.gantt import _GanttModule
from proeng.modules.eap import _EAPModule
from proeng.modules.bpmn import _BPMNModule
from proeng.modules.canvas import _CanvasModule
from proeng.modules.ishikawa import _IshikawaModule
from proeng.modules.w5h2 import _W5H2Module
from proeng.modules.kanban import _ModuloKanban
from proeng.modules.scrum import _ScrumModule
from proeng.modules.pdca import _PDCAModule
from proeng.modules.script_module import _ScriptModule


# =============================================================================
# MODULE METADATA
# =============================================================================

# Dicionario de configuracao de visualizacao previa dos modulos.
# Estrutura: {module_id: {name, desc, color1, color2, icon, tag}}
# Usado para: WelcomeScreen (ModuleCardNB), MainApp (titulos de modulo),
# geracao de miniaturas programaticas.
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
    "kanban": {
        "name": "Kanban Board",
        "desc": "Quadro Kanban para gestao visual de tarefas e workflows.",
        "color1": "#1a6b3a",
        "color2": "#0d4a2a",
        "icon": "KNB",
        "tag": "TAREFAS",
    },
    "scrum": {
        "name": "Scrum Sprint",
        "desc": "Sprint board com backlog, story points e metricas.",
        "color1": "#1a3a6b",
        "color2": "#0d2847",
        "icon": "SCR",
        "tag": "AGILE",
    },
    "pdca": {
        "name": "Ciclo PDCA",
        "desc": "Gestão e melhoria contínua com método Plan-Do-Check-Act.",
        "color1": "#1a6b3a",
        "color2": "#0d4a2a",
        "icon": "PDCA",
        "tag": "MELHORIA",
    },
    "script": {
        "name": "Script Engineer",
        "desc": "Interpretador Python para equações e simulações de engenharia.",
        "color1": "#1a5a6b",
        "color2": "#0d3a47",
        "icon": "PY",
        "tag": "SIMULAÇÃO",
    },
}

# Mapeamento de cores especificas por modulo.
# Usado para: Aplicar cor identidade visual ao NavBar de cada modulo.
# Estrutura: {module_id: hex_color}
MODULE_COLORS = {
    "welcome": "#FFE500",   # Amarelo neon - cor primaria
    "gantt": "#0057FF",     # Azul eletrico - cronograma
    "flowsheet": "#00C44F", # Verde limao - processos industriais
    "bpmn": "#7C3AFF",      # Roxo vibrante - processos de negocio
    "eap": "#FF6B00",       # Laranja vivo - estrutura de escopo
    "canvas": "#FF3CAC",    # Rosa choque - planejamento estrategico
    "w5h2": "#0057FF",      # Azul eletrico - plano de acao
    "ishikawa": "#FF2222",  # Vermelho vivo - analise de causa raiz
    "kanban": "#00C44F",    # Verde limao - quadro Kanban
    "scrum": "#0057FF",     # Azul eletrico - sprint board
    "pdca": "#00C44F",      # Verde limao - ciclo pdca
    "script": "#00B4D8",    # Ciano - simulacao python
}


# =============================================================================
# MainApp - Janela Principal
# =============================================================================


class MainApp(QMainWindow):
    """
    Janela principal da aplicacao PRO ENG.

    Responsabilidade: Orquestrar toda a aplicacao, gerenciar navegacao entre
    modulos (lazy loading via QStackedWidget), carregar/salvar projetos,
    aplicar temas globais, gerenciar menu e atalhos.

    Atributos publicos:
        project: Instancia de AppProject para gerenciamento de estado
        nav_bar: Instancia de NavBar (barra de navegacao superior)

    Atributos privados:
        _stack: QStackedWidget para navegacao entre telas
        _modules: Dict de modulos carregados lazily {module_id: widget}
        _welcome: Referencia para WelcomeScreen

    Design patterns:
        - Facade: Simplifica acesso a modulos e funcionalidades
        - Factory (lazy): Modulos sao criados sob demanda via _get_or_create_module
    """

    def __init__(self):
        """
        Inicializa a aplicacao principal.

        Fluxo de inicializacao:
            1. Configura janela (titulo, geometria, frameless)
            2. Carrega icone do aplicativo
            3. Configura paleta de cores global e stylesheet
            4. Cria layout principal com NavBar
            5. Setup QStackedWidget com WelcomeScreen
            6. Configura barra de status e menus
            7. Exibe janela maximizada
        """
        super().__init__()

        self.project = AppProject()
        self.setWindowTitle("PRO ENG - Inicio")
        self.setGeometry(80, 60, 1440, 880)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._setup_palette()

        # --- Layout principal ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from proeng.ui.nav_bar import NavBar

        self.nav_bar = NavBar(
            lambda: self._navigate_to_module("welcome"),
            self._on_theme_toggle_refresh,
            self._on_module_help,
        )
        self.nav_bar.example_requested.connect(self._on_load_example)
        main_layout.addWidget(self.nav_bar)

        # --- Stack de navegacao ---
        self._stack = QStackedWidget()
        self._modules = {}

        from proeng.ui.welcome import WelcomeScreen

        self._welcome = WelcomeScreen()
        self._welcome.new_project.connect(self._new_project)
        self._welcome.open_project.connect(self._open_project)
        self._welcome.open_module.connect(self._navigate_to_module)
        self._welcome.load_example.connect(self._on_load_example)
        self._stack.addWidget(self._welcome)

        main_layout.addWidget(self._stack, 1)

        # --- Status bar ---
        self.statusBar().setStyleSheet(
            f"background: {T()['bg_app']}; color: {T()['text_muted']}; "
            f"border-top: 1px solid {T()['accent_dim']};"
        )
        self.statusBar().showMessage("Pronto")

        # --- Menu ---
        self.menuBar().hide()
        self._create_menu()

        self.showMaximized()

    def resizeEvent(self, event):
        """
        Evento de redimensionamento da janela.

        Args:
            event: QResizeEvent com informacoes de dimensionamento
        """
        super().resizeEvent(event)

    # ─── Navegacao ──────────────────────────────────────────────────────

    def _navigate_to_module(self, module_id: str):
        """
        Navega para um modulo especifico pelo ID com lazy loading.

        O modulo e criado apenas na primeira solicitacao. Modulos ja
        criados sao reaproveitados. Aplica cor especifica do modulo ao
        NavBar para identidade visual.

        Args:
            module_id: Identificador do modulo de destino.
                        'welcome' retorna para a tela inicial.
        """
        module_color = MODULE_COLORS.get(module_id, "#FFE500")
        self._apply_module_header_color(module_color, module_id)

        if module_id == "welcome":
            self._stack.setCurrentIndex(0)
            self.setWindowTitle("PRO ENG - Inicio")
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
                "kanban": _ModuloKanban,
                "scrum": _ScrumModule,
                "pdca": _PDCAModule,
            }.get(module_id)

            if mod_class:
                mod_widget = mod_class()
                self._modules[module_id] = mod_widget
                self._stack.addWidget(mod_widget)

        if module_id in self._modules:
            idx = self._stack.indexOf(self._modules[module_id])
            self._stack.setCurrentIndex(idx)
            title = MODULE_PREVIEWS.get(module_id, {}).get("name", "Modulo")
            self.setWindowTitle(f"PRO ENG - {title}")

    def _apply_module_header_color(self, module_color: str, module_id: str):
        """
        Aplica cor especifica do modulo ao NavBar.

        Args:
            module_color: Cor hex (ex: #0057FF) para o header do modulo
            module_id: ID do modulo para contextualizacao de estilo
        """
        t = T()
        is_nb = t["name"] == "neo_brutalist"
        bw = t.get("border_width", 4)
        br = t.get("border_radius", 0)

        if is_nb and hasattr(self, "nav_bar"):
            self.nav_bar.setStyleSheet(f"""
                QFrame {{
                    background-color: {module_color};
                    border-bottom: {bw}px solid #000000;
                    border-radius: {br}px;
                }}
                QFrame QLabel {{
                    color: #000000;
                    font-weight: 900;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                QFrame QPushButton {{
                    background-color: transparent;
                    color: #000000;
                    border: none;
                    font-weight: 900;
                    padding: 4px 8px;
                }}
                QFrame QPushButton:hover {{
                    background-color: rgba(0, 0, 0, 0.1);
                    border-radius: {br}px;
                }}
            """)

    # ─── Estilizacao ────────────────────────────────────────────────────

    def _style_dialog(self, dialog):
        """
        Aplica estilizacao Neo-Brutalism a dialogos (QMessageBox, QDialog, etc).

        Nota: Este metodo deve ser chamado ANTES de exibir o dialogo.
        Para QMessageBox static methods (question, information, etc), o
        dialogo ja e exibido antes do retorno — ver _new_project para
        padrao correto com QMessageBox.setStandardButtons.

        Args:
            dialog: Instancia de QMessageBox ou QDialog a ser estilizado
        """
        t = T()
        is_nb = _is_nb(t)

        if is_nb:
            bw = t.get("border_width", 3)
            dialog.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {t["bg_app"]};
                    color: {t["text"]};
                }}
                QDialog {{
                    background-color: {t["bg_app"]};
                    color: {t["text"]};
                }}
                QMessageBox QLabel {{
                    color: {t["text"]};
                    background: transparent;
                }}
                QMessageBox QPushButton, QDialog QPushButton {{
                    background-color: {t["accent"]};
                    color: #FFFFFF;
                    border: {bw}px solid {t["glass_border"]};
                    border-radius: 0px;
                    padding: 6px 20px;
                    font-weight: 900;
                    font-family: Arial;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    min-width: 60px;
                    min-height: 30px;
                }}
                QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
                    background-color: {t["accent_bright"]};
                }}
                QMessageBox QPushButton:pressed, QDialog QPushButton:pressed {{
                    background-color: {t["accent_dim"]};
                    color: #FFFFFF;
                }}
            """)

    def _setup_palette(self):
        """
        Configura paleta de cores global e stylesheet da aplicacao.

        Aplica QPalette do sistema com cores do tema atual,
        depois define stylesheet global abrangente para todos os widgets
        (inputs, listas, scrollbars, tooltips, menus, tabelas, checkboxes,
        sliders, tabs, botoes).
        """
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

        glass_border = t.get("glass_border", "#000000")
        is_nb = _is_nb(t)
        bw = t.get("border_width", 4)
        br = 0  # Neo-Brutalism: sempre 0 radius
        ff = t.get("font_family", "'Space Grotesk', 'Inter', 'Segoe UI', sans-serif")

        global_style = f"""
            /* CORE LAYOUT */
            QMainWindow {{ background-color: {t["bg_app"]}; }}
            QWidget {{ background-color: {t["bg_app"]}; }}
            QFrame {{ border-radius: {br}px; }}

            /* TEXT INPUTS */
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDateEdit {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 8px;
                font-weight: 700;
                font-family: {ff};
                selection-background-color: {t["accent"]};
                selection-color: #000;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QDateEdit:focus {{
                border: {bw}px solid {t["accent_bright"]};
                background-color: {t["bg_input"]};
                outline: none;
            }}

            /* LISTS */
            QListWidget, QListView {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 0px;
            }}
            QListWidget::item, QListView::item {{
                padding: 8px;
                border-radius: {br}px;
                background-color: {t["bg_card"]};
            }}
            QListWidget::item:selected, QListView::item:selected {{
                background-color: {t["accent"]};
                color: #000;
                font-weight: 900;
            }}
            QListWidget::item:hover, QListView::item:hover {{
                background-color: {t["bg_card2"]};
            }}

            /* SCROLLBARS */
            QScrollBar:vertical {{
                border: {bw}px solid {glass_border};
                background: {t["bg_app"]};
                width: {14 + bw}px;
                margin: 0;
                border-radius: {br}px;
            }}
            QScrollBar::handle:vertical {{
                background: {glass_border};
                min-height: 30px;
                border-radius: {br}px;
                border: 1px solid {glass_border};
            }}
            QScrollBar::handle:vertical:hover {{ background: {t["accent"]}; }}
            QScrollBar::add-line:vertical {{ background: {glass_border}; height: {14 + bw}px; border: 1px solid {glass_border}; }}
            QScrollBar::sub-line:vertical {{ background: {glass_border}; height: {14 + bw}px; border: 1px solid {glass_border}; }}

            QScrollBar:horizontal {{
                border: {bw}px solid {glass_border};
                background: {t["bg_app"]};
                height: {14 + bw}px;
                margin: 0;
                border-radius: {br}px;
            }}
            QScrollBar::handle:horizontal {{
                background: {glass_border};
                min-width: 30px;
                border-radius: {br}px;
                border: 1px solid {glass_border};
            }}
            QScrollBar::handle:horizontal:hover {{ background: {t["accent"]}; }}
            QScrollBar::add-line:horizontal {{ background: {glass_border}; width: {14 + bw}px; border: 1px solid {glass_border}; }}
            QScrollBar::sub-line:horizontal {{ background: {glass_border}; width: {14 + bw}px; border: 1px solid {glass_border}; }}

            /* TOOLTIPS */
            QToolTip {{
                background-color: {glass_border};
                color: {t["accent"]};
                border: 3px solid {t["accent"]};
                border-radius: {br}px;
                padding: 6px;
                font-weight: 700;
            }}

            /* MENUS */
            QMenuBar {{
                background-color: {glass_border};
                color: {t["accent"]};
                border: none;
                font-weight: 900;
            }}
            QMenuBar::item:selected {{
                background-color: {t["accent"]};
                color: {glass_border};
            }}
            QMenu {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 4px;
            }}
            QMenu::item:selected {{
                background-color: {glass_border};
                color: {t["accent"]};
                border-radius: {br}px;
            }}
            QMessageBox {{
                background-color: {t["bg_app"]};
            }}
            QMessageBox QLabel {{
                color: {t["text"]};
                background: transparent;
            }}
            QMessageBox QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 8px 20px;
                font-weight: 900;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {t["accent"]};
                color: #000;
            }}

            /* COMBOBOX */
            QComboBox {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 6px;
                font-weight: 700;
                font-family: {ff};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                selection-background-color: {t["accent"]};
                selection-color: #000;
            }}
            QComboBox:focus {{
                border: {bw}px solid {t["accent_bright"]};
            }}

            /* TABLES */
            QTableWidget {{
                background-color: {t["bg_input"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                gridline-color: {glass_border};
            }}
            QTableWidget::item {{
                padding: 6px;
                background-color: {t["bg_card"]};
            }}
            QTableWidget::item:selected {{
                background-color: {t["accent"]};
                color: #000;
            }}
            QHeaderView::section {{
                background-color: {glass_border};
                color: {t["accent"]};
                border: 2px solid {glass_border};
                padding: 6px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            /* CHECKBOXES */
            QCheckBox {{
                color: {t["text"]};
                spacing: 8px;
                font-weight: 700;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                background: {t["bg_input"]};
            }}
            QCheckBox::indicator:checked {{
                background: {t["accent"]};
                border-color: {glass_border};
            }}
            QRadioButton {{
                color: {t["text"]};
                spacing: 8px;
                font-weight: 700;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                background: {t["bg_input"]};
            }}
            QRadioButton::indicator:checked {{
                background: {t["accent"]};
                border-color: {glass_border};
            }}

            /* PUSHBUTTONS */
            QPushButton {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 8px 16px;
                font-weight: 900;
                font-family: {ff};
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {t["accent"]};
                color: #000;
                border-color: {glass_border};
            }}
            QPushButton:pressed {{
                background-color: {t["accent_bright"]};
                color: #FFF;
                padding: 10px 14px;
            }}

            /* SPLITTERS */
            QSplitter::handle {{
                background-color: {glass_border};
            }}
            QSplitter::handle:horizontal {{
                width: {bw}px;
            }}
            QSplitter::handle:vertical {{
                height: {bw}px;
            }}

            /* SLIDERS */
            QSlider::groove:horizontal {{
                border: {bw}px solid {glass_border};
                background: {t["bg_card"]};
                height: 8px;
                border-radius: {br}px;
            }}
            QSlider::handle:horizontal {{
                background: {glass_border};
                border: {bw}px solid {glass_border};
                width: 18px;
                margin: -6px 0;
                border-radius: {br}px;
            }}
            QSlider::handle:horizontal:hover {{ background: {t["accent"]}; }}
            QSlider::groove:vertical {{
                border: {bw}px solid {glass_border};
                background: {t["bg_card"]};
                width: 8px;
                border-radius: {br}px;
            }}
            QSlider::handle:vertical {{
                background: {glass_border};
                border: {bw}px solid {glass_border};
                height: 18px;
                margin: 0 -6px;
                border-radius: {br}px;
            }}
            QSlider::handle:vertical:hover {{ background: {t["accent"]}; }}

            /* DIALOGS */
            QDialog {{
                background-color: {t["bg_app"]};
                color: {t["text"]};
            }}

            /* TABS */
            QTabWidget::pane {{
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
            }}
            QTabBar::tab {{
                background-color: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {glass_border};
                border-radius: {br}px;
                padding: 8px 20px;
                margin-right: 4px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QTabBar::tab:selected {{
                background-color: {t["accent"]};
                color: #000;
            }}
            QTabBar::tab:hover {{
                background-color: {t["bg_card2"]};
            }}

            /* STATUS BAR */
            QStatusBar {{
                background-color: {glass_border};
                color: {t["accent"]};
                border-top: {bw}px solid {glass_border};
                font-weight: 700;
            }}
        """
        QApplication.instance().setStyleSheet(global_style)

    # ─── Barra de Menus ─────────────────────────────────────────────────

    def _create_menu(self):
        """
        Cria a barra de menus da aplicacao.

        Menus criados:
            - Arquivo: Novo, Abrir, Salvar, Salvar como, Exportar (PNG/PDF), Sair
            - Modulos: Acesso direto a todos os modulos
        """
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
        except Exception:
            menu_style = ""

        # --- Arquivo ---
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

        home_act = QAction("Ir para Inicio", self)
        home_act.triggered.connect(lambda: self._navigate_to_module("welcome"))
        file_menu.addAction(home_act)

        file_menu.addSeparator()

        exit_act = QAction("Sair", self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        self.nav_bar._btn_file.setMenu(file_menu)

        # --- Modulos ---
        modules_menu = QMenu(self)
        modules_menu.setStyleSheet(menu_style)
        modules_info = [
            ("welcome", "Inicio"),
            ("gantt", "Cronograma Gantt"),
            ("flowsheet", "PFD Flowsheet"),
            ("bpmn", "BPMN Modeler"),
            ("eap", "Gerador EAP"),
            ("canvas", "PM Canvas"),
            ("w5h2", "Plano 5W2H"),
            ("ishikawa", "Ishikawa"),
            ("kanban", "Kanban Board"),
            ("scrum", "Scrum Sprint"),
            ("pdca", "Ciclo PDCA"),
        ]
        for mid, label in modules_info:
            act = QAction(label, self)
            act.triggered.connect(lambda _, m=mid: self._navigate_to_module(m))
            modules_menu.addAction(act)

        self.nav_bar._btn_modules.setMenu(modules_menu)

        # Atalhos globais
        self.addActions([new_act, open_act, save_act, pdf_act])

    # ─── Acoes de Modulo (Export, Zoom, Help) ───────────────────────────

    def _on_export(self, fmt: str):
        """
        Executa exportacao do modulo atual para PNG ou PDF.

        Tenta multiplas formas de obter a view para exportacao:
            1. Via BaseModule.get_view()
            2. Via atributo get_view() direto
            3. Via _inner.view
            4. Via _inner.canvas

        Args:
            fmt: Formato de exportacao ('png' ou 'pdf')
        """
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            QMessageBox.warning(
                self,
                "Acao Invalida",
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
                self, "Exportar", "Este modulo nao suporta exportacao direta."
            )

    def _on_zoom_action(self, action: str):
        """
        Executa acao de zoom no modulo atual.

        Args:
            action: Acao de zoom ('in', 'out', 'reset')
        """
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            return

        target = mod
        if not hasattr(target, "zoom_in") and hasattr(mod, "_inner"):
            target = mod._inner

        try:
            if action == "in" and hasattr(target, "zoom_in"):
                target.zoom_in()
            elif action == "out" and hasattr(target, "zoom_out"):
                target.zoom_out()
            elif action == "reset" and hasattr(target, "reset_zoom"):
                target.reset_zoom()
        except Exception:
            pass

    def _on_module_help(self):
        """
        Exibe dialogo de ajuda para o modulo atual.

        Para WelcomeScreen: exibe ajuda generica.
        Para outros modulos: tenta obter help_text do modulo.
        """
        mod = self._stack.currentWidget()
        if mod == self._welcome:
            help_dialog = QMessageBox(self)
            help_dialog.setWindowTitle("Ajuda: Inicio")
            help_dialog.setText(
                "Bem-vindo ao PRO ENG!\n\nSelecione um dos modulos a direita ou "
                "pelo menu 'Modulos' para iniciar seu projeto."
            )
            self._style_dialog(help_dialog)
            help_dialog.exec_()
            return

        help_txt = getattr(
            mod, "help_text", "Guia rapido nao disponivel para este modulo."
        )
        title = self.windowTitle().replace("PRO ENG - ", "")
        help_dialog = QMessageBox(self)
        help_dialog.setWindowTitle(f"Guia: {title}")
        help_dialog.setText(help_txt)
        self._style_dialog(help_dialog)
        help_dialog.exec_()

    # ─── Gerenciamento de Projetos ──────────────────────────────────────

    def _sync_all_to_project(self):
        """
        Sincroniza estado de todos os modulos para o projeto atual.
        """
        for m_id, widget in self._modules.items():
            if hasattr(widget, "get_state"):
                self.project.update_module_state(m_id, widget.get_state())

    def _sync_project_to_all(self):
        """
        Sincroniza estado salvo do projeto para todos os modulos.
        """
        for m_id, widget in self._modules.items():
            if hasattr(widget, "set_state"):
                widget.set_state(self.project.get_module_state(m_id))

    def _new_project(self):
        """
        Cria novo projeto limpando estado atual.

        Fluxo: Confirma com usuario -> cria novo AppProject -> limpa modulos
        -> retorna para Welcome.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Novo Projeto")
        msg.setText("Sua area de trabalho atual sera apagada. Deseja continuar?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self._style_dialog(msg)
        ans = msg.exec_()
        if ans == QMessageBox.Yes:
            self.project = AppProject()
            self.setWindowTitle("PRO ENG  - Sem Titulo")
            for widget in self._modules.values():
                if hasattr(widget, "set_state"):
                    widget.set_state({})
            self._navigate_to_module("welcome")

    def _save_project(self):
        """
        Salva projeto atual no arquivo existente.

        Se nao houver arquivo associado (primeimo save), redireciona para
        _save_project_as().
        """
        self._sync_all_to_project()
        if not self.project.has_file:
            self._save_project_as()
        else:
            try:
                self.project.save(self.project.filename)
                self.statusBar().showMessage(
                    f"Projeto Salvo: {os.path.basename(self.project.filename)}", 3000
                )
                self.setWindowTitle(
                    f"PRO ENG  - {os.path.basename(self.project.filename)}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _save_project_as(self):
        """
        Salva projeto atual com novo nome via QFileDialog.

        Adiciona extensao .proeng automaticamente se necessario.
        """
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
                    f"Projeto Salvo: {os.path.basename(path)}", 3000
                )
                self.setWindowTitle(f"PRO ENG  - {os.path.basename(path)}")
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _open_project(self):
        """
        Abre projeto existente via QFileDialog.

        Fluxo: Dialog -> carrega AppProject -> cria todos os modulos ->
        sincroniza estados -> navega para flowsheet.
        """
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Projeto", "", "Projeto PRO ENG (*.proeng)"
        )
        if path:
            try:
                self.project.load(path)
                # Pre-create modules needed for state restoration
                for mid in ("flowsheet", "bpmn", "eap", "canvas", "w5h2", "ishikawa"):
                    self._get_or_create_module(mid)
                self._sync_project_to_all()
                self.setWindowTitle(f"PRO ENG - {os.path.basename(path)}")
                self.statusBar().showMessage("Projeto Carregado com Sucesso!", 3000)
                self._navigate_to_module("flowsheet")
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro ao Abrir", f"Erro carregando o arquivo: {str(e)}"
                )

    # ─── Factory de Modulos ─────────────────────────────────────────────

    def _get_or_create_module(self, module_name: str):
        """
        Factory method para obter ou criar modulo sob demanda.

        Implementa lazy loading - modulos sao criados apenas quando
        necessarios. Se o projeto possui estado salvo para o modulo,
        aplica automaticamente.

        Args:
            module_name: Nome/ID do modulo a obter ou criar.

        Returns:
            Widget do modulo solicitado.
        """
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
            "kanban": _ModuloKanban,
            "scrum": _ScrumModule,
        }
        if module_name not in self._modules:
            w = builders[module_name]()
            w.setStyleSheet(f"background: {T()['bg_app']};")
            self._stack.addWidget(w)
            self._modules[module_name] = w

            if hasattr(w, "set_state") and self.project.get_module_state(module_name):
                w.set_state(self.project.get_module_state(module_name))

        return self._modules[module_name]

    # ─── Exemplos ───────────────────────────────────────────────────────

    def _on_load_example(self, example_name: str):
        """
        Manipula sinal da NavBar para carregar projeto de exemplo.

        Exibe confirmation dialog. Se confirmado, navega para flowsheet
        e tenta carregar dados de exemplo.

        Args:
            example_name: Nome do exemplo a ser carregado
        """
        ask = QMessageBox(self)
        ask.setWindowTitle("Carregar Exemplo")
        ask.setText(
            f"Isso ira apagar seu desenho atual para carregar o exemplo '{example_name}'.\n\nDeseja continuar?"
        )
        ask.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self._style_dialog(ask)
        ans = ask.exec_()
        if ans != QMessageBox.Yes:
            return

        self._navigate_to_module("flowsheet")

        fw = self._modules.get("flowsheet")
        if fw and hasattr(fw, "_inner"):
            fw._inner.load_example(example_name)

    # ─── Temas ──────────────────────────────────────────────────────────

    def _toggle_theme_action(self):
        """
        Alterna entre temas disponiveis.

        Chama cycle_theme() e executa refresh completo da UI.
        """
        cycle_theme()
        self._on_theme_toggle_refresh()

    def _on_theme_toggle_refresh(self):
        """
        Atualiza toda a UI apos mudanca de tema.

        Propaga atualizacao para WelcomeScreen, NavBar, todos os modulos
        e children widgets, incluindo QGraphicsView backgrounds e
        QListWidget palettes.
        """
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
                except Exception:
                    pass

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


# =============================================================================
# Entrada da aplicacao
# =============================================================================

if __name__ == "__main__":
    """
    Ponto de entrada principal da aplicacao.

    Fluxo:
        1. Cria QApplication instance
        2. Define estilo Fusion (base)
        3. Cria instancia MainApp
        4. Exibe maximizado
        5. Executa loop de eventos
    """
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.showMaximized()
    sys.exit(app.exec_())
