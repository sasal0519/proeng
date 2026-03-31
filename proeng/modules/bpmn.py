# -*- coding: utf-8 -*-
"""Módulo BPMN — Business Process Model and Notation 2.0."""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QListWidget, QListWidgetItem, QSplitter, QGraphicsPathItem, QMenu,
    QListView, QLineEdit, QLabel, QStackedWidget, QTextEdit,
    QGraphicsRectItem, QInputDialog, QFileDialog, QSizePolicy
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QPalette, QCursor, QPolygonF,
    QFont, QFontMetrics, QIcon, QPixmap, QPainterPath, QDrag, QLinearGradient
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QMimeData, QByteArray, QDataStream,
    QIODevice, QSize, QPoint, QTimer, pyqtSignal, QObject, QSizeF
)

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.utils import (_export_view, _c, _glass_grad)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule

import math as _math

class BPMNNodeSignals(QObject):
    commit_text  = pyqtSignal(object, str)
    add_child    = pyqtSignal(int)
    add_sibling  = pyqtSignal(int)
    delete_node  = pyqtSignal(int)
    edit_start   = pyqtSignal(object)
    change_shape = pyqtSignal(int)
    add_root     = pyqtSignal(int)
    link_to      = pyqtSignal(int)
    move_lane    = pyqtSignal(int, int)


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

    def hoverEnterEvent(self, e): self.hovered = True; self.update()
    def hoverLeaveEvent(self, e): self.hovered = False; self.update()

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
            menu.setStyleSheet(f"""
                QMenu {{ background-color: {t["bg_card"]}; color: {t["text"]}; border: 1px solid {t["accent"]};
                        font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }}
                QMenu::item {{ padding: 8px 30px; border-radius: 4px; }}
                QMenu::item:selected {{ background-color: {t["accent"]}; color: #FFFFFF; }}
            """)
            m_add = menu.addAction("➕ Inserir Evento Inicial nesta Baia")
            action = menu.exec_(event.screenPos())
            if action == m_add:
                lane_idx = int(self.type_id.split("_")[1])
                self.signals.add_root.emit(lane_idx)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setBrush(QBrush(_glass_grad(r, self.hovered)))
        painter.setPen(QPen(Qt.NoPen))
        rad = 20 if self.type_id == "pool" else 8
        painter.drawRoundedRect(r, rad, rad)

        # ── Accent strip logic (CLIPPED to round container) ──────────────────
        painter.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(r, rad, rad)
        painter.setClipPath(clip_path)

        sg = QLinearGradient(r.left(), 0, r.right(), 0)
        sg.setColorAt(0, _c("accent_bright") if self.type_id == "project" else _c("accent")); sg.setColorAt(0.5, QColor(0,0,0,0))
        painter.setBrush(QBrush(sg)); painter.setPen(Qt.NoPen)
        if self.vertical:
            painter.drawRect(QRectF(r.left(), r.top(), r.width(), 3))
        else:
            painter.drawRect(QRectF(r.left(), r.top(), r.width(), 4))
        painter.restore()

        # ── Text Drawing (Highest contrast) ──────────────────────────────────
        painter.setPen(QColor(T()["text"])) 
        font_size = 14 if self.type_id == "project" else 11
        font = QFont("Segoe UI", max(7, int(font_size * self.zoom)), QFont.Bold)
        painter.setFont(font)
        if self.vertical:
            painter.save()
            painter.translate(self.rect().x() + self.rect().width()/2, self.rect().y() + self.rect().height()/2)
            painter.rotate(-90)
            tr = QRectF(-self.rect().height()/2 + 10*self.zoom, -self.rect().width()/2 + 2*self.zoom, 
                         self.rect().height() - 20*self.zoom, self.rect().width() - 4*self.zoom)
            fm = QFontMetrics(font)
            elided = fm.elidedText(self.text, Qt.ElideRight, int(tr.width()))
            painter.drawText(tr, Qt.AlignCenter, elided)
            painter.restore()
        else:
            text_r = r.adjusted(15*self.zoom, 8*self.zoom, -15*self.zoom, -8*self.zoom)
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

    def hoverEnterEvent(self, e): self.hovered = True; self.update()
    def hoverLeaveEvent(self, e): self.hovered = False; self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            e.accept()
            # Clique esquerdo agora adiciona uma baia diretamente
            self.lane_callback()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        # 0. Body background with glassmorphism gradient
        grad = QLinearGradient(0, 0, 0, self.rect().height())
        bg_col1 = _c("bg_card2") if self.hovered else _c("bg_app")
        bg_col2 = _c("bg_app")
        grad.setColorAt(0, bg_col1)
        grad.setColorAt(1, bg_col2)
        
        pen_color = _c("accent_bright") if self.hovered else _c("accent_dim")
        # Refine lane addition button rounding
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(self.rect(), 20, 20)
        t = T()
        painter.setPen(QColor(t["accent_bright"] if self.hovered else t["text_dim"]))
        font = QFont("Segoe UI", max(7, int(11 * self.zoom)), QFont.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "⊞ Clique aqui para Adicionar Nova Baia (Setor)")


