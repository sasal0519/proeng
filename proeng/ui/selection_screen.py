# -*- coding: utf-8 -*-

# Tela de Seleção de Módulos e Componentes Visuais
#
# Responsabilidade: Construir tela de entrada/seleção da aplicação com
# galeria de módulos disponíveis em cards interativos, exemplos reais em
# forma de screenshots, botão de alternância de tema e elementos de marca.
#
# Componentes principais:
# - ModuleCard: Botão customizado renderizando card de seleção de módulo
# - SignatureOverlay: Faixa de assinatura flutuante com gradiente
# - GalleryItem: Item individual de galeria com verificação de arquivo/tema
# - ScreenshotGallery: Galeria horizontal scrollável de todos os módulos
# - SelectionScreen: Tela global organizando cards em seções e branding
#
# Estrutura visual da tela:
#   [Barra acento 4px] | [Topbar 48px com brand/toggle tema] |
#   [Conteúdo central com galeria e cards] |
#   [Barra acento 4px]
#
# Inputs: Callbacks on_select (módulo selecionado), on_theme_toggle
# Outputs: Widget SelectionScreen com toda interface

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QGraphicsPathItem,
    QMenu,
    QListView,
    QLineEdit,
    QLabel,
    QStackedWidget,
    QTextEdit,
    QGraphicsRectItem,
    QInputDialog,
    QFileDialog,
    QSizePolicy,
    QScrollArea,
    QFrame,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QPalette,
    QCursor,
    QPolygonF,
    QFont,
    QFontMetrics,
    QIcon,
    QPixmap,
    QPainterPath,
    QDrag,
    QLinearGradient,
)
from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    QMimeData,
    QByteArray,
    QDataStream,
    QIODevice,
    QSize,
    QPoint,
    QTimer,
    pyqtSignal,
    QObject,
    QSizeF,
)
from PyQt5.QtWidgets import QScrollArea, QFrame

from proeng.core.themes import T, THEMES, _ACTIVE, cycle_theme
from proeng.ui.nav_bar import ThemeToggle


def _draw_icon_arrow(p, x, y, size, col):
    # Desenha ícone de seta indicando ação de clique ou affordance de hover.
    #
    # Símbolo visual: Linha horizontal com duas pequenas linhas diagonais
    # na ponta (seta apontando para a direita).
    #
    # Parâmetros:
    #   p: QPainter em operação de desenho
    #   x, y: coordenadas do canto superior-esquerdo de encaixe
    #   size: dimensão do ícone em pixels
    #   col: cor da linha em hex (#RRGGBB)
    #
    # Utilitário: Renderiza affordance visual para usuário clicar no card.
    pen = QPen(QColor(col), 2.5, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(x, y + size / 2), QPointF(x + size, y + size / 2))
    p.drawLine(QPointF(x + size - 6, y + size / 2 - 5), QPointF(x + size, y + size / 2))
    p.drawLine(QPointF(x + size - 6, y + size / 2 + 5), QPointF(x + size, y + size / 2))


