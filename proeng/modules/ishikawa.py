# -*- coding: utf-8 -*-
"""Módulo Ishikawa — Diagrama Espinha de Peixe (Causa e Efeito)."""
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
from proeng.core.utils import (_export_view, C_BG_APP, C_BG_NODE,
    C_BORDER, C_TEXT_MAIN, C_PLACEHOLDER, C_BTN_ADD, C_BTN_DEL, C_LINE,
    C_BTN_SIB, C_BG_ROOT, C_BORDER_ROOT, W5H2_TYPES)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar


class IshikawaSignals(QObject):
    add_child   = pyqtSignal(int)
    delete_node = pyqtSignal(int)
    edit_start  = pyqtSignal(int)
    commit_text = pyqtSignal(int, str)


class IshikawaFloatingEditor(QLineEdit):
    committed = pyqtSignal(int, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._target_id, self._original, self._done = -1, "", False
        self.hide()

    def _apply_style(self):
        try:
            t   = T()
            bg  = t["bg_card2"]
            fg  = t["text"]
            bdr = t["accent_bright"]
        except Exception:
            bg, fg, bdr = "#1A0A0A", "#FAE8E8", "#CC2222"
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                color: {fg};
                border: 2px solid {bdr};
                border-radius: 6px;
                font-family: 'Segoe UI'; font-size: 11pt;
                padding: 5px 10px;
            }}
        """)

    def open(self, target_id, current_text, scene_rect, view):
        self._apply_style()
        self._target_id, self._original, self._done = target_id, current_text, False
        rv = view.mapFromScene(scene_rect).boundingRect()
        self.setGeometry(rv.x(), rv.y() + rv.height()//2 - 18, max(160, rv.width()), 36)
        self.setText(current_text)
        self.selectAll(); self.show(); self.raise_(); self.setFocus()

    def _commit(self, text=None):
        if self._done: return
        self._done = True
        self.hide()
        self.committed.emit(self._target_id,
                            (text if text is not None else self.text()).strip())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter): self._commit()
        elif event.key() == Qt.Key_Escape: self._commit(self._original)
        else: super().keyPressEvent(event)

    def focusOutEvent(self, event): self._commit(); super().focusOutEvent(event)


class IshikawaNode(QGraphicsItem):
    """Nó do Ishikawa — Nível 0: Cabeça, 1: Categoria, 2: Causa"""

    def __init__(self, node_id, text, level, signals, zoom):
        super().__init__()
        self.node_id = node_id
        self.text    = text
        self.level   = level
        self.signals = signals
        self.zoom    = zoom
        self.hovered = False

        if self.level == 0:
            self._font   = QFont("Segoe UI", max(8, int(14 * zoom)), QFont.Bold)
            self.base_w, self.base_h = 200 * zoom, 72 * zoom
        elif self.level == 1:
            self._font   = QFont("Segoe UI", max(7, int(10 * zoom)), QFont.Bold)
            self.base_w, self.base_h = 130 * zoom, 38 * zoom
        else:
            self._font   = QFont("Segoe UI", max(6, int(8 * zoom)))
            self.base_w, self.base_h = 110 * zoom, 28 * zoom

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setZValue(10)

    def _calc_size(self):
        sample = self.text if self.text else ("Efeito / Problema" if self.level == 0 else "Nova Causa")
        fm = QFontMetrics(self._font)
        tw = fm.horizontalAdvance(sample) if hasattr(fm, "horizontalAdvance") else fm.width(sample)
        th = fm.height()
        self.w = max(self.base_w, tw + 28 * self.zoom)
        self.h = max(self.base_h, th + 16 * self.zoom)

    def boundingRect(self):
        m = 14 * self.zoom
        return QRectF(-m, -m, self.w + m * 2, self.h + m * 2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        r = QRectF(0, 0, self.w, self.h)

        # Fundo com gradiente
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        if self.level == 0:
            grad.setColorAt(0, QColor(t["bg_card2"]))
            grad.setColorAt(1, QColor(t["bg_card"]))
            border_col = t["accent_bright"] if not self.hovered else "#FF8888" if t["name"] == "dark" else "#0050CC"
            pen_w = 2.5 * self.zoom
            radius = 6
        elif self.level == 1:
            grad.setColorAt(0, QColor(t["bg_card"]))
            grad.setColorAt(1, QColor(t["bg_app"]))
            border_col = t["accent"] if not self.hovered else t["accent_bright"]
            pen_w = 1.8 * self.zoom
            radius = 5
        else:
            grad.setColorAt(0, QColor(t["bg_card"]))
            grad.setColorAt(1, QColor(t["bg_card"]))
            border_col = t["accent_dim"] if not self.hovered else t["accent"]
            pen_w = 1.2 * self.zoom
            radius = 4

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(border_col), pen_w))
        painter.drawRoundedRect(r, radius, radius)

        # Accent strip topo
        if self.level <= 1:
            sg = QLinearGradient(0, 0, self.w, 0)
            sg.setColorAt(0, QColor(t["accent_bright"] if self.hovered else t["accent"]))
            sg.setColorAt(0.6, QColor(0, 0, 0, 0))
            painter.setBrush(QBrush(sg)); painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(0, 0, self.w, 3 * self.zoom), 2, 2)

        # Texto
        display = self.text if self.text else ("✎ Efeito/Problema" if self.level == 0 else "✎ Nomear")
        painter.setPen(QColor(t["text"] if self.text else t["text_dim"]))
        painter.setFont(self._font)
        inner = r.adjusted(6 * self.zoom, 4 * self.zoom, -6 * self.zoom, -4 * self.zoom)
        painter.drawText(inner, Qt.AlignCenter | Qt.TextWordWrap, display)

        # Botões hover
        if self.hovered:
            bs = 20 * self.zoom; hbs = bs / 2
            painter.setFont(QFont("Consolas", max(7, int(12 * self.zoom)), QFont.Bold))

            if self.level < 2:
                add_r = QRectF(self.w - hbs, -hbs, bs, bs)
                painter.setBrush(QBrush(QColor(t["btn_add"]))); painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(add_r, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.drawText(add_r, Qt.AlignCenter, "+")

            if self.level > 0:
                del_r = QRectF(-hbs, -hbs, bs, bs)
                painter.setBrush(QBrush(QColor(t["btn_del"]))); painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(del_r, 4, 4)
                painter.setPen(QColor("#FFF"))
                painter.drawText(del_r, Qt.AlignCenter, "−")

    def hoverEnterEvent(self, e): self.hovered = True;  self.update()
    def hoverLeaveEvent(self, e): self.hovered = False; self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.hovered:
            bs = 20 * self.zoom; hbs = bs / 2
            add_r = QRectF(self.w - hbs, -hbs, bs, bs)
            del_r = QRectF(-hbs, -hbs, bs, bs)
            if self.level < 2 and add_r.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.add_child.emit(self.node_id))
                event.accept(); return
            if self.level > 0 and del_r.contains(event.pos()):
                QTimer.singleShot(0, lambda: self.signals.delete_node.emit(self.node_id))
                event.accept(); return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_start.emit(self.node_id))


class IshikawaWidget(QWidget):
    """Diagrama de Ishikawa (Espinha de Peixe) completo e integrado ao sistema de temas."""

    def __init__(self):
        super().__init__()
        self.sigs     = IshikawaSignals()
        self.sigs.add_child.connect(self._on_add_child)
        self.sigs.delete_node.connect(self._on_delete_node)
        self.sigs.edit_start.connect(self._on_edit_start)
        self.sigs.commit_text.connect(self._on_commit_text)

        self.zoom_level    = 1.0
        self.next_id       = 2
        self.node_dims     = {}
        self.node_positions = {}

        # Estrutura inicial com 6 categorias clássicas M
        self.nodes = {1: {"text": "EFEITO / PROBLEMA", "level": 0, "children": [], "parent": None}}
        cat_names = ["Método", "Máquina", "Material", "Mão de Obra", "Meio Ambiente", "Medição"]
        for name in cat_names:
            nid = self.next_id; self.next_id += 1
            self.nodes[nid] = {"text": name, "level": 1, "children": [], "parent": 1}
            self.nodes[1]["children"].append(nid)

        self._setup_ui()
        self._float_editor = IshikawaFloatingEditor(self.view)
        self._float_editor.committed.connect(self.sigs.commit_text.emit)
        self._draw_diagram()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0); layout.setContentsMargins(0, 0, 0, 0)
        self.scene = QGraphicsScene()
        self.view  = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setStyleSheet("border:none;")
        self._apply_view_bg()
        layout.addWidget(self.view)

    def _apply_view_bg(self):
        try:
            self.view.setBackgroundBrush(QBrush(QColor(T()["bg_app"])))
        except Exception:
            self.view.setBackgroundBrush(QBrush(QColor(C_BG_APP)))

    def refresh_theme(self):
        self._apply_view_bg()
        if self.scene:
            self.scene.update()

    def zoom_in(self):  self._scale(1.15)
    def zoom_out(self): self._scale(1 / 1.15)
    def reset_zoom(self):
        self.view.resetTransform()
        self.zoom_level = 1.0
        self._draw_diagram()

    def _scale(self, factor):
        new_z = self.zoom_level * factor
        if 0.2 <= new_z <= 4.0:
            self.zoom_level = new_z
            self.view.scale(factor, factor)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3)

    def _export_scene(self, fmt):
        _export_view(self.view, fmt, self)

    # ──────────────────────────────────────────────────────────────
    #   MOTOR DE LAYOUT ISHIKAWA
    # ──────────────────────────────────────────────────────────────
    def _draw_diagram(self):
        self.scene.clear()
        t  = T()
        z  = self.zoom_level

        # 1. Pré-calcular dimensões
        self.node_dims.clear()
        for nid, data in self.nodes.items():
            tmp = IshikawaNode(nid, data["text"], data["level"], self.sigs, z)
            self.node_dims[nid] = (tmp.w, tmp.h)

        # 2. Geometria base
        spine_end_x  = 1100 * z
        spine_y      = 480  * z
        cat_ids      = self.nodes[1]["children"]
        top_cats     = [c for i, c in enumerate(cat_ids) if i % 2 == 0]
        bot_cats     = [c for i, c in enumerate(cat_ids) if i % 2 != 0]
        n_slots      = max(len(top_cats), len(bot_cats), 1)
        spine_step   = max(260 * z, 260 * z)
        spine_start  = spine_end_x - (n_slots + 1) * spine_step

        # 3. Espinha central
        pen_spine = QPen(QColor(t["accent_bright"]),
                         max(2, int(5 * z)), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.scene.addLine(spine_start, spine_y, spine_end_x, spine_y, pen_spine)

        # Seta na ponta
        asz = 18 * z
        arrow = QPolygonF([
            QPointF(spine_end_x, spine_y),
            QPointF(spine_end_x - asz, spine_y - asz * 0.5),
            QPointF(spine_end_x - asz, spine_y + asz * 0.5),
        ])
        self.scene.addPolygon(arrow, QPen(Qt.NoPen), QBrush(QColor(t["accent_bright"])))

        # 4. Nó cabeça
        hw, hh = self.node_dims[1]
        hx = spine_end_x + 12 * z
        hy = spine_y - hh / 2
        self.node_positions[1] = (hx, hy)

        # 5. Ramos e causas
        pen_branch = QPen(QColor(t["line"]),   max(1, int(3 * z)), Qt.SolidLine, Qt.RoundCap)
        pen_cause  = QPen(QColor(t["line_eap"]), max(1, int(2 * z)), Qt.SolidLine, Qt.RoundCap)

        def draw_branch(cat_list, is_top):
            sign = -1 if is_top else 1
            for k, cid in enumerate(cat_list):
                ax = spine_end_x - (k + 1) * spine_step
                ay = spine_y

                n_causes  = len(self.nodes[cid]["children"])
                branch_h  = max(220 * z, (n_causes * 75 + 120) * z)
                ox = ax - branch_h * 0.75
                oy = spine_y + sign * branch_h

                # Linha diagonal da categoria
                self.scene.addLine(ox, oy, ax, ay, pen_branch)

                # Posição da caixa da categoria (acima/abaixo do ponto ox,oy)
                cw, ch = self.node_dims[cid]
                cx = ox - cw / 2
                cy = oy - ch - 12 * z if is_top else oy + 12 * z
                self.node_positions[cid] = (cx, cy)

                # Causas ramos menores
                causes = self.nodes[cid]["children"]
                if causes:
                    dy = (ay - oy) / (len(causes) + 1)
                    for j, scid in enumerate(causes):
                        py  = oy + (j + 1) * dy
                        px  = ox + ((py - oy) / (ay - oy)) * (ax - ox)
                        seg = max(120 * z, 120 * z)

                        # Linha horizontal da causa
                        self.scene.addLine(px - seg, py, px, py, pen_cause)

                        # Pequena seta na causa
                        ca = 7 * z
                        self.scene.addPolygon(
                            QPolygonF([QPointF(px, py),
                                       QPointF(px - ca, py - ca * 0.5),
                                       QPointF(px - ca, py + ca * 0.5)]),
                            QPen(Qt.NoPen), QBrush(QColor(t["line_eap"])))

                        sw, sh = self.node_dims[scid]
                        self.node_positions[scid] = (px - seg, py - sh - 4 * z)

        draw_branch(top_cats, True)
        draw_branch(bot_cats, False)

        # 6. Renderizar nós
        for nid, (nx, ny) in self.node_positions.items():
            item = IshikawaNode(nid, self.nodes[nid]["text"],
                                self.nodes[nid]["level"], self.sigs, z)
            item.setPos(nx, ny)
            self.scene.addItem(item)

        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(-120*z, -120*z, 120*z, 120*z))
        self.view.centerOn(spine_end_x - (n_slots * spine_step) / 2, spine_y)

    # ──────────────────────────────────────────────────────────────
    #   LÓGICA DE DADOS
    # ──────────────────────────────────────────────────────────────
    def _on_add_child(self, parent_id):
        new_level = self.nodes[parent_id]["level"] + 1
        nid = self.next_id; self.next_id += 1
        self.nodes[nid] = {"text": "", "level": new_level, "children": [], "parent": parent_id}
        self.nodes[parent_id]["children"].append(nid)
        self._draw_diagram()
        QTimer.singleShot(60, lambda: self._on_edit_start(nid))

    def _on_delete_node(self, node_id):
        if QMessageBox.question(self, "Excluir",
                                "Excluir este nó e todos os seus filhos?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            pid = self.nodes[node_id]["parent"]
            if pid is not None:
                self.nodes[pid]["children"].remove(node_id)
            self._remove_rec(node_id)
            self._draw_diagram()

    def _remove_rec(self, nid):
        for cid in list(self.nodes[nid]["children"]):
            self._remove_rec(cid)
        del self.nodes[nid]

    def _on_edit_start(self, node_id):
        if node_id not in self.node_positions: return
        nw, nh = self.node_dims[node_id]
        x, y   = self.node_positions[node_id]
        self._float_editor.open(node_id, self.nodes[node_id]["text"],
                                QRectF(x, y, nw, nh), self.view)

    def _on_commit_text(self, node_id, text):
        if node_id in self.nodes:
            self.nodes[node_id]["text"] = text
            self._draw_diagram()


# ═══════════════════════════════════════════════════════════════════


class _IshikawaModule(QWidget):
    def __init__(self):
        super().__init__()
        self._inner = IshikawaWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Passe o mouse sobre as categorias e use o botão (+) para adicionar sub-causas ou (-) para excluir.\n"
            "• Clique duas vezes em qualquer texto pontilhado para editá-lo.\n"
            "• O layout das espinhas é posicionado e escalonado automaticamente.\n"
            "• Use o menu 'Exibir' para Zoom."
        )
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        layout.addWidget(self._inner)

    def reset_zoom(self): self._inner.update_zoom(1.0)
    def zoom_in(self): self._inner.zoom_in()
    def zoom_out(self): self._inner.zoom_out()




    def get_state(self):
        return {
            "nodes": self._inner.nodes,
            "next_id": self._inner.next_id
        }

    def set_state(self, state):
        if not state: return
        nodes = {}
        for k, v in state.get("nodes", {}).items():
            try: k_int = int(k)
            except: k_int = k
            nodes[k_int] = v
            
        if not nodes:
            nodes = {1: {"text": "EFEITO / PROBLEMA", "level": 0, "children": [], "parent": None}}
            cat_names = ["Método", "Máquina", "Material", "Mão de Obra", "Meio Ambiente", "Medição"]
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _IshikawaModule()
    w.setWindowTitle("Ishikawa — Causa e Efeito — ProEng")
    w.resize(1400, 900)
    w.show()
    sys.exit(app.exec_())