class BPMNAutoNode(QGraphicsItem):
    def __init__(self, node_id, text, shape, lane, signals, zoom):
        super().__init__()
        self.node_id  = node_id
        self.text     = text.strip()
        self.shape    = shape
        self.lane     = lane
        self.signals  = signals
        self.zoom     = zoom
        self._hovered = False

        self._font_text = QFont("Segoe UI", max(6, int(9 * zoom)), QFont.Bold)
        self._font_ph   = QFont("Segoe UI", max(5, int(8 * zoom)))
        self._font_ph.setItalic(True)
        self._font_btn  = QFont("Consolas", max(6, int(10 * zoom)), QFont.Bold)

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _calc_size(self):
        fm = QFontMetrics(self._font_text)
        sample = self.text if self.text else "Nova Tarefa"
        if "Evento" in self.shape or "Gateway" in self.shape or "Base de Dados" in self.shape:
            self._w = self._h = 46 * self.zoom
        elif "Objeto" in self.shape:
            self._w = 40 * self.zoom; self._h = 50 * self.zoom
        else:
            # Dynamic text wrap calculation for Tasks
            pad_x, pad_y = 20 * self.zoom, 16 * self.zoom
            max_w = 160 * self.zoom
            text_rect = fm.boundingRect(0, 0, int(max_w - pad_x), 1000, Qt.AlignCenter | Qt.TextWordWrap, sample)
            self._w = max(90 * self.zoom, text_rect.width() + pad_x)
            self._h = max(45 * self.zoom, text_rect.height() + pad_y)

    def width(self):  return self._w
    def height(self): return self._h

    def boundingRect(self):
        m = 24 * self.zoom
        if "Evento" in self.shape or "Gateway" in self.shape or "Objeto" in self.shape or "Base" in self.shape:
            return QRectF(-m, -m, self._w + m * 2, self._h + m * 2 + 30 * self.zoom)
        return QRectF(-m, -m, self._w + m * 2, self._h + m * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0, 0, self._w, self._h)
        t = T()
        
        # Definir cores e espessuras antes do desenho
        border_color, pen_width = t["accent"], 2.0
        if "Início" in self.shape:         border_color, pen_width = "#41CD52", 3.0
        elif "Fim" in self.shape:           border_color, pen_width = "#CC2222", 4.0
        elif "Gateway" in self.shape:       border_color = "#D4A017" if t["name"]=="dark" else "#B8860B"
        elif "Intermediário" in self.shape:   border_color = "#D4A017" if t["name"]=="dark" else "#B8860B"

        # Fundo sólido conforme solicitado (Branco ou Escuro)
        bg_color = QColor(255, 255, 255) if t["name"] == "light" else QColor(30, 30, 30)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(border_color), pen_width))

        if "Evento" in self.shape:
            painter.drawEllipse(r)
            if "Intermediário" in self.shape:
                painter.drawEllipse(QRectF(4, 4, self._w-8, self._h-8))
            if "Mensagem" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.drawRect(QRectF(self._w*0.25, self._h*0.3, self._w*0.5, self._h*0.4))
                painter.drawLine(QPointF(self._w*0.25, self._h*0.3), QPointF(self._w*0.5, self._h*0.5))
                painter.drawLine(QPointF(self._w*0.5, self._h*0.5), QPointF(self._w*0.75, self._h*0.3))
                painter.setPen(QPen(Qt.NoPen))
            if "Tempo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.drawEllipse(QRectF(self._w*0.2, self._h*0.2, self._w*0.6, self._h*0.6))
                painter.drawLine(QPointF(self._w*0.5, self._h*0.5), QPointF(self._w*0.5, self._h*0.3))
                painter.drawLine(QPointF(self._w*0.5, self._h*0.5), QPointF(self._w*0.65, self._h*0.5))
                painter.setPen(QPen(Qt.NoPen))

        elif "Gateway" in self.shape:
            painter.drawPolygon(QPolygonF([QPointF(self._w/2, 0), QPointF(self._w, self._h/2),
                                           QPointF(self._w/2, self._h), QPointF(0, self._h/2)]))
            if "Exclusivo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 2.5))
                painter.drawLine(QPointF(self._w*0.35, self._h*0.35), QPointF(self._w*0.65, self._h*0.65))
                painter.drawLine(QPointF(self._w*0.65, self._h*0.35), QPointF(self._w*0.35, self._h*0.65))
                painter.setPen(QPen(Qt.NoPen))
            elif "Paralelo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 2.5))
                painter.drawLine(QPointF(self._w*0.5, self._h*0.25), QPointF(self._w*0.5, self._h*0.75))
                painter.drawLine(QPointF(self._w*0.25, self._h*0.5), QPointF(self._w*0.75, self._h*0.5))
                painter.setPen(QPen(Qt.NoPen))
            elif "Inclusivo" in self.shape:
                painter.setPen(QPen(QColor(border_color), 1.5))
                painter.drawEllipse(QRectF(self._w*0.3, self._h*0.3, self._w*0.4, self._h*0.4))
                painter.setPen(QPen(Qt.NoPen))

        elif "Objeto de Dados" in self.shape:
            poly = QPolygonF([QPointF(0, 0), QPointF(self._w*0.7, 0), QPointF(self._w, self._h*0.3),
                              QPointF(self._w, self._h), QPointF(0, self._h)])
            painter.drawPolygon(poly)
            painter.drawLine(QPointF(self._w*0.7, 0), QPointF(self._w*0.7, self._h*0.3))
            painter.drawLine(QPointF(self._w*0.7, self._h*0.3), QPointF(self._w, self._h*0.3))

        elif "Base de Dados" in self.shape:
            painter.drawRect(QRectF(0, self._h*0.15, self._w, self._h*0.7))
            painter.drawEllipse(QRectF(0, 0, self._w, self._h*0.3))
            painter.drawEllipse(QRectF(0, self._h*0.7, self._w, self._h*0.3))

        else:
            painter.drawRoundedRect(r, 4, 4)
            if "Usuário" in self.shape:
                painter.drawEllipse(QRectF(self._w*0.05, self._h*0.1, self._w*0.1, self._h*0.15))
                painter.drawArc(QRectF(self._w*0.02, self._h*0.25, self._w*0.16, self._h*0.2), 0, 180*16)
            elif "Serviço" in self.shape:
                painter.drawEllipse(QRectF(self._w*0.05, self._h*0.1, self._w*0.1, self._h*0.15))
                painter.drawLine(QPointF(self._w*0.05, self._h*0.1), QPointF(self._w*0.15, self._h*0.25))
            elif "Subprocesso" in self.shape:
                painter.drawRect(QRectF(self._w/2 - 6*self.zoom, self._h - 12*self.zoom, 12*self.zoom, 12*self.zoom))
                painter.drawLine(QPointF(self._w/2, self._h - 10*self.zoom), QPointF(self._w/2, self._h - 2*self.zoom))
                painter.drawLine(QPointF(self._w/2 - 4*self.zoom, self._h - 6*self.zoom), QPointF(self._w/2 + 4*self.zoom, self._h - 6*self.zoom))

        painter.setFont(self._font_text if self.text else self._font_ph)
        painter.setPen(QColor(T()["text"] if self.text else T()["text_dim"]))
        display_text = self.text if self.text else "✎ Nomear"
        if "Evento" in self.shape or "Gateway" in self.shape or "Objeto" in self.shape or "Base" in self.shape:
            # Labels below the shape - use word wrap and high-Z for visibility
            text_rect = QRectF(-self._w, self._h + 4*self.zoom, self._w*3, 60*self.zoom)
            painter.drawText(text_rect, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, display_text)
        else:
            # Task text - precisely centered with padding
            px = 8 * self.zoom
            inner = r.adjusted(px, 4*self.zoom, -px, -4*self.zoom)
            painter.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, display_text)

    def _draw_btn(self, painter, rect, label, color):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor("#FF6666"), 1))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor("#FAE8E8"))
        painter.drawText(rect, Qt.AlignCenter, label)

    def hoverEnterEvent(self, event): self._hovered = True; self.update()
    def hoverLeaveEvent(self, event): self._hovered = False; self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton: return
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))

    def contextMenuEvent(self, event):
        menu = QMenu()
        t_m = T()
        menu.setStyleSheet(f"""
            QMenu {{ background-color: {t_m["bg_card"]}; color: {t_m["text"]}; border: 1px solid {t_m["accent"]};
                    font-family: 'Segoe UI'; font-size: 13px; font-weight: bold; padding: 5px; }}
            QMenu::item {{ padding: 8px 30px; border-radius: 4px; }}
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: #FFFFFF; }}
        """)
        
        m_add = menu.addMenu("➕ Adicionar Próxima Etapa")
        m_add.addAction("Nesta mesma baia").triggered.connect(lambda: self.signals.add_child.emit(self.node_id))
        m_add.addAction("Em outra baia...").triggered.connect(lambda: self.signals.add_root.emit(-self.node_id)) # Negativo indica conexão interdisciplinar
        
        m_link = menu.addAction("🔗 Interligar com outro Elemento")
        menu.addSeparator()
        
        m_lane = menu.addMenu("↕ Mover entre Baias")
        m_lane.addAction("⬆ Subir de Baia").triggered.connect(lambda: self.signals.move_lane.emit(self.node_id, -1))
        m_lane.addAction("⬇ Descer de Baia").triggered.connect(lambda: self.signals.move_lane.emit(self.node_id, 1))
        
        m_shape = menu.addAction("🔄 Mudar Formato")
        menu.addSeparator()
        m_del = menu.addAction("🗑 Excluir Elemento")
        
        action = menu.exec_(event.screenPos())
        if action == m_link:  self.signals.link_to.emit(self.node_id)
        elif action == m_shape: self.signals.change_shape.emit(self.node_id)
        elif action == m_del:   self.signals.delete_node.emit(self.node_id)


