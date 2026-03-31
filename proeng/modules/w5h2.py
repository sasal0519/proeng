# -*- coding: utf-8 -*-
"""Módulo Plano 5W2H — Gestão de Ações com Auto-layout."""
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
from proeng.core.utils import (_export_view, _c, _glass_grad, W5H2_TYPES)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class W5H2Signals(QObject):
    add_action   = pyqtSignal(int)
    delete_node  = pyqtSignal(int)
    edit_start   = pyqtSignal(int)
    commit_text  = pyqtSignal(int, str)

class W5H2FloatingEditor(QTextEdit):
    committed = pyqtSignal(int, str)
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = -1, "", False
        self.apply_theme()
        self.hide()

    def apply_theme(self):
        t = T()
        self.setStyleSheet(f"QTextEdit {{ background: {t['bg_card']}; color: {t['text']}; border: 2px solid {t['accent']}; border-radius: 5px; font-family: 'Segoe UI'; font-size: 11pt; padding: 6px; }}")

    def open(self, target_id, current_text, scene_rect, view):
        self._target_id, self._original, self._done = target_id, current_text, False
        rect_in_view = view.mapFromScene(scene_rect).boundingRect()
        self.setGeometry(rect_in_view)
        self.setPlainText(current_text)
        self.selectAll(); self.show(); self.raise_(); self.setFocus()

    def _commit(self, text=None):
        if self._done: return
        self._done = True
        self.hide()
        self.committed.emit(self._target_id, (text if text is not None else self.toPlainText()).strip())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier: super().keyPressEvent(event)
            else: self._commit()
        elif event.key() == Qt.Key_Escape: self._commit(self._original)
        else: super().keyPressEvent(event)
        
    def focusOutEvent(self, event): 
        self._commit(); super().focusOutEvent(event)

class W5H2Node(QGraphicsItem):
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
        sample = self.text if self.text else "✎ Preencher"
        
        # 1. Calcula a largura do Título/Cabeçalho (Header)
        header_font = QFont("Consolas", int(9 * self.zoom), QFont.Bold)
        fm_header = QFontMetrics(header_font)
        header_w = (fm_header.horizontalAdvance(self.type_data["t"]) if hasattr(fm_header, 'horizontalAdvance') else fm_header.width(self.type_data["t"])) + 40 * self.zoom
        
        # 2. Calcula a largura e altura do Texto Interno
        fm_text = QFontMetrics(self._font)
        
        # O texto interno precisa de um espaço mínimo. 
        # A largura começa restrita pela base, ou pelo header, o que for maior.
        base_available_w = max(self.base_w, header_w) - 20 * self.zoom
        
        text_rect = fm_text.boundingRect(0, 0, int(base_available_w), 5000, Qt.AlignCenter | Qt.TextWordWrap, sample)
        
        # Se o texto for apenas uma palavra muito longa que excede o available_w, text_rect.width() será maior que available_w
        text_w = text_rect.width() + 30 * self.zoom
        
        # 3. Define w e h finais garantindo que nada estoure
        self.w = max(self.base_w, header_w, text_w)
        self.h = max(self.base_h, text_rect.height() + 40 * self.zoom)

    def boundingRect(self):
        m = 15 * self.zoom
        return QRectF(0, 0, self.w, self.h).adjusted(-m, -m, m, m)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        t = T()
        r = QRectF(0, 0, self.w, self.h)
        
        # Centralized glass gradient for excellent visual clarity (No-Border ready)
        painter.setBrush(QBrush(_glass_grad(r, self.hovered or self.node_type == "ROOT")))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRoundedRect(r, 12, 12)

        # 1. Header with dynamic gradient and precision clipping
        header_h = 28 * self.zoom
        painter.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(r, 12, 12) # Use main rect to clip header
        painter.setClipPath(clip_path)

        header_col = QColor(self.type_data["c"])
        h_grad = QLinearGradient(0, 0, 0, header_h)
        h_grad.setColorAt(0, header_col)
        h_grad.setColorAt(1, header_col.darker(115))
        
        painter.setBrush(QBrush(h_grad))
        painter.setPen(QPen(Qt.NoPen))
        painter.drawRect(QRectF(0, 0, self.w, header_h))
        painter.restore()
        
        painter.setPen(QColor("#000000" if self.node_type in ["WHY", "WHEN", "WHERE"] else "#FFFFFF"))
        painter.setFont(QFont("Consolas", int(10 * self.zoom), QFont.Bold))
        # Move levemente o texto do cabeçalho um pouco para cima dentro da barra (offset vertical)
        header_text_rect = QRectF(0, -2 * self.zoom, self.w, header_h)
        painter.drawText(header_text_rect, Qt.AlignCenter, self.type_data["t"])

        painter.setPen(_c("text" if self.text else "text_dim"))
        painter.setFont(self._font)
        
        # 2. Posiciona o texto principal mais para cima, colado ao cabeçalho (com padding)
        p_val = 15 * self.zoom
        text_rect = QRectF(p_val, header_h + 8 * self.zoom, self.w - 2 * p_val, self.h - header_h - 16 * self.zoom)
        # Usa AlignTop para colar o texto no alto
        painter.drawText(text_rect, Qt.AlignTop | Qt.AlignHCenter | Qt.TextWordWrap, self.text if self.text else "✎ Preencher")

        if self.hovered:
            btn_s = 24 * self.zoom
            if self.node_type in ["ROOT", "WHAT"]:
                add_rect = QRectF(self.w - btn_s/2, self.h/2 - btn_s/2, btn_s, btn_s)
                painter.setBrush(QBrush(QColor("#1A5C1A"))); painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(add_rect, 4, 4)
                painter.setPen(QColor("#FFF")); painter.setFont(QFont("Consolas", int(14*self.zoom), QFont.Bold))
                painter.drawText(add_rect, Qt.AlignCenter, "+")
            
            if self.node_type == "WHAT":
                del_rect = QRectF(-btn_s/2, -btn_s/2, btn_s, btn_s)
                painter.setBrush(QBrush(QColor("#8B1515"))); painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(del_rect, 4, 4)
                painter.setPen(QColor("#FFF")); painter.setFont(QFont("Consolas", int(16*self.zoom), QFont.Bold))
                painter.drawText(del_rect, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e): self.hovered = True; self.update()
    def hoverLeaveEvent(self, e): self.hovered = False; self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            btn_s = 24 * self.zoom
            add_rect = QRectF(self.w - btn_s/2, self.h/2 - btn_s/2, btn_s, btn_s)
            del_rect = QRectF(-btn_s/2, -btn_s/2, btn_s, btn_s)
            
            if self.node_type in ["ROOT", "WHAT"] and add_rect.contains(event.pos()) and self.hovered:
                QTimer.singleShot(0, lambda: self.signals.add_action.emit(self.node_id))
                event.accept(); return
            if self.node_type == "WHAT" and del_rect.contains(event.pos()) and self.hovered:
                QTimer.singleShot(0, lambda: self.signals.delete_node.emit(self.node_id))
                event.accept(); return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))