class ModuleCard(QPushButton):
    # Card de seleção de módulo com renderização neo-brutalista customizada.
    #
    # Responsabilidade: Exibir botão interativo para seleção de módulo com
    # faixa de acento colorida, ícone emoji, título bold, descrição de duas
    # linhas, e affordance visual (seta) em hover. Design: bordas duras,
    # sombra com offset, sem gradientes/transparência.
    #
    # Estrutura visual:
    #   [Barra acento 6px] | [Ícone 36x36] [Título] | [Seta no hover]
    #                      | [Descrição de duas linhas]
    #
    # Atributos:
    #   _emoji: string de ícone emoji para módulo
    #   _title: título curto exibido em bold
    #   _desc: descrição (suporta múltiplas linhas)
    #   _hov: flag boolean para estado hover

    def __init__(self, emoji, title, desc, key, callback):
        # Inicializa card de módulo com callbacks e dimensões.
        #
        # Parâmetros:
        #   emoji: string ícone emoji (ex: "📊", "🔀")
        #   title: nome do módulo (string curta)
        #   desc: descrição técnica (pode conter quebras de linha)
        #   key: identificador único do módulo ("gantt", "bpmn", etc)
        #   callback: função chamada ao clicar: callback(key)
        #
        # Layout: Tamanho dinâmico com altura mínima/máxima para adaptar-se
        # a layouts de grade. Hover detection habilitado via WA_Hover attribute.
        super().__init__()
        self._emoji = emoji
        self._title = title
        self._desc = desc
        self._hov = False
        self.setMinimumSize(240, 128)
        self.setMaximumHeight(148)
        self.setMinimumHeight(128)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFlat(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.clicked.connect(lambda: callback(key))

    def event(self, e):
        # Intercepta eventos de mouse para detectar entrada/saída (hover).
        #
        # Lógica:
        #   - QEvent.HoverEnter: Define _hov=True, solicita repintura
        #   - QEvent.HoverLeave: Define _hov=False, solicita repintura
        #   - Todos eventos: Delega ao handler pai
        #
        # Propósito: Alterar renderização (sombra, acento) em estado hover.
        from PyQt5.QtCore import QEvent

        if e.type() == QEvent.HoverEnter:
            self._hov = True
            self.update()
        elif e.type() == QEvent.HoverLeave:
            self._hov = False
            self.update()
        return super().event(e)

    def paintEvent(self, _):
        # Renderização customizada do card com tema dinâmico.
        #
        # Estrutura de pintura:
        #   1. Obtém propriedades do tema (cores, dimensões, fonte)
        #   2. Calcula rectangle do card com padding de 2px
        #   3. Desenha sombra sólida com offset menor em hover
        #   4. Desenha fundo (bg_card) com borda (glass_border)
        #   5. Desenha faixa acento colorida no topo (6px altura)
        #   6. Renderiza ícone em caixa com borda
        #   7. Renderiza texto de título (elipsis se necessário)
        #   8. Renderiza descrição (text wrap, múltiplas linhas)
        #   9. Renderiza seta em hover (affordance)
        #
        # Design: Zero antialiasing (performance), cores sólidas, sombra dura.
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)
        hsx = t.get("shadow_hover_offset_x", 2)
        hsy = t.get("shadow_hover_offset_y", 2)

        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        if self._hov:
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(r.translated(hsx, hsy))
        else:
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(r.translated(sx, sy))

        p.setBrush(QBrush(QColor(t["bg_card"])))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        p.setBrush(QBrush(QColor(t["accent"] if self._hov else t["accent_bright"])))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), r.width(), 6))

        ff = t.get("font_family", "'Segoe UI', sans-serif").replace("'", "")

        icon_box = QRectF(r.left() + 12, r.top() + 16, 36, 36)
        p.setPen(QPen(QColor(t["glass_border"]), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(icon_box)
        p.setFont(QFont(ff, 16, QFont.Bold))
        p.setPen(QColor(t["text"]))
        p.drawText(icon_box, Qt.AlignCenter, self._emoji)

        p.setFont(QFont(ff, 12, QFont.Bold))
        p.setPen(QColor(t["text"]))
        title_rect = QRectF(r.left() + 58, r.top() + 14, r.width() - 76, 22)
        fm = QFontMetrics(p.font())
        p.drawText(
            title_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            fm.elidedText(self._title, Qt.ElideRight, int(title_rect.width())),
        )

        p.setFont(QFont(ff, 9, QFont.Normal))
        p.setPen(QColor(t["text_dim"]))
        desc_top = r.top() + 40
        desc_h = r.bottom() - desc_top - 10
        desc_r = QRectF(r.left() + 58, desc_top, r.width() - 76, max(desc_h, 28))
        p.drawText(desc_r, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._desc)

        if self._hov:
            _draw_icon_arrow(p, r.right() - 28, r.bottom() - 22, 16, t["text"])

        p.end()


class SignatureOverlay(QWidget):
    # Overlay de assinatura flutuante exibido no rodapé da tela.
    #
    # Responsabilidade: Renderizar faixa horizontal com texto de autoria
    # usando gradiente linear (transição de bg_l para bg_r) suavizado com
    # borda arredondada. Permanece fixo no canto inferior direito com
    # interseção zero de mouse (WA_TransparentForMouseEvents).
    #
    # Posição: 10px da borda direita, 32px da borda inferior, largura 320px.
    # Altura fixa: 26px. Renderização: Gradiente linear com cores do tema.
    #
    # Atributos: parent (widget pai para reposicionamento automático)
    #
    # Design: Gradiente suave de esquerda para direita, borda arredondada
    # (raio 13px), cores sig_bg_l/sig_bg_r/sig_border/sig_text do tema.

    def __init__(self, parent):
        # Inicializa overlay de assinatura.
        #
        # Configuração:
        #   - WA_TransparentForMouseEvents: Não interfere com cliques em elementos abaixo
        #   - WA_TranslucentBackground: Suporte a transparência parcial
        #   - Altura fixa 26px
        #   - Repositioning automático no método _reposition()
        #
        # Parâmetro parent: widget pai (geralmente a tela principal)
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(26)
        self._reposition()

    def _reposition(self):
        # Calcula e aplica posição do overlay no canto inferior direito.
        #
        # Cálculo: Posição anchored no canto inferior direito:
        #   x = parent.width - 320 - 10
        #   y = parent.height - 26 - 32
        #
        # Nota: Deve ser chamado após redimensionamento da janela pai
        # (não implementado resizeEvent, depender de chamada manual).
        p = self.parent()
        if p:
            w = 320
            self.setGeometry(p.width() - w - 10, p.height() - 32, w, 26)

    def paintEvent(self, _):
        # Renderiza faixa de assinatura com gradiente linear e texto.
        #
        # Renderização:
        #   1. Cria QPainter com antialiasing habilitado
        #   2. Desenha gradiente linear de esquerda para direita:
        #      - 0%: sig_bg_l (cor esquerda)
        #      - 25%: sig_bg_r (cor direita)
        #      - 100%: sig_bg_r (cor direita)
        #   3. Desenha retângulo arredondado (raio 13px) com borda sig_border
        #   4. Desenha texto de autoria centrado verticalmente
        #
        # Tipografia: font 9px Segoe UI com cor sig_text do tema.
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        g.setColorAt(0, QColor(t["sig_bg_l"]))
        g.setColorAt(0.25, QColor(t["sig_bg_r"]))
        g.setColorAt(1, QColor(t["sig_bg_r"]))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor(t["sig_border"]), 1))
        p.drawRoundedRect(r, 13, 13)
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(t["sig_text"]))
        p.drawText(
            QRectF(r.left() + 12, r.top(), r.width() - 16, r.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            "♥  Desenvolvido com carinho por Salomão Félix",
        )
        p.end()


class GalleryItem(QFrame):
    # Item individual de galeria de exemplos reais.
    #
    # Responsabilidade: Exibir miniatura de screenshot do módulo com título
    # e feedback visual de hover para indicar seleção/atuação. Carrega imagem
    # do disco formato "módulo_tema.png" ou mostra texto "No Preview".
    #
    # Estrutura: Retângulo fixo (280x180) contendo QLabel de imagem (240x130)
    # e QLabel de título abaixo. Borda dinâmica responde a hover/tema.
    #
    # Atributos:
    #   title: string exibido abaixo da miniatura
    #   module_key: chave do módulo ("gantt", "bpmn", etc) para localização de arquivo
    #   _hover: boolean rastreando estado hover

    def __init__(self, title, module_key):
        # Inicializa item de galeria com título e referência de módulo.
        #
        # Parâmetros:
        #   title: nome exibido do módulo (ex: "Cronograma Gantt")
        #   module_key: chave do módulo para localização de arquivo (ex: "gantt")
        #
        # Layout: Frame fixo (280x180) com sub-labels internos:
        #   - _img_label: Imagem (240x130) posicionada em (20,10)
        #   - _title_label: Título (280px largura) posicionado em (0,150)
        super().__init__()
        self.title = title
        self.module_key = module_key
        self.setFixedSize(280, 180)
        self._hover = False
        self.setCursor(Qt.PointingHandCursor)
        self._img_label = QLabel(self)
        self._img_label.setScaledContents(True)
        self._img_label.setFixedSize(240, 130)
        self._img_label.move(20, 10)

        self._title_label = QLabel(title, self)
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setFixedWidth(280)
        self._title_label.move(0, 150)
        self._refresh_img()

    def _refresh_img(self):
        # Carrega imagem do módulo baseada no tema ativo.
        #
        # Estratégia de carregamento:
        #   1. Constrói caminho: "proeng/resources/screenshots/{module_key}_{theme_name}.png"
        #   2. Verifica existência do arquivo
        #   3. Se existe: carrega QPixmap e exibe
        #   4. Se não existe: exibe texto "No Preview" como fallback
        #   5. Aplica estilos (font label de título, cores de tema)
        #
        # Temas suportados: dark, light, neo_brutalist (conforme T()["name"])
        t = T()
        theme_name = t["name"]
        img_path = f"proeng/resources/screenshots/{self.module_key}_{theme_name}.png"
        import os

        if os.path.exists(img_path):
            self._img_label.setPixmap(QPixmap(img_path))
        else:
            self._img_label.setText("No Preview")

        self._title_label.setStyleSheet(
            f"color: {t['text']}; font-weight: bold; font-size: 11px;"
        )
        self.update_style()

    def update_style(self):
        # Atualiza aparência visual do frame baseado em estado hover e tema.
        #
        # Variação:
        #   Em hover:
        #     - Borda: #000000 (preto)
        #     - Fundo: bg_card2 (cor secundária)
        #   Em normal:
        #     - Borda: glass_border do tema
        #     - Fundo: bg_card (cor primária)
        #   - Borderwidth: sempre 3px
        #   - Border-radius: 0px (brutalista)
        t = T()
        border = "#000000" if self._hover else t.get("glass_border", "#000000")
        bg = t["bg_card2"] if self._hover else t["bg_card"]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 3px solid {border};
                border-radius: 0px;
            }}
        """)

    def enterEvent(self, e):
        # Callback de entrada do mouse - ativa estado hover.
        #
        # Efeito: Define _hover=True e chama update_style() para renderizar
        # feedback visual de que o item é interativo/seleível.
        self._hover = True
        self.update_style()

    def leaveEvent(self, e):
        # Callback de saída do mouse - desativa estado hover.
        #
        # Efeito: Define _hover=False e chama update_style() para restaurar
        # aparência visual padrão.
        self._hover = False
        self.update_style()


class ScreenshotGallery(QScrollArea):
    # Área de rolagem contendo galeria horizontal de exemplos.
    #
    # Responsabilidade: Exibir linha horizontal de GalleryItem para todos
    # os módulos disponíveis. Implementa scroll horizontal (oculta scrollbars),
    # e fornece método refresh() para atualizar imagens quando tema muda.
    #
    # Estrutura: QScrollArea invisível com QWidget container (layout HBox)
    # contendo lista de GalleryItem (um para cada módulo).
    #
    # Atributos:
    #   items: lista de GalleryItem renderizados
    #   container: QWidget pai dos items
    #   layout_g: QHBoxLayout contendo items

    def __init__(self):
        # Inicializa galeria com todos os módulos disponíveis.
        #
        # Processo:
        #   1. Configura scrollarea (height 190, no scrollbars)
        #   2. Cria container widget transparente com layout horizontal
        #   3. Instancia 7 GalleryItem (um para cada módulo suportado)
        #   4. Adiciona items ao layout com spacing de 20px
        #   5. Define container como widget principal
        #
        # Módulos: gantt, flowsheet, eap, bpmn, canvas, ishikawa, w5h2
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(190)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout_g = QHBoxLayout(self.container)
        self.layout_g.setContentsMargins(10, 0, 10, 0)
        self.layout_g.setSpacing(20)

        self.items = [
            GalleryItem("Cronograma Gantt", "gantt"),
            GalleryItem("Fluxograma PFD", "flowsheet"),
            GalleryItem("EAP do Projeto", "eap"),
            GalleryItem("Processo BPMN", "bpmn"),
            GalleryItem("Project Canvas", "canvas"),
            GalleryItem("Ishikawa (6M)", "ishikawa"),
            GalleryItem("Plano 5W2H", "w5h2"),
        ]
        for item in self.items:
            self.layout_g.addWidget(item)

        self.setWidget(self.container)

    def refresh(self):
        # Refresca todas as imagens da galeria após mudança de tema.
        #
        # Operação: Itera todos os GalleryItem e chama _refresh_img()
        # para carregar arquivo de imagem específico do novo tema.
        for item in self.items:
            item._refresh_img()


class SelectionScreen(QWidget):
    # Tela principal de seleção de módulos da aplicação.
    #
    # Responsabilidade: Construir layout completo da tela inicial/home com
    # galeria de exemplos, cards de módulos organizados em seções (Engenharia
    # e Gestão de Projetos), barras de acento visuais, branding, e gerenciar
    # alternância de temas. Coordena callbacks de seleção de módulo e mudança de tema.
    #
    # Estrutura visual:
    #   [Barra acento 4px] | [Topbar 48px: brand + toggle tema] |
    #   [Conteúdo central: badge, galeria, cards em grid] |
    #   [Barra acento 4px]
    #
    # Atributos:
    #   on_select: callback chamado com key quando módulo é clicado
    #   _on_theme: callback para propagar mudança de tema à janela pai
    #   _cards: lista de ModuleCard instanciados
    #   _gallery: instância de ScreenshotGallery

    def __init__(self, on_select, on_theme_toggle):
        # Inicializa tela de seleção com callbacks e construção de UI.
        #
        # Parâmetros:
        #   on_select: função callback executada ao selecionar módulo: on_select(key)
        #   on_theme_toggle: função callback executada ao clicar toggle tema
        #
        # Processo:
        #   1. Inicializa herança QWidget
        #   2. Armazena callbacks para uso em métodos
        #   3. Habilita atributo WA_StyledBackground para aceitar stylesheet
        #   4. Chama _build() para construir UI completa
        super().__init__()
        self.on_select = on_select
        self._on_theme = on_theme_toggle
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()

    def _build(self):
        # Constrói estrutura de layout vertical da tela.
        #
        # Estrutura:
        #   1. Layout externo (outer) vertical sem margens
        #   2. Barra de acento superior 4px (cor accent do tema)
        #   3. Topbar 48px (brand logo + botão toggle tema)
        #   4. Conteúdo scrollável (imagens, cards, pills)
        #   5. Barra de acento inferior 4px
        #
        # Cada elemento recebe marca WA_StyledBackground para aceitar css.
        # Topbar usa HBox com brand na esquerda e toggle na direita (com stretch).
        # Conteúdo usa VBox com alinhamento horizontal centro e padding/spacing.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._top_bar = QWidget()
        self._top_bar.setFixedHeight(4)
        self._top_bar.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._top_bar)

        self._topbar_widget = QWidget()
        self._topbar_widget.setFixedHeight(48)
        self._topbar_widget.setAttribute(Qt.WA_StyledBackground, True)
        tl = QHBoxLayout(self._topbar_widget)
        tl.setContentsMargins(24, 0, 24, 0)
        tl.setSpacing(12)
        self._brand_lbl = QLabel("⚙  PRO ENG")
        tl.addWidget(self._brand_lbl)
        tl.addStretch()
        tog = ThemeToggle()
        tog.theme_changed.connect(self._refresh)
        tog.theme_changed.connect(self._on_theme)
        tl.addWidget(tog)
        outer.addWidget(self._topbar_widget)

        self._content = QWidget()
        self._content.setAttribute(Qt.WA_StyledBackground, True)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setAlignment(Qt.AlignHCenter)
        self._content_layout.setContentsMargins(80, 36, 80, 36)
        self._content_layout.setSpacing(0)
        outer.addWidget(self._content, 1)

        self._cards = []
        self._populate_content()

        self._bot_bar = QWidget()
        self._bot_bar.setFixedHeight(4)
        self._bot_bar.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._bot_bar)

        self._apply_styles()

    def _populate_content(self):
        # Preenche conteúdo com todos os elementos visuais.
        #
        # Elementos renderizados (de cima para baixo):
        #   1. Badge de tagline decorativa (✦ Ferramentas... ✦)
        #   2. Título maiúsculo grande "PRO ENG"
        #   3. Subtítulo técnico (PyQt5 · Zoom · Exportação)
        #   4. Título galeria "✦ GALERIA DE EXEMPLOS REAIS ✦"
        #   5. ScreenshotGallery com 7 items (gantt, flowsheet, eap, bpmn, canvas, ishikawa, w5h2)
        #   6. 2 seções em linha (wrappers):
        #      a) Engenharia com 1 card (Flowsheet)
        #      b) Gestão de Projetos com 6 cards (em grid 2x3)
        #   7. Pills de autoria no rodapé "Desenvolvido por : Salomão Félix"
        #
        # Processo: Usa self._content_layout (VBox) para adicionar elementos
        # verticalmente. Cards criados (ModuleCard) são adicionados a self._cards list.
        # Seções usam layouts HBox/VBox/Grid para organização espacial.
        lay = self._content_layout

        br = QHBoxLayout()
        br.setAlignment(Qt.AlignCenter)
        self._badge = QLabel("✦Ferramentas de Engenharia e Gestão✦")
        self._badge.setAlignment(Qt.AlignCenter)
        br.addWidget(self._badge)
        lay.addLayout(br)
        lay.addSpacing(18)

        self._t1 = QLabel("PRO ENG")
        self._t1.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t1)
        self._t2 = QLabel("— ")
        self._t2.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t2)
        lay.addSpacing(8)

        self._sub = QLabel("PyQt5  ·  Zoom Infinito  ·  Exportação PDF & PNG")
        self._sub.setAlignment(Qt.AlignCenter)
        self._sub.setWordWrap(True)
        lay.addWidget(self._sub)
        lay.addSpacing(24)

        self._gallery_title = QLabel("✦ GALERIA DE EXEMPLOS REAIS ✦")
        self._gallery_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._gallery_title)
        lay.addSpacing(8)

        self._gallery = ScreenshotGallery()
        lay.addWidget(self._gallery)
        lay.addSpacing(32)

        main_row = QHBoxLayout()
        main_row.setSpacing(24)
        main_row.setAlignment(Qt.AlignHCenter)

        eng_wrapper = QWidget()
        eng_wrapper.setFixedWidth(280)
        eng_layout = QVBoxLayout(eng_wrapper)
        eng_layout.setSpacing(12)
        eng_layout.setContentsMargins(0, 0, 0, 0)
        eng_label = QLabel("🔧 ENGENHARIA")
        eng_label.setAlignment(Qt.AlignCenter)
        eng_layout.addWidget(eng_label)
        eng_modules = [
            (
                "🏭",
                "PFD Flowsheet",
                "Diagrama de processo industrial\ncom 26 equipamentos e tubulações",
                "flowsheet",
            ),
        ]
        for em, ti, de, key in eng_modules:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c)
            eng_layout.addWidget(c)
        main_row.addWidget(eng_wrapper)

        gp_wrapper = QWidget()
        gp_wrapper.setFixedWidth(600)
        gp_layout = QVBoxLayout(gp_wrapper)
        gp_layout.setSpacing(12)
        gp_layout.setContentsMargins(0, 0, 0, 0)
        gp_label = QLabel("📁 GESTÃO DE PROJETOS")
        gp_label.setAlignment(Qt.AlignCenter)
        gp_layout.addWidget(gp_label)
        gp_modules = [
            (
                "📊",
                "Cronograma Gantt",
                "Cronograma com CPM\nCaminho Crítico Automático",
                "gantt",
            ),
            (
                "📋",
                "Gerador EAP",
                "Estrutura Analítica do Projeto\ncom numeração WBS automática",
                "eap",
            ),
            (
                "🔀",
                "BPMN Modeler",
                "Pools, Lanes e fluxos\nde processo BPMN 2.0",
                "bpmn",
            ),
            (
                "📝",
                "PM Canvas",
                "Project Model Canvas\nGrelha Finocchio completa",
                "canvas",
            ),
            (
                "🐟",
                "Ishikawa",
                "Diagrama Espinha de Peixe\nCausa e Efeito (6M)",
                "ishikawa",
            ),
            (
                "🎯",
                "Plano 5W2H",
                "Gestão de Ações (5W2H)\nDistribuição Automática",
                "w5h2",
            ),
        ]
        gp_grid = QGridLayout()
        gp_grid.setSpacing(12)
        gp_grid.setContentsMargins(0, 0, 0, 0)
        row, col = 0, 0
        for em, ti, de, key in gp_modules:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c)
            gp_grid.addWidget(c, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        gp_layout.addLayout(gp_grid)
        main_row.addWidget(gp_wrapper)

        lay.addLayout(main_row)
        lay.addSpacing(22)

        lay.addSpacing(22)

        self._pills_row = QHBoxLayout()
        self._pills_row.setAlignment(Qt.AlignCenter)
        self._pills_row.setSpacing(8)
        self._pills = []
        for tag in ["Desenvolvido por : Salomão Félix"]:
            lbl = QLabel(tag)
            self._pills.append(lbl)
            self._pills_row.addWidget(lbl)
        lay.addLayout(self._pills_row)

    def _apply_bg(self):
        # Alias para aplicar estilos de fundo (mantido por compatibilidade).
        #
        # Propósito: Chamada alternativa a _apply_styles() (compatibilidade reversa).
        self._apply_styles()

    def _apply_styles(self):
        # Aplica estilos visuais a todos os elementos baseado no tema ativo.
        #
        # Controles estilizados:
        #   - Background principal (bg_app)
        #   - Barras de acento superior/inferior (accent)
        #   - Topbar com borda inferior (glass_border)
        #   - Labels de título (t1=48px) e subtítulo (text_dim)
        #   - Badge com fundo accent e border glass_border
        #   - Título galeria com border e styling
        #   - Pills de autoria com border glass_border
        #
        # Processo: Extrai cores/dimensões de T(), constrói stylesheets CSS
        # para cada widget, aplica via setStyleSheet(). Font utiliza font_family do tema.
        t = T()
        bw = t.get("border_width", 3)
        ff = t.get("font_family", "'Segoe UI', 'Arial', sans-serif")

        self.setStyleSheet(f"QWidget {{ background-color: {t['bg_app']}; }}")

        self._top_bar.setStyleSheet(f"QWidget {{ background: {t['accent']}; }}")
        self._bot_bar.setStyleSheet(f"QWidget {{ background: {t['accent']}; }}")

        self._topbar_widget.setStyleSheet(
            f"QWidget {{ background: {t['bg_card']}; border-bottom: {bw}px solid {t['glass_border']}; }}"
        )
        self._brand_lbl.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 16px; font-weight: 900; background: {t['bg_app']}; border: {bw}px solid {t['glass_border']}; padding: 5px 10px; }}"
        )

        self._content.setStyleSheet(f"QWidget {{ background-color: {t['bg_app']}; }}")

        self._badge.setStyleSheet(
            f"QLabel {{ color: #FFFFFF; font-family: {ff};"
            f" font-size: 11px; font-weight: 900;"
            f" background: {t['accent']}; border: {bw}px solid {t['glass_border']};"
            f" padding: 4px 18px; }}"
        )

        self._t1.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 48px; font-weight: 900; background: transparent; letter-spacing: 2px; }}"
        )

        self._t2.setStyleSheet(
            f"QLabel {{ color: {t['accent']}; font-family: {ff};"
            f" font-size: 28px; font-weight: 900; background: transparent; }}"
        )

        self._sub.setStyleSheet(
            f"QLabel {{ color: {t['text_dim']}; font-family: {ff};"
            f" font-size: 12px; font-weight: bold; background: transparent; }}"
        )

        self._gallery_title.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 12px; font-weight: 900; background: {t['bg_card']}; border: {bw}px solid {t['glass_border']}; padding: 5px; }}"
        )

        pill_s = (
            f"QLabel {{ color: {t['text']}; font-family: {ff}; font-size: 11px;"
            f" background: {t['bg_card']}; border: {bw}px solid {t['glass_border']};"
            f" padding: 4px 14px; font-weight: bold; }}"
        )
        for p in self._pills:
            p.setStyleSheet(pill_s)

    def _refresh(self):
        # Atualiza completamente a tela após mudança de tema.
        #
        # Ações sequenciais:
        #   1. _apply_styles(): Regenera stylesheets CSS com cores do novo tema
        #   2. _gallery.refresh(): Recarrega imagens dos módulos (tema-específicas)
        #   3. Itera _cards: Chama update() para solicitar repintura de cada card
        #   4. self.update(): Solicita repintura do widget pai (SelectionScreen)
        #   5. self.repaint(): Força repintura síncrona (flush do buffer de paint)
        self._apply_styles()
        self._gallery.refresh()
        for c in self._cards:
            c.update()
        self.update()
        self.repaint()

    def paintEvent(self, event):
        # Renderiza fundo sólido para garantir visibilidade em mudanças de tema.
        #
        # Responsabilidade: Preencher explicitamente background rect com cor
        # bg_app do tema ativo. Necessário para evitar problemas de transparência
        # em alguns estilos de decoração de janela do SO.
        #
        # Processo:
        #   1. Obtém QPainter para desenho no widget
        #   2. Preenche rect inteiro com QColor de bg_app do tema
        #   3. Chama super().paintEvent() para renderização padrão de widgets
        #
        # Timing: Executado ANTES de super().paintEvent() para que conteúdo
        # seja renderizado sobre fundo sólido.
        t = T()
        from PyQt5.QtGui import QColor

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(t["bg_app"]))
        painter.end()
        super().paintEvent(event)
