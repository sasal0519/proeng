# -*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MÓDULO: Plano de Ação 5W2H — Gestão de Ações com Auto-layout             ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# Responsabilidade:
#   Diagrama 5W2H para gestão de ações (What/Who/When/Where/Why/How/Cost).
#   Estrutura hierárquica 2 níveis: Raiz (ROOT) → Ações (WHAT) → Detalhes (WHY/WHO/...).
#   Layout automático: ações em coluna central, detalhes em coluna direita.
#   Conectores (bezier curves) vinculam elementos visuamente.
#
# Padrões de Projeto:
#   - Observer Pattern: W5H2Signals emite sinais (add_action, delete_node)
#     conectados aos slots de W5H2Widget
#   - Factory Pattern: W5H2Node factory para renderização customizada
#     conforme tipo (ROOT 240px, WHAT 220px, detalhe 200px)
#   - Strategy Pattern: calcular_posicoes() layout engine com distribuição
#     automática em colunas (raiz → ações → detalhes lado-a-lado)
#   - State Pattern: nodes dict com ["text", "type", "parent", "children"]
#     persistido via get_state()/set_state()
#
# Fluxo de Interação:
#   1. Click (+) botão → emit add_action() → cria WHAT + 6 detalhes (WHY/...) vazios
#   2. Double-click → emit edit_start() → abre W5H2FloatingEditor
#   3. Edição → emit commit_text() → atualiza nodes[nid]["text"] + redesenha
#   4. Click (−) → emit delete_node() → remove ação + all 6 detalhes
#
# Estrutura Inicial:
#   - Node 1: ROOT "Novo Projeto/Meta" (nível raiz)
#   - User cria N ações (WHAT) sob ROOT
#   - Cada ação tem exatamente 6 detalhes (WHY/WHO/WHERE/WHEN/HOW/COST)
#
# Características de Rendering (Neo-brutalist):
#   - Sem gradientes, apenas cores sólidas
#   - Bordas 3px retas (sem border-radius)
#   - Nós com header colorido (cor específica por tipo 5W2H)
#   - Conectores: linhas com "joelhos" (L-shaped bezier curves)
#   - Zoom responsivo 0.3x a 3.0x (menor range que Ishikawa)

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
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

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.utils import (
    _export_view,
    _c,
    _solid_fill,
    W5H2_TYPES,
    _nb_paint_node,
    _is_nb,
)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class W5H2Signals(QObject):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Emissora de Sinais para Operações de Nó do 5W2H                     ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Broker de eventos centralizado para operações de edição do plano 5W2H.
    #   Conecta cliques do mouse (em W5H2Node) às operações de lógica
    #   (em W5H2Widget).
    #
    # Sinais Emitidos:
    #   - add_action(int parent_id): user clicou (+) para criar sub-ação
    #   - delete_node(int nid): user clicou (−) para remover nó (ação + 6 detalhes)
    #   - edit_start(int nid): user deu double-click para editar texto
    #   - commit_text(int nid, str texto): usuario confirmou edição (Enter/Escape)
    #
    add_action = pyqtSignal(int)
    delete_node = pyqtSignal(int)
    edit_start = pyqtSignal(int)
    commit_text = pyqtSignal(int, str)