class W5H2Widget(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = W5H2Signals()
        self.signals.add_action.connect(self._on_add_action)
        self.signals.delete_node.connect(self._on_delete_node)
        self.signals.edit_start.connect(self._on_edit_start)
        self.signals.commit_text.connect(self._on_commit_text)
        
        self.zoom_level = 0.8
        self.next_id = 2
        
        self.nodes = {1: {"text": "Novo Projeto / Meta", "type": "ROOT", "parent": None, "children": []}}
        self.node_dimensions, self.node_positions = {}, {}

        self._setup_ui()
        self._float_editor = W5H2FloatingEditor(self.view)
        self._float_editor.committed.connect(self.signals.commit_text.emit)
        self.update_zoom(1.0) 

    def refresh_theme(self):
        t = T()
        if hasattr(self, 'view'):
            self.view.setBackgroundBrush(QBrush(_c("bg_app")))
        
        if hasattr(self, '_float_editor'):
            self._float_editor.apply_theme()

        # Redesenha para atualizar conectores e itens
        self._draw_diagram()

    def _setup_ui(self):
        layout = QVBoxLayout(self); layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)

    def zoom_in(self): self.update_zoom(self.zoom_level * 1.15)
    def zoom_out(self): self.update_zoom(self.zoom_level / 1.15)
    def reset_zoom(self): self.update_zoom(1.0)
    def update_zoom(self, z):
        self.zoom_level = max(0.3, min(z, 3.0))
        self._draw_diagram()

    def calcular_posicoes(self):
        z = self.zoom_level
        self.node_positions.clear()
        dist_x_l1 = 350 * z
        dist_x_l2 = 320 * z
        pad_y_l2  = 15 * z
        pad_y_l1  = 80 * z
        current_y = 0
        action_ids = self.nodes[1]["children"]
        for aid in action_ids:
            aw, ah = self.node_dimensions[aid]
            detail_ids = self.nodes[aid]["children"]
            details_total_h = 0
            detail_ys = []
            start_y = current_y
            for did in detail_ids:
                dw, dh = self.node_dimensions[did]
                self.node_positions[did] = (dist_x_l1 + aw + dist_x_l2, current_y)
                detail_ys.append(current_y + dh/2)
                current_y += dh + pad_y_l2
                details_total_h += dh + pad_y_l2
            if detail_ys: action_y = sum(detail_ys) / len(detail_ys) - ah/2
            else: action_y = start_y; current_y += ah
            self.node_positions[aid] = (dist_x_l1, action_y)
            current_y += pad_y_l1
        rw, rh = self.node_dimensions[1]
        if action_ids: root_y = sum(self.node_positions[aid][1] + self.node_dimensions[aid][1]/2 for aid in action_ids) / len(action_ids) - rh/2
        else: root_y = 0
        self.node_positions[1] = (0, root_y)

    def _draw_diagram(self):
        self.scene.clear()
        if not self.nodes: return
        t = T()
        z = self.zoom_level
        self.node_dimensions.clear()
        for nid, data in self.nodes.items():
            tmp = W5H2Node(nid, data["text"], data["type"], self.signals, z)
            self.node_dimensions[nid] = (tmp.w, tmp.h)
        self.calcular_posicoes()
        pen_conn = QPen(QColor(t["accent_dim"]), max(2, int(3*z)), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        root_x, root_y = self.node_positions[1]
        rw, rh = self.node_dimensions[1]
        p1_root = QPointF(root_x + rw, root_y + rh/2)
        for aid in self.nodes[1]["children"]:
            ax, ay = self.node_positions[aid]
            aw, ah = self.node_dimensions[aid]
            p2_action = QPointF(ax, ay + ah/2)
            mid_x = (p1_root.x() + p2_action.x()) / 2
            path = QPainterPath()
            path.moveTo(p1_root); path.lineTo(mid_x, p1_root.y()); path.lineTo(mid_x, p2_action.y()); path.lineTo(p2_action)
            self.scene.addPath(path, pen_conn)
            p1_action = QPointF(ax + aw, ay + ah/2)
            for did in self.nodes[aid]["children"]:
                dx, dy = self.node_positions[did]
                dw, dh = self.node_dimensions[did]
                p2_detail = QPointF(dx, dy + dh/2)
                mid_x2 = (p1_action.x() + p2_detail.x()) / 2
                path2 = QPainterPath()
                path2.moveTo(p1_action); path2.lineTo(mid_x2, p1_action.y()); path2.lineTo(mid_x2, p2_detail.y()); path2.lineTo(p2_detail)
                self.scene.addPath(path2, pen_conn)
        for nid, (nx, ny) in self.node_positions.items():
            item = W5H2Node(nid, self.nodes[nid]["text"], self.nodes[nid]["type"], self.signals, z)
            item.setPos(nx, ny)
            self.scene.addItem(item)
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-100*z, -100*z, 100*z, 100*z))

    def _on_add_action(self, parent_id=1):
        new_action_id = self.next_id; self.next_id += 1
        self.nodes[new_action_id] = {"text": "", "type": "WHAT", "parent": 1, "children": []}
        self.nodes[1]["children"].append(new_action_id)
        details = ["WHY", "WHO", "WHERE", "WHEN", "HOW", "COST"]
        for d_type in details:
            did = self.next_id; self.next_id += 1
            self.nodes[did] = {"text": "", "type": d_type, "parent": new_action_id, "children": []}
            self.nodes[new_action_id]["children"].append(did)
        self._draw_diagram()
        QTimer.singleShot(60, lambda: self._on_edit_start(new_action_id))

    def _on_delete_node(self, node_id):
        if QMessageBox.question(self, "Excluir", "Excluir esta Ação e todos os seus detalhes 5W2H?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            pid = self.nodes[node_id]["parent"]
            if pid is not None: self.nodes[pid]["children"].remove(node_id)
            self._remove_recursively(node_id)
            self._draw_diagram()

    def _remove_recursively(self, node_id):
        for cid in list(self.nodes[node_id]["children"]): self._remove_recursively(cid)
        del self.nodes[node_id]

    def _on_edit_start(self, node_id):
        if node_id not in self.node_positions: return
        nw, nh = self.node_dimensions[node_id]; x, y = self.node_positions[node_id]
        header_h = 20 * self.zoom_level
        edit_rect = QRectF(x, y + header_h, nw, nh - header_h)
        self._float_editor.open(node_id, self.nodes[node_id]["text"], edit_rect, self.view)

    def _on_commit_text(self, node_id, text):
        if node_id in self.nodes:
            self.nodes[node_id]["text"] = text
            self._draw_diagram()

# ═══════════════════════════════════════════════════════════════════


class _W5H2Module(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = W5H2Widget()
        # Oculta toolbar interna original
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Adicione uma nova Ação clicando no botão (+) vermelho.\n"
            "• Clique duas vezes nas caixas (WHAT, WHO, WHEN...) para preencher os detalhes.\n"
            "• O balão ajusta seu tamanho automaticamente ao seu texto.\n"
            "• Use o menu 'Exibir' para controlar o Zoom do plano."
        )
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(self._inner)

    def reset_zoom(self): self._inner.reset_zoom()
    def zoom_in(self): self._inner.zoom_in()
    def zoom_out(self): self._inner.zoom_out()





    def get_state(self):
        return {
            "schema": "w5h2.v1",
            "nodes": self._inner.nodes,
            "next_id": self._inner.next_id
        }

    def set_state(self, state):
        if not state:
            return
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try: k_int = int(k)
            except: k_int = k
            nodes[k_int] = v
        
        self._inner.nodes = nodes if nodes else {1: {"text": "Novo Projeto / Meta", "type": "ROOT", "parent": None, "children": []}}
        self._inner.next_id = state.get("next_id", 2)
        self._inner._draw_diagram()
    def refresh_theme(self):
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()
    def get_view(self):
        return getattr(self._inner, "view", None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _W5H2Module()
    w.setWindowTitle("Plano de Ação 5W2H — PRO ENG")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())

