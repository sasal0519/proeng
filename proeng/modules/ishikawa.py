# -*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MÓDULO: Ishikawa — Diagrama Espinha de Peixe (Causa e Efeito)            ║
# ╚════════════════════════════════════════════════════════════════════════════╝
# 
# Responsabilidade:
#   Diagrama de Ishikawa (Espinha de Peixe, Fishbone Diagram) para análise
#   de causa-raiz. Estrutura hierárquica 3 níveis: Efeito/Problema (cabeça) →
#   6 Categorias clássicas "6M" (Método, Máquina, Material, Mão de Obra,
#   Meio Ambiente, Medição) → Causas específicas (múltiplas por categoria).
#
# Padrões de Projeto:
#   - Observer Pattern: IshikawaSignals emite sinais (add_child, delete_node,
#     edit_start, commit_text) conectados aos slots de IshikawaWidget
#   - Factory Pattern: IshikawaNode factory para renderização customizada
#     conforme nível (cabeça=200px, categoria=130px, causa=110px)
#   - Strategy Pattern: _draw_diagram() orquestra layout via geometria
#     calculada (espinha central + ramos diagonais + subramos de causa)
#   - State Pattern: nodes dict com ["text", "level", "children", "parent"]
#     persistido via get_state()/set_state()
#
# Fluxo de Interação:
#   1. Hover sobre nó → mostra botões (+) adicionar filho, (−) deletar
#   2. Click (+) → emit add_child(parent_id) → cria novo nó vazio nivel+1
#   3. Double-click → emit edit_start(nid) → abre IshikawaFloatingEditor
#   4. Usuario edita + Enter/Escape → emit commit_text(nid, novo_texto)
#   5. Slot _on_commit_text atualiza nodes[nid]["text"] + redesenha
#   6. get_state()/set_state() serializam para persistência de projeto
#
# Características de Rendering (Neo-brutalist):
#   - Sem gradientes, apenas cores sólidas
#   - Bordas 3-4px retas (sem border-radius)
#   - Nós com fundo + barra colorida superior (accent ou accent_bright)
#   - Linhas espinha vermelha accent_bright, ramos cinzas (line/line_eap)
#   - Zoom responsivo (0.2x a 4.0x) com Ctrl+Scroll

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
from proeng.core.utils import _export_view, _c, _solid_fill, _nb_paint_node, _is_nb
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class IshikawaSignals(QObject):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Emissora de Sinais para Operações de Nó do Ishikawa                 ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Broker de eventos centralizado para todas as operações de edição
    #   do diagrama Ishikawa. Conecta cliques do mouse (em IshikawaNode)
    #   às operações de lógica de negócio (em IshikawaWidget).
    #
    # Sinais Emitidos:
    #   - add_child(int parent_id): user clicou (+) para criar sub-nó
    #   - delete_node(int nid): user clicou (−) para remover nó + filhos
    #   - edit_start(int nid): user deu double-click para editar texto
    #   - commit_text(int nid, str texto): usuario confirmou edição (Enter/Escape)
    #
    add_child = pyqtSignal(int)
    delete_node = pyqtSignal(int)
    edit_start = pyqtSignal(int)
    commit_text = pyqtSignal(int, str)