class W5H2FloatingEditor(QTextEdit):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Editor Flutuante Multi-linha para Texto de Nó 5W2H                  ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   QTextEdit customizado que sobrepõe o diagrama para edição inline
    #   de detalhes de ações/nós (suporta múltiplas linhas, diferente do Ishikawa).
    #   Posiciona-se dinamicamente sobre o nó alvo (excluindo header colorido),
    #   aplica estilos tema, emite confirmação (Shift+Enter para nova linha).
    #
    # Fluxo:
    #   1. _on_edit_start(nid) → open(nid, texto_atual, scene_rect, view)
    #   2. Editor aparece (abaixo do header) com foco + seleção total
    #   3. User digita (Enter=confirma, Shift+Enter=nova linha, Escape=cancela)
    #   4. _commit(texto) propaga para W5H2Widget
    #
    # Atributos:
    #   - _target_id: ID do nó em edição (default -1 = nenhum)
    #   - _original: Texto anterior (para reverter com Escape)
    #   - _done: Flag para evitar múltiplas emissões de commit (proteção)
    #
    committed = pyqtSignal(int, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = -1, "", False
        self.apply_theme()
        self.hide()

    def apply_theme(self):
        # Aplica stylesheet fixo (tema não afeta muito para editor)
        # Neo-brutalist: branco fundo, preto texto, borda 3px preta sólida
        t = T()
        self.setStyleSheet(
            f"QTextEdit {{ background: #FFFFFF; color: #000000; border: 3px solid #000000; border-radius: 0px; font-family: 'Courier New'; font-size: 11pt; font-weight: bold; padding: 6px; }}"
        )

    def open(self, target_id, current_text, scene_rect, view):
        # Prepara e exibe o editor flutuante
        # Parâmetros:
        #   - target_id: Qual nó estamos editando
        #   - current_text: Texto inicial do QTextEdit
        #   - scene_rect: Bounding box do nó em coordenadas de cena (apenas área de texto, não header)
        #   - view: QGraphicsView para conversão coordenadas
        self._target_id, self._original, self._done = target_id, current_text, False
        rect_in_view = view.mapFromScene(scene_rect).boundingRect()
        self.setGeometry(rect_in_view)
        self.setPlainText(current_text)
        self.selectAll()
        self.show()
        self.raise_()
        self.setFocus()

    def _commit(self, text=None):
        # Confirma edição e emite sinal
        # Se _done já é True, ignora (proteção contra duplas emissões)
        if self._done:
            return
        self._done = True
        self.hide()
        self.committed.emit(
            self._target_id, (text if text is not None else self.toPlainText()).strip()
        )

    def keyPressEvent(self, event):
        # Intercepta atalhos: Enter (sem Shift) confirma, Shift+Enter novvinha linha, Escape cancela
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter → nova linha
                super().keyPressEvent(event)
            else:
                # Enter (sem Shift) → confirma
                self._commit()
        elif event.key() == Qt.Key_Escape:
            # Escape cancela e reverte ao original
            self._commit(self._original)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        # Quando editor perde foco (click fora), confirma com novo texto
        self._commit()
        super().focusOutEvent(event)


class W5H2Node(QGraphicsItem):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Item Gráfico — Nó de 5W2H (ROOT, WHAT, ou Detalhe 5W2H)            ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Renderização individual de nó do diagrama 5W2H. Suporta tipos:
    #   - ROOT (raiz): "Novo Projeto/Meta", 240px×80px
    #   - WHAT (ação): "Nova Ação...", 220px×70px
    #   - Detalhes (WHY/WHO/WHERE/WHEN/HOW/COST): 200px×60px cada
    #   
    #   Cada tipo tem cor única (do dict W5H2_TYPES em themes.py).
    #   Header colorido em topo, texto preenchido abaixo.
    #   Responde a hover com affordances (+/−).
    #
    # Hierarquia de Tipos:
    #   - ROOT: Header "Raiz", 240px×80px, negrito 14pt
    #   - WHAT: Header "O QUÊ", 220px×70px, negrito 12pt
    #   - WHY/WHO/WHERE/WHEN/HOW/COST: Headers específicos, 200px×60px, normal 10pt
    #   Tamanhos escalam com zoom_level
    #
    # Rendering (Neo-brutalist):
    #   - Header colorido (cor do tipo, 28px altura)
    #   - Texto em baixo (ao redor, alinhado top center)
    #   - Borde 3px ao redor (sem border-radius em neo-brutalist)
    #   - Hover: botões (+) para ROOT/WHAT, (−) apenas para WHAT
    #   - Se texto vazio: placeholder "✎ Preencher"
    #
    # Atributos:
    #   - node_id: Chave unívoca no dict nodes de W5H2Widget
    #   - text: Conteúdo textual (multiline suportado via QTextEdit)
    #   - node_type: "ROOT" | "WHAT" | "WHY" | "WHO" | "WHERE" | "WHEN" | "HOW" | "COST"
    #   - type_data: Dict de W5H2_TYPES com ["t"=label, "c"=cor_hex]
    #   - hovered: Flag de estado hover
    #   - _font: QFont escalada por zoom + weight depende de tipo
    #   - w, h: Largura/altura calculadas em _calc_size()
    #
    def __init__(self, node_id, text, node_type, signals, zoom):
        super().__init__()
        self.node_id = node_id
        self.text = text
        self.node_type = node_type
        self.signals = signals
        self.zoom = zoom
        self.hovered = False

        self.type_data = W5H2_TYPES[self.node_type]

        if self.node_type == "ROOT":
            self._font = QFont("Segoe UI", int(14 * zoom), QFont.Bold)
            self.base_w, self.base_h = 240 * zoom, 80 * zoom
        elif self.node_type == "WHAT":
            self._font = QFont("Segoe UI", int(12 * zoom), QFont.Bold)
            self.base_w, self.base_h = 220 * zoom, 70 * zoom
        else:
            self._font = QFont("Segoe UI", int(10 * zoom), QFont.Normal)
            self.base_w, self.base_h = 200 * zoom, 60 * zoom

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(10)

    def _calc_size(self):
        # Calcula dimensões finais do nó baseado no texto + tipo
        # Considera largura do header (label tipo) + texto principal
        # Define placeholder se vazio
        sample = self.text if self.text else "✎ Preencher"

        # 1. Calcula largura do Título/Cabeçalho (Header)
        header_font = QFont("Consolas", int(9 * self.zoom), QFont.Bold)
        fm_header = QFontMetrics(header_font)
        header_w = (
            fm_header.horizontalAdvance(self.type_data["t"])
            if hasattr(fm_header, "horizontalAdvance")
            else fm_header.width(self.type_data["t"])
        ) + 40 * self.zoom

        # 2. Calcula largura e altura do Texto Interno
        fm_text = QFontMetrics(self._font)
        base_available_w = max(self.base_w, header_w) - 20 * self.zoom
        text_rect = fm_text.boundingRect(
            0, 0, int(base_available_w), 5000, Qt.AlignCenter | Qt.TextWordWrap, sample
        )

        # Se texto muito longo pode exceder available_w
        text_w = text_rect.width() + 30 * self.zoom

        # 3. Define dimensões finais (respeitando mínimos)
        self.w = max(self.base_w, header_w, text_w)
        self.h = max(self.base_h, text_rect.height() + 40 * self.zoom)

    def boundingRect(self):
        # Retorna área de clique + margem
        m = 15 * self.zoom
        return QRectF(0, 0, self.w, self.h).adjusted(-m, -m, m, m)

    def paint(self, painter, option, widget=None):
        # Renderiza o nó com header + texto + botões hover
        # Header: fundo colorido do tipo (28px altura)
        # Texto: abaixo do header, alinhado center-top
        # Se neo-brutalist: sombra + borda via _nb_paint_node
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()
        r = QRectF(0, 0, self.w, self.h)

        if _is_nb(t):
            # Neo-brutalist: fundo sólido + sombra offset
            _nb_paint_node(painter, r, self.hovered or self.node_type == "ROOT")
            bw = t.get("border_width", 3)
            header_h = 28 * self.zoom
            painter.save()
            painter.setBrush(QBrush(QColor(self.type_data["c"])))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(bw, bw, self.w - bw * 2, header_h - bw))
            painter.restore()
        else:
            # Não neo-brutalist: fundo rounded
            painter.setBrush(
                QBrush(_solid_fill(r, self.hovered or self.node_type == "ROOT"))
            )
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(r, 12, 12)

            header_h = 28 * self.zoom
            painter.save()
            clip_path = QPainterPath()
            clip_path.addRoundedRect(r, 12, 12)
            painter.setClipPath(clip_path)

            painter.setBrush(QBrush(QColor(self.type_data["c"])))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(0, 0, self.w, header_h))
            painter.restore()

        # Renderiza texto do header (label do tipo 5W2H)
        header_h = 28 * self.zoom
        painter.setPen(
            QColor(
                "#000000" if self.node_type in ["WHY", "WHEN", "WHERE"] else "#FFFFFF"
            )
        )
        painter.setFont(QFont("Consolas", int(10 * self.zoom), QFont.Bold))
        header_text_rect = QRectF(0, 0, self.w, header_h)
        painter.drawText(header_text_rect, Qt.AlignCenter, self.type_data["t"])

        # Renderiza texto principal (conteúdo do nó)
        painter.setPen(_c("text" if self.text else "text_dim"))
        painter.setFont(self._font)

        p_val = 15 * self.zoom
        text_rect = QRectF(
            p_val,
            header_h + 8 * self.zoom,
            self.w - 2 * p_val,
            self.h - header_h - 16 * self.zoom,
        )
        painter.drawText(
            text_rect,
            Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap,
            self.text if self.text else "✎ Preencher",
        )

        if self.hovered:
            # Botões de affordance
            btn_s = 24 * self.zoom
            if self.node_type in ["ROOT", "WHAT"]:
                # Botão (+) adicionar ação — top-right
                add_rect = QRectF(
                    self.w - btn_s / 2, self.h / 2 - btn_s / 2, btn_s, btn_s
                )
                if _is_nb(t):
                    painter.setBrush(QBrush(QColor(t["btn_add"])))
                    painter.setPen(QPen(QColor("#000000"), 2))
                    painter.drawRect(add_rect)
                else:
                    painter.setBrush(QBrush(QColor("#1A5C1A")))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(add_rect, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.setFont(QFont("Consolas", int(14 * self.zoom), QFont.Bold))
                painter.drawText(add_rect, Qt.AlignCenter, "+")

            if self.node_type == "WHAT":
                # Botão (−) deletar ação — top-left
                del_rect = QRectF(-btn_s / 2, -btn_s / 2, btn_s, btn_s)
                if _is_nb(t):
                    painter.setBrush(QBrush(QColor(t["btn_del"])))
                    painter.setPen(QPen(QColor("#000000"), 2))
                    painter.drawRect(del_rect)
                else:
                    painter.setBrush(QBrush(QColor("#8B1515")))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(del_rect, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.setFont(QFont("Consolas", int(16 * self.zoom), QFont.Bold))
                painter.drawText(del_rect, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        # Intercepta cliques em botões (+) e (−)
        # Emite sinais via QTimer.singleShot (defer para evitar reentrância)
        if event.button() == Qt.LeftButton:
            btn_s = 24 * self.zoom
            add_rect = QRectF(self.w - btn_s / 2, self.h / 2 - btn_s / 2, btn_s, btn_s)
            del_rect = QRectF(-btn_s / 2, -btn_s / 2, btn_s, btn_s)

            if (
                self.node_type in ["ROOT", "WHAT"]
                and add_rect.contains(event.pos())
                and self.hovered
            ):
                QTimer.singleShot(0, lambda: self.signals.add_action.emit(self.node_id))
                event.accept()
                return
            if (
                self.node_type == "WHAT"
                and del_rect.contains(event.pos())
                and self.hovered
            ):
                QTimer.singleShot(
                    0, lambda: self.signals.delete_node.emit(self.node_id)
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Double-click abre editor flutuante para este nó
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))


class W5H2Widget(QWidget):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Widget Principal — Orquestrador do Plano 5W2H                       ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Manager central do plano 5W2H. Mantém estrutura hierárquica (ROOT →
    #   WHAT/Ações → Detalhes 5W2H), orquestra layout via calcular_posicoes(),
    #   gerencia zoom (0.3x a 3.0x), persiste via get_state()/set_state().
    #
    # Estrutura de Dados (nodes):
    #   Dict[int, {
    #     "text": str,            # Conteúdo do nó
    #     "type": "ROOT"|"WHAT"|"WHY"|... # Tipo do nó
    #     "parent": int|None      # ID nó pai (None se raiz)
    #     "children": [int]       # IDs dos nós filhos
    #   }]
    #
    # Estrutura Hierárquica:
    #   - Nível 0: Node 1 (ROOT) — "Novo Projeto"
    #   - Nível 1: N nós WHAT (ações) — filhos de ROOT
    #   - Nível 2: Sempre exatamente 6 nós (WHY/WHO/WHERE/WHEN/HOW/COST) por WHAT
    #
    # Layout Engine (calcular_posicoes):
    #   Coloca componentes em 3 "colunas": raiz (0,0) → ações (x1,y*) → detalhes (x2,y**)
    #   Ações distribuídas verticalmente em coluna central
    #   Detalhes lado a lado com suas ações na coluna direita
    #
    # Estados Iniciais:
    #   - 1 nó raiz (ROOT): "Novo Projeto / Meta"
    #   - 0 nós ação iniciais — usuário adiciona
    #   - Detalhes criados automaticamente quando ação é adicionada
    #
    
    def __init__(self):
        super().__init__()
        self.signals = W5H2Signals()
        self.signals.add_action.connect(self._on_add_action)
        self.signals.delete_node.connect(self._on_delete_node)
        self.signals.edit_start.connect(self._on_edit_start)
        self.signals.commit_text.connect(self._on_commit_text)

        self.zoom_level = 0.8  # Começa em 80% (diagrama é denso)
        self.next_id = 2
        self.node_dimensions, self.node_positions = {}, {}

        # Estrutura inicial com Raiz apenas
        self.nodes = {
            1: {
                "text": "Novo Projeto / Meta",
                "type": "ROOT",
                "parent": None,
                "children": [],
            }
        }

        self._setup_ui()
        self._float_editor = W5H2FloatingEditor(self.view)
        self._float_editor.committed.connect(self.signals.commit_text.emit)
        self.update_zoom(1.0)

    def _setup_ui(self):
        # Configura layout do widget: QGraphicsView para diagrama
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)

    def refresh_theme(self):
        # Chamado quando tema global muda
        # Atualiza fundo + editor + redesenha diagrama
        t = T()
        if hasattr(self, "view"):
            self.view.setBackgroundBrush(QBrush(_c("bg_app")))

        if hasattr(self, "_float_editor"):
            self._float_editor.apply_theme()

        # Redesenha para atualizar cores dos conectores
        self._draw_diagram()

    def zoom_in(self):
        # Aumenta zoom 15%
        self.update_zoom(self.zoom_level * 1.15)

    def zoom_out(self):
        # Diminui zoom 15%
        self.update_zoom(self.zoom_level / 1.15)

    def reset_zoom(self):
        # Volta para zoom 1.0
        self.update_zoom(1.0)

    def update_zoom(self, z):
        # Aplica novo zoom level se dentro limites [0.3, 3.0]
        # Range menor que Ishikawa porque diagrama é mais denso
        self.zoom_level = max(0.3, min(z, 3.0))
        self._draw_diagram()

    def calcular_posicoes(self):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Motor de Layout Automático — Distribuição 3-Coluna do Diagrama      ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Calcula as posições (x, y) de cada nó para criar uma visualização
        #   organizada em 3 colunas:
        #   1. Coluna 0 (x=0): Nó ROOT (raiz) — centralizado verticalmente
        #   2. Coluna 1 (x=dist_x_l1): Nós WHAT (ações) — distribuídos verticalmente
        #   3. Coluna 2 (x=dist_x_l1+aw+dist_x_l2): Detalhes (WHY/...) — lado-a-lado
        #
        # Algoritmo:
        #   1. Iterar ações (filhos de ROOT)
        #   2. Para cada ação: posicionar seus 6 detalhes verticalmente (com padding)
        #   3. Calcular a Y da ação como centro vertical dos seus detalhes
        #   4. Centralizar ROOT verticalmente sobre a mediana das ações
        #
        # Parâmetros: Nenhum (usa self.zoom_level, self.nodes, self.node_dimensions)
        # Retorno: Popula self.node_positions Dict[int, (x, y)]
        # Why:
        #   O layout hierárquico (raiz → ações → detalhes) requer espaçamento
        #   proporcional e alinhamento vertical para leitura fluida. O zoom afeta
        #   todas as distâncias para garantir responsividade visual.
        
        z = self.zoom_level
        self.node_positions.clear()
        
        # Distâncias entre colunas (escaladas com zoom)
        dist_x_l1 = 350 * z        # Coluna 1: distância ROOT → WHAT
        dist_x_l2 = 320 * z        # Coluna 2: distância WHAT → Detalhes
        pad_y_l2 = 15 * z          # Padding vertical entre detalhes
        pad_y_l1 = 80 * z          # Padding vertical entre ações
        
        current_y = 0
        action_ids = self.nodes[1]["children"]  # Todas as ações (filhos de ROOT)
        
        # Iterar cada ação (nível 1)
        for aid in action_ids:
            aw, ah = self.node_dimensions[aid]
            detail_ids = self.nodes[aid]["children"]  # 6 detalhes desta ação
            details_total_h = 0
            detail_ys = []        # Coordenadas Y centrais dos detalhes
            start_y = current_y
            
            # Posicionar os 6 detalhes (nível 2) verticalmente
            for did in detail_ids:
                dw, dh = self.node_dimensions[did]
                # X: coluna direita; Y: acumula verticalmente
                self.node_positions[did] = (dist_x_l1 + aw + dist_x_l2, current_y)
                detail_ys.append(current_y + dh / 2)  # Centro Y do detalhe
                current_y += dh + pad_y_l2
                details_total_h += dh + pad_y_l2
            
            # Posicionar ação: Y = centro dos seus detalhes
            if detail_ys:
                # Ação alinhada ao centro vertical dos 6 detalhes
                action_y = sum(detail_ys) / len(detail_ys) - ah / 2
            else:
                # Se sem detalhes (improvável), ação em start_y
                action_y = start_y
                current_y += ah
            
            self.node_positions[aid] = (dist_x_l1, action_y)
            current_y += pad_y_l1  # Espaçamento até próxima ação
        
        # Posicionar ROOT (nível 0): Y = centro da mediana das ações
        rw, rh = self.node_dimensions[1]
        if action_ids:
            # ROOT no centro de todas as ações
            root_y = (
                sum(
                    self.node_positions[aid][1] + self.node_dimensions[aid][1] / 2
                    for aid in action_ids
                )
                / len(action_ids)
                - rh / 2
            )
        else:
            # Se sem ações, ROOT em topo
            root_y = 0
        
        self.node_positions[1] = (0, root_y)

    def _draw_diagram(self):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Orquestrador de Renderização do Diagrama Completo 5W2H             ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Pipeline completo de renderização iniciado por qualquer mudança
        #   (zoom, adição/deleção/edição de nó). Executa em ordem:
        #   1. Limpar cena anterior (QGraphicsScene.clear())
        #   2. Calcular dimensões W×H de cada nó
        #   3. Calcular posições (x, y) via motor layout (calcular_posicoes)
        #   4. Desenhar conectores: linhas L-shaped (bezier com joelhos)
        #      - ROOT → WHAT: linha horizontal + vertical (mid_x)
        #      - WHAT → Detalhe: idem
        #   5. Desenhar itens nós (W5H2Node) em suas posições
        #   6. Ajustar scene rect com margem (padding de 100px)
        #
        # Parâmetros: Nenhum
        # Retorno: Nenhum (modifica self.scene)
        # Why:
        #   Centraliza toda lógica de renderização em um ponto. Permite
        #   que zoom e edições desencadeiem redesenho completo sem duplicação.
        
        self.scene.clear()
        if not self.nodes:
            return
        
        t = T()
        z = self.zoom_level
        
        # 1. Calcular dimensões de cada nó (W5H2Node._calc_size)
        self.node_dimensions.clear()
        for nid, data in self.nodes.items():
            # Factory: cria W5H2Node temporário apenas para medir tamanho
            tmp = W5H2Node(nid, data["text"], data["type"], self.signals, z)
            self.node_dimensions[nid] = (tmp.w, tmp.h)
        
        # 2. Calcular posições (x, y) de cada nó
        self.calcular_posicoes()
        
        # 3. Desenhar conectores (linhas L-shaped entre nós)
        pen_conn = QPen(
            QColor(t["accent_dim"]),          # Cor do conector (cinza tema)
            max(2, int(3 * z)),               # Espessura escalada com zoom
            Qt.SolidLine,
            Qt.RoundCap,                      # Extremidades arredondadas
            Qt.RoundJoin,
        )
        
        # Ponto de saída da RAIZ (lado direito do ROOT)
        root_x, root_y = self.node_positions[1]
        rw, rh = self.node_dimensions[1]
        p1_root = QPointF(root_x + rw, root_y + rh / 2)
        
        # Conectores ROOT → WHAT → Detalhes
        for aid in self.nodes[1]["children"]:
            ax, ay = self.node_positions[aid]
            aw, ah = self.node_dimensions[aid]
            p2_action = QPointF(ax, ay + ah / 2)  # Entrada da ação (lado esq)
            
            # Conector RAIZ → AÇÃO: caminho L-shaped
            # Estratégia: linha horiz até mid_x, depois vert até ação, depois horiz
            mid_x = (p1_root.x() + p2_action.x()) / 2
            path = QPainterPath()
            path.moveTo(p1_root)
            path.lineTo(mid_x, p1_root.y())        # Barra horizontal
            path.lineTo(mid_x, p2_action.y())      # Barra vertical
            path.lineTo(p2_action)                 # Entrada ação
            self.scene.addPath(path, pen_conn)
            
            # Ponto de saída da AÇÃO (lado direito)
            p1_action = QPointF(ax + aw, ay + ah / 2)
            
            # Conectores AÇÃO → DETALHES
            for did in self.nodes[aid]["children"]:
                dx, dy = self.node_positions[did]
                dw, dh = self.node_dimensions[did]
                p2_detail = QPointF(dx, dy + dh / 2)  # Entrada detalhe (lado esq)
                
                # Conector AÇÃO → DETALHE: caminho L-shaped (idem)
                mid_x2 = (p1_action.x() + p2_detail.x()) / 2
                path2 = QPainterPath()
                path2.moveTo(p1_action)
                path2.lineTo(mid_x2, p1_action.y())    # Barra horizontal
                path2.lineTo(mid_x2, p2_detail.y())    # Barra vertical
                path2.lineTo(p2_detail)                # Entrada detalhe
                self.scene.addPath(path2, pen_conn)
        
        # 4. Desenhar itens nós renderizados (W5H2Node)
        for nid, (nx, ny) in self.node_positions.items():
            # Factory: cria W5H2Node com renderização final
            item = W5H2Node(
                nid, self.nodes[nid]["text"], self.nodes[nid]["type"], self.signals, z
            )
            item.setPos(nx, ny)
            self.scene.addItem(item)
        
        # 5. Ajustar bounding rect da cena com margem
        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(
                -100 * z, -100 * z, 100 * z, 100 * z  # Margem responsiva
            )
        )

    def _on_add_action(self, parent_id=1):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Slot — Criar Nova Ação (WHAT) + 6 Detalhes Automáticos             ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Slot conectado ao sinal add_action (emitido por clique botão (+)).
        #   Cria uma cadeia de 7 nós:
        #   1. Um nó WHAT (ação) com texto vazio
        #   2. Seis nós detalhes (WHY/WHO/WHERE/WHEN/HOW/COST) vazios
        #   Abre automaticamente o editor para preenchimento do WHAT.
        #
        # Parâmetros:
        #   - parent_id (int): ID do nó pai. Default=1 (ROOT). Normalmente
        #     ações só são filhas de ROOT (não de outras ações).
        #
        # Retorno: Nenhum (modifica self.nodes, triggers redraw)
        # Why:
        #   Estrutura 5W2H exige exatamente 6 detalhes por ação. Auto-criação
        #   economiza cliques do usuário (sem precisar criar cada detalhe).
        #   Auto-foco no editor = UX fluida para preenchimento rápido.
        
        # Criar nó WHAT (ação)
        new_action_id = self.next_id
        self.next_id += 1
        self.nodes[new_action_id] = {
            "text": "",                    # Texto inicial vazio
            "type": "WHAT",
            "parent": 1,                   # Ações sempre filhas de ROOT
            "children": [],                # Será preenchido com 6 detalhes
        }
        self.nodes[1]["children"].append(new_action_id)
        
        # Criar 6 detalhes automáticos
        details = ["WHY", "WHO", "WHERE", "WHEN", "HOW", "COST"]
        for d_type in details:
            did = self.next_id
            self.next_id += 1
            self.nodes[did] = {
                "text": "",                # Texto inicial vazio (user preencherá)
                "type": d_type,            # Tipo 5W2H (WHY, WHO, ...)
                "parent": new_action_id,   # Detalhe é filho da ação
                "children": [],            # Detalhes não têm filhos
            }
            self.nodes[new_action_id]["children"].append(did)
        
        # Redesenhar diagrama com a nova ação
        self._draw_diagram()
        
        # Abrir editor flutuante para preenchimento da ação (após 60ms para render)
        QTimer.singleShot(60, lambda: self._on_edit_start(new_action_id))

    def _on_delete_node(self, node_id):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Slot — Deletar Ação + Todos os 6 Detalhes com Confirmação         ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Slot conectado ao sinal delete_node (emitido por clique botão (−)).
        #   Exibe diálogo de confirmação pedindo autorização do usuário.
        #   Se confirmado: remove a ação E recursivamente todos os 6 detalhes.
        #   Atualiza árvore: remove ação de nodes[parent]["children"].
        #
        # Parâmetros:
        #   - node_id (int): ID do nó a deletar (normalmente um WHAT/ação)
        #
        # Retorno: Nenhum (modifica self.nodes se confirmado)
        # Why:
        #   Diálogo de confirmação previne deleção acidental (operação
        #   não-reversível nesta versão). Recurso garante limpeza completa
        #   da subtree (ação + detalhes) em uma operação.
        
        # Confirmar com usuário antes de deletar
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir esta Ação e todos os seus detalhes 5W2H?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            # Remover da lista de filhos do pai (ROOT, normalmente)
            pid = self.nodes[node_id]["parent"]
            if pid is not None:
                self.nodes[pid]["children"].remove(node_id)
            
            # Deletar a ação + todos os 6 detalhes recursivamente
            self._remove_recursively(node_id)
            
            # Redesenhar diagrama sem a ação deletada
            self._draw_diagram()

    def _remove_recursively(self, node_id):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Helper — Deleção Recursiva em Pré-ordem (Profundidade-Primeira)    ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Percorre a subtree do nó em profundidade-primeira (DFS) e deleta
        #   todos os nós filhos recursivamente antes de deletar o nó pai.
        #   Estratégia: pré-ordem (delete filhos antes do pai).
        #
        # Parâmetros:
        #   - node_id (int): Raiz da subtree a deletar (normalmente uma AÇÃO)
        #
        # Retorno: Nenhum (modifica self.nodes)
        # Why:
        #   Quando uma ação é deletada, seus 6 detalhes devem ser removidos
        #   também (integridade hierárquica). Ordem pré-ordem garante que
        #   nenhum nó orfão fica para trás.
        
        # Deletar todos os filhos recursivamente (pré-ordem)
        for cid in list(self.nodes[node_id]["children"]):
            self._remove_recursively(cid)
        
        # Agora deletar o próprio nó (quando todos os filhos já foram removidos)
        del self.nodes[node_id]

    def _on_edit_start(self, node_id):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Slot — Abrir Editor Flutuante para Preenchimento de Nó             ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Slot conectado ao sinal edit_start (emitido por double-click).
        #   Valida que o nó existe em node_positions (foi renderizado).
        #   Calcula a altura do header colorido (20px * zoom).
        #   Passa a área de texto (rect do nó excluindo header) ao editor.
        #   Editor flutuante (QTextEdit) sobrescreve a área do nó abaixo do header.
        #
        # Parâmetros:
        #   - node_id (int): ID do nó a editar
        #
        # Retorno: Nenhum (abre editor flutuante)
        # Why:
        #   Separação de preocupações: W5H2Widget calcula rect + valida;
        #   W5H2FloatingEditor gerencia o QTextEdit overlay + atalhos (Enter/Escape).
        #   Editor posicionado dinâmicamente sobre o nó para edição inline.
        
        # Validar que nó foi renderizado (existe em node_positions)
        if node_id not in self.node_positions:
            return
        
        # Obter dimensões e posição do nó
        nw, nh = self.node_dimensions[node_id]
        x, y = self.node_positions[node_id]
        
        # Excluir header colorido (altura variável com zoom)
        header_h = 20 * self.zoom_level
        
        # Rect da área de texto (abaixo do header, restante do nó)
        edit_rect = QRectF(x, y + header_h, nw, nh - header_h)
        
        # Abrir editor flutuante nesta área
        self._float_editor.open(
            node_id, self.nodes[node_id]["text"], edit_rect, self.view
        )

    def _on_commit_text(self, node_id, text):
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  Slot — Confirmar Edição de Texto e Redesenhar                      ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        # Responsabilidade:
        #   Slot conectado ao sinal committed do W5H2FloatingEditor.
        #   Valida que o nó ainda existe (pode ter sido deletado durante edição).
        #   Atualiza o texto no dict nodes[node_id]["text"].
        #   Redesenha o diagrama (para refletir mudança de tamanho se texto mudou).
        #
        # Parâmetros:
        #   - node_id (int): ID do nó editado
        #   - text (str): Texto novo (já stripped de espaços em W5H2FloatingEditor)
        #
        # Retorno: Nenhum (modifica self.nodes + triggers _draw_diagram)
        # Why:
        #   Alteração de texto pode afetar tamanho do nó (W5H2Node._calc_size),
        #   logo requer redesenho completo layout + renderização. Validação
        #   evita erro se nó foi deletado (edge case).
        
        # Validar que nó ainda existe
        if node_id in self.nodes:
            # Atualizar texto no modelo
            self.nodes[node_id]["text"] = text
            
            # Redesenhar: recalcula dimensões + posições + renderiza
            self._draw_diagram()


# ═══════════════════════════════════════════════════════════════════

class _W5H2Module(BaseModule):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Adaptador — Implementador da Interface BaseModule para 5W2H         ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Wrapper (Adapter pattern) que adapta W5H2Widget para interface
    #   BaseModule (comum a todos os módulos PRO ENG: bpmn, ishikawa, ...).
    #   Implementa métodos obrigatórios: get_state, set_state, refresh_theme,
    #   get_view, e métodos de zoom. Delega operações à W5H2Widget interna.
    #
    # Interface BaseModule (que este implementa):
    #   - get_state() → Dict estado persistível (para salvar/carregar)
    #   - set_state(Dict) → Restaura estado (para carregar arquivo)
    #   - refresh_theme() → Reaplica tema global (quando muda em Settings)
    #   - get_view() → Retorna QGraphicsView para export de screenshots
    #   - zoom_in(), zoom_out(), reset_zoom() → Controles de zoom
    #
    # Parâmetros de __init__: Nenhum (cria W5H2Widget internamente)
    # Retorno: Instância pronta para uso em QApplication
    # Why:
    #   Desacoplamento: _W5H2Module = orquestração + interface módulo;
    #   W5H2Widget = lógica pura diagrama. Permite testar/reusar W5H2Widget
    #   em contextos diferentes (não apenas PRO ENG).
    
    def __init__(self):
        # Inicializa BaseModule parent
        super().__init__()
        
        # Cria widget interno (orquestrador do diagrama 5W2H)
        self._inner = W5H2Widget()
        
        # Oculta toolbar interna original (PRO ENG padrão)
        _hide_inner_toolbar(self._inner)
        
        # Texto de ajuda (exibido em painel lateral ou diálogo Help)
        self.help_text = (
            "• Adicione uma nova Ação clicando no botão (+) vermelho.\n"
            "• Clique duas vezes nas caixas (WHAT, WHO, WHEN...) para preencher os detalhes.\n"
            "• O balão ajusta seu tamanho automaticamente ao seu texto.\n"
            "• Use o menu 'Exibir' para controlar o Zoom do plano."
        )
        
        # Layout: agrupa widget interno em QVBoxLayout (padrão módulos)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Sem margens extras
        layout.setSpacing(0)                   # Sem gaps
        layout.addWidget(self._inner)

    def reset_zoom(self):
        # Delega reset_zoom ao widget interno
        # Volta para 100% (zoom_level = 1.0)
        self._inner.reset_zoom()

    def zoom_in(self):
        # Delega zoom_in ao widget interno
        # Aumenta 15% do zoom atual
        self._inner.zoom_in()

    def zoom_out(self):
        # Delega zoom_out ao widget interno
        # Diminui 15% do zoom atual
        self._inner.zoom_out()

    def get_state(self):
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║  Serialização — Retorna Estado Persistível do Diagrama 5W2H      ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        # Retorno:
        #   Dict com schema versionado + dados para reconstruir diagrama:
        #   {
        #     "schema": "w5h2.v1",         # Versão formato (compatibilidade)
        #     "nodes": Dict[int, {...}],  # Estrutura hierárquica completa
        #     "next_id": int               # Próximo ID a atribuir (continuidade)
        #   }
        # Why:
        #   Permite salvar projeto em arquivo (JSON) e recarregar sem perda
        #   de estrutura ou sequência de IDs.
        
        return {
            "schema": "w5h2.v1",
            "nodes": self._inner.nodes,
            "next_id": self._inner.next_id,
        }

    def set_state(self, state):
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║  Desserialização — Restaura Estado do Diagrama 5W2H             ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        # Parâmetros:
        #   - state (Dict|None): Estado obtido de get_state() ou arquivo JSON
        #
        # Lógica:
        #   1. Validar state (pode ser None se arquivo vazio)
        #   2. Converter chaves de nodes Dict str→int (se vindas de JSON)
        #   3. Restaurar nodes + next_id ao widget interno
        #   4. Se nodes vazio: restaurar estrutura inicial (1 ROOT)
        #   5. Redesenhar diagrama
        #
        # Why:
        #   JSON serializa keys de dicts como strings. Precisa converter
        #   'int'→int para manter compatibilidade com código (node_id sempre int).
        #   Fallback para estado inicial garante sempre diagrama consistente.
        
        if not state:
            return
        
        # Converter chaves de nodes de str para int (se vindas de JSON)
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try:
                k_int = int(k)
            except:
                k_int = k
            nodes[k_int] = v

        # Restaurar nodes ao widget: usar carregado ou estrutura padrão
        self._inner.nodes = (
            nodes
            if nodes
            else {
                1: {
                    "text": "Novo Projeto / Meta",
                    "type": "ROOT",
                    "parent": None,
                    "children": [],
                }
            }
        )
        
        # Restaurar next_id (para evitar conflito de IDs ao adicionar)
        self._inner.next_id = state.get("next_id", 2)
        
        # Redesenhar diagrama com estado restaurado
        self._inner._draw_diagram()

    def refresh_theme(self):
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║  Reaplica Tema Global — Chamado quando Configurações Mudam       ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        # Delega refresh_theme ao widget interno
        # Reaplica cores + fundo + conectores + editor flutuante
        
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║  Acesso ao QGraphicsView — Usado para Export de Screenshots      ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        # Retorno: QGraphicsView do widget (ou None se não existe)
        # Why:
        #   PRO ENG module permite export de diagrama como imagem.
        #   Precisa acessar a view (canvas renderizado) para screenshot.
        
        return getattr(self._inner, "view", None)


if __name__ == "__main__":
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Bloco Main — Teste Isolado do Diagrama 5W2H                        ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Permite executar módulo diretamente: python w5h2.py
    # Cria janela standalone com diagrama 5W2H (sem framework PRO ENG).
    # Útil para debug, prototipagem, ou demonstração isolada.
    
    app = QApplication(sys.argv)
    w = _W5H2Module()
    w.setWindowTitle("Plano de Ação 5W2H — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())