class BPMNFloatingEditor(QLineEdit):
    committed = pyqtSignal(object, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = None, "", False
        self._apply_fe_style()
        self.hide()

    def _apply_fe_style(self):
        try:
            t = T()
            self.setStyleSheet(f"""
                QLineEdit {{ background: {t["bg_card2"]}; color: {t["text"]};
                             border: 2px solid {t["accent_bright"]}; border-radius: 6px;
                             font-family: 'Segoe UI'; font-size: 10pt; padding: 4px 10px; }}
            """)
        except Exception:
            self.setStyleSheet("QLineEdit { background:#2A0F0F; color:#FAE8E8; border:2px solid #CC2222; border-radius:5px; font-size:10pt; padding:4px 10px; }")

    def open(self, target_id, current_text, scene_rect, view):
        self._apply_fe_style()
        self._target_id, self._original, self._done = target_id, current_text, False
        tl = view.mapFromScene(scene_rect.topLeft())
        w, h = max(150, int(scene_rect.width())), 32
        self.setGeometry(tl.x(), tl.y() + int(scene_rect.height() / 2) - h // 2, w, h)
        self.setText(current_text)
        self.selectAll(); self.show(); self.raise_(); self.setFocus()

    def _commit(self, text=None):
        if self._done: return
        self._done = True
        self.hide()
        self.committed.emit(self._target_id, (text if text is not None else self.text()).strip())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter): self._commit()
        elif event.key() == Qt.Key_Escape: self._commit(self._original)
        else: super().keyPressEvent(event)

    def focusOutEvent(self, event): self._commit(); super().focusOutEvent(event)


class BPMNAutoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.zoom = 1.0
        self.next_id = 2
        self.project_name = "Projeto BPMN"
        self.pool_name    = "Organização / Empresa"
        self.lanes        = ["Setor Inicial"]
        self.node_dimensions, self.node_positions, self._scene_items = {}, {}, []
        self.nodes = {1: {"text": "Início", "shape": "Evento Início", "level": 0, "lane": 0, "children": [], "parent": None}}

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

        self._setup_ui()
        self._float_editor = BPMNFloatingEditor(self.view)
        self._float_editor.committed.connect(self._on_commit)
        self.update_zoom(1.2)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar_bpmn = QWidget(); self._toolbar_bpmn.setFixedHeight(44)
        toolbar = self._toolbar_bpmn
        tb = QHBoxLayout(toolbar)

        self._bpmn_title_lbl = QLabel("🔀  BPMN Modeler — Pools, Lanes & Fluxos")
        self._bpmn_title_lbl.setMaximumWidth(480)
        tb.addWidget(self._bpmn_title_lbl); tb.addStretch()

        self._bpmn_btns = []
        for lbl, fn in [("🔍−", lambda *a: self.zoom_out()), ("🔍+", lambda *a: self.zoom_in()), ("⟳ 100%", lambda *a: self.update_zoom(1.0))]:
            b = QPushButton(lbl); b.clicked.connect(fn); tb.addWidget(b); self._bpmn_btns.append(b)

        self._bpmn_exp_btns = []
        for lbl, key in [("📄 PDF","pdf"),("🖼 PNG","png")]:
            be = QPushButton(lbl); be.clicked.connect(lambda _,k=key: self._export_scene(k))
            tb.addWidget(be); self._bpmn_exp_btns.append(be)

        layout.addWidget(toolbar)
        self.scene = QGraphicsScene()
        self.view  = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)
        self.refresh_theme()

    def refresh_theme(self):
        t = T()
        self._toolbar_bpmn.setStyleSheet(f"""
            QWidget {{ background: {t["toolbar_bg"]}; border-bottom: 1px solid {t["accent"]}; }}
        """)
        self._bpmn_title_lbl.setStyleSheet(f"""
            color: {t["accent_bright"]}; font-family: 'Segoe UI';
            font-size: 12px; font-weight: bold; background: transparent;
        """)
        btn_s = f"""QPushButton {{ background: {t["toolbar_btn"]}; color: {t["text"]};
            border: 1px solid {t["accent_dim"]}; border-radius:5px; padding:4px 12px; font-weight:bold; }}
            QPushButton:hover {{ background: {t["toolbar_btn_h"]}; border-color:{t["accent"]}; color:{t["accent_bright"]}; }}"""
        exp_s = f"""QPushButton {{ background: {t["toolbar_btn"]}; color: {t["accent"]};
            border: 1px solid {t["accent_dim"]}; border-radius:5px; padding:4px 12px; font-weight:bold; }}
            QPushButton:hover {{ background: {t["accent"]}; color: white; }}"""
        for b in self._bpmn_btns: b.setStyleSheet(btn_s)
        for b in self._bpmn_exp_btns: b.setStyleSheet(exp_s)
        if hasattr(self, 'view'):
            try:
                self.view.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                self.view.viewport().update()
            except Exception: pass
        if hasattr(self, 'scene'):
            try: self.draw_diagram()
            except Exception: pass

    def zoom_in(self): self.update_zoom(self.zoom * 1.15)
    def zoom_out(self): self.update_zoom(self.zoom / 1.15)
    def update_zoom(self, z): self.zoom = max(0.3, min(z, 3.0)); self.draw_diagram()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3)

    def _create_shape_icon(self, shape_type):
        pixmap = QPixmap(32, 32); pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(_c("accent"), 2)); painter.setBrush(QBrush(_c("bg_card")))
        r = QRectF(4, 4, 24, 24)
        if "Tarefa" in shape_type or "Subprocesso" in shape_type:
            painter.drawRoundedRect(r, 3, 3)
        elif "Início" in shape_type:
            painter.setPen(QPen(QColor("#41CD52"), 3)); painter.drawEllipse(r)
        elif "Fim" in shape_type:
            painter.setPen(QPen(QColor("#CC2222"), 4)); painter.drawEllipse(r)
        elif "Intermediário" in shape_type:
            painter.setPen(QPen(QColor("#D4A017"), 2)); painter.drawEllipse(r); painter.drawEllipse(QRectF(8,8,16,16))
        elif "Gateway" in shape_type:
            painter.setPen(QPen(QColor("#D4A017"), 2))
            painter.drawPolygon(QPolygonF([QPointF(16, 2), QPointF(30, 16), QPointF(16, 30), QPointF(2, 16)]))
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
            QMenu::item:selected {{ background-color: {t_m["accent"]}; color: #0D0D0D; }}
        """)
        m_task = menu.addMenu("⚙️ Tarefas & Atividades")
        a1 = m_task.addAction(self._create_shape_icon("Tarefa"),           "Tarefa Simples")
        a2 = m_task.addAction(self._create_shape_icon("Tarefa de Usuário"), "Tarefa de Usuário")
        a3 = m_task.addAction(self._create_shape_icon("Tarefa de Serviço"), "Tarefa de Serviço")
        a4 = m_task.addAction(self._create_shape_icon("Subprocesso"),       "Subprocesso [+]")

        m_evt = menu.addMenu("⚪ Eventos")
        e1 = m_evt.addAction(self._create_shape_icon("Evento Início"),        "Evento de Início")
        e2 = m_evt.addAction(self._create_shape_icon("Evento Intermediário"),  "Evento Intermediário")
        e3 = m_evt.addAction(self._create_shape_icon("Evento de Tempo"),       "Evento de Tempo (Timer)")
        e4 = m_evt.addAction(self._create_shape_icon("Evento de Mensagem"),    "Evento de Mensagem")
        e5 = m_evt.addAction(self._create_shape_icon("Evento Fim"),            "Evento de Fim")

        m_gate = menu.addMenu("🔷 Gateways")
        g1 = m_gate.addAction(self._create_shape_icon("Gateway Exclusivo"), "Gateway Exclusivo (X)")
        g2 = m_gate.addAction(self._create_shape_icon("Gateway Paralelo"),  "Gateway Paralelo (+)")
        g3 = m_gate.addAction(self._create_shape_icon("Gateway Inclusivo"), "Gateway Inclusivo (O)")

        m_art = menu.addMenu("📄 Artefatos")
        d1 = m_art.addAction(self._create_shape_icon("Objeto de Dados"), "Objeto de Dados")
        d2 = m_art.addAction(self._create_shape_icon("Base de Dados"),   "Base de Dados")

        action_map = {
            a1: "Tarefa", a2: "Tarefa de Usuário", a3: "Tarefa de Serviço", a4: "Subprocesso",
            e1: "Evento Início", e2: "Evento Intermediário", e3: "Evento de Tempo",
            e4: "Evento de Mensagem", e5: "Evento Fim",
            g1: "Gateway Exclusivo", g2: "Gateway Paralelo", g3: "Gateway Inclusivo",
            d1: "Objeto de Dados", d2: "Base de Dados"
        }
        return action_map.get(menu.exec_(QCursor.pos()), None)

    def _add_new_lane(self):
        text, ok = QInputDialog.getText(self, "Nova Baia", "Nome do novo Setor/Raia:")
        if ok and text: self.lanes.append(text); self.draw_diagram()

    def _add_node_in_lane(self):
        if not self.lanes:
            return
        lane_choices = [f"Baia {i+1}: {name}" for i, name in enumerate(self.lanes)]
        lane_item, ok = QInputDialog.getItem(
            self, "Selecionar Baia",
            "Em qual baia deseja inserir o novo elemento?",
            lane_choices, 0, False)
        if not ok: return
        lane_idx = lane_choices.index(lane_item)
        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {
            "text": "", "shape": shape,
            "level": 0, "lane": lane_idx,
            "children": [], "parent": None
        }
        self.draw_diagram()
        if "Tarefa" in shape:
            QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_add_root(self, lane_idx):
        parent_id = None
        if lane_idx < 0: # Caso de "Em outra baia..." via menu de contexto de um nó
            parent_id = abs(lane_idx)
            lane_choices = [f"Baia {i+1}: {name}" for i, name in enumerate(self.lanes)]
            lane_item, ok = QInputDialog.getItem(self, "Selecionar Baia de Destino",
                                                "Para qual baia deseja enviar o fluxo?", lane_choices, 0, False)
            if not ok: return
            lane_idx = lane_choices.index(lane_item)

        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {"text": "", "shape": shape, "level": 0, "lane": lane_idx, "children": [], "parent": parent_id}
        
        if parent_id is not None:
             # Ajustar nível para ser depois do pai
             self.nodes[new_id]["level"] = self.nodes[parent_id]["level"] + 1
             self.nodes[parent_id]["children"].append(new_id)

        self.draw_diagram()
        if "Tarefa" in shape: QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_link_to(self, node_id):
        choices = []
        mapping = {}
        for nid, data in self.nodes.items():
            if nid != node_id:
                lbl = f"ID {nid} - {data['text'] or data['shape']}"
                choices.append(lbl)
                mapping[lbl] = nid
        if not choices: return
        item, ok = QInputDialog.getItem(self, "Interligar Item", "Selecione o destino da ligação:", choices, 0, False)
        if ok and item:
            dest_id = mapping[item]
            if "cross_links" not in self.nodes[node_id]: self.nodes[node_id]["cross_links"] = []
            if dest_id not in self.nodes[node_id]["cross_links"]:
                self.nodes[node_id]["cross_links"].append(dest_id)
                self.draw_diagram()

    def _on_move_lane(self, node_id, direction):
        new_lane = self.nodes[node_id]["lane"] + direction
        if 0 <= new_lane < len(self.lanes):
            self.nodes[node_id]["lane"] = new_lane; self.draw_diagram()

    def _on_change_shape(self, node_id):
        shape = self._choose_shape()
        if shape: self.nodes[node_id]["shape"] = shape; self.draw_diagram()

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
        self.draw_diagram()

    def _on_edit_start(self, target_id):
        if isinstance(target_id, int):
            if target_id not in self.node_positions: return
            nw, nh = self.node_dimensions[target_id]; x, y = self.node_positions[target_id]
            shape = self.nodes[target_id]["shape"]
            if "Evento" in shape or "Gateway" in shape or "Objeto" in shape or "Base" in shape:
                edit_rect = QRectF(x - nw*1.5, y + nh/2 + 4*self.zoom, nw*3, 30*self.zoom)
            else:
                edit_rect = QRectF(x - nw/2, y - nh/2, nw, nh)
            self._float_editor.open(target_id, self.nodes[target_id]["text"], edit_rect, self.view)
        elif isinstance(target_id, str):
            for item in self.scene.items():
                if isinstance(item, HeaderItem) and hasattr(item, 'type_id') and item.type_id == target_id:
                    self._float_editor.open(target_id, item.text, item.sceneBoundingRect(), self.view)
                    break

    def _on_add_child(self, parent_id):
        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {"text": "", "shape": shape, "level": self.nodes[parent_id]["level"] + 1,
                               "lane": self.nodes[parent_id]["lane"], "children": [], "parent": parent_id}
        self.nodes[parent_id]["children"].append(new_id); self.draw_diagram()
        if shape == "Tarefa": QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_add_sibling(self, node_id):
        parent_id = self.nodes[node_id]["parent"]
        if parent_id is None: return
        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {"text": "", "shape": shape, "level": self.nodes[node_id]["level"],
                               "lane": self.nodes[node_id]["lane"], "children": [], "parent": parent_id}
        self.nodes[parent_id]["children"].append(new_id); self.draw_diagram()
        if shape == "Tarefa": QTimer.singleShot(60, lambda: self._on_edit_start(new_id))

    def _on_delete(self, node_id):
        if QMessageBox.question(self, "Excluir", "Excluir etapa e todo o caminho dependente?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            pid = self.nodes[node_id]["parent"]
            if pid is not None: self.nodes[pid]["children"].remove(node_id)
            self._remove_recursively(node_id); self.draw_diagram()

    def _remove_recursively(self, node_id):
        for cid in list(self.nodes[node_id]["children"]): self._remove_recursively(cid)
        del self.nodes[node_id]

    def calcular_grid(self):
        self.node_dimensions.clear()
        for nid in self.nodes:
            tmp = BPMNAutoNode(nid, self.nodes[nid]["text"], self.nodes[nid]["shape"],
                               self.nodes[nid]["lane"], self.signals, self.zoom)
            self.node_dimensions[nid] = (tmp.width(), tmp.height())

        grid = {}
        self.max_level = 0
        for nid, data in self.nodes.items():
            lvl, lane = data['level'], data['lane']
            self.max_level = max(self.max_level, lvl)
            if lane not in grid: grid[lane] = {}
            if lvl not in grid[lane]: grid[lane][lvl] = []
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

        self.total_width  = (self.max_level + 1) * level_width
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

        item_proj = HeaderItem(QRectF(proj_x, proj_y, proj_w, proj_h),
                               self.project_name, "project", self.signals, self.zoom, vertical=False)
        self.scene.addItem(item_proj); self._scene_items.append(item_proj)

        path_p = QPainterPath()
        path_p.addRoundedRect(pool_x, pool_y, w, h, 20*self.zoom, 20*self.zoom)
        rect_item = self.scene.addPath(path_p, QPen(Qt.NoPen), QBrush(_c("bg_app")))
        rect_item.setZValue(-20); self._scene_items.append(rect_item)

        pool_header_w = 40 * self.zoom
        item_pool = HeaderItem(QRectF(pool_x - pool_header_w, pool_y, pool_header_w, h),
                               self.pool_name, "pool", self.signals, self.zoom, vertical=True)
        self.scene.addItem(item_pool); self._scene_items.append(item_pool)

        curr_y = pool_y
        for i, lane_name in enumerate(self.lanes):
            lh = self.lane_heights[i]
            # Use a path for lane background to match pool rounding at top/bottom
            lane_bg_key = "bg_card" if i % 2 == 0 else "bg_app"
            lane_path = QPainterPath()
            lx, ly, lw, lh_val = pool_x + 40 * self.zoom, curr_y, w - 40 * self.zoom, lh
            
            # If it's the first or last lane, we need some rounding to match the pool
            is_first = (i == 0)
            is_last  = (i == len(self.lanes) - 1)
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
                
            lane_rect_item = self.scene.addPath(lane_path, QPen(Qt.NoPen), QBrush(_c(lane_bg_key)))
            lane_rect_item.setZValue(-18); self._scene_items.append(lane_rect_item)

            if i > 0:
                # Remove dashed separator, use subtle space or zero-width line
                pass
            lane_header_w = 40 * self.zoom
            item_lane = HeaderItem(QRectF(pool_x, curr_y, lane_header_w, lh),
                                   lane_name, f"lane_{i}", self.signals, self.zoom, vertical=True)
            self.scene.addItem(item_lane); self._scene_items.append(item_lane)
            curr_y += lh

        btn_h    = 36 * self.zoom
        btn_rect = QRectF(pool_x, curr_y, w, btn_h)
        btn_add  = AddLaneItem(btn_rect, self._add_node_in_lane, self.zoom, self._add_new_lane)
        self.scene.addItem(btn_add); self._scene_items.append(btn_add)

    def draw_diagram(self):
        self._scene_items = []
        self.scene.clear()
        if not self.nodes: return
        self.calcular_grid()
        self.draw_pool()

        vh = self.view.viewport().height() or 800
        offset_y = vh / 2 - self.total_height / 2
        for n in self.node_positions:
            x, y = self.node_positions[n]
            self.node_positions[n] = (x, y + offset_y)
        for item in self._scene_items: item.moveBy(0, offset_y)

        # Recursively draw tree connections, and also handle independent roots
        for root_id in [n for n, data in self.nodes.items() if data["parent"] is None]:
            self._draw_connections(root_id)
        self._draw_nodes()
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-100, -100, 100, 100))

    def _draw_connections(self, node_id):
        px, py = self.node_positions[node_id]
        pw, _  = self.node_dimensions[node_id]
        t = T()
        
        # Conexões hierárquicas (filhos)
        pen = QPen(QColor(t["line"]), max(1, int(2 * self.zoom)), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        for cid in self.nodes[node_id]["children"]:
            if cid not in self.node_positions: continue
            cx, cy = self.node_positions[cid]
            cw, _  = self.node_dimensions[cid]
            
            p1 = QPointF(px + pw / 2, py)
            p2 = QPointF(cx - cw / 2, cy)
            
            path = QPainterPath()
            path.moveTo(p1)
            
            # Se estão em raias diferentes, faz o roteamento em "S"
            if self.nodes[node_id]["lane"] != self.nodes[cid]["lane"]:
                mid_x = px + pw/2 + 40*self.zoom
                path.lineTo(mid_x, py)
                path.lineTo(mid_x, cy)
            else:
                mid_x = (p1.x() + p2.x()) / 2
                path.lineTo(mid_x, py)
                path.lineTo(mid_x, cy)
            
            path.lineTo(p2)
            self._scene_items.append(self.scene.addPath(path, pen))
            
            arrow_size = 10 * self.zoom
            poly = QPolygonF([p2, QPointF(p2.x() - arrow_size, p2.y() - arrow_size/2),
                              QPointF(p2.x() - arrow_size, p2.y() + arrow_size/2)])
            self._scene_items.append(self.scene.addPolygon(poly, QPen(Qt.NoPen), QBrush(QColor(t["line"]))))
            self._draw_connections(cid)

        # Conexões cruzadas (links manuais)
        if "cross_links" in self.nodes[node_id]:
            pen_cross = QPen(QColor(t["accent_bright"]), max(1.5, int(2 * self.zoom)), Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
            for cid in self.nodes[node_id]["cross_links"]:
                if cid not in self.node_positions: continue
                cx, cy = self.node_positions[cid]
                cw, _  = self.node_dimensions[cid]
                
                p1_c = QPointF(px, py + self.node_dimensions[node_id][1]/2) if cy > py else QPointF(px, py - self.node_dimensions[node_id][1]/2)
                p2_c = QPointF(cx, cy - self.node_dimensions[cid][1]/2) if cy > py else QPointF(cx, cy + self.node_dimensions[cid][1]/2)
                
                path = QPainterPath()
                path.moveTo(p1_c)
                mid_y = (p1_c.y() + p2_c.y()) / 2
                path.lineTo(p1_c.x(), mid_y)
                path.lineTo(p2_c.x(), mid_y)
                path.lineTo(p2_c)
                self._scene_items.append(self.scene.addPath(path, pen_cross))

                arrow_size = 8 * self.zoom
                dir_y = -1 if cy < py else 1
                poly = QPolygonF([p2_c, QPointF(p2_c.x() - arrow_size/2, p2_c.y() - arrow_size*dir_y), 
                                  QPointF(p2_c.x() + arrow_size/2, p2_c.y() - arrow_size*dir_y)])
                self._scene_items.append(self.scene.addPolygon(poly, QPen(Qt.NoPen), QBrush(QColor(t["accent_bright"]))))

    def _draw_nodes(self):
        for nid, (x, y) in self.node_positions.items():
            nw, nh = self.node_dimensions[nid]
            item = BPMNAutoNode(nid, self.nodes[nid]["text"], self.nodes[nid]["shape"],
                                self.nodes[nid]["lane"], self.signals, self.zoom)
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
            "• Clique com o Botão Direito sobre as etapas para adicionar, mudar forma ou conectar elementos.\n"
            "• As conexões entre baias são roteadas automaticamente.\n"
            "• Clique esquerdo abaixo da última baia para adicionar novas raias horizontais.\n"
            "• Use o menu 'Exibir' para Zoom e ajuste de escala."
        )
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
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
            "next_id": self._inner.next_id
        }

    def set_state(self, state):
        if not state:
            return
        # Aceita tanto formato antigo (sem schema) quanto o novo.
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try: k_int = int(k)
            except: k_int = k
            nodes[k_int] = v
        self._inner.nodes = nodes if nodes else {
            1: {"text": "Início", "shape": "Evento Início", "level": 0, "lane": 0, "children": [], "parent": None}
        }
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

