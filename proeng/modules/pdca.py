# -*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MÓDULO: PDCA — Ciclo de Melhoria Contínua (Estrutura Circular PCDA)       ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import sys
import math
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsItem,
    QLineEdit,
    QMessageBox,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QFont,
    QFontMetrics,
    QPainterPath,
    QCursor,
)
from PyQt5.QtCore import (
    Qt,
    QRectF,
    QPointF,
    pyqtSignal,
    QObject,
    QTimer,
)

from proeng.core.themes import T
from proeng.core.utils import _c, _is_nb, _nb_paint_node, _solid_fill, _export_view
from proeng.core.toolbar import _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class PDCASignals(QObject):
    add_block = pyqtSignal(str)
    delete_block = pyqtSignal(str)
    edit_block = pyqtSignal(str)
    commit_block = pyqtSignal(str, str)


class PDCAFloatingEditor(QLineEdit):
    """Editor flutuante para edição inline dos cards."""
    committed = pyqtSignal(str, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id = ""
        self._original = ""
        self._done = False
        self.hide()

    def _apply_style(self):
        try:
            t = T()
            bg, fg, bdr = t["bg_card2"], t["text"], t["accent_bright"]
        except Exception:
            bg, fg, bdr = "#FFFFFF", "#000000", "#FF0000"
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                color: {fg};
                border: 2px solid {bdr};
                border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 11pt;
                padding: 6px;
            }}
        """)

    def open(self, target_id, current_text, scene_rect, view):
        self._apply_style()
        self._target_id = target_id
        self._original = current_text
        self._done = False
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


class PDCABlockSolid(QGraphicsItem):
    """Post-it / Card gráfico para o PDCA."""
    def __init__(self, pid, text, signals, zoom):
        super().__init__()
        self.pid = pid
        self.text = text
        self.signals = signals
        self.zoom = zoom
        self.hovered = False
        self._font_text = QFont("Segoe UI", max(8, int(11 * zoom)), QFont.Bold)
        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(10)

    def _calc_size(self):
        self.PADX = 12
        self.PADY = 10
        self.BOTTOM_EXTRA = 12
        self.base_w = 180 * self.zoom
        if not self.text:
            base_h = 80 * self.zoom
            self.w, self.h = self.base_w, base_h
        else:
            self.w = self.base_w
            inner_w = self.base_w - 2 * self.PADX * self.zoom
            fm = QFontMetrics(self._font_text)
            text_rect = fm.boundingRect(
                0, 0, int(inner_w), 10000,
                Qt.AlignCenter | Qt.TextWordWrap, self.text,
            )
            text_h = text_rect.height()
            self.h = max(80 * self.zoom, text_h + (self.PADY + self.BOTTOM_EXTRA) * self.zoom)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def paint(self, painter, option, widget=None):
        r = self.boundingRect()
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()

        if _is_nb(t):
            _nb_paint_node(painter, r, self.hovered)
        else:
            painter.setBrush(QBrush(_solid_fill(r, self.hovered)))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(r, 8, 8)

        if self.hovered:
            painter.save()
            clip = QPainterPath()
            clip.addRoundedRect(r, 8, 8)
            painter.setClipPath(clip)
            painter.setBrush(QBrush(QColor(t["accent_bright"])))
            painter.setPen(Qt.NoPen)
            painter.drawRect(QRectF(0, 0, max(3, int(4 * self.zoom)), self.h))
            painter.restore()

        if not self.text:
            painter.setFont(QFont("Segoe UI", max(6, int(9 * self.zoom))))
            painter.setPen(QColor(t["text_muted"]))
            painter.drawText(r, Qt.AlignCenter, "Duplo clique")
        else:
            painter.setFont(self._font_text)
            txt_color = t.get("text_on_accent", "#FFFFFF") if self.hovered else t["text"]
            painter.setPen(QColor(txt_color))
            px = self.PADX * self.zoom
            py = self.PADY * self.zoom
            inner = r.adjusted(px, py, -px, -py - self.BOTTOM_EXTRA * self.zoom)
            painter.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        if self.hovered:
            del_s = 18 * self.zoom
            del_r = QRectF(self.w - del_s - 4 * self.zoom, 4 * self.zoom, del_s, del_s)
            painter.setBrush(QBrush(QColor(t["btn_del"])))
            painter.setPen(QPen(QColor("#FF0000"), 1) if _is_nb(t) else Qt.NoPen)
            painter.drawRoundedRect(del_r, 4, 4)
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Consolas", max(8, int(12 * self.zoom)), QFont.Bold))
            painter.drawText(del_r, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            del_s = 20 * self.zoom
            del_r = QRectF(self.w - del_s - 5 * self.zoom, 5 * self.zoom, del_s, del_s)
            if self.hovered and del_r.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.delete_block.emit(self.pid))
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_block.emit(self.pid))


class PDCACircleBackground(QGraphicsItem):
    """Renderiza a estrutura circular divisora dos quadrantes P C D A."""
    def __init__(self, radius, zoom):
        super().__init__()
        self.R = radius
        self.zoom = zoom
        self.setZValue(-20)

    def boundingRect(self):
        return QRectF(-self.R, -self.R, self.R * 2, self.R * 2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.boundingRect()
        
        bw = int(4 * self.zoom) if _is_nb(t) else max(2, int(3 * self.zoom))
        pen_color = QColor(t["glass_border"] if _is_nb(t) else t["accent"])
        painter.setPen(QPen(pen_color, bw))

        # Cores para cada quadrante tiradas ativamente do tema
        c_p = QColor(t.get("block_blue", "#2979FF"))
        c_c = QColor(t.get("block_yellow", "#FFD600"))
        c_d = QColor(t.get("block_orange", "#FF6D00"))
        c_a = QColor(t.get("block_green", "#00C853"))

        # PyQt drawPie usa 1/16 de grau. 0 é direita.
        # TR (C): 0 a 90, TL (P): 90 a 180, BL (D): 180 a 270, BR (A): 270 a 360
        slices = [
            (c_p, 90 * 16, 90 * 16),
            (c_c, 0 * 16, 90 * 16),
            (c_d, 180 * 16, 90 * 16),
            (c_a, 270 * 16, 90 * 16)
        ]

        for color, start_angle, span_angle in slices:
            painter.setBrush(QBrush(color))
            painter.drawPie(r, start_angle, span_angle)

        painter.setPen(QPen(pen_color, bw))
        painter.drawLine(QPointF(0, -self.R), QPointF(0, self.R))
        painter.drawLine(QPointF(-self.R, 0), QPointF(self.R, 0))


class PDCAQuadrantLabel(QGraphicsItem):
    """Letras grandes P, C, D, A em seus respectivos quadrantes com botões de adicionar."""
    def __init__(self, q_id, label, rect, signals, zoom):
        super().__init__()
        self.q_id = q_id
        self.label = label
        self.rect = rect
        self.signals = signals
        self.zoom = zoom
        self.hovered = False
        self.setPos(rect.topLeft())
        self.setZValue(-10)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return QRectF(0, 0, self.rect.width(), self.rect.height())

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Letra gigante centralizada como marca d'água
        painter.setFont(QFont("Segoe UI", int(150 * self.zoom), QFont.Bold))
        painter.setPen(QColor(t["text"]))
        txt_pen = painter.pen()
        txt_pen.setColor(QColor(t["text"]))
        alpha = 40 if _is_nb(t) else 80
        txt_pen.setColor(QColor(QColor(t["text"]).red(), QColor(t["text"]).green(), QColor(t["text"]).blue(), alpha))
        painter.setPen(txt_pen)
        painter.drawText(self.boundingRect(), Qt.AlignCenter, self.label)

        # Botão + centralizado no topo do quadrante
        btn_s = 40 * self.zoom
        btn_x = self.rect.width() / 2 - btn_s / 2
        btn_y = 20 * self.zoom
        btn_rect = QRectF(btn_x, btn_y, btn_s, btn_s)

        if self.hovered:
            if _is_nb(t):
                painter.setBrush(QBrush(QColor(t["accent"])))
                painter.setPen(QPen(QColor("#000000"), 2))
                painter.drawRect(btn_rect)
            else:
                painter.setBrush(QBrush(QColor(t["bg_card"])))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(btn_rect, 8, 8)
            painter.setPen(QColor("#FFFFFF") if _is_nb(t) else QColor(t["text"]))
            painter.setFont(QFont("Segoe UI", int(20 * self.zoom), QFont.Bold))
            painter.drawText(btn_rect, Qt.AlignCenter, "+")
        else:
            painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(btn_rect, 8, 8)
            painter.setPen(QColor(t["text_muted"]))
            painter.setFont(QFont("Segoe UI", int(20 * self.zoom), QFont.Bold))
            painter.drawText(btn_rect, Qt.AlignCenter, "+")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            btn_s = 50 * self.zoom
            btn_x = self.rect.width() / 2 - btn_s / 2 - 5 * self.zoom
            btn_y = 15 * self.zoom
            btn_rect = QRectF(btn_x, btn_y, btn_s, btn_s)
            if btn_rect.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.add_block.emit(self.q_id))
                event.accept()
                return
        super().mousePressEvent(event)


class WidgetPDCAView(QWidget):
    """Widget principal que gerencia o zoom, pan e visualização do diagrama circular PDCA."""
    
    def __init__(self):
        super().__init__()
        self.signals = PDCASignals()
        self.signals.add_block.connect(self._on_add_block)
        self.signals.delete_block.connect(self._on_delete_block)
        self.signals.edit_block.connect(self._on_edit_block)
        self.signals.commit_block.connect(self._on_commit_block)

        self.zoom_level = 0.8
        self.next_pid = 1

        # Quadrantes definidos: P (TopLeft), C (TopRight), D (BottomLeft), A (BottomRight)
        # Baseado no pedido do usuário de left to right (P C D A)
        self.quadrants_data = [
            {"id": "P", "label": "P", "dx": -1, "dy": -1}, # Top-Left
            {"id": "C", "label": "C", "dx": 1,  "dy": -1}, # Top-Right
            {"id": "D", "label": "D", "dx": -1, "dy": 1},  # Bottom-Left
            {"id": "A", "label": "A", "dx": 1,  "dy": 1},  # Bottom-Right
        ]
        self.quadrants = {q["id"]: [] for q in self.quadrants_data}
        self.blocks_items = {}
        
        # Test demo blocks
        self.quadrants["P"].append({"id": "b_101", "text": "Planejamento Mestre"})
        self.quadrants["C"].append({"id": "b_102", "text": "Checagem de Metricas"})
        self.quadrants["D"].append({"id": "b_103", "text": "Execução Piloto"})
        self.quadrants["A"].append({"id": "b_104", "text": "Agir Corretivamente"})
        self.next_pid = 200

        self._setup_ui()
        self._float_editor = PDCAFloatingEditor(self.view)
        self._float_editor.committed.connect(self.signals.commit_block.emit)
        self.update_zoom(0.8)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        self.view.scale(self.zoom_level, self.zoom_level)
        self._apply_view_bg()
        
        layout.addWidget(self.view)

    def _apply_view_bg(self):
        try:
            self.view.setBackgroundBrush(QBrush(_c("bg_app")))
        except Exception:
            self.view.setBackgroundBrush(QBrush(QColor("#FFFFFF")))

    def refresh_theme(self):
        self._apply_view_bg()
        if hasattr(self, "_float_editor"):
            self._float_editor._apply_style()
        self._draw_board()

    def zoom_in(self):
        self.update_zoom(self.zoom_level * 1.15)

    def zoom_out(self):
        self.update_zoom(self.zoom_level / 1.15)

    def reset_zoom(self):
        self.update_zoom(0.8)

    def update_zoom(self, z):
        self.zoom_level = max(0.2, min(z, 3.0))
        self.view.resetTransform()
        self.view.scale(self.zoom_level, self.zoom_level)
        self._draw_board()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            super().wheelEvent(event)

    def _draw_board(self):
        self.scene.clear()
        self.blocks_items.clear()
        z = self.zoom_level
        
        # Raio da estrutura circular base
        R = 480 * z
        
        # Adiciona o background circular dividido
        circle_bg = PDCACircleBackground(R, z)
        self.scene.addItem(circle_bg)

        # Adiciona a estrutura de cada quadrante (labels e gerador de cards)
        # O retângulo base de cada um é um quadrado [R x R]
        for q in self.quadrants_data:
            q_id = q["id"]
            
            # Posição base do quadrante
            if q["dx"] < 0:
                x = -R
            else:
                x = 0
            if q["dy"] < 0:
                y = -R
            else:
                y = 0
                
            q_rect = QRectF(x, y, R, R)
            label_item = PDCAQuadrantLabel(q_id, q["label"], q_rect, self.signals, z)
            self.scene.addItem(label_item)

            # Posicionamento dinâmico dos cards dentro deste quadrante
            pad_x, pad_y = 20 * z, 100 * z
            curr_px, curr_py = pad_x, pad_y
            
            for pdata in self.quadrants[q_id]:
                pid = pdata["id"]
                p_item = PDCABlockSolid(pid, pdata["text"], self.signals, z)
                
                # Wrap inside quadrant bounding logic
                if curr_px + p_item.w > R - 20 * z and curr_px > pad_x:
                    curr_px = pad_x
                    curr_py += p_item.h + 10 * z
                
                p_item.setPos(q_rect.x() + curr_px, q_rect.y() + curr_py)
                self.scene.addItem(p_item)
                self.blocks_items[pid] = p_item
                
                curr_px += p_item.w + 10 * z

        # Scene bounds
        self.scene.setSceneRect(-R - 100 * z, -R - 100 * z, R * 2 + 200 * z, R * 2 + 200 * z)

    def _on_add_block(self, q_id):
        pid = f"b_{self.next_pid}"
        self.next_pid += 1
        self.quadrants[q_id].append({"id": pid, "text": ""})
        self._draw_board()
        QTimer.singleShot(60, lambda: self._on_edit_block(pid))

    def _on_delete_block(self, pid):
        for q_id, blocks in self.quadrants.items():
            for i, b in enumerate(blocks):
                if b["id"] == pid:
                    del blocks[i]
                    self._draw_board()
                    return

    def _on_edit_block(self, pid):
        if pid in self.blocks_items:
            p_item = self.blocks_items[pid]
            self._float_editor.open(
                pid, p_item.text, p_item.sceneBoundingRect(), self.view
            )

    def _on_commit_block(self, pid, text):
        for q_id, blocks in self.quadrants.items():
            for b in blocks:
                if b["id"] == pid:
                    b["text"] = text
                    self._draw_board()
                    return

    def get_state(self):
        return {
            "schema": "pdca_circular.v1",
            "quadrants": self.quadrants,
            "next_pid": self.next_pid,
        }

    def set_state(self, state):
        if not state:
            return
        if state.get("schema") == "pdca_circular.v1":
            secs = state.get("quadrants", {})
            if secs:
                self.quadrants = secs
            self.next_pid = state.get("next_pid", 1)
            self._draw_board()

    def _export_scene(self, fmt):
        _export_view(self.view, fmt, self)


class _PDCAModule(BaseModule):
    """Adaptador que implementa interface BaseModule para PDCA Circular."""
    def __init__(self):
        super().__init__()
        self._interno = WidgetPDCAView()
        _hide_inner_toolbar(self._interno)
        
        self.help_text = (
            "CICLO PDCA — Guia Rapido\n\n"
            "O PDCA (Plan-Do-Check-Act) e um metodo iterativo de "
            "melhoria continua utilizado para resolver problemas e "
            "otimizar processos. O ciclo e representado como um "
            "diagrama circular dividido em 4 quadrantes coloridos.\n\n"
            "OS 4 QUADRANTES:\n"
            "• P (Plan / Planejar): Identificar o problema, analisar "
            "causas e planejar acoes de melhoria.\n"
            "• D (Do / Executar): Implementar as acoes planejadas "
            "em escala piloto ou controlada.\n"
            "• C (Check / Verificar): Medir resultados, comparar "
            "com metas e avaliar a eficacia das acoes.\n"
            "• A (Act / Agir): Padronizar as acoes bem-sucedidas "
            "ou corrigir desvios e reiniciar o ciclo.\n\n"
            "COMO USAR:\n"
            "• Clique no botao (+) dentro de cada quadrante para "
            "adicionar um novo card com uma etapa ou tarefa.\n"
            "• Clique duas vezes em um card para editar seu texto.\n"
            "• Para excluir um card, passe o mouse sobre ele e "
            "clique no botao (-) que aparece.\n\n"
            "NAVEGACAO:\n"
            "• Use Ctrl + Scroll do mouse ou Ctrl +/- para zoom.\n"
            "• Cada quadrante possui uma cor tematica distinta "
            "que se adapta automaticamente ao tema ativo."
        )
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._interno)
    
    def get_state(self):
        return self._interno.get_state()
    
    def set_state(self, state):
        self._interno.set_state(state)
    
    def refresh_theme(self):
        self._interno.refresh_theme()
    
    def get_view(self):
        return self._interno.view
    
    def zoom_in(self): 
        self._interno.zoom_in()
        
    def zoom_out(self): 
        self._interno.zoom_out()
        
    def reset_zoom(self): 
        self._interno.reset_zoom()
