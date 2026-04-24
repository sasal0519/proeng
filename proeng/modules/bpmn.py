# -*- coding: utf-8 -*-
"""Módulo BPMN — Business Process Model and Notation 2.0."""

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
    QPainterPathStroker,
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

import math as _math


class BPMNNodeSignals(QObject):
    commit_text = pyqtSignal(object, str)
    add_child = pyqtSignal(int)
    add_sibling = pyqtSignal(int)
    delete_node = pyqtSignal(int)
    edit_start = pyqtSignal(object)
    change_shape = pyqtSignal(int)
    add_root = pyqtSignal(int)
    link_to = pyqtSignal(int)
    move_lane = pyqtSignal(int, int)
    recall_create = pyqtSignal(int)  # Sinal para criar recall


class HeaderItem(QGraphicsRectItem):
    def __init__(self, rect, text, type_id, signals, zoom, vertical=False):
        super().__init__(rect)
        self.text = text
        self.type_id = type_id
        self.signals = signals
        self.zoom = zoom
        self.vertical = vertical
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setZValue(-15)

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mouseDoubleClickEvent(self, e):
        e.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.type_id))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.type_id))

    def contextMenuEvent(self, event):
        if self.type_id.startswith("lane_"):
            menu = QMenu()
            t = T()
            br = t.get("border_radius", 0)
            menu.setStyleSheet(f"""
                QMenu {{ background-color: {t["bg_card"]}; color: {t["text"]}; border: 3px solid #000000;
                        border-radius: 0px; font-family: 'Segoe UI'; font-size: 13px;
                        font-weight: bold; padding: 5px; }}
                QMenu::item {{ padding: 8px 30px; border-radius: 0px; }}
                QMenu::item:selected {{ background-color: {t["accent"]}; color: #FFFFFF; }}
            """)
            m_add = menu.addAction("➕ Inserir Evento Inicial nesta Baia")
            action = menu.exec_(event.screenPos())
            if action == m_add:
                lane_idx = int(self.type_id.split("_")[1])
                self.signals.add_root.emit(lane_idx)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()
        r = self.rect().adjusted(0.5, 0.5, -0.5, -0.5)

        # ── Renderização Neo-Brutalist (estilo 5W2H) ──────────────────────────
        br = t.get("border_radius", 0)
        if _is_nb(t):
            _nb_paint_node(painter, r, self.hovered, radius=0)
            bw = t.get("border_width", 3)
            # Accent strip (clipped)
            painter.save()
            painter.setClipRect(r)
            painter.setBrush(
                QBrush(
                    QColor(_c("accent_bright") if self.type_id == "project" else _c("accent"))
                )
            )
            painter.setPen(Qt.NoPen)
            if self.vertical:
                painter.drawRect(QRectF(r.left(), r.top(), r.width(), 3))
            else:
                painter.drawRect(QRectF(r.left(), r.top(), r.width(), 4))
            painter.restore()
        else:
            painter.setBrush(QBrush(_solid_fill(r, self.hovered)))
            painter.setPen(QPen(Qt.NoPen))
            rad = 20 if self.type_id == "pool" else 8
            painter.drawRoundedRect(r, rad, rad)

            # Accent strip logic (clip to rounded container)
            painter.save()
            clip_path = QPainterPath()
            clip_path.addRoundedRect(r, rad, rad)
            painter.setClipPath(clip_path)

            painter.setBrush(
                QBrush(
                    QColor(
                        _c("accent_bright") if self.type_id == "project" else _c("accent")
                    )
                )
            )
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(r.left(), r.top(), r.width(), 4))
            painter.restore()

        # ── Text Drawing (Highest contrast) ──────────────────────────────────
        painter.setPen(QColor(T()["text"]))
        font_size = 14 if self.type_id == "project" else 11
        ff = T().get("font_family_content", "'Segoe UI', sans-serif").replace("'", "")
        font = QFont(ff, max(7, int(font_size * self.zoom)), QFont.Bold)
        painter.setFont(font)
        if self.vertical:
            painter.save()
            painter.translate(
                self.rect().x() + self.rect().width() / 2,
                self.rect().y() + self.rect().height() / 2,
            )
            painter.rotate(-90)
            tr = QRectF(
                -self.rect().height() / 2 + 10 * self.zoom,
                -self.rect().width() / 2 + 2 * self.zoom,
                self.rect().height() - 20 * self.zoom,
                self.rect().width() - 4 * self.zoom,
            )
            fm = QFontMetrics(font)
            elided = fm.elidedText(self.text, Qt.ElideRight, int(tr.width()))
            painter.drawText(tr, Qt.AlignCenter, elided)
            painter.restore()
        else:
            text_r = r.adjusted(
                15 * self.zoom, 8 * self.zoom, -15 * self.zoom, -8 * self.zoom
            )
            painter.drawText(text_r, Qt.AlignCenter | Qt.TextWordWrap, self.text)


class AddLaneItem(QGraphicsRectItem):
    def __init__(self, rect, callback, zoom, lane_callback=None):
        super().__init__(rect)
        self.callback = callback
        self.lane_callback = lane_callback or callback
        self.zoom = zoom
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setZValue(-15)

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            e.accept()
            # Clique esquerdo agora adiciona uma baia diretamente
            self.lane_callback()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()
        if _is_nb(t):
            _nb_paint_node(painter, self.rect(), self.hovered, radius=0)
        else:
            painter.setBrush(
                QBrush(QColor(_c("bg_card2") if self.hovered else _c("bg_app")))
            )
            painter.setPen(QPen(Qt.NoPen))
            br = t.get("border_radius", 0)
            if br > 0:
                painter.drawRoundedRect(self.rect(), br, br)
            else:
                painter.drawRect(QRectF(self.rect()))
        painter.setPen(QColor(t["accent_bright"] if self.hovered else t["text_dim"]))
        ff = t.get("font_family_content", "'Segoe UI', sans-serif").replace("'", "")
        font = QFont(ff, max(7, int(11 * self.zoom)), QFont.Bold)
        painter.setFont(font)
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "⊞ Clique aqui para Adicionar Nova Baia (Setor)",
        )


def _nb_paint_geometric_shape(painter, shape_type, rect, border_color, bg_color, zoom, hovered=False):
    """
    Desenha forma geométrica BPMN com estilo neo-brutalist.
    
    Parâmetros:
        painter: QPainter em operação
        shape_type: tipo de forma (Evento, Gateway, Base de Dados, Objeto de Dados)
        rect: QRectF da forma
        border_color: cor da borda (hex string)
        bg_color: cor de fundo (hex string) - segue o tema ativo
        zoom: fator de zoom
        hovered: boolean para estado de hover
    """
    t = T()
    # Borda grossa no estilo neo-brutalista
    border_width = 4.0 if hovered else 4.0
    
    # Fundo usa cor do tema (bg_color passado)
    fill_color = QColor(bg_color)
    
    # Desenhar forma principal sem sombra
    painter.setBrush(QBrush(fill_color))
    painter.setPen(QPen(QColor(border_color), border_width))
    
    if "Evento" in shape_type:
        painter.drawEllipse(rect)
    elif "Gateway" in shape_type:
        poly = QPolygonF([
            QPointF(rect.center().x(), rect.top()),
            QPointF(rect.right(), rect.center().y()),
            QPointF(rect.center().x(), rect.bottom()),
            QPointF(rect.left(), rect.center().y()),
        ])
        painter.drawPolygon(poly)
    elif "Base de Dados" in shape_type:
        painter.drawRect(QRectF(rect.left(), rect.top() + rect.height() * 0.15, rect.width(), rect.height() * 0.7))
        painter.drawEllipse(QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.3))
        painter.drawEllipse(QRectF(rect.left(), rect.top() + rect.height() * 0.7, rect.width(), rect.height() * 0.3))
    elif "Objeto de Dados" in shape_type:
        poly = QPolygonF([
            QPointF(rect.left(), rect.top()),
            QPointF(rect.left() + rect.width() * 0.7, rect.top()),
            QPointF(rect.right(), rect.top() + rect.height() * 0.3),
            QPointF(rect.right(), rect.bottom()),
            QPointF(rect.left(), rect.bottom()),
        ])
        painter.drawPolygon(poly)


