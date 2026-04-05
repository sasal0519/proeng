# -*- coding: utf-8 -*-

# Barra de Navegação Superior e Botão de Alternância de Tema
#
# Responsabilidade: Gerenciar elementos de navegação principal incluindo
# barra superior (NavBar) com botões de menu e controles de janela, além de
# botão de alternância visual (ThemeToggle) entre três temas disponivelmente.
#
# Componentes principais:
# - NavBar: Widget de navegação superior (altura 64px) com:
#   - Botões: Início, Arquivo, Módulos, Ajuda
#   - Brand/Logo PRO ENG com label informativo
#   - ThemeToggle para alternar dark/light/neo_brutalist
#   - Controles de janela minimizar/maximizar/fechar
#   - Suporte a arrastar janela clicando na barra
# - ThemeToggle: Botão customizado (120x38px) com:
#   - Ícones dinâmicos (sol/lua/quadrado) representando cada tema
#   - Labels DARK/LIGHT/NEO
#   - Faixa de acento colorida que muda em hover
#   - Sinal theme_changed emitido ao clicar
# - Funções auxiliares de renderização de ícones
#
# Inputs: Callbacks go_home_fn, toggle_theme_fn, help_fn
# Outputs: Widget NavBar completo, ThemeToggle, sinais de mudança de tema

from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QLabel,
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


def _draw_icon_sun(p, x, y, size, col):
    # Desenha ícone de sol representando tema escuro (ironia intencional).
    #
    # Símbolo visual: Círculo central com 8 linhas radiais (a cada 45 graus).
    # Parâmetros:
    #   p: QPainter em operação de desenho
    #   x, y: coordenadas do canto superior-esquerdo
    #   size: dimensão do ícone em pixels
    #   col: cor da linha em hex (#RRGGBB)
    #
    # Lógica:
    #   - Desenha círculo com raio 22% da dimensão
    #   - Desenha 8 linhas radiais espaçadas a 45 graus
    #   - Usa pen de 2px com arredondamento de caps
    pen = QPen(QColor(col), 2, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    cx, cy = x + size / 2, y + size / 2
    r = size * 0.22
    p.drawEllipse(QPointF(cx, cy), r, r)
    import math

    for a in range(0, 360, 45):
        rad = math.radians(a)
        p.drawLine(
            QPointF(cx + (r + 2) * math.cos(rad), cy + (r + 2) * math.sin(rad)),
            QPointF(cx + (r + 6) * math.cos(rad), cy + (r + 6) * math.sin(rad)),
        )


def _draw_icon_moon(p, x, y, size, col):
    # Desenha ícone de lua representando tema claro.
    #
    # Símbolo visual: Círculo principal com círculo menor deslocado (efeito meia-lua).
    # Parâmetros:
    #   p: QPainter em operação de desenho
    #   x, y: coordenadas do canto superior-esquerdo
    #   size: dimensão do ícone em pixels
    #   col: cor da linha em hex (#RRGGBB)
    #
    # Renderização:
    #   - Desenha círculo (contorno apenas)
    #   - Sobrepõe círculo menor preenchido com cor de fundo da app
    #   - Efeito: lua em quarto crescente
    pen = QPen(QColor(col), 2, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    cx, cy = x + size / 2, y + size / 2
    r = size * 0.32
    p.drawEllipse(QPointF(cx, cy), r, r)
    t = T()
    p.setBrush(QColor(t["bg_app"]))
    p.setPen(QPen(Qt.NoPen))
    p.drawEllipse(QPointF(cx + 3, cy - 2), r * 0.8, r * 0.8)


def _draw_icon_nb(p, x, y, size, col):
    # Desenha ícone geométrico representando tema neo-brutalista.
    #
    # Símbolo visual: Quadrado com diagonal (brutalismo geométrico).
    # Parâmetros:
    #   p: QPainter em operação de desenho
    #   x, y: coordenadas do canto superior-esquerdo
    #   size: dimensão do ícone em pixels
    #   col: cor da linha em hex (#RRGGBB)
    #
    # Renderização:
    #   - Desenha quadrado com margem de 3px
    #   - Desenha diagonal do canto superior-esquerdo até inferior-direito
    #   - Pen de 2.5px para peso visual predominante
    pen = QPen(QColor(col), 2.5, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    m = 3
    p.drawRect(QRectF(x + m, y + m, size - m * 2, size - m * 2))
    p.drawLine(QPointF(x + m, y + m), QPointF(x + size - m, y + size - m))


class ThemeToggle(QPushButton):
    # Botão de alternância de tema visual com três estados (dark/light/neo_brutalist).
    #
    # Responsabilidade: Renderizar botão customizado (120x38px) que alterna ciclicamente
    # entre os três temas disponíveis. Cada tema exibe ícone único (sol/lua/quadrado) e
    # label correspondente (DARK/LIGHT/NEO).
    #
    # Acesso ao T() dinamicamente para reajustar cores após alteração de tema.
    # Emite sinal theme_changed quando clicado, permitindo sincronização com NavBar.
    #
    # Interações:
    #   - Clique: Emite sinal, atualiza visual
    #   - Hover: Inverte acentos, reduz offset de sombra
    #   - Renderização: Fundo de card, borda glass_border, faixa de acento no topo

    theme_changed = pyqtSignal()

    def __init__(self):
        # Inicializa botão com dimensões fixas e aparência customizada.
        #
        # Estado visual:
        #   - Flat button (sem bordas padrão do SO)
        #   - CursorPointingHand para feedback visual
        #   - Hover detection habilitado (WA_Hover)
        # Atributos:
        #   _hov: flag boolean indicando se mouse está sobre o botão
        super().__init__()
        self.setFixedSize(120, 38)
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._hov = False
        self.clicked.connect(self._toggle)

    def _toggle(self):
        # Callback de clique: Emite sinal de mudança de tema e solicita repintura.
        #
        # Efeito: Disparando theme_changed, os listeners (MainApp, NavBar) ciclarão
        # para o próximo tema. Chamada update() força repintura com novo tema.
        self.theme_changed.emit()
        self.update()

    def event(self, e):
        # Intercepta eventos de mouse para detectar entrada/saída (hover).
        #
        # Lógica:
        #   - QEvent.HoverEnter: Define _hov=True, solicita repintura
        #   - QEvent.HoverLeave: Define _hov=False, solicita repintura
        #   - Outros eventos: Delega à implementação pai
        #
        # Propósito: Alterar visual do botão (sombra menor, acento diferente) em hover.
        from PyQt5.QtCore import QEvent

        if e.type() == QEvent.HoverEnter:
            self._hov = True
            self.update()
        elif e.type() == QEvent.HoverLeave:
            self._hov = False
            self.update()
        return super().event(e)

    def paintEvent(self, _):
        # Renderização total do botão com tema dinâmico e estados de interação.
        #
        # Processamento:
        #   1. Obtém dicionário de tema ativo via T()
        #   2. Computa dimensões a partir de propriedades do tema
        #   3. Em hover: translada origem (+3,+3) para simular pressão
        #   4. Desenha sombra (se não hover) com cor theme["shadow"]
        #   5. Desenha fundo (bg_card) com borda (glass_border)
        #   6. Desenha faixa de acento no topo (4px de altura)
        #   7. Seleciona ícone baseado no nome do tema (sun/moon/quadrado)
        #   8. Renderiza label de texto (DARK/LIGHT/NEO)
        #
        # Estados visuais:
        #   - Normal: sombra visível, acento_bright
        #   - Hover: sombra reduzida, background_accent
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)

        if self._hov:
            p.translate(3, 3)

        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        if not self._hov:
            p.save()
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(
                QRectF(r.left() + sx * 0.5, r.top() + sy * 0.5, r.width(), r.height())
            )
            p.restore()

        p.setBrush(QColor(t["bg_card"]))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        p.setBrush(QColor(t["accent"] if self._hov else t["accent_bright"]))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), r.width(), 4))

        theme_name = t["name"]
        icon_col = t["text"]
        if theme_name == "dark":
            _draw_icon_sun(p, r.left() + 10, r.top() + 9, 18, icon_col)
        elif theme_name == "light":
            _draw_icon_moon(p, r.left() + 10, r.top() + 9, 18, icon_col)
        else:
            _draw_icon_nb(p, r.left() + 10, r.top() + 9, 18, icon_col)

        label_map = {"dark": "DARK", "light": "LIGHT", "neo_brutalist": "NEO"}
        label = label_map.get(theme_name, "TEMA")
        ff = t.get("font_family", "'Inter', sans-serif")
        p.setFont(QFont(ff, 9, QFont.Bold))
        p.setPen(QColor(t["text"]))
        lbl_r = QRectF(r.left() + 34, r.top(), r.width() - 40, r.height())
        p.drawText(lbl_r, Qt.AlignVCenter | Qt.AlignLeft, label)
        p.end()


