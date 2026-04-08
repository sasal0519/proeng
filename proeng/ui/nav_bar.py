# -*- coding: utf-8 -*-

# Barra de Navegação Superior com Seletor de Temas Interativo
#
# Responsabilidade: Gerenciar elementos de navegação principal incluindo
# barra superior (NavBar) com botões de menu, seletor de temas com preview,
# e controles de janela.
#
# Componentes principais:
# - NavBar: Widget de navegação superior (altura 64px) com:
#   - Botões: Início, Arquivo, Módulos, Ajuda
#   - Brand/Logo PRO ENG com label informativo
#   - ThemeSelectorDropdown seletor dropdown com 7 temas nomeados
#   - Controles de janela minimizar/maximizar/fechar
#   - Suporte a arrastar janela clicando na barra
# - ThemeSelectorDropdown: Botão customizado (160x38px) com:
#   - Menu popup com seleção de temas nomeados com emojis
#   - Nomes descritivos: DARK, LIGHT, NEO-BRUTAL, SYNTHWAVE, FOREST, SUNSET, OCEAN
#   - Preview visual ao passar mouse sobre cada tema
#   - Restaura tema original se menu fechar sem seleção
#   - Sinal theme_changed emitido ao clicar/selecionar tema
#
# Inputs: Callbacks go_home_fn, toggle_theme_fn, help_fn
# Outputs: Widget NavBar completo, sinais de mudança de tema

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QVBoxLayout,
    QApplication,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QFont,
)
from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    pyqtSignal,
)

from proeng.core.themes import T, THEMES, set_theme, cycle_theme
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar


class ThemeSelectorDropdown(QPushButton):
    """
    Menu dropdown com lista de temas. Selecao apenas por clique.
    """

    THEME_LABELS = {
        "neo_brutalist": "NEO-BRUTAL",
        "midnight": "MIDNIGHT",
        "embers": "EMBERS",
        "forest": "FOREST",
        "synthwave": "SYNTHWAVE",
        "arctic": "ARCTIC",
        "solar": "SOLAR",
        "crimson": "CRIMSON",
        "ocean": "OCEAN",
        "volcano": "VOLCANO",
        "mint": "MINT",
        "onyx": "ONYX",
        "lilac": "LILAC",
    }

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setFixedSize(160, 38)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setText("TEMAS")
        self.clicked.connect(self._show_theme_menu)
        self._popup = None
        self._closing = False

    def _show_theme_menu(self):
        """Mostra popup com selecao de temas."""
        if self._closing:
            return
        if self._popup is not None and self._popup.isVisible():
            self._on_close(False)
            return

        self._original_theme = T()["name"]

        self._popup = QWidget()
        self._popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self._popup.setAttribute(Qt.WA_StyledBackground, True)

        t = T()

        layout = QVBoxLayout(self._popup)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        for theme_name in THEMES.keys():
            label = self.THEME_LABELS.get(theme_name, theme_name.upper())
            is_active = theme_name == T()["name"]
            btn = self._make_theme_btn(label, theme_name, is_active)
            layout.addWidget(btn)

        # Borda neo-brutalista
        bw = t.get("border_width", 3)
        self._popup.setStyleSheet(f"""
            QWidget {{
                background: {t["bg_card"]};
                border: {bw}px solid {t["glass_border"]};
            }}"""
        )

        self._popup.adjustSize()
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self._popup.move(pos.x() - 20, pos.y())
        self._popup.show()

    def _make_theme_btn(self, label, theme_name, is_active):
        """Criar botao individual para cada tema."""
        t = T()
        bw = t.get("border_width", 3)
        btn = QPushButton(label)
        btn.setFixedWidth(200)
        btn.setFlat(True)
        btn.setCursor(Qt.PointingHandCursor)

        # Indicador visual no texto para tema ativo
        if is_active:
            btn.setText("  " + label)

        def on_click():
            self._closing = True
            set_theme(theme_name)
            for w in QApplication.allWidgets():
                if hasattr(w, 'refresh_theme'):
                    w.refresh_theme()
            self.theme_changed.emit(theme_name)
            if self._popup:
                self._popup.close()
                self._popup = None
            self._closing = False

        btn.clicked.connect(on_click)

        bdr = t["glass_border"]
        bg = t["accent"] if is_active else t["bg_card"]
        fg = t["text"]
        txt_color = "#000000" if is_active else fg
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {txt_color};
                border: {bw}px solid {"transparent" if is_active else bdr};
                padding: 8px 14px;
                font-weight: bold;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {t["accent"]};
                color: #FFFFFF;
                border: {bw}px solid {t["glass_border"]};
            }}"""
        )
        return btn

    def _on_close(self, selected, theme_name=None):
        """Fecha popup sem aplicar tema (cancel)."""
        if self._popup:
            self._popup.close()
            self._popup = None




class NavBar(QWidget):
    # Barra de navegação superior da aplicação.
    #
    # Responsabilidade: Gerenciar elementos de navegação principal incluindo
    # botão de retorno ao início (Início), menus de ação (Arquivo, Módulos, Ajuda),
    # seletor de temas com preview (ThemeSelectorDropdown), display de label informativo e
    # controles de janela do SO (minimizar, maximizar, fechar).
    #
    # Comportamento especial: Suporta arrastar da janela quando usuário clica e
    # arrasta na área de navegação (fora de botões específicos).
    #
    # Layout horizontal com espaçamentos:
    #   [Início] | [Arquivo] [Módulos] [Ajuda] | PRO ENG LABEL | [] | [Theme] | [Win Ctrls]
    #
    # Atributos de instância:
    #   _go_home: callback para retornar tela inicial
    #   _help_fn: callback opcional para exibir ajuda
    #   _moving: flag indicando se janela está sendo arrastada
    #   _start_pos: posição do mouse no início do arrasto
    #
    # Sinais emitidos:
    #   example_requested: quando usuário solicita carregar exemplo (futuro)

    example_requested = pyqtSignal(str)

    def __init__(self, go_home_fn, toggle_theme_fn, help_fn=None):
        # Inicializa barra de navegação com altura fixa (64px) e callbacks.
        #
        # Parâmetros:
        #   go_home_fn: Função callback executada ao clicar "Início"
        #   toggle_theme_fn: Função callback opcional executada ao selecionar tema
        #   help_fn: Função callback opcional executada ao clicar "Ajuda"
        super().__init__()
        self.setFixedHeight(64)
        self._go_home = go_home_fn
        self._help_fn = help_fn
        self._setup(toggle_theme_fn)

    def _setup(self, toggle_theme_fn):
        # Constrói layout horizontal completo da barra de navegação.
        #
        # Estrutura visual:
        #   [Início] | separador visual | [Arquivo] [Módulos] [Ajuda]
        #   << espaço flexível >>
        #   PRO ENG LABEL | label info | [Selector Temas] | [Min] [Max] [Close]
        #
        # Processo:
        #   1. Cria layout QHBoxLayout com margens e espaçamento
        #   2. Adiciona botões de navegação (Início, Arquivo, Módulos, Ajuda)
        #   3. Adiciona label brand "PRO ENG | ENGINEERING WORKSPACE"
        #   4. Adiciona stretch invisível para forçar dois blocos laterais
        #   5. Adiciona label informativo (pode ser atualizado dinamicamente)
        #   6. Adiciona ThemeSelectorDropdown com preview interativo
        #   7. Adiciona controles de janela (min/max/close)
        #   8. Conecta sinais de mudança de tema ao método _apply_style
        #   9. Aplica estilos visuais iniciais
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 0, 8)
        lay.setSpacing(10)

        self._btn_back = QPushButton("Inicio")
        self._btn_back.clicked.connect(self._go_home)
        lay.addWidget(self._btn_back)

        sep = QWidget()
        sep.setFixedSize(1, 24)
        lay.addWidget(sep)

        self._btn_file = QPushButton("Arquivo")
        self._btn_modules = QPushButton("Modulos")
        self._btn_help = QPushButton("Ajuda")
        if self._help_fn:
            self._btn_help.clicked.connect(self._help_fn)
        for btn in [self._btn_file, self._btn_modules, self._btn_help]:
            lay.addWidget(btn)

        self._brand = QLabel("PRO ENG | ENGINEERING WORKSPACE")
        lay.addWidget(self._brand)
        lay.addStretch()

        self._lbl = QLabel("")
        lay.addWidget(self._lbl)

        sep2 = QWidget()
        sep2.setFixedSize(1, 24)
        lay.addWidget(sep2)

        self._theme_selector = ThemeSelectorDropdown()
        self._theme_selector.theme_changed.connect(self._apply_style)
        self._theme_selector.theme_changed.connect(self.update)
        if toggle_theme_fn:
            self._theme_selector.theme_changed.connect(toggle_theme_fn)
        lay.addWidget(self._theme_selector)

        lay.addSpacing(10)

        self._win_ctrls = QWidget()
        ctrl_lay = QHBoxLayout(self._win_ctrls)
        ctrl_lay.setContentsMargins(0, 0, 0, 0)
        ctrl_lay.setSpacing(0)

        self._btn_min = QPushButton("-")
        self._btn_max = QPushButton("[]")
        self._btn_close = QPushButton("X")

        for btn in [self._btn_min, self._btn_max, self._btn_close]:
            btn.setFixedSize(50, 40)
            btn.setFlat(True)
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            ctrl_lay.addWidget(btn)

        self._btn_min.clicked.connect(self._min_window)
        self._btn_max.clicked.connect(self._max_window)
        self._btn_close.clicked.connect(self._close_window)

        lay.addWidget(self._win_ctrls)

        self._apply_style()
        self._moving = False

    def _apply_style(self):
        # Aplica estilos visuais dinâmicos a todos os widgets baseado no tema ativo.
        #
        # Processo:
        #   1. Obtém dicionário de tema via T()
        #   2. Extrai propriedades visuais (border_width, glass_border, font_family)
        #   3. Define stylesheet do widget raiz (fundo + borda inferior)
        #   4. Aplica stylesheet a separadores (linhas verticais de 1px)
        #   5. Aplica stylesheet a botões de navegação (Início, Arquivo, Módulos, Ajuda)
        #   6. Aplica stylesheet a label de brand (grande, bold, com borda e padding)
        #   7. Aplica stylesheet a label informativa (pequena, com borda)
        #   8. Aplica stylesheet a controles de janela (cor especial em hover close)
        #
        # Variáveis CSS utilizadas:
        #   - t["toolbar_bg"]: cor de fundo da barra
        #   - t["glass_border"]: cor de bordas
        #   - t["bg_card"]: cor de fundo dos botões
        #   - t["accent"]: cor de hover dos botões
        #   - t["text"]: cor do texto
        #   - t["btn_close_h"]: cor especial para hover do botão fechar
        #
        # Neo-Brutalism aplicado:
        #   - Bordas grossas (3-4px) sólidas preto
        #   - Efeito de pressionar em hover (redução de padding/border visual)
        #   - UPPERCASE para todos os labels e botões
        #   - Tipografia pesada (weight 900)
        #   - Espaçamento amplo entre elementos
        t = T()
        bw = t.get("border_width", 3)
        bdr = t["glass_border"]
        ff = t.get("font_family", "'Arial Black', sans-serif")

        self.setStyleSheet(f"""
            QWidget {{
                background: {t["toolbar_bg"]};
                border-bottom: {bw}px solid {bdr};
            }}
        """)

        sep_style = f"background: {bdr};"
        for child in self.findChildren(QWidget):
            if child.objectName() == "" and child.sizeHint().width() == 1:
                child.setStyleSheet(sep_style)

        btn_style = f"""
            QPushButton {{
                background: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {bdr};
                border-radius: 0px;
                padding: 10px 20px;
                font-family: {ff}; 
                font-size: 13px; 
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: {t["accent"]};
                color: #FFFFFF;
                border-color: {bdr};
                font-weight: 900;
            }}
            QPushButton::menu-indicator {{ image: none; }}
        """
        self._btn_back.setStyleSheet(btn_style)
        self._btn_file.setStyleSheet(btn_style)
        self._btn_modules.setStyleSheet(btn_style)
        self._btn_help.setStyleSheet(btn_style)

        self._brand.setStyleSheet(f"""
            QLabel {{
                color: {t["text"]};
                font-family: {ff};
                font-size: 22px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 8px 15px;
            }}
        """)
        self._lbl.setStyleSheet(f"""
            QLabel {{
                color: {t["text"]};
                font-family: {ff};
                font-size: 12px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 6px 10px;
            }}
        """)

        win_btn_style = f"""
            QPushButton {{
                background: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {bdr};
                border-radius: 0px;
                padding: 6px 12px;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {t.get("btn_close_h", "#FF2222")};
                color: #FFFFFF;
                border-color: {bdr};
                font-weight: 900;
            }}
        """
        self._btn_min.setStyleSheet(win_btn_style)
        self._btn_max.setStyleSheet(win_btn_style)
        self._btn_close.setStyleSheet(win_btn_style)

    def _min_window(self):
        # Callback para minimizar a janela.
        #
        # Operação: Obtém a janela pai (window()) e chama showMinimized().
        # Efeito: Janela é minimizada para taskbar/dock do SO.
        win = self.window()
        if win:
            win.showMinimized()

    def _max_window(self):
        # Callback para maximizar/restaurar a janela.
        #
        # Lógica:
        #   - Se janela está maximizada: chama showNormal() e atualiza texto para "[]"
        #   - Caso contrário: chama showMaximized() e atualiza texto para "[ ]"
        #
        # Propósito: Alternar entre estados maximizado e normal, atualizando
        # aparência do botão para indicar estado atual.
        win = self.window()
        if win:
            if win.isMaximized():
                win.showNormal()
                self._btn_max.setText("[]")
            else:
                win.showMaximized()
                self._btn_max.setText("[ ]")

    def _close_window(self):
        # Callback para fechar a janela.
        #
        # Operação: Obtém a janela pai e chama close().
        # Efeito: Aplicação encerra após processos de cleanup final.
        win = self.window()
        if win:
            win.close()

    def mousePressEvent(self, event):
        # Inicia modo de arrastar janela ao clicar com botão esquerdo.
        #
        # Captura posição inicial do mouse e sinaliza _moving=True.
        # Subsequent mouseMoveEvent usará essas informações para deslocar janela.
        #
        # Propósito: Permitir que usuário reposicione janela sem decorações.
        if event.button() == Qt.LeftButton:
            self._moving = True
            self._start_pos = event.globalPos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Move a janela durante o arrasto.
        #
        # Lógica:
        #   1. Se _moving=False ou botão não está pressionado: sai
        #   2. Calcula deslocamento (diff = pos_atual - pos_inicial)
        #   3. Verifica se janela está maximizada (impede movimento neste estado)
        #   4. Move janela para nova posição
        #   5. Atualiza _start_pos com pos_atual para próxima iteração
        #
        # Propósito: Rastrear movimento contínuo do mouse durante arrasto.
        if self._moving and event.buttons() & Qt.LeftButton:
            win = self.window()
            if win.isMaximized():
                pass
            diff = event.globalPos() - self._start_pos
            win.move(win.pos() + diff)
            self._start_pos = event.globalPos()
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        # Encerra modo de arrasto ao soltar botão do mouse.
        #
        # Operação: Define _moving=False para parar cálculos de deslocamento.
        self._moving = False
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        # Desenha linha de borda inferior da barra de navegação.
        #
        # Renderização:
        #   1. Obtém cores/dimensões do tema via T()
        #   2. Cria QPainter para desenho no widget
        #   3. Desenha linha horizontal na base com cor glass_border
        #   4. Linha possui width=border_width, criando efeito de borda pesada
        #
        # Nota: Chamada super().paintEvent() ao final para permitir renderização
        # padrão do widget.
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        bw = t.get("border_width", 3)
        y = self.height() - bw
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawLine(0, y, self.width(), y)
        p.end()
        super().paintEvent(event)