class IshikawaFloatingEditor(QLineEdit):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Editor Flutuante para Edição In-Place de Texto do Nó                ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   QLineEdit customizado que sobrepõe o diagrama para edição inline
    #   de texto dos nós (efeito/problema, categorias, causas). Posiciona-se
    #   dinamicamente sobre o nó alvo, aplica estilos do tema, e emite sinais
    #   de confirmação (Enter/Escape/focusOut).
    #
    # Fluxo:
    #   1. _on_edit_start(nid) → open(nid, texto_atual, scene_rect, view)
    #   2. Editor aparece com foco automático + seleção total do texto
    #   3. User pressiona Enter/Escape ou clica fora → _commit(texto)
    #   4. committed.emit(nid, texto_novo) propaga para IshikawaWidget
    #
    # Atributos:
    #   - _target_id: ID do nó em edição (default -1 = nenhum)
    #   - _original: Texto anterior (para reverter com Escape)
    #   - _done: Flag para evitar múltiplas emissões de commit
    #
    committed = pyqtSignal(int, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = -1, "", False
        self.hide()

    def _apply_style(self):
        # Aplica stylesheet usando cores do tema ativo
        # Fallback para cores neutras se tema falhar
        try:
            t = T()
            bg = t["bg_card2"]
            fg = t["text"]
            bdr = t["accent_bright"]
        except Exception:
            bg, fg, bdr = t["bg_card2"], t["text"], t["accent_bright"]
        br = t.get("border_radius", 0)
        ff = t.get("font_family_content", "'Segoe UI', 'Arial', sans-serif")
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                color: {fg};
                border: 2px solid {bdr};
                border-radius: {br}px;
                font-family: {ff}; font-size: 11pt;
                padding: 5px 10px;
            }}
        """)

    def open(self, target_id, current_text, scene_rect, view):
        # Prepara e exibe o editor flutuante
        # Parâmetros:
        #   - target_id: Qual nó estamos editando
        #   - current_text: Texto inicial do QLineEdit
        #   - scene_rect: Bounding box do nó em coordenadas de cena
        #   - view: QGraphicsView para conversão de coordenadas
        # O editor posiciona-se sobre o nó (centrado verticalmente)
        self._apply_style()
        self._target_id, self._original, self._done = target_id, current_text, False
        rv = view.mapFromScene(scene_rect).boundingRect()
        self.setGeometry(
            rv.x(), rv.y() + rv.height() // 2 - 18, max(160, rv.width()), 36
        )
        self.setText(current_text)
        self.selectAll()
        self.show()
        self.raise_()
        self.setFocus()

    def _commit(self, text=None):
        # Confirma edição e emite sinal
        # Se _done já é True, ignora (proteção contra duplas emissões)
        # Parâmetros:
        #   - text: texto customizado para emitir (None = usar self.text())
        if self._done:
            return
        self._done = True
        self.hide()
        self.committed.emit(
            self._target_id, (text if text is not None else self.text()).strip()
        )

    def keyPressEvent(self, event):
        # Intercepta atalhos: Enter/Return confirma, Escape cancela
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._commit()
        elif event.key() == Qt.Key_Escape:
            self._commit(self._original)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        # Quando editor perde foco (click fora), confirma com novo texto
        self._commit()
        super().focusOutEvent(event)


class IshikawaNode(QGraphicsItem):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Item Gráfico — Nó de Ishikawa (Cabeça, Categoria, ou Causa)        ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Renderização individual de nó do diagrama Ishikawa com suporte a
    #   3 níveis hierárquicos. Cada nível tem tamanho/fonte diferentes.
    #   Responde a hover com affordances visuais (botões +/−).
    #   Emite sinais via IshikawaSignals para operações de edição/exclusão.
    #
    # Hierarquia de Níveis:
    #   - Level 0 (Cabeça): "Efeito / Problema" | 200px×72px | Bold 14pt
    #   - Level 1 (Categoria): "Método", "Máquina", etc | 130px×38px | Bold 10pt
    #   - Level 2 (Causa): Nomes de causas específicas | 110px×28px | Regular 8pt
    #   Tamanhos escalam com zoom_level para manter proporções
    #
    # Rendering (Neo-brutalist):
    #   - Fundo sólido sem gradiente (usa _solid_fill ou _nb_paint_node)
    #   - Barra colorida no topo (level 0-1 apenas)
    #   - Borda 3px ao redor
    #   - Hover: botões (+) top-right para filhos, (−) top-left para deleção
    #   - No hover, exibe texto placeholder se vazio ("✎ Efeito/..." ou "✎ Nomear")
    #
    # Atributos:
    #   - node_id: Chave unívoca no dict nodes de IshikawaWidget
    #   - text: Conteúdo textual (vazio = placeholder)
    #   - level: 0=cabeça, 1=categoria, 2=causa
    #   - hovered: Flag de estado hover (dispara redraw via update())
    #   - zoom: Escala de zoom.level de IshikawaWidget
    #   - _font: QFont configurada por level + zoom
    #   - w, h: Largura/altura calculadas em _calc_size()
    #
    """Nó do Ishikawa — Nível 0: Cabeça, 1: Categoria, 2: Causa"""

    def __init__(self, node_id, text, level, signals, zoom):
        super().__init__()
        self.node_id = node_id
        self.text = text
        self.level = level
        self.signals = signals
        self.zoom = zoom
        self.hovered = False

        t = T()
        ff = t.get("font_family", "Segoe UI")
        if self.level == 0:
            self._font = QFont(ff, max(8, int(14 * zoom)), QFont.Bold)
            self.base_w, self.base_h = 200 * zoom, 72 * zoom
        elif self.level == 1:
            self._font = QFont(ff, max(7, int(10 * zoom)), QFont.Bold)
            self.base_w, self.base_h = 130 * zoom, 38 * zoom
        else:
            self._font = QFont(ff, max(6, int(8 * zoom)))
            self.base_w, self.base_h = 110 * zoom, 28 * zoom

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(10)

    def _calc_size(self):
        # Calcula dimensões finais do nó baseado no texto + nível
        # Define placeholder se vazio, normaliza quebras de linha
        # Respeita largura máxima por nível (240px/160px com padding)
        sample = (
            self.text
            if self.text
            else ("Efeito / Problema" if self.level == 0 else "Nova Causa")
        )
        fm = QFontMetrics(self._font)

        # Largura máxima e padding interno variam por nível
        max_node_w = (240 if self.level == 0 else 160) * self.zoom
        pad_x = (40 if self.level == 0 else 24) * self.zoom
        pad_y = (30 if self.level == 0 else 18) * self.zoom

        text_rect = fm.boundingRect(
            0,
            0,
            int(max_node_w - pad_x),
            1000,
            Qt.AlignCenter | Qt.TextWordWrap,
            sample,
        )

        self.w = max(self.base_w, text_rect.width() + pad_x)
        self.h = max(self.base_h, text_rect.height() + pad_y)

    def boundingRect(self):
        # Retorna área de clique + margem para não colidir com vizinhos
        m = 14 * self.zoom
        return QRectF(-m, -m, self.w + m * 2, self.h + m * 2)

    def paint(self, painter, option, widget=None):
        # Renderiza o nó com fundo + barra superior + texto + botões hover
        # Se neo-brutalist: fundo sólido via _nb_paint_node(), barra stripe
        # Senão: fundo rounded com gradient via _solid_fill, barra clipped
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0, 0, self.w, self.h)

        if _is_nb(t):
            # Neo-brutalist: _nb_paint_node maneja sombra + borda
            _nb_paint_node(painter, r, self.hovered or self.level == 0)
            bw = t.get("border_width", 3)
            if self.level <= 1:
                # Barra colorida no topo (6px altura)
                strip_h = 6 * self.zoom
                painter.save()
                painter.setBrush(
                    QBrush(QColor(t["accent_bright"] if self.hovered else t["accent"]))
                )
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRect(QRectF(bw, bw, self.w - bw * 2, strip_h))
                painter.restore()
        else:
            # Não neo-brutalist: rounded rect com fundo solid (opcional gradient)
            painter.setBrush(QBrush(_solid_fill(r, self.hovered or self.level == 0)))
            painter.setPen(QPen(Qt.NoPen))
            radius = t.get("border_radius", 12)
            painter.drawRoundedRect(r, radius, radius)

            if self.level <= 1:
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(r, radius, radius)
                painter.setClipPath(clip_path)

                painter.setBrush(
                    QBrush(QColor(t["accent_bright"] if self.hovered else t["accent"]))
                )
                painter.setPen(Qt.NoPen)
                painter.drawRect(QRectF(0, 0, self.w, 4 * self.zoom))
                painter.restore()

        # Renderiza texto (placeholder se vazio)
        display = (
            self.text
            if self.text
            else ("✎ Efeito/Problema" if self.level == 0 else "✎ Nomear")
        )
        painter.setPen(_c("text" if self.text else "text_dim"))
        painter.setFont(self._font)
        px = 15 * self.zoom if self.level == 0 else 8 * self.zoom
        py = 10 * self.zoom if self.level == 0 else 4 * self.zoom
        inner = r.adjusted(px, py, -px, -py)
        painter.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, display)

        if self.hovered:
            # Botões de affordance (+) adicionar filho, (−) deletar
            bs = 20 * self.zoom
            hbs = bs / 2
            painter.setFont(QFont("Consolas", max(7, int(12 * self.zoom)), QFont.Bold))

            if self.level < 2:
                # Botão (+) adicionar filho — top-right
                add_r = QRectF(self.w - hbs, -hbs, bs, bs)
                if _is_nb(t):
                    painter.setBrush(QBrush(QColor(t["btn_add"])))
                    painter.setPen(QPen(QColor("#000000"), 2))
                    painter.drawRect(add_r)
                else:
                    painter.setBrush(QBrush(QColor(t["btn_add"])))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(add_r, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.drawText(add_r, Qt.AlignCenter, "+")

            if self.level > 0:
                # Botão (−) deletar nó — top-left
                del_r = QRectF(-hbs, -hbs, bs, bs)
                if _is_nb(t):
                    painter.setBrush(QBrush(QColor(t["btn_del"])))
                    painter.setPen(QPen(QColor("#000000"), 2))
                    painter.drawRect(del_r)
                else:
                    painter.setBrush(QBrush(QColor(t["btn_del"])))
                    painter.setPen(Qt.NoPen)
                    painter.drawRoundedRect(del_r, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.drawText(del_r, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e):
        # Quando mouse entra na área do nó
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        # Quando mouse sai da área do nó
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        # Intercepta cliques em botões (+) e (−)
        # Emite sinais de add_child ou delete_node via QTimer.singleShot
        # (defer para evitar reentrância durante paint)
        if event.button() == Qt.LeftButton and self.hovered:
            bs = 20 * self.zoom
            hbs = bs / 2
            add_r = QRectF(self.w - hbs, -hbs, bs, bs)
            del_r = QRectF(-hbs, -hbs, bs, bs)
            if self.level < 2 and add_r.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.add_child.emit(self.node_id))
                event.accept()
                return
            if self.level > 0 and del_r.contains(event.pos()):
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


class IshikawaWidget(QWidget):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Widget Principal — Orquestrador do Diagrama Ishikawa                ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Manager central do diagrama Ishikawa. Mantém estrutura de nós
    #   (nodes dict), orquestra layout via _draw_diagram(), responde a
    #   sinais de edição/deleção, persiste via get_state()/set_state().
    #   Suporta zoom responsivo (0.2x a 4.0x via Ctrl+Scroll).
    #
    # Estrutura de Dados (nodes):
    #   Dict[int, {
    #     "text": str,           # Conteúdo do nó
    #     "level": int,          # 0=cabeça, 1=categoria, 2=causa
    #     "children": [int],     # IDs dos nós filhos
    #     "parent": int|None     # ID nó pai (None se raiz)
    #   }]
    #
    # Layout Engine (_draw_diagram):
    #   1. Calcula dimensões de cada nó em _calc_size()
    #   2. Posiciona espinha central (linha horizontal)
    #   3. Distribui categorias (6M) acima/abaixo em slots
    #   4. Desenha ramos diagonais para categorias
    #   5. Desenha subramos para causas (pequenas linhas horizontais)
    #   6. Renderiza nós (IshikawaNode items) nas posições calculadas
    #
    # Estados Iniciais:
    #   - 1 nó raiz (Level 0): "EFEITO / PROBLEMA"
    #   - 6 nós categoria (Level 1): Método, Máquina, Material, etc.
    #   - 0 nós causa iniciais (Level 2) — usuário adiciona
    #   - next_id: Counter para atribuição de IDs únicos
    #
    # Interações de Usuário:
    #   - Hover nó: mostra botões (+/-) 
    #   - Click +: adiciona novo nó filho (level+1)
    #   - Click −: deleta nó + todos descendentes (com confirmação)
    #   - Double-click: abre editor flutuante para inline editing
    #   - Ctrl+Scroll: zoom in/out (altera zoom_level + redesenha)
    #
    """Diagrama de Ishikawa (Espinha de Peixe) completo e integrado ao sistema de temas."""

    def __init__(self):
        super().__init__()
        self.sigs = IshikawaSignals()
        self.sigs.add_child.connect(self._on_add_child)
        self.sigs.delete_node.connect(self._on_delete_node)
        self.sigs.edit_start.connect(self._on_edit_start)
        self.sigs.commit_text.connect(self._on_commit_text)

        self.zoom_level = 1.0
        self.next_id = 2
        self.node_dims = {}
        self.node_positions = {}

        # Estrutura inicial com 6 categorias clássicas M
        # (Método, Máquina, Material, Mão de Obra, Meio Ambiente, Medição)
        self.nodes = {
            1: {"text": "EFEITO / PROBLEMA", "level": 0, "children": [], "parent": None}
        }
        cat_names = [
            "Método",
            "Máquina",
            "Material",
            "Mão de Obra",
            "Meio Ambiente",
            "Medição",
        ]
        for name in cat_names:
            nid = self.next_id
            self.next_id += 1
            self.nodes[nid] = {"text": name, "level": 1, "children": [], "parent": 1}
            self.nodes[1]["children"].append(nid)

        self._setup_ui()
        self._float_editor = IshikawaFloatingEditor(self.view)
        self._float_editor.committed.connect(self.sigs.commit_text.emit)
        self._draw_diagram()

    def _setup_ui(self):
        # Configura layout do widget: QGraphicsView para diagrama
        # Habilita ScrollHandDrag para navegação tipo "hand cursor"
        # Aplica stylesheet vazio (border:none) para integrar com tema
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        self._apply_view_bg()
        layout.addWidget(self.view)

    def _apply_view_bg(self):
        # Aplica cor de fundo da view usando tema ativo
        # Fallback para branco se cor falhar
        try:
            self.view.setBackgroundBrush(QBrush(_c("bg_app")))
        except Exception:
            try:
                self.view.setBackgroundBrush(QBrush(QColor("#FFFFFF")))
            except Exception:
                pass

    def refresh_theme(self):
        # Chamado quando tema global muda
        # Atualiza fundo da view + editor flutuante + redesenha todo diagrama
        # (linhas/cores/estilos mudam, nós precisam renderizar novamente)
        self._apply_view_bg()

        if hasattr(self, "_float_editor"):
            self._float_editor._apply_style()

        # Redesenha para atualizar cores de linhas/setas
        if hasattr(self, "scene"):
            self._draw_diagram()

    def zoom_in(self):
        # Aumenta zoom 15% mantendo limite 4.0x superior
        self._scale(1.15)

    def zoom_out(self):
        # Diminui zoom 15% mantendo limite 0.2x inferior
        self._scale(1 / 1.15)

    def reset_zoom(self):
        # Volta para zoom 1.0 e redesenha diagrama com proporções originais
        self.view.resetTransform()
        self.zoom_level = 1.0
        self._draw_diagram()

    def _scale(self, factor):
        # Aplica fator de escala se dentro limites [0.2, 4.0]
        # Atualiza zoom_level + transform da view + redesenha
        new_z = self.zoom_level * factor
        if 0.2 <= new_z <= 4.0:
            self.zoom_level = new_z
            self.view.scale(factor, factor)

    def wheelEvent(self, event):
        # Ctrl+Scroll: zoom in/out, outros scrolls: navegação vertical normal
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3
            )

    def _export_scene(self, fmt):
        # Exporta diagrama para PNG ou PDF usando _export_view
        _export_view(self.view, fmt, self)

    # ──────────────────────────────────────────────────────────────
    #   MOTOR DE LAYOUT ISHIKAWA — Cálculo e Renderização
    # ──────────────────────────────────────────────────────────────
    
    def _draw_diagram(self):
        # Orquestrador de rendering completo do diagrama Ishikawa
        # Fluxo:
        #   1. Limpa cena anterior (scene.clear())
        #   2. Pré-calcula dimensões de TODOS nós com zoom ativo
        #   3. Calcula geometria GLOBAL: espinha central, distribuição de categorias
        #   4. Desenha elementos estruturais (linhas, setas)
        #   5. Renderiza nós como QGraphicsItems nos coords calculadas
        #   6. Ajusta sceneRect para englobar tudo + margem
        #   7. Centraliza view no meio da espinha
        #
        self.scene.clear()
        t = T()
        z = self.zoom_level

        # 1. Pré-calcular dimensões
        # Cria nós temporários para saber size de cada um (para layout)
        self.node_dims.clear()
        for nid, data in self.nodes.items():
            tmp = IshikawaNode(nid, data["text"], data["level"], self.sigs, z)
            self.node_dims[nid] = (tmp.w, tmp.h)

        # 2. Geometria base
        # Espinha horizontal: end_x é ponta (após cabeça)
        # Categorias distribuídas em top_cats/bot_cats em 6 slots aprox
        spine_end_x = 1100 * z
        spine_y = 480 * z
        cat_ids = self.nodes[1]["children"]
        top_cats = [c for i, c in enumerate(cat_ids) if i % 2 == 0]
        bot_cats = [c for i, c in enumerate(cat_ids) if i % 2 != 0]
        n_slots = max(len(top_cats), len(bot_cats), 1)
        spine_step = max(260 * z, 260 * z)
        spine_start = spine_end_x - (n_slots + 1) * spine_step

        # 3. Espinha central (linha vermelha de ponta)
        pen_spine = QPen(
            QColor(t["accent_bright"]),
            max(2, int(5 * z)),
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin,
        )
        self.scene.addLine(spine_start, spine_y, spine_end_x, spine_y, pen_spine)

        # Seta na ponta da espinha (triângulo apontando direita)
        asz = 18 * z
        arrow = QPolygonF(
            [
                QPointF(spine_end_x, spine_y),
                QPointF(spine_end_x - asz, spine_y - asz * 0.5),
                QPointF(spine_end_x - asz, spine_y + asz * 0.5),
            ]
        )
        self.scene.addPolygon(arrow, QPen(Qt.NoPen), QBrush(QColor(t["accent_bright"])))

        # 4. Nó cabeça (Efeito/Problema) à direita da espinha
        hw, hh = self.node_dims[1]
        hx = spine_end_x + 12 * z
        hy = spine_y - hh / 2
        self.node_positions[1] = (hx, hy)

        # 5. Ramos e causas
        # Linhas de categoria (ramos diagonais)
        pen_branch = QPen(
            QColor(t["line"]), max(1, int(3 * z)), Qt.SolidLine, Qt.RoundCap
        )
        # Linhas de causa (subramos menores)
        pen_cause = QPen(
            QColor(t["line_eap"]), max(1, int(2 * z)), Qt.SolidLine, Qt.RoundCap
        )

        def draw_branch(cat_list, is_top):
            # Helper para desenhar ramos ACIMA ou ABAIXO da espinha
            # Parâmetros:
            #   - cat_list: Lista de IDs de categorias para este lado
            #   - is_top: True=acima, False=abaixo
            # Para cada categoria:
            #   a) Posiciona caixa da categoria
            #   b) Desenha linha diagonal da espinha até category box
            #   c) Para cada causa sob esta categoria:
            #      - Desenha subramo horizontal
            #      - Posiciona caixa de causa
            sign = -1 if is_top else 1
            for k, cid in enumerate(cat_list):
                ax = spine_end_x - (k + 1) * spine_step
                ay = spine_y

                n_causes = len(self.nodes[cid]["children"])
                branch_h = max(220 * z, (n_causes * 75 + 120) * z)
                ox = ax - branch_h * 0.75
                oy = spine_y + sign * branch_h

                # Linha diagonal da categoria (do eixo até off-axial point)
                self.scene.addLine(ox, oy, ax, ay, pen_branch)

                # Posição da caixa da categoria (acima/abaixo do ponto ox,oy)
                cw, ch = self.node_dims[cid]
                cx = ox - cw / 2
                cy = oy - ch - 12 * z if is_top else oy + 12 * z
                self.node_positions[cid] = (cx, cy)

                # Causas ramos menores (subramos)
                causes = self.nodes[cid]["children"]
                if causes:
                    dy = (ay - oy) / (len(causes) + 1)
                    for j, scid in enumerate(causes):
                        py = oy + (j + 1) * dy
                        px = ox + ((py - oy) / (ay - oy)) * (ax - ox)
                        seg = max(120 * z, 120 * z)

                        # Linha horizontal da causa (pequeno ramo)
                        self.scene.addLine(px - seg, py, px, py, pen_cause)

                        # Pequena seta na causa (apontando left se is_top, right se bottom)
                        ca = 7 * z
                        self.scene.addPolygon(
                            QPolygonF(
                                [
                                    QPointF(px, py),
                                    QPointF(px - ca, py - ca * 0.5),
                                    QPointF(px - ca, py + ca * 0.5),
                                ]
                            ),
                            QPen(Qt.NoPen),
                            QBrush(QColor(t["line_eap"])),
                        )

                        # Posição da caixa de causa
                        sw, sh = self.node_dims[scid]
                        self.node_positions[scid] = (px - seg, py - sh - 4 * z)

        draw_branch(top_cats, True)
        draw_branch(bot_cats, False)

        # 6. Renderizar nós gráficos
        for nid, (nx, ny) in self.node_positions.items():
            item = IshikawaNode(
                nid, self.nodes[nid]["text"], self.nodes[nid]["level"], self.sigs, z
            )
            item.setPos(nx, ny)
            self.scene.addItem(item)

        # 7. Ajusta cena e centraliza view
        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(
                -120 * z, -120 * z, 120 * z, 120 * z
            )
        )
        self.view.centerOn(spine_end_x - (n_slots * spine_step) / 2, spine_y)

    # ──────────────────────────────────────────────────────────────
    #   LÓGICA DE DADOS — Slots de Edição e Estados
    # ──────────────────────────────────────────────────────────────
    
    def _on_add_child(self, parent_id):
        # Slot: Cria novo nó filho quando user clica (+)
        # Parâmetros:
        #   - parent_id: ID do nó pai
        # Fluxo:
        #   1. Calcula level do novo nó (parent.level + 1)
        #   2. Aloca novo ID (incrementa next_id)
        #   3. Cria entry em nodes dict (vazio, aguarda input)
        #   4. Alimenta parent["children"]
        #   5. Redesenha diagrama
        #   6. Abre editor flutuante em 60ms (defer para estabilizar)
        new_level = self.nodes[parent_id]["level"] + 1
        nid = self.next_id
        self.next_id += 1
        self.nodes[nid] = {
            "text": "",
            "level": new_level,
            "children": [],
            "parent": parent_id,
        }
        self.nodes[parent_id]["children"].append(nid)
        self._draw_diagram()
        QTimer.singleShot(60, lambda: self._on_edit_start(nid))

    def _on_delete_node(self, node_id):
        # Slot: Deleta nó (com confirmação do usuário)
        # Parâmetros:
        #   - node_id: ID do nó a deletar
        # Comportamento:
        #   - Mostra diálogo "Excluir este nó e todos os seus filhos?"
        #   - Se SIM: remove nó, desvincula do pai, recursivamente deleta filhos
        #   - Redesenha após sucesso
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir este nó e todos os seus filhos?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            pid = self.nodes[node_id]["parent"]
            if pid is not None:
                self.nodes[pid]["children"].remove(node_id)
            self._remove_rec(node_id)
            self._draw_diagram()

    def _remove_rec(self, nid):
        # Helper: Recursivamente delete todos os descendentes de nid
        # Percorre filhos em depth-first order (filhos primeiro)
        for cid in list(self.nodes[nid]["children"]):
            self._remove_rec(cid)
        del self.nodes[nid]

    def _on_edit_start(self, node_id):
        # Slot: Abre editor flutuante para node_id
        # Parâmetros:
        #   - node_id: ID do nó a editar
        # Recupera dimensões/posição do nó e abre editor sobre ele
        if node_id not in self.node_positions:
            return
        nw, nh = self.node_dims[node_id]
        x, y = self.node_positions[node_id]
        self._float_editor.open(
            node_id, self.nodes[node_id]["text"], QRectF(x, y, nw, nh), self.view
        )

    def _on_commit_text(self, node_id, text):
        # Slot: Confirma edição de texto para node_id
        # Parâmetros:
        #   - node_id: ID do nó editado
        #   - text: Novo texto (já stripped)
        # Atualiza nodes[node_id]["text"] e redesenha
        if node_id in self.nodes:
            self.nodes[node_id]["text"] = text
            self._draw_diagram()


# ═══════════════════════════════════════════════════════════════════


class _IshikawaModule(BaseModule):
    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  Wrapper Module — Interface BaseModule para Ishikawa Widget          ║
    # ╚═══════════════════════════════════════════════════════════════════════╝
    # Responsabilidade:
    #   Adaptador que encapsula IshikawaWidget dentro de interface BaseModule.
    #   Expõe get_state()/set_state() para persistência, refresh_theme() para
    #   tema global, get_view() para renderização (QGraphicsView).
    #   Integra com ProjectFile, MainApp, e sistema de temas ProEng.
    #
    # Interface Implementada:
    #   - get_state() → dict: Serializa nodes + next_id para JSON
    #   - set_state(dict): Desserializa nodes + next_id de JSON
    #   - refresh_theme(): Atualiza cores quando tema muda
    #   - get_view(): Retorna QGraphicsView para renderização
    #   - zoom_in/out/reset_zoom(): Controles de zoom (delegates a widget)
    #
    # Fluxo de Integração:
    #   1. MainApp cria _IshikawaModule() na seleção de módulo
    #   2. MainApp chama get_view() para renderizar em central widget
    #   3. ProjectFile chama get_state() para serializar ao salvar
    #   4. ProjectFile chama set_state() para restaurar ao carregar
    #   5. MainApp chama refresh_theme() ao mudar tema global
    #   6. User controla zoom via toolbar/shortcuts
    #
    
    def __init__(self):
        super().__init__()
        self._inner = IshikawaWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "DIAGRAMA DE ISHIKAWA — Guia Rapido\n\n"
            "O Diagrama de Ishikawa (ou Espinha de Peixe) e uma "
            "ferramenta de analise de causa raiz utilizada para "
            "identificar e organizar as possiveis causas de um "
            "problema ou efeito. As causas sao agrupadas nas "
            "6 categorias classicas (6M): Mao de Obra, Metodo, "
            "Maquina, Material, Meio Ambiente e Medida.\n\n"
            "COMO USAR:\n"
            "• Clique duas vezes na caixa do 'Efeito' (a direita) "
            "para definir o problema que esta sendo analisado.\n"
            "• Passe o mouse sobre cada categoria (espinha) para "
            "revelar o botao (+) e adicionar sub-causas.\n"
            "• Clique duas vezes em qualquer sub-causa para editar "
            "seu texto.\n"
            "• Use o botao (-) que aparece ao passar o mouse para "
            "excluir uma sub-causa.\n\n"
            "ESTRUTURA 6M:\n"
            "• Mao de Obra: competencias, treinamento, motivacao\n"
            "• Metodo: procedimentos, instrucoes, padroes\n"
            "• Maquina: equipamentos, manutencao, tecnologia\n"
            "• Material: insumos, qualidade, fornecedores\n"
            "• Meio Ambiente: condicoes fisicas, clima, layout\n"
            "• Medida: instrumentos, calibracao, indicadores\n\n"
            "NAVEGACAO:\n"
            "• Use Ctrl + Scroll do mouse para zoom.\n"
            "• O layout das espinhas e posicionado automaticamente."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def reset_zoom(self):
        # Reseta zoom para 1.0 (tamanho original)
        # Delegates a IshikawaWidget.reset_zoom()
        self._inner.reset_zoom()

    def zoom_in(self):
        # Aumenta zoom 15%
        # Delegates a IshikawaWidget.zoom_in()
        self._inner.zoom_in()

    def zoom_out(self):
        # Diminui zoom 15%
        # Delegates a IshikawaWidget.zoom_out()
        self._inner.zoom_out()

    def get_state(self):
        # Serializador: Retorna dict pronto para JSON em ProjectFile
        # Inclui schema versão para futuras migrations
        # Copia nodes + next_id do widget interno
        return {
            "schema": "ishikawa.v1",
            "nodes": self._inner.nodes,
            "next_id": self._inner.next_id,
        }

    def set_state(self, state):
        # Desserializador: Restaura estado de diagrama de dict (inverse get_state)
        # Handles JSON key→int conversion, null states, missing schemas
        # Delegates lógica a IshikawaWidget.set_state antes de redesenhar
        if not state:
            return
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try:
                k_int = int(k)
            except:
                k_int = k
            nodes[k_int] = v

        if not nodes:
            # Reinicializa 6M padrão se vazio/corrupted
            nodes = {
                1: {
                    "text": "EFEITO / PROBLEMA",
                    "level": 0,
                    "children": [],
                    "parent": None,
                }
            }
            cat_names = [
                "Método",
                "Máquina",
                "Material",
                "Mão de Obra",
                "Meio Ambiente",
                "Medição",
            ]
            next_id = 2
            for name in cat_names:
                nodes[next_id] = {"text": name, "level": 1, "children": [], "parent": 1}
                nodes[1]["children"].append(next_id)
                next_id += 1
            self._inner.next_id = next_id
        else:
            self._inner.next_id = state.get("next_id", 2)

        self._inner.nodes = nodes
        self._inner._draw_diagram()

    def refresh_theme(self):
        # Atualiza cores quando tema global muda
        # Delegates a IshikawaWidget.refresh_theme()
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        # Retorna view gráfica para MainApp renderizar
        # Expõe QGraphicsView contendo diagrama Ishikawa renderizado
        return getattr(self._inner, "view", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _IshikawaModule()
    w.setWindowTitle("Ishikawa — Causa e Efeito — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())