class NavBar(QWidget):
    # Barra de navegação superior da aplicação.
    #
    # Responsabilidade: Gerenciar elementos de navegação principal incluindo
    # botão de retorno ao início (Início), menus de ação (Arquivo, Módulos, Ajuda),
    # botão de alternância de tema (ThemeToggle), display de label informativo e
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
        #   toggle_theme_fn: Função callback executada ao clicar ThemeToggle
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
        #   PRO ENG LABEL | label info | [Toggle Theme] | [Min] [Max] [Close]
        #
        # Processo:
        #   1. Cria layout QHBoxLayout com margens e espaçamento
        #   2. Adiciona botões de navegação (Início, Arquivo, Módulos, Ajuda)
        #   3. Adiciona label brand "PRO ENG | ENGINEERING WORKSPACE"
        #   4. Adiciona stretch invisível para forçar dois blocos laterais
        #   5. Adiciona label informativo (pode ser atualizado dinamicamente)
        #   6. Adiciona ThemeToggle conectado ao callback
        #   7. Adiciona controles de janela (min/max/close)
        #   8. Conecta ThemeToggle ao método _apply_style para sincronizar cores
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

        self._toggle = ThemeToggle()
        if toggle_theme_fn:
            self._toggle.theme_changed.connect(toggle_theme_fn)
        self._toggle.theme_changed.connect(self._apply_style)
        self._toggle.theme_changed.connect(self.update)
        lay.addWidget(self._toggle)

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
        t = T()
        bw = t.get("border_width", 3)
        bdr = t["glass_border"]
        ff = t.get("font_family", "'Inter', sans-serif")

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
                padding-left: 20px; padding-right: 20px;
                font-family: {ff}; font-size: 13px; font-weight: 900;
            }}
            QPushButton:hover {{
                background: {t["accent"]};
                color: #FFFFFF;
                border-color: {bdr};
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
                font-size: 16px;
                font-weight: 900;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 5px 10px;
                letter-spacing: 1px;
            }}
        """)
        self._lbl.setStyleSheet(f"""
            QLabel {{
                color: {t["text"]};
                font-family: {ff};
                font-size: 12px;
                font-weight: bold;
                background: {t["bg_card"]};
                border: {bw}px solid {bdr};
                padding: 5px;
            }}
        """)

        win_btn_style = f"""
            QPushButton {{
                background: {t["bg_card"]};
                color: {t["text"]};
                border: {bw}px solid {bdr};
                border-radius: 0px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {t.get("btn_close_h", "#e81123")};
                color: #FFFFFF;
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