class BPMNConnectionLine(QGraphicsItem):
    """
    Linha de conexão entre dois nós com supporte a texto no meio.
    Renderiza a linha (reta ou com curvas) e permite exibir um rótulo (label) no ponto médio.
    """
    def __init__(self, p1, p2, label="", zoom=1.0, line_type="solid", color=None, path=None):
        super().__init__()
        self.p1 = p1  # QPointF início (usado se path for None)
        self.p2 = p2  # QPointF fim
        self.path = path  # QPainterPath opcional (para linhas com curvas)
        self.label = label  # Texto a exibir no meio
        self.zoom = zoom
        self.line_type = line_type  # "solid" ou "dash"
        self.color = color or QColor("#7367F0")
        self._hovered = False
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)  # Aceitar cliques
        self.setCursor(Qt.PointingHandCursor)
        self.connection_key = None
        self.parent_widget = None
    
    @staticmethod
    def _is_light_theme(theme_dict: dict) -> bool:
        """
        Detecta se o tema é claro ou escuro baseado na luminância do bg_app.
        
        Args:
            theme_dict: Dicionário do tema contendo "bg_app"
            
        Returns:
            True se é tema claro, False se é escuro
        """
        try:
            bg_app = theme_dict.get("bg_app", "#FFFFFF")
            # Converter hex para RGB
            bg_app = bg_app.lstrip('#')
            r = int(bg_app[0:2], 16)
            g = int(bg_app[2:4], 16)
            b = int(bg_app[4:6], 16)
            
            # Calcular luminância relativa (fórmula de luminância)
            # L = 0.299*R + 0.587*G + 0.114*B
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            
            # Se luminância > 127.5 (~50%), é claro
            return luminance > 127.5
        except Exception:
            # Default: assumir escuro
            return False
        
    def boundingRect(self):
        if self.path:
            return self.path.boundingRect().adjusted(-50, -50, 50, 50)
        rect = QRectF(self.p1, self.p2)
        return rect.adjusted(-50, -50, 50, 50)
    
    def shape(self):
        """Aumentar área clicável da linha"""
        path = QPainterPath()
        if self.path:
            # Para paths complexos, usar stroke path para aumentar área
            stroker = QPainterPathStroker()
            stroker.setWidth(10)  # Área clicável de 10px
            return stroker.createStroke(self.path)
        else:
            # Para linhas retas, criar área ao redor
            stroker = QPainterPathStroker()
            stroker.setWidth(10)  # 10px de área clicável
            path.moveTo(self.p1)
            path.lineTo(self.p2)
            return stroker.createStroke(path)
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Desenhar linha
        pen_width = max(1, int(2 * self.zoom))
        pen = QPen(self.color, pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        
        if self.line_type == "dash":
            pen.setDashPattern([5, 5])
        
        painter.setPen(pen)
        
        # Desenhar path se existir, senão desenhar reta
        if self.path:
            painter.drawPath(self.path)
        else:
            painter.drawLine(self.p1, self.p2)
        
        # Desenhar rótulo (label) acima da linha
        if self.label:
            # Calcular ponto médio (simplificado)
            if self.path:
                # Para paths complexos, usar aproximação
                mid_point = self.path.pointAtPercent(0.5)
            else:
                mid_point = (self.p1 + self.p2) * 0.5
            
            # Posicionar texto acima da seta (com pequeno offset)
            offset_y = -25 * self.zoom  # Acima da seta
            label_pos = QPointF(mid_point.x(), mid_point.y() + offset_y)
            
            # Fonte e métrica
            t = T()
            font = QFont(t.get("font_family", "Segoe UI"), max(8, int(10 * self.zoom)), QFont.Bold)
            fm = QFontMetrics(font)
            text_width = fm.width(self.label)
            text_height = fm.height()
            
            # Rect do texto
            text_rect = QRectF(
                label_pos.x() - text_width / 2,
                label_pos.y() - text_height / 2,
                text_width,
                text_height
            )
            
            # Cor do texto: preto em temas claros, branco em temas escuros
            is_light = self._is_light_theme(t)
            text_color = QColor(0, 0, 0) if is_light else QColor(255, 255, 255)
            
            # Desenhar texto SEM background
            painter.setPen(text_color)
            painter.setFont(font)
            painter.drawText(text_rect, Qt.AlignCenter, self.label)
    
    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
    
    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._edit_label()
            event.accept()
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        t_m = T()
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {t_m["bg_card"]}; color: {t_m["text"]}; border: 3px solid #000000;
                    border-radius: 0px; font-family: 'Segoe UI'; font-size: 13px;
                    font-weight: bold; padding: 5px; }}
            QMenu::item {{ padding: 8px 30px; border-radius: 0px; }}
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: #FFFFFF; }}
        """)
        
        menu.addAction("✏️ Editar Rótulo").triggered.connect(self._edit_label)
        menu.addAction("🗑 Remover Rótulo").triggered.connect(self._remove_label)
        
        menu.exec_(event.screenPos())
    
    def _edit_label(self):
        """Abre diálogo para editar o rótulo da seta"""
        new_label, ok = QInputDialog.getText(
            None,
            "Editar Rótulo da Seta",
            "Digite o texto para a seta:",
            text=self.label
        )
        if ok:
            self.label = new_label.strip()
            if self.connection_key and self.parent_widget:
                self.parent_widget._connection_labels[self.connection_key] = self.label
            self.update()
    
    def _remove_label(self):
        """Remove o rótulo da seta"""
        self.label = ""
        if self.connection_key and self.parent_widget:
            if self.connection_key in self.parent_widget._connection_labels:
                del self.parent_widget._connection_labels[self.connection_key]
        self.update()


class BPMNRecallArrow(QGraphicsItem):
    """
    Seta de recall que sai de um ponto origem, vai para baixo, depois para esquerda, 
    e sobe até o elemento destino. Composta por linhas retas.
    
    Trajetória: Começa no ponto de origem → vai para baixo (offset_down) → 
    vai para esquerda (offset_left) → sobe até o destino
    """
    def __init__(self, origin_pos, target_pos, zoom):
        super().__init__()
        self.origin_pos = origin_pos  # QPointF
        self.target_pos = target_pos  # QPointF
        self.zoom = zoom
        self._stroke_width = 2.5
        self._arrow_size = 10 * zoom
        
    def boundingRect(self):
        return QRectF(-3000, -3000, 6000, 6000)
    
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Cores do tema
        t = T()
        pen_color = QColor(t.get("accent", "#7367F0"))
        
        # Criar caneta tracejada
        pen = QPen(pen_color, self._stroke_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setDashPattern([5, 5])  # Padrão tracejado: 5px traço, 5px espaço
        painter.setPen(pen)
        
        # Desenhar a trajetória: DOWN→LEFT→UP→RIGHT→UP (entrando pelo BAIXO)
        down_offset = 60 * self.zoom
        left_offset = 80 * self.zoom
        bottom_offset = 40 * self.zoom  # Offset abaixo do alvo para entrar por baixo
        
        # Segmento 1: Vertical para BAIXO
        p1 = QPointF(self.origin_pos.x(), self.origin_pos.y() + down_offset)
        painter.drawLine(self.origin_pos, p1)
        
        # Segmento 2: Horizontal para ESQUERDA
        p2 = QPointF(self.origin_pos.x() - left_offset, self.origin_pos.y() + down_offset)
        painter.drawLine(p1, p2)
        
        # Segmento 3: Vertical para CIMA até estar ABAIXO do target
        p3 = QPointF(p2.x(), self.target_pos.y() + bottom_offset)
        painter.drawLine(p2, p3)
        
        # Segmento 4: Horizontal para DIREITA até o target
        p4 = QPointF(self.target_pos.x(), self.target_pos.y() + bottom_offset)
        painter.drawLine(p3, p4)
        
        # Segmento 5: Vertical para CIMA ENTRANDO pelo BAIXO
        painter.drawLine(p4, self.target_pos)
        
        # Desenhar a ponta da seta (vindo de baixo)
        self._draw_arrow_head(painter, p4, self.target_pos, pen_color)
    
    def _draw_arrow_head(self, painter, start, end, color):
        """Desenha a ponta da seta"""
        line = end - start
        if line.manhattanLength() < 0.001:
            return
        
        # Normalizar a direção
        angle = _math.atan2(-line.y(), -line.x())
        arrow_p1 = end + QPointF(
            _math.cos(angle - _math.pi / 6) * self._arrow_size,
            _math.sin(angle - _math.pi / 6) * self._arrow_size
        )
        arrow_p2 = end + QPointF(
            _math.cos(angle + _math.pi / 6) * self._arrow_size,
            _math.sin(angle + _math.pi / 6) * self._arrow_size
        )
        
        # Desenhar triângulo de seta
        painter.setBrush(QBrush(color))
        painter.drawPolygon(QPolygonF([end, arrow_p1, arrow_p2]))


class BPMNAutoNode(QGraphicsItem):
    def __init__(self, node_id, text, shape, lane, signals, zoom, saved_texts=None):
        super().__init__()
        self.node_id = node_id
        self.text = text.strip()
        self.shape = shape
        self.lane = lane
        self.signals = signals
        self.zoom = zoom
        self._hovered = False
        
        # Dicionário para armazenar textos em múltiplas posições
        # Chaves: "inside", "below", "right", "left", "above"
        if saved_texts:
            # ← RESTAURAR Estado anterior (quando usuário moveu texto entre posições)
            self._texts = dict(saved_texts)
        else:
            # ← Inicializar normalmente (nó novo ou recém-criado)
            self._texts = {
                "inside": "",
                "below": text.strip(),  # Text principal fica em "below" por padrão
                "right": "",
                "left": "",
                "above": ""
            }

        t = T()
        ff = t.get("font_family_content", "Segoe UI")
        ff_ui = t.get("font_family", "Segoe UI")
        self._font_text = QFont(ff_ui, max(6, int(9 * zoom)), QFont.Bold)
        self._font_ph = QFont(ff_ui, max(5, int(8 * zoom)))
        self._font_ph.setItalic(True)
        self._font_btn = QFont(ff, max(6, int(10 * zoom)), QFont.Bold)

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _calc_size(self):
        fm = QFontMetrics(self._font_text)
        sample = self.text if self.text else "Nova Tarefa"
        if (
            "Evento" in self.shape
            or "Gateway" in self.shape
            or "Base de Dados" in self.shape
        ):
            self._w = self._h = 46 * self.zoom
        elif "Objeto" in self.shape:
            self._w = 40 * self.zoom
            self._h = 50 * self.zoom
        else:
            # Dynamic text wrap calculation for Tasks
            pad_x, pad_y = 20 * self.zoom, 16 * self.zoom
            max_w = 160 * self.zoom
            text_rect = fm.boundingRect(
                0, 0, int(max_w - pad_x), 1000, Qt.AlignCenter | Qt.TextWordWrap, sample
            )
            self._w = max(90 * self.zoom, text_rect.width() + pad_x)
            self._h = max(45 * self.zoom, text_rect.height() + pad_y)

    def width(self):
        return self._w

    def height(self):
        return self._h

    def boundingRect(self):
        m = 24 * self.zoom
        # Adicionar espaço extra para textos em todas as posições
        text_space = 70 * self.zoom  # espaço para textos acima, abaixo, esquerda, direita
        if (
            "Evento" in self.shape
            or "Gateway" in self.shape
            or "Objeto" in self.shape
            or "Base" in self.shape
        ):
            return QRectF(
                -m - text_space, 
                -m - text_space, 
                self._w + m * 2 + text_space * 2, 
                self._h + m * 2 + text_space * 2 + 30 * self.zoom
            )
        return QRectF(
            -m - text_space, 
            -m - text_space, 
            self._w + m * 2 + text_space * 2, 
            self._h + m * 2 + text_space * 2
        )

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0, 0, self._w, self._h)
        t = T()

        # Definir cores e espessuras antes do desenho
        border_color, pen_width = t["accent"], 2.0
        if "Início" in self.shape:
            border_color, pen_width = t["btn_add"], 3.0
        elif "Fim" in self.shape:
            border_color, pen_width = t["btn_del"], 4.0
        elif "Gateway" in self.shape:
            border_color = t.get("block_orange", t["accent"])
        elif "Intermediário" in self.shape:
            border_color = t.get("block_orange", t["accent"])

        # Fundo sólido — neo-brutalist ou convencional
        # Não aplicar _nb_paint_node para formas geométricas
        is_geometric_shape = any(
            keyword in self.shape 
            for keyword in ["Evento", "Gateway", "Base de Dados", "Objeto de Dados"]
        )
        
        bg_color = QColor(t.get("bg_card", "#FFFFFF" if t["name"] == "light" else "#1E1E1E")).name()
        
        if is_geometric_shape:
            # Usar helper para formas geométricas com estilo neo-brutalista
            _nb_paint_geometric_shape(
                painter, self.shape, r, border_color, bg_color, self.zoom, self._hovered
            )
        elif _is_nb(t):
            # Usar _nb_paint_node para formas retangulares
            _nb_paint_node(
                painter, r, self._hovered,
                border_color=border_color,
                shadow=False,
                radius=4,
            )
        else:
            bg_color_q = QColor(255, 255, 255) if t["name"] == "light" else QColor(30, 30, 30)
            painter.setBrush(QBrush(bg_color_q))
            painter.setPen(QPen(QColor(border_color), pen_width))
        
        # Desenhar detalhes (ícones internos) das formas geométricas
        # Notar: as formas base já foram desenhadas por _nb_paint_geometric_shape
        if "Evento" in self.shape:
            if "Intermediário" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QRectF(4, 4, self._w - 8, self._h - 8))
            if "Mensagem" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(
                    QRectF(self._w * 0.25, self._h * 0.3, self._w * 0.5, self._h * 0.4)
                )
                painter.drawLine(
                    QPointF(self._w * 0.25, self._h * 0.3),
                    QPointF(self._w * 0.5, self._h * 0.5),
                )
                painter.drawLine(
                    QPointF(self._w * 0.5, self._h * 0.5),
                    QPointF(self._w * 0.75, self._h * 0.3),
                )
            if "Tempo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    QRectF(self._w * 0.2, self._h * 0.2, self._w * 0.6, self._h * 0.6)
                )
                painter.drawLine(
                    QPointF(self._w * 0.5, self._h * 0.5),
                    QPointF(self._w * 0.5, self._h * 0.3),
                )
                painter.drawLine(
                    QPointF(self._w * 0.5, self._h * 0.5),
                    QPointF(self._w * 0.65, self._h * 0.5),
                )

        elif "Gateway" in self.shape:
            # Detalhes do gateway (cruzes, linhas)
            if "Exclusivo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 2.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(
                    QPointF(self._w * 0.35, self._h * 0.35),
                    QPointF(self._w * 0.65, self._h * 0.65),
                )
                painter.drawLine(
                    QPointF(self._w * 0.65, self._h * 0.35),
                    QPointF(self._w * 0.35, self._h * 0.65),
                )
            elif "Paralelo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 2.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(
                    QPointF(self._w * 0.5, self._h * 0.25),
                    QPointF(self._w * 0.5, self._h * 0.75),
                )
                painter.drawLine(
                    QPointF(self._w * 0.25, self._h * 0.5),
                    QPointF(self._w * 0.75, self._h * 0.5),
                )
            elif "Inclusivo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(
                    QRectF(self._w * 0.3, self._h * 0.3, self._w * 0.4, self._h * 0.4)
                )

        elif "Objeto de Dados" in self.shape:
            # Detalhes do objeto de dados (linhas de dobradura)
            painter.setPen(QPen(QColor(border_color), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawLine(
                QPointF(self._w * 0.7, 0), QPointF(self._w * 0.7, self._h * 0.3)
            )
            painter.drawLine(
                QPointF(self._w * 0.7, self._h * 0.3), QPointF(self._w, self._h * 0.3)
            )

        elif not is_geometric_shape:
            # Para formas retangulares (Tarefas)
            if not _is_nb(t):
                painter.drawRoundedRect(r, 4, 4)
            if "Usuário" in self.shape:
                painter.setPen(QColor(border_color))
                painter.setBrush(QBrush(QColor(border_color)))
                painter.drawEllipse(
                    QRectF(self._w * 0.05, self._h * 0.1, self._w * 0.1, self._h * 0.15)
                )
                painter.setBrush(Qt.NoBrush)
                painter.drawArc(
                    QRectF(
                        self._w * 0.02, self._h * 0.25, self._w * 0.16, self._h * 0.2
                    ),
                    0,
                    180 * 16,
                )
            elif "Serviço" in self.shape:
                painter.setPen(QColor(border_color))
                painter.setBrush(QBrush(QColor(border_color)))
                painter.drawEllipse(
                    QRectF(self._w * 0.05, self._h * 0.1, self._w * 0.1, self._h * 0.15)
                )
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(
                    QPointF(self._w * 0.05, self._h * 0.1),
                    QPointF(self._w * 0.15, self._h * 0.25),
                )
            elif "Subprocesso" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(
                    QRectF(
                        self._w / 2 - 6 * self.zoom,
                        self._h - 12 * self.zoom,
                        12 * self.zoom,
                        12 * self.zoom,
                    )
                )
                painter.drawLine(
                    QPointF(self._w / 2, self._h - 10 * self.zoom),
                    QPointF(self._w / 2, self._h - 2 * self.zoom),
                )
                painter.drawLine(
                    QPointF(self._w / 2 - 4 * self.zoom, self._h - 6 * self.zoom),
                    QPointF(self._w / 2 + 4 * self.zoom, self._h - 6 * self.zoom),
                )

        # ───────────────────────────────────────────────────────────────────
        # RENDERIZAR TEXTOS - Desativar clipping e salvar estado
        # ───────────────────────────────────────────────────────────────────
        painter.save()
        painter.setClipping(False)  # ← Desativa QUALQUER clipping anterior
        
        # Verificar se há algum texto para renderizar
        has_text = any(self._texts.values())
        painter.setFont(self._font_text if has_text else self._font_ph)
        painter.setPen(QColor(T()["text"] if has_text else T()["text_dim"]))
        
        # Renderizar textos de TODAS as 5 posições
        for position, text_content in self._texts.items():
            if not text_content:  # Se vazio, pula
                continue
            
            display_text = text_content
            
            if position == "inside":
                # Dentro da forma
                if self._w > 0 and self._h > 0:
                    text_rect = QRectF(r.left() + 4 * self.zoom, r.top() + 4 * self.zoom, 
                                       self._w - 8 * self.zoom, self._h - 8 * self.zoom)
                    painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, display_text)
            elif position == "right":
                # À direita da forma
                text_rect = QRectF(r.right() + 8 * self.zoom, r.top(), 
                                   100 * self.zoom, self._h + 20 * self.zoom)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, display_text)
            elif position == "left":
                # À esquerda da forma
                text_rect = QRectF(r.left() - 108 * self.zoom, r.top(), 
                                   100 * self.zoom, self._h + 20 * self.zoom)
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter | Qt.TextWordWrap, display_text)
            elif position == "above":
                # Acima da forma
                text_rect = QRectF(-self._w, -60 * self.zoom, self._w * 3, 50 * self.zoom)
                painter.drawText(text_rect, Qt.AlignBottom | Qt.AlignHCenter | Qt.TextWordWrap, display_text)
            elif position == "below":
                # Abaixo da forma (padrão)
                text_rect = QRectF(-self._w, self._h + 4 * self.zoom, self._w * 3, 60 * self.zoom)
                painter.drawText(text_rect, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, display_text)
        
        painter.restore()  # ← Restaurar estado completo

    def _draw_btn(self, painter, rect, label, color):
        t = T()
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor(t["glass_border"]), 1))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor(t["node_text"]))
        painter.drawText(rect, Qt.AlignCenter, label)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def _set_text_position(self, position):
        """Define/edita texto em uma posição específica"""
        text, ok = QInputDialog.getText(
            None,
            f"Adicionar/Editar Texto - {position.upper()}",
            f"Digite o texto para {position}:",
            text=self._texts.get(position, "")
        )
        if ok:
            self._texts[position] = text.strip()
            self.update()

    def _delete_text_position(self, position):
        """Deleta texto de uma posição específica"""
        self._texts[position] = ""
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))

    def contextMenuEvent(self, event):
        menu = QMenu()
        t_m = T()
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {t_m["bg_card"]}; color: {t_m["text"]}; border: 3px solid #000000;
                    border-radius: 0px; font-family: 'Segoe UI'; font-size: 13px;
                    font-weight: bold; padding: 5px; }}
            QMenu::item {{ padding: 8px 30px; border-radius: 0px; }}
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: #FFFFFF; }}
        """)

        m_add = menu.addMenu("➕ Adicionar Próxima Etapa")
        m_add.addAction("Nesta mesma baia").triggered.connect(
            lambda: self.signals.add_child.emit(self.node_id)
        )
        m_add.addAction("Em outra baia...").triggered.connect(
            lambda: self.signals.add_root.emit(-self.node_id)
        )  # Negativo indica conexão interdisciplinar

        m_link = menu.addAction("🔗 Interligar com outro Elemento")
        m_recall = menu.addAction("🔄↩ Criar Recall (Seta de Volta)")
        menu.addSeparator()

        m_lane = menu.addMenu("↕ Mover entre Baias")
        m_lane.addAction("⬆ Subir de Baia").triggered.connect(
            lambda: self.signals.move_lane.emit(self.node_id, -1)
        )
        m_lane.addAction("⬇ Descer de Baia").triggered.connect(
            lambda: self.signals.move_lane.emit(self.node_id, 1)
        )

        m_shape = menu.addAction("🔄 Mudar Formato")
        menu.addSeparator()
        
        m_edit_arrows = menu.addAction("🏷️ Editar Rótulos das Setas")
        
        menu.addSeparator()
        
        # Opção para ADICIONAR/EDITAR TEXTO em qualquer posição
        m_add_text = menu.addMenu("➕ Adicionar/Editar Texto")
        a_inside = m_add_text.addAction("📍 Dentro")
        a_below = m_add_text.addAction("📍 Abaixo")
        a_right = m_add_text.addAction("📍 À Direita")
        a_left = m_add_text.addAction("📍 À Esquerda")
        a_above = m_add_text.addAction("📍 Acima")
        menu.addSeparator()
        
        a_inside.triggered.connect(lambda: self._set_text_position("inside"))
        a_below.triggered.connect(lambda: self._set_text_position("below"))
        a_right.triggered.connect(lambda: self._set_text_position("right"))
        a_left.triggered.connect(lambda: self._set_text_position("left"))
        a_above.triggered.connect(lambda: self._set_text_position("above"))
        
        # Opção para DELETAR TEXTOS de posições específicas
        m_del_text = menu.addMenu("🗑 Excluir Texto")
        d_inside = m_del_text.addAction("🗑 Dentro")
        d_below = m_del_text.addAction("🗑 Abaixo")
        d_right = m_del_text.addAction("🗑 À Direita")
        d_left = m_del_text.addAction("🗑 À Esquerda")
        d_above = m_del_text.addAction("🗑 Acima")
        menu.addSeparator()
        
        d_inside.triggered.connect(lambda: self._delete_text_position("inside"))
        d_below.triggered.connect(lambda: self._delete_text_position("below"))
        d_right.triggered.connect(lambda: self._delete_text_position("right"))
        d_left.triggered.connect(lambda: self._delete_text_position("left"))
        d_above.triggered.connect(lambda: self._delete_text_position("above"))
        
        m_del = menu.addAction("🗑 Excluir Elemento")

        action = menu.exec_(event.screenPos())
        if action == m_link:
            self.signals.link_to.emit(self.node_id)
        elif action == m_recall:
            self.signals.recall_create.emit(self.node_id)
        elif action == m_shape:
            self.signals.change_shape.emit(self.node_id)
        elif action == m_edit_arrows:
            # Buscar parent widget para editar rótulos
            scene = self.scene()
            parent = scene.parent() if scene else None
            if parent and hasattr(parent, '_show_connection_labels_dialog'):
                parent._show_connection_labels_dialog(self.node_id)
        elif action == m_del:
            self.signals.delete_node.emit(self.node_id)


