# -*- coding: utf-8 -*-
"""
Módulo EAP — Estrutura Analítica do Projeto (WBS - Work Breakdown Structure)

Responsabilidades:
- Gerar hierárquica WBS (Work Breakdown Structure) para decomposição de projetos
- 4 níveis máximos de hierarquia: nível 0 (Projeto) > nível 1 (Seção) > 
  nível 2 (Subseção) > nível 3 (Tarefa)
- Auto-numeração WBS: 1.0, 1.1, 1.1.1, 1.1.1.1 (padrão PMI)
- Renderização hierárquica: árvore visual com conexões (L-shaped routing)
- Suporta 3 formas de nó: retângulo arredondado (padrão), elípse, losango
- Drag-drop para reordenar nós dentro de restrições (máximo 4 níveis)
- Persistência: Serialização JSON de árvore de nós

Arquitetura:
- NodeSignals: PubSub para eventos de edição (adicionar, deletar, editar)
- NodeItem: QGraphicsItem polimórfico para renderizar nós com 3 formas
  * Nó raiz (Projeto): Maior, bold, sem botões de deletar/irmão
  * Nós filhos: Com botões de ação (+filho, +irmão, -deletar) no hover
  * WBS code renderizado no topo de cada nó
- FloatingEditor: QLineEdit para edição inline de texto de nó
- EAPWidget: Canvas principal com QGraphicsScene
  * calculate_wbs(): Gera códigos WBS recursivamente (1.0, 1.1, 1.1.1, ...)
  * pre_calcular_dimensoes(): Calcula (w, h) de cada nó baseado em texto
  * calcular_posicoes(): Layout hierárquico com pai ao centro de filhos
  * draw_eap(): Renderiza árvore com conexões L-shaped
- _EAPModule: Adaptador BaseModule com persistência JSON

Fluxo de Renderização:
1. draw_eap() inicia renderização:
   a. calculate_wbs(1, "1"): Auto-numeração de todos nós
   b. pre_calcular_dimensoes(): Calcula tamanho de cada nó
   c. calcular_posicoes(1, 0): Calcula posições em grid é hierárquico
      * Y = 80px + nível * (altura_nó + espaçamento)
      * X = média das posições de filhos (pai centralizado)
2. _draw_connections(): Renderiza linhas L-shaped entre pai e filhos
3. _draw_nodes(): Posiciona NodeItem gráficos

Conceitos-chave:
- WBS Code: Número decimál hierarquizado (1.0 = raiz, 1.1 = primeiro filho, 1.1.1 = neto)
- Hierarquia: Máximo 4 níveis de profundidade
- Layout: Árvore com pai ao centro de filhos horizontais; cada nível incrementa Y
- Forma: 3 opções polimórficas (retângulo, elipse, losango)

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


class NodeSignals(QObject):
    """
    PubSub para eventos de manipulação de nós EAP/WBS.
    Sinais emitidos por NodeItem para notificar EAPWidget de mudanças.
    """
    # Edição de texto: commit_text(node_id, novo_texto)
    commit_text = pyqtSignal(int, str)
    # Adicionar filho (expand level)
    add_child = pyqtSignal(int)
    # Adicionar irmão (mismo level)
    add_sibling = pyqtSignal(int)
    # Deletar nó e filhos recursivamente
    delete_node = pyqtSignal(int)
    # Iniciar edição inline
    edit_start = pyqtSignal(int)


class NodeItem(QGraphicsItem):
    """
    QGraphicsItem polimórfico para renderizar nó da EAP/WBS.
    
    Renderização:
    - 3 formas: retângulo arredondado (default), elípse (círculo), losango
    - Conteúdo em 3 linhas: WBS code (topo, accent), título (bold para raiz), descrição
    - Botões de ação no hover: +filho (bottom-center), +irmão (right-center), -deletar (left-center)
    - Nó raiz: Sem botões de irmão/deletar; tamanho maior, texto bold
    - Feedback hover: Muda cor de fundo
    
    Interação:
    - Clique simples: Se em botão de ação, emite sinal correspondente
      Caso contrário, abre editor inline
    - Duplo clique: Sempre abre editor inline
    
    Parámetros:
    - node_id: int identificador único
    - wbs: str código WBS (ex: "1.1.2")
    - text: str conteúdo/rótulo do nó
    - is_root: bool True para nó raíz (nível 0)
    - shape: str "roundrect", "ellipse" ou "diamond"
    - signals: NodeSignals para emitência de eventos
    - zoom: float fator de escala de renderização
    """
    def __init__(self, node_id, wbs, text, is_root, shape, signals, zoom):
        super().__init__()
        self.node_id = node_id
        self.wbs = wbs
        self.text = text
        self.is_root = is_root
        self.shape = shape
        self.signals = signals
        self.zoom = zoom
        self._hovered = False

        self._font_wbs = QFont("Consolas", max(5, int(8 * zoom)), QFont.Bold)
        self._font_text = QFont(
            "Segoe UI", max(5, int(10 * zoom)), QFont.Bold if is_root else QFont.Normal
        )
        self._font_ph = QFont("Segoe UI", max(5, int(9 * zoom)))
        self._font_ph.setItalic(True)
        self._font_btn = QFont("Consolas", max(6, int(9 * zoom)), QFont.Bold)

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _get_text_width(self, fm, text):
        if hasattr(fm, "horizontalAdvance"):
            return fm.horizontalAdvance(text)
        return fm.width(text)

    def _calc_size(self):
        fm = QFontMetrics(self._font_text)
        fmw = QFontMetrics(self._font_wbs)
        sample = self.text if self.text.strip() else "Nomear"
        pad_x = 30 * self.zoom
        pad_y = 24 * self.zoom  # Slightly more vertical padding
        if self.shape in ["ellipse", "diamond"]:
            pad_x *= 1.6
            pad_y *= 1.8

        # Max width for EAP nodes
        max_node_w = 180 * self.zoom
        wbs_w = self._get_text_width(fmw, self.wbs)

        # Calculate text height with wrapping
        available_text_w = max_node_w - pad_x
        text_rect = fm.boundingRect(
            0, 0, int(available_text_w), 1000, Qt.AlignCenter | Qt.TextWordWrap, sample
        )

        self._w = max(100 * self.zoom, max(text_rect.width(), wbs_w) + pad_x)
        self._h = max(45 * self.zoom, text_rect.height() + fmw.height() + pad_y)

    def width(self):
        return self._w

    def height(self):
        return self._h

    def boundingRect(self):
        m = 14 * self.zoom
        return QRectF(-m, -m, self._w + m * 2, self._h + m * 2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        empty = not self.text.strip()
        r = QRectF(0, 0, self._w, self._h)
        bs = 14 * self.zoom
        hbs = bs / 2

        if _is_nb(t):
            _nb_paint_node(painter, r, self._hovered or self.is_root)
            if self.is_root and not empty and self.shape == "roundrect":
                bw = t.get("border_width", 3)
                strip_h = 6 * self.zoom
                painter.save()
                painter.setBrush(QBrush(QColor(t["accent_bright"])))
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRect(QRectF(bw, bw, self._w - bw * 2, strip_h))
                painter.restore()
        else:
            painter.setBrush(QBrush(_solid_fill(r, self._hovered or self.is_root)))
            border = (
                t["accent_bright"]
                if self.is_root
                else (t["accent"] if not empty else t["accent_dim"])
            )
            style = Qt.SolidLine if not empty else Qt.DashLine
            painter.setPen(QPen(Qt.NoPen))

            if self.shape == "roundrect":
                painter.drawRoundedRect(r, 12, 12)
            elif self.shape == "ellipse":
                painter.drawEllipse(r)
            elif self.shape == "diamond":
                poly = QPolygonF(
                    [
                        QPointF(self._w / 2, 0),
                        QPointF(self._w, self._h / 2),
                        QPointF(self._w / 2, self._h),
                        QPointF(0, self._h / 2),
                    ]
                )
                painter.drawPolygon(poly)

            if self.is_root and not empty and self.shape == "roundrect":
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(r, 12, 12)
                painter.setClipPath(clip_path)

            painter.setBrush(QBrush(QColor(t["accent_bright"])))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRect(QRectF(0, 0, self._w, 4 * self.zoom))
            painter.restore()

        if empty:
            painter.setFont(self._font_ph)
            painter.setPen(QColor(t["accent"] if self._hovered else t["accent_dim"]))
            painter.drawText(r, Qt.AlignCenter, "✎ Nomear")
        else:
            # WBS number — elide if needed
            fmw = QFontMetrics(self._font_wbs)
            painter.setFont(self._font_wbs)
            painter.setPen(QPen(_c("accent"), 1.2))
            # Offset and padding
            offset_y = 8 * self.zoom
            if self.shape in ["ellipse", "diamond"]:
                offset_y += 10 * self.zoom
            wbs_rect = QRectF(
                6 * self.zoom, offset_y, self._w - 12 * self.zoom, fmw.height()
            )
            painter.drawText(wbs_rect, Qt.AlignHCenter | Qt.AlignVCenter, self.wbs)

            # Subtitle (text) — increase padding
            painter.setFont(self._font_text)
            painter.setPen(QColor(t["text"]))
            # Add padding to avoid rounded corner clipping
            p_val = 15 * self.zoom if self.is_root else 8 * self.zoom
            text_rect = QRectF(
                p_val,
                offset_y + fmw.height(),
                self._w - 2 * p_val,
                self._h - offset_y - fmw.height() - 5 * self.zoom,
            )
            painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)
            # Main text — word-wrap with bounded height
            painter.setFont(self._font_text)
            painter.setPen(QColor(t["text"]))
            txt_fm = QFontMetrics(self._font_text)
            txt_y = offset_y + fmw.height() + 2 * self.zoom
            txt_h = self._h - txt_y - 4 * self.zoom
            txt_rect = QRectF(
                4 * self.zoom,
                txt_y,
                self._w - 8 * self.zoom,
                max(txt_h, txt_fm.height()),
            )
            painter.drawText(txt_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        if self._hovered:
            t_btn = T()
            painter.setFont(self._font_btn)
            self._draw_btn(
                painter,
                QRectF(self._w / 2 - hbs, self._h - hbs, bs, bs),
                "+",
                t_btn["btn_add"],
            )
            if not self.is_root:
                self._draw_btn(
                    painter,
                    QRectF(self._w - hbs, self._h / 2 - hbs, bs, bs),
                    "+",
                    t_btn["btn_sib"],
                )
                self._draw_btn(
                    painter,
                    QRectF(-hbs, self._h / 2 - hbs, bs, bs),
                    "−",
                    t_btn["btn_del"],
                )

    def _draw_btn(self, painter, rect, label, color):
        t = T()
        if _is_nb(t):
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor("#000000"), 2))
            painter.drawRect(rect)
        else:
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(QPen(QColor("#FF6666"), 1))
            painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(rect, Qt.AlignCenter, label)

    def _btn_rects(self):
        bs = 14 * self.zoom
        hbs = bs / 2
        rects = {"child": QRectF(self._w / 2 - hbs, self._h - hbs, bs, bs)}
        if not self.is_root:
            rects["sibling"] = QRectF(self._w - hbs, self._h / 2 - hbs, bs, bs)
            rects["delete"] = QRectF(-hbs, self._h / 2 - hbs, bs, bs)
        return rects

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        event.accept()
        sinais = self.signals
        nid = self.node_id
        if self._hovered:
            for action, rect in self._btn_rects().items():
                if rect.contains(event.pos()):
                    if action == "child":
                        QTimer.singleShot(
                            0, lambda s=sinais, n=nid: s.add_child.emit(n)
                        )
                    elif action == "sibling":
                        QTimer.singleShot(
                            0, lambda s=sinais, n=nid: s.add_sibling.emit(n)
                        )
                    elif action == "delete":
                        QTimer.singleShot(
                            0, lambda s=sinais, n=nid: s.delete_node.emit(n)
                        )
                    return
        QTimer.singleShot(0, lambda s=sinais, n=nid: s.edit_start.emit(n))

    def mouseDoubleClickEvent(self, event):
        event.accept()
        sinais = self.signals
        nid = self.node_id
        QTimer.singleShot(0, lambda s=sinais, n=nid: s.edit_start.emit(n))


class FloatingEditor(QLineEdit):
    """
    QLineEdit flutuante para edição inline de texto de nó EAP.
    
    Renderiza:
    - Posicionado sobre o nó selecionado na scene
    - Estilo matching tema com borda de destaque
    - Seleção automática de texto ao abrir
    
    Ciclo de Vida:
    - open(node_id, text, scene_rect, view): Abre editor sobre nó
    - keyPressEvent: Return/Enter confirma; Escape reverte
    - focusOutEvent: Confirma automaticamente
    
    Sinais:
    - committed.emit(node_id, novo_texto): Emitido ao salvar
    """

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._node_id = -1
        self._original = ""
        self._done = False
        self._apply_style()

    def _apply_style(self):
        try:
            t = T()
            self.setStyleSheet(f"""
                QLineEdit {{
                    background  : {t["bg_card2"]};
                    color       : {t["text"]};
                    border      : 2px solid {t["accent_bright"]};
                    border-radius: 6px;
                    font-family : 'Segoe UI';
                    font-size   : 11pt;
                    padding     : 4px 10px;
                }}
            """)
        except Exception:
            self.setStyleSheet(
                "QLineEdit { background:#2A0F0F; color:#FAE8E8; border:2px solid #CC2222; border-radius:5px; font-family:'Segoe UI'; font-size:11pt; padding:4px 10px; }"
            )
        self.hide()

    def open(self, node_id, current_text, scene_rect, view):
        self._apply_style()
        self._node_id = node_id
        self._original = current_text
        self._done = False
        tl = view.mapFromScene(scene_rect.topLeft())
        w = max(120, int(scene_rect.width()))
        h = 32
        self.setGeometry(tl.x(), tl.y() + int(scene_rect.height() / 2) - h // 2, w, h)
        self.setText(current_text)
        self.selectAll()
        self.show()
        self.raise_()
        self.setFocus()

    def _commit(self, text=None):
        if self._done:
            return
        self._done = True
        result = (text if text is not None else self.text()).strip()
        self.hide()
        self.committed.emit(self._node_id, result)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._commit()
        elif event.key() == Qt.Key_Escape:
            self._commit(self._original)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        self._commit()
        super().focusOutEvent(event)


class EAPWidget(QWidget):
    """
    Widget principal para edição interativa de EAP/WBS hierárquica.
    
    Responsabilidades:
    - Gerenciar hierárquica de nós (pai-filho-irmão)
    - Renderizar layout árvore com posicionamento automático
    - Calcular e atualizar códigos WBS (1.0, 1.1, 1.1.1, ...)
    - Orquestra interações: adicionar, deletar, editar, reordenar nós
    - Zoom e pan com suporte Ctrl+Scroll
    - Serializar/desserializar estado JSON
    
    Estado Interno:
    - self.nodes: dict[int, {text, children[], parent, shape}]
    - self.wbs_numbers: dict[int, "1.0"] - códigos WBS
    - self.node_positions: dict[int, (x, y)] - coordenadas renderizadas
    - self.node_dimensions: dict[int, (w, h)] - tamanhos calculados
    - self.zoom: float fator de zoom
    
    Pipeline de Renderização (draw_eap()):
    1. calculate_wbs(node_id, wbs_str): Numeração recursíva
    2. pre_calcular_dimensoes(): Calcula (w, h) de cada nó baseado em texto
    3. calcular_posicoes(node_id, nivel): Layout hierárquico
       a. Y = 80px + nível * (altura_nó + espaçamento)
       b. X = média de filhos (pai centralizado)
    4. _draw_connections(node_id): Renderiza linhas em L entre pai-filhos
    5. _draw_nodes(): Posiciona NodeItem gráficos
    
    Restrições:
    - Máximo 4 níveis de hierarquia (raiz + 3 níveis de filhos)
    - Cada filho tem padrão de forma (retângulo, elípse, losango)
    - WBS auto-gerado: Noão pode ser editado manualmente
    """

    def __init__(self):
        super().__init__()

        self.base_pad_x = 35
        self.base_pad_y = 60
        self.base_min_width = 100
        self.base_box_height = 40
        self.zoom = 1.0
        self.next_id = 2
        self.wbs_numbers = {}
        self.node_dimensions = {}
        self.node_positions = {}
        self._scene_items = []
        self.nodes = {
            1: {"text": "", "children": [], "parent": None, "shape": "roundrect"}
        }
        self.pad_x = 30
        self.pad_y = 60
        self.signals = NodeSignals()
        self.signals.commit_text.connect(self._on_commit)
        self.signals.add_child.connect(self._on_add_child)
        self.signals.add_sibling.connect(self._on_add_sibling)
        self.signals.delete_node.connect(self._on_delete)
        self.signals.edit_start.connect(self._on_edit_start)

        self._setup_ui()

        self._float_editor = FloatingEditor(self.view)
        self._float_editor.committed.connect(self._on_commit)
        self.update_zoom(1.0)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar_eap = QWidget()
        self._toolbar_eap.setFixedHeight(44)
        toolbar = self._toolbar_eap
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(10, 4, 10, 4)
        tb.setSpacing(6)

        self._eap_title_lbl = QLabel("📋  EAP — Estrutura Analítica do Projeto")
        tb.addWidget(self._eap_title_lbl)

        sep = QWidget()
        sep.setFixedSize(1, 26)
        tb.addWidget(sep)

        self._eap_btns = []
        for lbl, fn in [
            ("🔍−", lambda *a: self.zoom_out()),
            ("🔍+", lambda *a: self.zoom_in()),
            ("⟳ 100%", lambda *a: self.update_zoom(1.0)),
        ]:
            b = QPushButton(lbl)
            b.clicked.connect(fn)
            tb.addWidget(b)
            self._eap_btns.append(b)

        tb.addStretch()

        self._eap_exp_btns = []
        for lbl, key in [("📄 PDF", "pdf"), ("🖼 PNG", "png")]:
            b2 = QPushButton(lbl)
            b2.clicked.connect(lambda _, k=key: self._export_scene(k))
            tb.addWidget(b2)
            self._eap_exp_btns.append(b2)

        layout.addWidget(toolbar)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)
        self.refresh_theme()

    def _refresh_view_bg(self):
        if not hasattr(self, "view"):
            return
        try:
            self.view.setBackgroundBrush(QBrush(QColor(T()["bg_app"])))
        except Exception:
            self.view.setBackgroundBrush(QBrush(QColor("#FFFFFF")))

    def refresh_theme(self):
        t = T()
        self._toolbar_eap.setStyleSheet(f"""
            QWidget {{ background: {t["toolbar_bg"]}; border-bottom: 1px solid {t["accent"]}; }}
        """)
        self._eap_title_lbl.setStyleSheet(f"""
            color: {t["accent_bright"]}; font-family: 'Segoe UI';
            font-size: 12px; font-weight: bold; background: transparent;
        """)
        btn_s = f"""
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["text"]};
                border: 1px solid {t["accent_dim"]}; border-radius: 5px;
                padding: 4px 12px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {t["toolbar_btn_h"]}; border-color: {t["accent"]}; color: {t["accent_bright"]}; }}
        """
        exp_s = f"""
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["accent"]};
                border: 1px solid {t["accent_dim"]}; border-radius: 5px;
                padding: 4px 12px; font-size: 11px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {t["accent"]}; color: white; }}
        """
        for b in self._eap_btns:
            b.setStyleSheet(btn_s)
        for b in self._eap_exp_btns:
            b.setStyleSheet(exp_s)
        if hasattr(self, "view"):
            self._refresh_view_bg()

        # Refresh scene items and connections
        if hasattr(self, "scene"):
            self.scene.update()
            # Redesenha para garantir que cores de linhas (que não são itens custom) atualizem
            self.draw_eap()

        if hasattr(self, "_float_editor"):
            self._float_editor._apply_style()

    def zoom_in(self, *args):
        self.update_zoom(self.zoom * 1.15)

    def zoom_out(self, *args):
        self.update_zoom(self.zoom / 1.15)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3
            )

    def update_zoom(self, z):
        self.zoom = max(0.3, min(z, 3.0))
        self.pad_x = self.base_pad_x * self.zoom
        self.pad_y = self.base_pad_y * self.zoom
        self.min_width = self.base_min_width * self.zoom
        self.box_height = self.base_box_height * self.zoom
        self.draw_eap()

    def _create_shape_icon(self, shape_type):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(_c("accent"), 2))
        painter.setBrush(QBrush(_c("bg_card")))
        rect = QRectF(4, 4, 24, 24)
        if shape_type == "roundrect":
            painter.drawRoundedRect(rect, 4, 4)
        elif shape_type == "ellipse":
            painter.drawEllipse(rect)
        elif shape_type == "diamond":
            poly = QPolygonF(
                [QPointF(16, 4), QPointF(28, 16), QPointF(16, 28), QPointF(4, 16)]
            )
            painter.drawPolygon(poly)
        painter.end()
        return QIcon(pixmap)

    def _choose_shape(self):
        menu = QMenu(self)
        try:
            t = T()
            menu.setStyleSheet(f"""
                QMenu {{ background-color: {t["bg_card"]}; color: {t["text"]};
                        border: 1px solid {t["accent"]}; font-family: 'Segoe UI'; font-size: 10pt; }}
                QMenu::item {{ padding: 6px 24px 6px 36px; }}
                QMenu::item:selected {{ background-color: {t["accent"]}; color: white; }}
                QMenu::icon {{ padding-left: 10px; }}
            """)
        except Exception:
            pass
        action_rect = menu.addAction(
            self._create_shape_icon("roundrect"), "Retângulo Arredondado"
        )
        action_ellipse = menu.addAction(
            self._create_shape_icon("ellipse"), "Elipse (Círculo)"
        )
        action_diamond = menu.addAction(
            self._create_shape_icon("diamond"), "Losango (Decisão)"
        )
        selected = menu.exec_(QCursor.pos())
        if selected == action_rect:
            return "roundrect"
        if selected == action_ellipse:
            return "ellipse"
        if selected == action_diamond:
            return "diamond"
        return None

    def _on_commit(self, node_id, new_text):
        if node_id in self.nodes:
            self.nodes[node_id]["text"] = new_text
        self.draw_eap()

    def _on_edit_start(self, node_id):
        if node_id not in self.node_positions:
            return
        nw, nh = self.node_dimensions[node_id]
        x, y = self.node_positions[node_id]
        scene_r = QRectF(x - nw / 2, y - nh / 2, nw, nh)
        self._float_editor.open(
            node_id, self.nodes[node_id]["text"], scene_r, self.view
        )

    def _on_add_child(self, parent_id):
        shape = self._choose_shape()
        if not shape:
            return
        new_id = self.next_id
        self.next_id += 1
        self.nodes[new_id] = {
            "text": "",
            "children": [],
            "parent": parent_id,
            "shape": shape,
        }
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_eap()
        QTimer.singleShot(60, lambda n=new_id: self._on_edit_start(n))

    def _on_add_sibling(self, node_id):
        parent_id = self.nodes[node_id]["parent"]
        if parent_id is None:
            return
        shape = self._choose_shape()
        if not shape:
            return
        new_id = self.next_id
        self.next_id += 1
        self.nodes[new_id] = {
            "text": "",
            "children": [],
            "parent": parent_id,
            "shape": shape,
        }
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_eap()
        QTimer.singleShot(60, lambda n=new_id: self._on_edit_start(n))

    def _on_delete(self, node_id):
        label = self.nodes[node_id]["text"] or "nó sem nome"
        ans = QMessageBox.question(
            self,
            "Excluir",
            f"Excluir '{label}' e todas as suas sub-tarefas?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            pid = self.nodes[node_id]["parent"]
            if pid is not None:
                self.nodes[pid]["children"].remove(node_id)
            self._remove_recursively(node_id)
            self.draw_eap()

    def _remove_recursively(self, node_id):
        for cid in list(self.nodes[node_id]["children"]):
            self._remove_recursively(cid)
        del self.nodes[node_id]

    def calculate_wbs(self, node_id, wbs):
        """
        Calcula e armazena números WBS para cada nó recursivamente.
        
        Algoritmo:
        - wbs para nó atual: Armazenado em self.wbs_numbers[node_id]
        - Para cada filho i: self.calculate_wbs(child_id, f"{wbs}.{i+1}")
        
        Exemplo:
        - Raíz (node_id=1): "1.0"
        - Filho 0: "1.0.1"
        - Filho 1: "1.0.2"
        - Neto de filho 0, subfilho 0: "1.0.1.1"
        
        Parámetros:
        - node_id: int ID do nó sendo numerado
        - wbs: str código WBS para esse nó
        """
        for i, cid in enumerate(self.nodes[node_id]["children"]):
            self.calculate_wbs(cid, f"{wbs}.{i + 1}")

    def pre_calcular_dimensoes(self):
        """
        Pré-calcula dimensões (w, h) de cada nó baseado em texto e zoom.
        
        Algoritmo:
        1. Para cada nó em self.nodes:
           a. Cria instância temporária de NodeItem
           b. Armazena (width, height) em self.node_dimensions[node_id]
        
        Resultado: Dict preenchido para uso em calcular_posicoes()
        """
        for nid in self.nodes:
            shape = self.nodes[nid].get("shape", "roundrect")
            tmp = NodeItem(
                nid,
                self.wbs_numbers.get(nid, ""),
                self.nodes[nid]["text"],
                nid == 1,
                shape,
                self.signals,
                self.zoom,
            )
            self.node_dimensions[nid] = (tmp.width(), tmp.height())

    def calcular_posicoes(self, node_id, nivel):
        """
        Calcula posições (x, y) de nós em layout hierárquico.
        
        Algoritmo (post-order traversal):
        1. Para cada filho: calcular_posicoes(child, nivel+1)
        2. Se nó é folha (sem filhos): X = current_leaf_x; incrementa
        3. Se nó tem filhos: X = média de posições de filhos
        4. Y = 80px + nivel * (altura_nó + espaçamento)
        
        Resultado:
        - self.node_positions[node_id] = (x, y)
        - Retorna X do nó para cálculo média do pai
        
        Ex: Raíz tem 3 filhos nas posições X=[100, 200, 300]
            Raíz X = (100 + 200 + 300) / 3 = 200 (centrado)
        """
        filhos = self.nodes[node_id]["children"]
        nw, nh = self.node_dimensions[node_id]
        y = 80 * self.zoom + nivel * (nh + self.pad_y)
        if not filhos:
            x = self.current_leaf_x + nw / 2
            self.current_leaf_x += nw + self.pad_x
        else:
            xs = [self.calcular_posicoes(c, nivel + 1) for c in filhos]
            x = sum(xs) / len(xs)
        self.node_positions[node_id] = (x, y)
        return x

    def draw_eap(self):
        """
        Orquestra renderização completa da árvore EAP/WBS.
        
        Etapas:
        1. Limpa scene anterior
        2. calculate_wbs(1, "1.0"): Auto-numeração de todos nós
        3. pre_calcular_dimensoes(): Calcula tamanho de cada nó
        4. current_leaf_x = 0; calcular_posicoes(1, 0): Layout hierárquico
        5. _draw_connections(1): Renderiza linhas entre pai-filhos
        6. _draw_nodes(): Posiciona NodeItem gráficos na scene
        
        Resultado: Diagrama completo visível em QGraphicsView
        """
        self.calculate_wbs(1, "1")
        self.pre_calcular_dimensoes()
        self.current_leaf_x = 80 * self.zoom
        self.calcular_posicoes(1, nivel=0)
        vw = self.view.viewport().width() or 800
        offset_x = vw / 2 - self.node_positions[1][0]
        min_x = min(
            p[0] - self.node_dimensions[n][0] / 2
            for n, p in self.node_positions.items()
        )
        if min_x + offset_x < 80 * self.zoom:
            offset_x = 80 * self.zoom - min_x
        for n in self.node_positions:
            x, y = self.node_positions[n]
            self.node_positions[n] = (x + offset_x, y)
        # Recursively draw tree connections, and also handle independent roots
        for root_id in [n for n, data in self.nodes.items() if data["parent"] is None]:
            self._draw_connections(root_id)
        self._draw_nodes()
        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40)
        )

    def _draw_connections(self, node_id):
        """
        Renderiza linhas de conexão (L-shaped routing) de pai para filhos.
        
        Padrão de Roteamento:
        - Linha vertical: De nó pai (bottom) para meio (mid_y)
        - Linha horizontal: De meio para x de cada filho
        - Linha vertical: De meio para nó filho (top)
        
        Renderiza:
        - Linhas de conexão primária (pai-filho)
        - Linhas cruzadas (cross_links) em tracejadas com cor accent_bright
        - Pontas de seta nos extremos de linhas cruzadas
        
        Recursão: Chama _draw_connections() para cada filho
        """
        px, py = self.node_positions[node_id]
        pw, _ = self.node_dimensions[node_id]
        p1 = QPointF(px + pw / 2, py)

        if "cross_links" in self.nodes[node_id]:
            pen_cross = QPen(
                QColor(T()["accent_bright"]),
                max(1.5, int(2 * self.zoom)),
                Qt.DashLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
            for cid in self.nodes[node_id]["cross_links"]:
                if cid not in self.node_positions:
                    continue
                cx, cy = self.node_positions[cid]
                cw, _ = self.node_dimensions[cid]
                # Distancia entre eles
                p2 = QPointF(cx - cw / 2, cy) if cx > px else QPointF(cx + cw / 2, cy)

                path = QPainterPath()
                path.moveTo(p1)
                mid_x = (p1.x() + p2.x()) / 2
                path.lineTo(mid_x, p1.y())
                path.lineTo(mid_x, p2.y())
                path.lineTo(p2)
                self._scene_items.append(self.scene.addPath(path, pen_cross))

                arrow_size = 8 * self.zoom
                dir_x = -1 if cx > px else 1
                poly = QPolygonF(
                    [
                        p2,
                        QPointF(p2.x() + arrow_size * dir_x, p2.y() - arrow_size / 2),
                        QPointF(p2.x() + arrow_size * dir_x, p2.y() + arrow_size / 2),
                    ]
                )
                self._scene_items.append(
                    self.scene.addPolygon(
                        poly, QPen(Qt.NoPen), QBrush(QColor(T()["accent_bright"]))
                    )
                )

        filhos = self.nodes[node_id]["children"]
        if not filhos:
            return
        _, ph = self.node_dimensions[node_id]
        py_bot = py + ph / 2
        mid_y = py_bot + self.pad_y / 2
        t_draw = T()
        pen = QPen(
            QColor(t_draw["line_eap"]),
            max(1, int(2 * self.zoom)),
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin,
        )
        for cid in filhos:
            cx, cy = self.node_positions[cid]
            cy_top = cy - self.node_dimensions[cid][1] / 2
            for coords in [
                (px, py_bot, px, mid_y),
                (px, mid_y, cx, mid_y),
                (cx, mid_y, cx, cy_top),
            ]:
                self._scene_items.append(self.scene.addLine(*coords, pen))
            self._draw_connections(cid)

    def _draw_nodes(self):
        """
        Renderiza todos os nós gráficos NodeItem em posições calculadas.
        
        Para cada node_id em self.node_positions:
        1. Cria instância de NodeItem com parâmetros do nó
        2. Posiciona em (x - w/2, y - h/2) para centralização
        3. Adiciona à scene
        4. Registra em self._scene_items para limpeza futura
        """
            nw, nh = self.node_dimensions[nid]
            shape = self.nodes[nid].get("shape", "roundrect")
            item = NodeItem(
                nid,
                self.wbs_numbers[nid],
                self.nodes[nid]["text"],
                nid == 1,
                shape,
                self.signals,
                self.zoom,
            )
            item.setPos(x - nw / 2, y - nh / 2)
            self.scene.addItem(item)
            self._scene_items.append(item)


class _EAPModule(BaseModule):
    """
    Adaptador BaseModule para EAP/WBS integração em ProEng.
    
    Responsabilidades:
    - Wrapper do EAPWidget com interface padrão BaseModule
    - Gerencia zoom (reset_zoom, zoom_in, zoom_out)
    - Persistência JSON via get_state/set_state (serialização de árvore)
    - Integração com sistema de temas
    - Exporta árvore para formatos suportados
    
    Métodos BaseModule:
    - get_state(): Retorna {schema: 'eap.v1', nodes, next_id}
    - set_state(state): Restaura árvore anterior com validação backward-compatible
    - get_view(): Retorna QGraphicsView para renderização
    - refresh_theme(): Reconecta cores de tema após mudança
    
    API de Zoom:
    - reset_zoom(): Volta a 1.0 (100%)
    - zoom_in(): Incrementa fator de zoom (~15% por clique)
    - zoom_out(): Decrementa fator de zoom
    """
        super().__init__()
        self._inner = EAPWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Passe o mouse sobre um bloco para ver botões de adicionar Filho (+) ou Irmão (+).\n"
            "• O código WBS (1.1, 1.2...) é gerado e atualizado sozinho.\n"
            "• Clique duplo para renomear os pacotes de trabalho.\n"
            "• Use o menu 'Exibir' para Zoom e ajuste de tela."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def reset_zoom(self):
        self._inner.update_zoom(1.0)

    def zoom_in(self):
        self._inner.zoom_in()

    def zoom_out(self):
        self._inner.zoom_out()

    # --- BaseModule API -------------------------------------------------
    def get_state(self):
        """
        Exporta estado atual da EAP para JSON persistência.
        
        Retorna:
        - schema: 'eap.v1' (versão do formato)
        - nodes: dict[int, {text, children[], parent, shape}]
        - next_id: Próximo ID disponível para novo nó
        """
            "schema": "eap.v1",
            "nodes": self._inner.nodes,
            "next_id": self._inner.next_id,
        }

    def set_state(self, state):
        """
        Restaura estado anterior da EAP a partir de JSON.
        
        Validação:
        - Converte chaves de string para int (JSON é sempre string)
        - Padrão fallback: Se state vazio, cria nó raiz vazio
        - next_id: Restaurado ou padrão 2
        
        Etapas:
        1. Parse nodes dict com conversão de chaves
        2. Restaura self._inner.nodes
        3. Atualiza self._inner.next_id
        4. Redesenha canvas
        
        Parámetros:
        - state: dict com 'nodes' e 'next_id' (pode ser None)
        """

    def refresh_theme(self):
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        return getattr(self._inner, "view", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _EAPModule()
    w.setWindowTitle("Gerador EAP — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())