class BPMNFloatingEditor(QLineEdit):
    committed = pyqtSignal(object, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = None, "", False
        self._apply_fe_style()
        self.hide()

    def _apply_fe_style(self):
        t = T()
        self.setStyleSheet(f"""
            QLineEdit {{ background: #FFFFFF; color: #000000; border: 3px solid #000000;
                         border-radius: 0px; font-family: 'Courier New'; font-size: 10pt;
                         padding: 4px 10px; }}
        """)

    def open(self, target_id, current_text, scene_rect, view):
        self._apply_fe_style()
        self._target_id, self._original, self._done = target_id, current_text, False
        tl = view.mapFromScene(scene_rect.topLeft())
        w, h = max(150, int(scene_rect.width())), 32
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
        self.hide()
        self.committed.emit(
            self._target_id, (text if text is not None else self.text()).strip()
        )

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


class BPMNAutoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.zoom = 1.0
        self.next_id = 2
        self.project_name = "Projeto BPMN"
        self.pool_name = "Organização / Empresa"
        self.lanes = ["Setor Inicial"]
        self.node_dimensions, self.node_positions, self._scene_items = {}, {}, []
        self._is_editing = False  # ← Flag para proteger contra redraws durante edição
        
        # Dicionário para armazenar rótulos/textos das conexões
        # Chave: (source_id, target_id), Valor: texto do rótulo
        self._connection_labels = {}
        
        # Dicionário para armazenar textos em múltiplas posições (persistente entre redraws)
        # Chave: node_id, Valor: {"inside": "", "below": "", ...}
        self._node_text_positions = {}
        
        self.nodes = {
            1: {
                "text": "Início",
                "shape": "Evento Início",
                "level": 0,
                "lane": 0,
                "children": [],
                "parent": None,
                "recall_links": [],
            }
        }

        self.signals = BPMNNodeSignals()
        self.signals.commit_text.connect(self._on_commit)
        self.signals.add_child.connect(self._on_add_child)
        self.signals.add_sibling.connect(self._on_add_sibling)
        self.signals.delete_node.connect(self._on_delete)
        self.signals.edit_start.connect(self._on_edit_start)
        self.signals.move_lane.connect(self._on_move_lane)
        self.signals.change_shape.connect(self._on_change_shape)
        self.signals.add_root.connect(self._on_add_root)
        self.signals.link_to.connect(self._on_link_to)
        self.signals.recall_create.connect(self._on_recall_create)

        self._setup_ui()
        self._float_editor = BPMNFloatingEditor(self.view)
        self._float_editor.committed.connect(self._on_commit)
        self.update_zoom(1.2)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)
        self.refresh_theme()

    def refresh_theme(self):
        t = T()
        if hasattr(self, "view"):
            try:
                self.view.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                self.view.viewport().update()
            except Exception:
                pass
        if hasattr(self, "scene"):
            try:
                self.draw_diagram()
            except Exception:
                pass

    def _on_recall_create(self, node_id: int) -> None:
        """Handler para criação de recall arrow com dialog de seleção.
        
        Args:
            node_id: ID do nó que iniciou o recall
        """
        choices = []
        mapping = {}
        for nid, data in self.nodes.items():
            if nid != node_id:
                lbl = f"ID {nid} - {data['text'] or data['shape']}"
                choices.append(lbl)
                mapping[lbl] = nid
        if not choices:
            return
        
        item, ok = QInputDialog.getItem(
            self,
            "Criar Seta de Recall",
            "Selecione o elemento de destino (DOWN→LEFT→UP):",
            choices,
            0,
            False,
        )
        if ok and item:
            dest_id = mapping[item]
            self._add_recall_link(node_id, dest_id)

    def _add_recall_link(self, source_id: int, target_id: int) -> None:
        """Adiciona uma seta de recall entre dois nós.
        
        Args:
            source_id: ID do nó de origem
            target_id: ID do nó de destino
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return
        if source_id == target_id:
            return
        if "recall_links" not in self.nodes[source_id]:
            self.nodes[source_id]["recall_links"] = []
        if target_id not in self.nodes[source_id]["recall_links"]:
            self.nodes[source_id]["recall_links"].append(target_id)
            self.draw_diagram()

    def zoom_in(self):
        self.update_zoom(self.zoom * 1.15)

    def zoom_out(self):
        self.update_zoom(self.zoom / 1.15)

    def update_zoom(self, z):
        self.zoom = max(0.3, min(z, 3.0))
        self.draw_diagram()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3
            )

    def _create_shape_icon(self, shape_type):
        t = T()
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(_c("accent"), 2))
        painter.setBrush(QBrush(_c("bg_card")))
        r = QRectF(4, 4, 24, 24)
        if "Tarefa" in shape_type or "Subprocesso" in shape_type:
            painter.drawRoundedRect(r, 3, 3)
        elif "Início" in shape_type:
            painter.setPen(QPen(QColor(t["btn_add"]), 3))
            painter.drawEllipse(r)
        elif "Fim" in shape_type:
            painter.setPen(QPen(QColor(t["btn_del"]), 4))
            painter.drawEllipse(r)
        elif "Intermediário" in shape_type:
            painter.setPen(QPen(QColor(t.get("block_orange", t["accent"])), 2))
            painter.drawEllipse(r)
            painter.drawEllipse(QRectF(8, 8, 16, 16))
        elif "Gateway" in shape_type:
            painter.setPen(QPen(QColor(t.get("block_orange", t["accent"])), 2))
            painter.drawPolygon(
                QPolygonF(
                    [QPointF(16, 2), QPointF(30, 16), QPointF(16, 30), QPointF(2, 16)]
                )
            )
        elif "Dados" in shape_type:
            painter.drawRect(r)
        painter.end()
        return QIcon(pixmap)

    def _choose_shape(self):
        t_m = T()
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {t_m["bg_card"]}; color: {t_m["text"]}; border: 1px solid {t_m["accent"]};
                    font-family: 'Segoe UI'; font-size: 10pt; }}
            QMenu::item {{ padding: 8px 30px; }}
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: {t_m["bg_card"]}; }}
        """)
        m_task = menu.addMenu("⚙️ Tarefas & Atividades")
        a1 = m_task.addAction(self._create_shape_icon("Tarefa"), "Tarefa Simples")
        a2 = m_task.addAction(
            self._create_shape_icon("Tarefa de Usuário"), "Tarefa de Usuário"
        )
        a3 = m_task.addAction(
            self._create_shape_icon("Tarefa de Serviço"), "Tarefa de Serviço"
        )
        a4 = m_task.addAction(self._create_shape_icon("Subprocesso"), "Subprocesso [+]")

        m_evt = menu.addMenu("⚪ Eventos")
        e1 = m_evt.addAction(
            self._create_shape_icon("Evento Início"), "Evento de Início"
        )
        e2 = m_evt.addAction(
            self._create_shape_icon("Evento Intermediário"), "Evento Intermediário"
        )
        e3 = m_evt.addAction(
            self._create_shape_icon("Evento de Tempo"), "Evento de Tempo (Timer)"
        )
        e4 = m_evt.addAction(
            self._create_shape_icon("Evento de Mensagem"), "Evento de Mensagem"
        )
        e5 = m_evt.addAction(self._create_shape_icon("Evento Fim"), "Evento de Fim")

        m_gate = menu.addMenu("🔷 Gateways")
        g1 = m_gate.addAction(
            self._create_shape_icon("Gateway Exclusivo"), "Gateway Exclusivo (X)"
        )
        g2 = m_gate.addAction(
            self._create_shape_icon("Gateway Paralelo"), "Gateway Paralelo (+)"
        )
        g3 = m_gate.addAction(
            self._create_shape_icon("Gateway Inclusivo"), "Gateway Inclusivo (O)"
        )

        m_art = menu.addMenu("📄 Artefatos")
        d1 = m_art.addAction(
            self._create_shape_icon("Objeto de Dados"), "Objeto de Dados"
        )
        d2 = m_art.addAction(self._create_shape_icon("Base de Dados"), "Base de Dados")

        action_map = {
            a1: "Tarefa",
            a2: "Tarefa de Usuário",
            a3: "Tarefa de Serviço",
            a4: "Subprocesso",
            e1: "Evento Início",
            e2: "Evento Intermediário",
            e3: "Evento de Tempo",
            e4: "Evento de Mensagem",
            e5: "Evento Fim",
            g1: "Gateway Exclusivo",
            g2: "Gateway Paralelo",
            g3: "Gateway Inclusivo",
            d1: "Objeto de Dados",
            d2: "Base de Dados",
        }
        return action_map.get(menu.exec_(QCursor.pos()), None)

    def _add_new_lane(self):
        text, ok = QInputDialog.getText(self, "Nova Baia", "Nome do novo Setor/Raia:")
        if ok and text:
            self.lanes.append(text)
            self.draw_diagram()

    def _add_node_in_lane(self):
        if not self.lanes:
            return
        lane_choices = [f"Baia {i + 1}: {name}" for i, name in enumerate(self.lanes)]
        lane_item, ok = QInputDialog.getItem(
            self,
            "Selecionar Baia",
            "Em qual baia deseja inserir o novo elemento?",
            lane_choices,
            0,
            False,
        )
        if not ok:
            return
        lane_idx = lane_choices.index(lane_item)
        shape = self._choose_shape()
        if not shape:
            return
        new_id = self.next_id
        self.next_id += 1
        self.nodes[new_id] = {
            "text": "",
            "shape": shape,
            "level": 0,
            "lane": lane_idx,
            "children": [],
            "parent": None,
            "recall_links": [],
        }
        self.draw_diagram()
        if "Tarefa" in shape:
            QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_add_root(self, lane_idx):
        parent_id = None
        if lane_idx < 0:  # Caso de "Em outra baia..." via menu de contexto de um nó
            parent_id = abs(lane_idx)
            lane_choices = [
                f"Baia {i + 1}: {name}" for i, name in enumerate(self.lanes)
            ]
            lane_item, ok = QInputDialog.getItem(
                self,
                "Selecionar Baia de Destino",
                "Para qual baia deseja enviar o fluxo?",
                lane_choices,
                0,
                False,
            )
            if not ok:
                return
            lane_idx = lane_choices.index(lane_item)

        shape = self._choose_shape()
        if not shape:
            return
        new_id = self.next_id
        self.next_id += 1
        self.nodes[new_id] = {
            "text": "",
            "shape": shape,
            "level": 0,
            "lane": lane_idx,
            "children": [],
            "parent": parent_id,
            "recall_links": [],
        }

        if parent_id is not None:
            # Ajustar nível para ser depois do pai
            self.nodes[new_id]["level"] = self.nodes[parent_id]["level"] + 1
            self.nodes[parent_id]["children"].append(new_id)

        self.draw_diagram()
        if "Tarefa" in shape:
            QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_link_to(self, node_id):
        choices = []
        mapping = {}
        for nid, data in self.nodes.items():
            if nid != node_id:
                lbl = f"ID {nid} - {data['text'] or data['shape']}"
                choices.append(lbl)
                mapping[lbl] = nid
        if not choices:
            return
        item, ok = QInputDialog.getItem(
            self,
            "Interligar Item",
            "Selecione o destino da ligação:",
            choices,
            0,
            False,
        )
        if ok and item:
            dest_id = mapping[item]
            if "cross_links" not in self.nodes[node_id]:
                self.nodes[node_id]["cross_links"] = []
            if dest_id not in self.nodes[node_id]["cross_links"]:
                self.nodes[node_id]["cross_links"].append(dest_id)
                self.draw_diagram()

    def _on_move_lane(self, node_id, direction):
        new_lane = self.nodes[node_id]["lane"] + direction
        if 0 <= new_lane < len(self.lanes):
            self.nodes[node_id]["lane"] = new_lane
            self.draw_diagram()

    def _on_change_shape(self, node_id):
        shape = self._choose_shape()
        if shape:
            self.nodes[node_id]["shape"] = shape
            self.draw_diagram()

    def _on_commit(self, target_id, new_text):
        if isinstance(target_id, int) and target_id in self.nodes:
            self.nodes[target_id]["text"] = new_text
        elif target_id == "project":
            self.project_name = new_text
        elif target_id == "pool":
            self.pool_name = new_text
        elif isinstance(target_id, str) and target_id.startswith("lane_"):
            idx = int(target_id.split("_")[1])
            self.lanes[idx] = new_text
        
        self._is_editing = False  # ← Flag de edição desligada
        self.draw_diagram()

    def _on_edit_start(self, target_id):
        self._is_editing = True  # ← Flag de edição ligada
        if isinstance(target_id, int):
            if target_id not in self.node_positions:
                self._is_editing = False
                return
            nw, nh = self.node_dimensions[target_id]
            x, y = self.node_positions[target_id]
            shape = self.nodes[target_id]["shape"]
            if (
                "Evento" in shape
                or "Gateway" in shape
                or "Objeto" in shape
                or "Base" in shape
            ):
                edit_rect = QRectF(
                    x - nw * 1.5, y + nh / 2 + 4 * self.zoom, nw * 3, 30 * self.zoom
                )
            else:
                edit_rect = QRectF(x - nw / 2, y - nh / 2, nw, nh)
            self._float_editor.open(
                target_id, self.nodes[target_id]["text"], edit_rect, self.view
            )
        elif isinstance(target_id, str):
            for item in self.scene.items():
                if (
                    isinstance(item, HeaderItem)
                    and hasattr(item, "type_id")
                    and item.type_id == target_id
                ):
                    self._float_editor.open(
                        target_id, item.text, item.sceneBoundingRect(), self.view
                    )
                    break

    def _on_add_child(self, parent_id):
        shape = self._choose_shape()
        if not shape:
            return
        new_id = self.next_id
        self.next_id += 1
        self.nodes[new_id] = {
            "text": "",
            "shape": shape,
            "level": self.nodes[parent_id]["level"] + 1,
            "lane": self.nodes[parent_id]["lane"],
            "children": [],
            "parent": parent_id,
            "recall_links": [],
        }
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_diagram()
        if shape == "Tarefa":
            QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

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
            "shape": shape,
            "level": self.nodes[node_id]["level"],
            "lane": self.nodes[node_id]["lane"],
            "children": [],
            "parent": parent_id,
            "recall_links": [],
        }
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_diagram()
        if shape == "Tarefa":
            QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_delete(self, node_id):
        if (
            QMessageBox.question(
                self,
                "Excluir",
                "Excluir etapa e todo o caminho dependente?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            pid = self.nodes[node_id]["parent"]
            if pid is not None:
                self.nodes[pid]["children"].remove(node_id)
            self._remove_recursively(node_id)
            self.draw_diagram()

    def _remove_recursively(self, node_id):
        for cid in list(self.nodes[node_id]["children"]):
            self._remove_recursively(cid)
        del self.nodes[node_id]

    def calcular_grid(self):
        self.node_dimensions.clear()
        for nid in self.nodes:
            tmp = BPMNAutoNode(
                nid,
                self.nodes[nid]["text"],
                self.nodes[nid]["shape"],
                self.nodes[nid]["lane"],
                self.signals,
                self.zoom,
                saved_texts=None,  # ← Não restaurar em cálculo de tamanho
            )
            self.node_dimensions[nid] = (tmp.width(), tmp.height())

        grid = {}
        self.max_level = 0
        for nid, data in self.nodes.items():
            lvl, lane = data["level"], data["lane"]
            self.max_level = max(self.max_level, lvl)
            if lane not in grid:
                grid[lane] = {}
            if lvl not in grid[lane]:
                grid[lane][lvl] = []
            grid[lane][lvl].append(nid)

        self.lane_heights = []
        base_h = 380 * self.zoom
        node_spacing_y = 180 * self.zoom
        for lane_idx in range(len(self.lanes)):
            max_nodes_in_a_cell = 1
            if lane_idx in grid:
                for lvl, nodes_list in grid[lane_idx].items():
                    max_nodes_in_a_cell = max(max_nodes_in_a_cell, len(nodes_list))
            self.lane_heights.append(max(base_h, max_nodes_in_a_cell * node_spacing_y))

        self.node_positions.clear()
        level_width = 280 * self.zoom
        current_y = 0
        for lane_idx in range(len(self.lanes)):
            lane_h = self.lane_heights[lane_idx]
            if lane_idx in grid:
                for lvl, nodes_list in grid[lane_idx].items():
                    cell_x = lvl * level_width + level_width / 2
                    num_nodes = len(nodes_list)
                    for i, nid in enumerate(nodes_list):
                        node_y = current_y + (i + 0.5) * (lane_h / num_nodes)
                        self.node_positions[nid] = (cell_x, node_y)
            current_y += lane_h

        self.total_width = (self.max_level + 1) * level_width
        self.total_height = current_y

    def draw_pool(self):
        pool_x = -80 * self.zoom
        pool_y = 0
        w = self.total_width + 250 * self.zoom
        h = self.total_height

        proj_w = max(400 * self.zoom, len(self.project_name) * 15 * self.zoom)
        proj_h = 50 * self.zoom
        proj_x = pool_x + (w / 2) - (proj_w / 2)
        proj_y = pool_y - proj_h - (30 * self.zoom)

        item_proj = HeaderItem(
            QRectF(proj_x, proj_y, proj_w, proj_h),
            self.project_name,
            "project",
            self.signals,
            self.zoom,
            vertical=False,
        )
        self.scene.addItem(item_proj)
        self._scene_items.append(item_proj)

        path_p = QPainterPath()
        path_p.addRoundedRect(pool_x, pool_y, w, h, 20 * self.zoom, 20 * self.zoom)
        rect_item = self.scene.addPath(path_p, QPen(Qt.NoPen), QBrush(_c("bg_app")))
        rect_item.setZValue(-20)
        self._scene_items.append(rect_item)

        pool_header_w = 40 * self.zoom
        item_pool = HeaderItem(
            QRectF(pool_x - pool_header_w, pool_y, pool_header_w, h),
            self.pool_name,
            "pool",
            self.signals,
            self.zoom,
            vertical=True,
        )
        self.scene.addItem(item_pool)
        self._scene_items.append(item_pool)

        curr_y = pool_y
        for i, lane_name in enumerate(self.lanes):
            lh = self.lane_heights[i]
            # Use a path for lane background to match pool rounding at top/bottom
            lane_bg_key = "bg_card" if i % 2 == 0 else "bg_app"
            lane_path = QPainterPath()
            lx, ly, lw, lh_val = pool_x + 40 * self.zoom, curr_y, w - 40 * self.zoom, lh

            # If it's the first or last lane, we need some rounding to match the pool
            is_first = i == 0
            is_last = i == len(self.lanes) - 1
            rad = 20 * self.zoom

            if is_first or is_last:
                lane_path.addRoundedRect(lx, ly, lw, lh_val, rad, rad)
                # Flatten the 'inner' side
                if is_first and not is_last:
                    lane_path.addRect(lx, ly + rad, lw, lh_val - rad)
                elif is_last and not is_first:
                    lane_path.addRect(lx, ly, lw, lh_val - rad)
            else:
                lane_path.addRect(lx, ly, lw, lh_val)

            lane_rect_item = self.scene.addPath(
                lane_path, QPen(Qt.NoPen), QBrush(_c(lane_bg_key))
            )
            lane_rect_item.setZValue(-18)
            self._scene_items.append(lane_rect_item)

            if i > 0:
                # Remove dashed separator, use subtle space or zero-width line
                pass
            lane_header_w = 40 * self.zoom
            item_lane = HeaderItem(
                QRectF(pool_x, curr_y, lane_header_w, lh),
                lane_name,
                f"lane_{i}",
                self.signals,
                self.zoom,
                vertical=True,
            )
            self.scene.addItem(item_lane)
            self._scene_items.append(item_lane)
            curr_y += lh

        btn_h = 36 * self.zoom
        btn_rect = QRectF(pool_x, curr_y, w, btn_h)
        btn_add = AddLaneItem(
            btn_rect, self._add_node_in_lane, self.zoom, self._add_new_lane
        )
        self.scene.addItem(btn_add)
        self._scene_items.append(btn_add)

    def _edit_connection_label_dialog(self, source_id, target_id):
        """Abre diálogo para editar rótulo de uma conexão"""
        conn_key = (source_id, target_id)
        current_label = self._connection_labels.get(conn_key, "")
        
        new_label, ok = QInputDialog.getText(
            self,
            "Editar Rótulo da Seta",
            f"Digite o rótulo para a seta do elemento {source_id} → {target_id}:",
            text=current_label
        )
        
        if ok:
            if new_label.strip():
                self._connection_labels[conn_key] = new_label.strip()
            else:
                # Remover se vazio
                if conn_key in self._connection_labels:
                    del self._connection_labels[conn_key]
            
            # Redesenhar o diagrama
            self.draw_diagram()
    
    def _show_connection_labels_dialog(self, node_id):
        """Mostra diálogo para editar rótulos das setas que saem do nó"""
        if node_id not in self.nodes:
            return
        
        node = self.nodes[node_id]
        children = node.get("children", [])
        
        if not children:
            QMessageBox.information(self, "Sem Setas", f"O elemento {node_id} não tem conexões de saída.")
            return
        
        # Criar lista de opções
        choices = []
        for child_id in children:
            if child_id in self.nodes:
                choice_text = f"→ {child_id}: {self.nodes[child_id]['text'] or self.nodes[child_id]['shape']}"
                choices.append((choice_text, node_id, child_id))
        
        if not choices:
            return
        
        # Dialog para selecionar qual seta editar
        choice_texts = [c[0] for c in choices]
        choice_text, ok = QInputDialog.getItem(
            self,
            "Editar Rótulo de Seta",
            "Selecione a seta para editar:",
            choice_texts,
            0,
            False
        )
        
        if ok:
            _, source_id, target_id = next((c for c in choices if c[0] == choice_text), (None, None, None))
            if source_id is not None:
                self._edit_connection_label_dialog(source_id, target_id)

    def draw_diagram(self):
        # ← SALVAR estado de _texts de TODOS os nós ANTES de limpar a cena
        for item in self.scene.items():
            if isinstance(item, BPMNAutoNode):
                self._node_text_positions[item.node_id] = dict(item._texts)
        
        self._scene_items = []
        self.scene.clear()
        if not self.nodes:
            return
        self.calcular_grid()
        self.draw_pool()

        vh = self.view.viewport().height() or 800
        offset_y = vh / 2 - self.total_height / 2
        for n in self.node_positions:
            x, y = self.node_positions[n]
            self.node_positions[n] = (x, y + offset_y)
        for item in self._scene_items:
            item.moveBy(0, offset_y)

        # Recursively draw tree connections, and also handle independent roots
        for root_id in [n for n, data in self.nodes.items() if data["parent"] is None]:
            self._draw_connections(root_id)
        self._draw_nodes()
        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100)
        )

    def _draw_connections(self, node_id):
        px, py = self.node_positions[node_id]
        pw, _ = self.node_dimensions[node_id]
        t = T()

        # Conexões hierárquicas (filhos)
        for cid in self.nodes[node_id]["children"]:
            if cid not in self.node_positions:
                continue
            cx, cy = self.node_positions[cid]
            cw, _ = self.node_dimensions[cid]

            p1 = QPointF(px + pw / 2, py)
            p2 = QPointF(cx - cw / 2, cy)

            # Obter rótulo desta conexão (se existir)
            conn_key = (node_id, cid)
            label = self._connection_labels.get(conn_key, "")

            # SEMPRE usar BPMNConnectionLine para permitir clique e edição
            conn_line = BPMNConnectionLine(p1, p2, label, self.zoom, "solid", QColor(t["line"]))
            conn_line.connection_key = conn_key
            conn_line.parent_widget = self
            self._scene_items.append(conn_line)
            self.scene.addItem(conn_line)

            # Desenhar seta
            arrow_size = 10 * self.zoom
            poly = QPolygonF(
                [
                    p2,
                    QPointF(p2.x() - arrow_size, p2.y() - arrow_size / 2),
                    QPointF(p2.x() - arrow_size, p2.y() + arrow_size / 2),
                ]
            )
            self._scene_items.append(
                self.scene.addPolygon(poly, QPen(Qt.NoPen), QBrush(QColor(t["line"])))
            )
            self._draw_connections(cid)

        # Conexões cruzadas (links manuais)
        if "cross_links" in self.nodes[node_id]:
            pen_cross = QPen(
                QColor(t["accent_bright"]),
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

                p1_c = (
                    QPointF(px, py + self.node_dimensions[node_id][1] / 2)
                    if cy > py
                    else QPointF(px, py - self.node_dimensions[node_id][1] / 2)
                )
                p2_c = (
                    QPointF(cx, cy - self.node_dimensions[cid][1] / 2)
                    if cy > py
                    else QPointF(cx, cy + self.node_dimensions[cid][1] / 2)
                )

                # Obter rótulo desta conexão cruzada (se existir)
                conn_key = (node_id, cid)
                label = self._connection_labels.get(conn_key, "")

                # SEMPRE usar BPMNConnectionLine para permitir clique e edição
                conn_line = BPMNConnectionLine(p1_c, p2_c, label, self.zoom, "dash", QColor(t["accent_bright"]))
                conn_line.connection_key = conn_key
                conn_line.parent_widget = self
                self._scene_items.append(conn_line)
                self.scene.addItem(conn_line)

                arrow_size = 8 * self.zoom
                dir_y = -1 if cy < py else 1
                poly = QPolygonF(
                    [
                        p2_c,
                        QPointF(
                            p2_c.x() - arrow_size / 2, p2_c.y() - arrow_size * dir_y
                        ),
                        QPointF(
                            p2_c.x() + arrow_size / 2, p2_c.y() - arrow_size * dir_y
                        ),
                    ]
                )
                self._scene_items.append(
                    self.scene.addPolygon(
                        poly, QPen(Qt.NoPen), QBrush(QColor(t["accent_bright"]))
                    )
                )

        # Conexões de recall (setas DOWN→LEFT→UP automáticas)
        if "recall_links" in self.nodes[node_id]:
            for cid in self.nodes[node_id]["recall_links"]:
                if cid not in self.node_positions:
                    continue
                
                # Posição central do nó de origem
                origin_x, origin_y = self.node_positions[node_id]
                # Posição central do nó de destino
                target_x, target_y = self.node_positions[cid]
                
                # Criar e adicionar BPMNRecallArrow ao scene
                arrow = BPMNRecallArrow(
                    QPointF(origin_x, origin_y),
                    QPointF(target_x, target_y),
                    self.zoom
                )
                self.scene.addItem(arrow)
                self._scene_items.append(arrow)

    def _draw_nodes(self):
        for nid, (x, y) in self.node_positions.items():
            nw, nh = self.node_dimensions[nid]
            # ← Restaurar textos salvos (quando usuário moveu texto entre posições)
            saved_texts = self._node_text_positions.get(nid, None)
            item = BPMNAutoNode(
                nid,
                self.nodes[nid]["text"],
                self.nodes[nid]["shape"],
                self.nodes[nid]["lane"],
                self.signals,
                self.zoom,
                saved_texts=saved_texts,
            )
            item.setPos(x - nw / 2, y - nh / 2)
            self.scene.addItem(item)
            self._scene_items.append(item)

    def _export_scene(self, fmt):
        _export_view(self.view, fmt, self)


class _BPMNModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = BPMNAutoWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "BPMN MODELER — Guia Rapido\n\n"
            "O BPMN (Business Process Model and Notation) e o padrao "
            "internacional para modelagem de processos de negocio. "
            "Permite mapear fluxos de trabalho com eventos, tarefas, "
            "gateways e raias organizacionais.\n\n"
            "COMO USAR:\n"
            "• Clique com o botao direito sobre qualquer elemento para "
            "acessar opcoes: adicionar filho, irmao, mudar forma, "
            "mover entre raias, interligar ou criar seta de recall.\n"
            "• Use os botoes na base do diagrama para adicionar novos "
            "elementos em uma raia especifica ou criar novas raias.\n"
            "• Clique duas vezes em qualquer elemento para editar "
            "seu texto (nome da tarefa, evento, etc.).\n"
            "• Clique duas vezes nos cabecalhos para renomear o "
            "projeto, pool ou raias.\n\n"
            "CONEXOES:\n"
            "• Interligar (🔗): Cria ligacao com linha tracejada e curvatura automatica.\n"
            "• Seta de Recall (🔄↩): Cria seta com 3 segmentos (DOWN→LEFT→UP) para voltar a elementos anteriores.\n\n"
            "ELEMENTOS DISPONIVEIS:\n"
            "• Tarefas: Simples, de Usuario, de Servico, Subprocesso\n"
            "• Eventos: Inicio, Fim, Intermediario, Tempo, Mensagem\n"
            "• Gateways: Exclusivo (X), Paralelo (+), Inclusivo (O)\n"
            "• Artefatos: Objeto de Dados, Base de Dados\n\n"
            "NAVEGACAO:\n"
            "• Use Ctrl + Scroll do mouse para zoom.\n"
            "• Arraste o fundo para navegar pelo diagrama.\n"
            "• As conexoes entre raias sao roteadas automaticamente."
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
        return {
            "schema": "bpmn.v1",
            "nodes": self._inner.nodes,
            "lanes": self._inner.lanes,
            "next_id": self._inner.next_id,
        }

    def set_state(self, state):
        if not state:
            return
        # Aceita tanto formato antigo (sem schema) quanto o novo.
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try:
                k_int = int(k)
            except:
                k_int = k
            nodes[k_int] = v
        self._inner.nodes = (
            nodes
            if nodes
            else {
                1: {
                    "text": "Início",
                    "shape": "Evento Início",
                    "level": 0,
                    "lane": 0,
                    "children": [],
                    "parent": None,
                }
            }
        )
        self._inner.lanes = state.get("lanes", ["Processo Principal"])
        self._inner.next_id = state.get("next_id", 2)
        self._inner.draw_diagram()

    def refresh_theme(self):
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        return getattr(self._inner, "view", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _BPMNModule()
    w.setWindowTitle("BPMN Modeler — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())
