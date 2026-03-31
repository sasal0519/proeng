# -*- coding: utf-8 -*-
"""Módulo EAP — Estrutura Analítica do Projeto (WBS)."""
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

class NodeSignals(QObject):
    commit_text = pyqtSignal(int, str)
    add_child   = pyqtSignal(int)
    add_sibling = pyqtSignal(int)
    delete_node = pyqtSignal(int)
    edit_start  = pyqtSignal(int)


class NodeItem(QGraphicsItem):
    def __init__(self, node_id, wbs, text, is_root, shape, signals, zoom):
        super().__init__()
        self.node_id  = node_id
        self.wbs      = wbs
        self.text     = text
        self.is_root  = is_root
        self.shape    = shape
        self.signals  = signals
        self.zoom     = zoom
        self._hovered = False

        self._font_wbs  = QFont("Consolas", max(5, int(8  * zoom)), QFont.Bold)
        self._font_text = QFont("Segoe UI",  max(5, int(10 * zoom)),
                                QFont.Bold if is_root else QFont.Normal)
        self._font_ph   = QFont("Segoe UI",  max(5, int(9  * zoom)))
        self._font_ph.setItalic(True)
        self._font_btn  = QFont("Consolas",  max(6, int(9  * zoom)), QFont.Bold)

        self._calc_size()
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def _get_text_width(self, fm, text):
        if hasattr(fm, 'horizontalAdvance'):
            return fm.horizontalAdvance(text)
        return fm.width(text)

    def _calc_size(self):
        fm  = QFontMetrics(self._font_text)
        fmw = QFontMetrics(self._font_wbs)
        sample = self.text if self.text.strip() else "Nomear"
        pad_x = 30 * self.zoom
        pad_y = 24 * self.zoom # Slightly more vertical padding
        if self.shape in ["ellipse", "diamond"]:
            pad_x *= 1.6
            pad_y *= 1.8
            
        # Max width for EAP nodes
        max_node_w = 180 * self.zoom
        wbs_w = self._get_text_width(fmw, self.wbs)
        
        # Calculate text height with wrapping
        available_text_w = max_node_w - pad_x
        text_rect = fm.boundingRect(0, 0, int(available_text_w), 1000, Qt.AlignCenter | Qt.TextWordWrap, sample)
        
        self._w = max(100 * self.zoom, max(text_rect.width(), wbs_w) + pad_x)
        self._h = max(45 * self.zoom, text_rect.height() + fmw.height() + pad_y)

    def width(self):  return self._w
    def height(self): return self._h

    def boundingRect(self):
        m = 14 * self.zoom
        return QRectF(-m, -m, self._w + m * 2, self._h + m * 2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)
        empty = not self.text.strip()
        r     = QRectF(0, 0, self._w, self._h)
        bs    = 14 * self.zoom
        hbs   = bs / 2

        # Fundo com o novo motor universal de gradiente (High-Fidelity)
        painter.setBrush(QBrush(_glass_grad(r, self._hovered or self.is_root)))

        border = t["accent_bright"] if self.is_root else (t["accent"] if not empty else t["accent_dim"])
        style  = Qt.SolidLine if not empty else Qt.DashLine
        painter.setPen(QPen(Qt.NoPen))

        if self.shape == "roundrect":
            painter.drawRoundedRect(r, 12, 12)
        elif self.shape == "ellipse":
            painter.drawEllipse(r)
        elif self.shape == "diamond":
            poly = QPolygonF([
                QPointF(self._w / 2, 0),
                QPointF(self._w, self._h / 2),
                QPointF(self._w / 2, self._h),
                QPointF(0, self._h / 2)
            ])
            painter.drawPolygon(poly)

        if self.is_root and not empty and self.shape == "roundrect":
            painter.save()
            clip_path = QPainterPath()
            clip_path.addRoundedRect(r, 12, 12)
            painter.setClipPath(clip_path)

            sg = QLinearGradient(0, 0, self._w, 0)
            sg.setColorAt(0, QColor(t["accent_bright"]))
            sg.setColorAt(0.7, QColor(0,0,0,0))
            painter.setBrush(QBrush(sg))
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
            wbs_rect = QRectF(6*self.zoom, offset_y, self._w - 12*self.zoom, fmw.height())
            painter.drawText(wbs_rect, Qt.AlignHCenter | Qt.AlignVCenter, self.wbs)
            
            # Subtitle (text) — increase padding
            painter.setFont(self._font_text)
            painter.setPen(QColor(t["text"]))
            # Add padding to avoid rounded corner clipping
            p_val = 15 * self.zoom if self.is_root else 8 * self.zoom
            text_rect = QRectF(p_val, offset_y + fmw.height(), self._w - 2*p_val, self._h - offset_y - fmw.height() - 5*self.zoom)
            painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)
            # Main text — word-wrap with bounded height
            painter.setFont(self._font_text)
            painter.setPen(QColor(t["text"]))
            txt_fm   = QFontMetrics(self._font_text)
            txt_y    = offset_y + fmw.height() + 2 * self.zoom
            txt_h    = self._h - txt_y - 4 * self.zoom
            txt_rect = QRectF(4 * self.zoom, txt_y, self._w - 8 * self.zoom, max(txt_h, txt_fm.height()))
            painter.drawText(txt_rect, Qt.AlignCenter | Qt.TextWordWrap, self.text)

        if self._hovered:
            t_btn = T()
            painter.setFont(self._font_btn)
            self._draw_btn(painter, QRectF(self._w / 2 - hbs, self._h - hbs, bs, bs), "+", t_btn["btn_add"])
            if not self.is_root:
                self._draw_btn(painter, QRectF(self._w - hbs, self._h / 2 - hbs, bs, bs), "+", t_btn["btn_sib"])
                self._draw_btn(painter, QRectF(-hbs, self._h / 2 - hbs, bs, bs), "−", t_btn["btn_del"])

    def _draw_btn(self, painter, rect, label, color):
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(QPen(QColor("#FF6666"), 1))
        painter.drawRoundedRect(rect, 4, 4)
        painter.setPen(QColor("#FAE8E8"))
        painter.drawText(rect, Qt.AlignCenter, label)

    def _btn_rects(self):
        bs  = 14 * self.zoom
        hbs = bs / 2
        rects = {"child": QRectF(self._w / 2 - hbs, self._h - hbs, bs, bs)}
        if not self.is_root:
            rects["sibling"] = QRectF(self._w - hbs, self._h / 2 - hbs, bs, bs)
            rects["delete"]  = QRectF(-hbs, self._h / 2 - hbs, bs, bs)
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
        nid    = self.node_id
        if self._hovered:
            for action, rect in self._btn_rects().items():
                if rect.contains(event.pos()):
                    if action == "child":
                        QTimer.singleShot(0, lambda s=sinais, n=nid: s.add_child.emit(n))
                    elif action == "sibling":
                        QTimer.singleShot(0, lambda s=sinais, n=nid: s.add_sibling.emit(n))
                    elif action == "delete":
                        QTimer.singleShot(0, lambda s=sinais, n=nid: s.delete_node.emit(n))
                    return
        QTimer.singleShot(0, lambda s=sinais, n=nid: s.edit_start.emit(n))

    def mouseDoubleClickEvent(self, event):
        event.accept()
        sinais = self.signals
        nid    = self.node_id
        QTimer.singleShot(0, lambda s=sinais, n=nid: s.edit_start.emit(n))


class FloatingEditor(QLineEdit):
    committed = pyqtSignal(int, str)

    def __init__(self, parent_view):
        super().__init__(parent_view)
        self._node_id  = -1
        self._original = ""
        self._done     = False
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
            self.setStyleSheet("QLineEdit { background:#2A0F0F; color:#FAE8E8; border:2px solid #CC2222; border-radius:5px; font-family:'Segoe UI'; font-size:11pt; padding:4px 10px; }")
        self.hide()

    def open(self, node_id, current_text, scene_rect, view):
        self._apply_style()
        self._node_id  = node_id
        self._original = current_text
        self._done     = False
        tl = view.mapFromScene(scene_rect.topLeft())
        w  = max(120, int(scene_rect.width()))
        h  = 32
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
    """Widget completo do EAP para embutir no app principal."""
    def __init__(self):
        super().__init__()

        self.base_pad_x      = 35
        self.base_pad_y      = 60
        self.base_min_width  = 100
        self.base_box_height = 40
        self.zoom            = 1.0
        self.next_id         = 2
        self.wbs_numbers     = {}
        self.node_dimensions = {}
        self.node_positions  = {}
        self._scene_items    = []
        self.nodes = {1: {"text": "", "children": [], "parent": None, "shape": "roundrect"}}
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

        sep = QWidget(); sep.setFixedSize(1, 26); tb.addWidget(sep)

        self._eap_btns = []
        for lbl, fn in [("🔍−", lambda *a: self.zoom_out()),
                         ("🔍+", lambda *a: self.zoom_in()),
                         ("⟳ 100%", lambda *a: self.update_zoom(1.0))]:
            b = QPushButton(lbl); b.clicked.connect(fn)
            tb.addWidget(b); self._eap_btns.append(b)

        tb.addStretch()

        self._eap_exp_btns = []
        for lbl, key in [("📄 PDF","pdf"),("🖼 PNG","png")]:
            b2 = QPushButton(lbl)
            b2.clicked.connect(lambda _,k=key: self._export_scene(k))
            tb.addWidget(b2); self._eap_exp_btns.append(b2)

        layout.addWidget(toolbar)

        self.scene = QGraphicsScene()
        self.view  = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.NoDrag)
        self.view.setStyleSheet("border:none;")
        layout.addWidget(self.view)
        self.refresh_theme()

    def _refresh_view_bg(self):
        if not hasattr(self, 'view'):
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
        for b in self._eap_btns: b.setStyleSheet(btn_s)
        for b in self._eap_exp_btns: b.setStyleSheet(exp_s)
        if hasattr(self, 'view'):
            self._refresh_view_bg()
        
        # Refresh scene items and connections
        if hasattr(self, 'scene'):
            self.scene.update()
            # Redesenha para garantir que cores de linhas (que não são itens custom) atualizem
            self.draw_eap()
        
        if hasattr(self, '_float_editor'):
            self._float_editor._apply_style()

    def zoom_in(self, *args):  self.update_zoom(self.zoom * 1.15)
    def zoom_out(self, *args): self.update_zoom(self.zoom / 1.15)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out()
        else:
            self.view.verticalScrollBar().setValue(
                self.view.verticalScrollBar().value() - event.angleDelta().y() // 3)

    def update_zoom(self, z):
        self.zoom       = max(0.3, min(z, 3.0))
        self.pad_x      = self.base_pad_x      * self.zoom
        self.pad_y      = self.base_pad_y      * self.zoom
        self.min_width  = self.base_min_width  * self.zoom
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
            poly = QPolygonF([QPointF(16, 4), QPointF(28, 16), QPointF(16, 28), QPointF(4, 16)])
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
        action_rect    = menu.addAction(self._create_shape_icon("roundrect"), "Retângulo Arredondado")
        action_ellipse = menu.addAction(self._create_shape_icon("ellipse"),   "Elipse (Círculo)")
        action_diamond = menu.addAction(self._create_shape_icon("diamond"),   "Losango (Decisão)")
        selected = menu.exec_(QCursor.pos())
        if selected == action_rect:    return "roundrect"
        if selected == action_ellipse: return "ellipse"
        if selected == action_diamond: return "diamond"
        return None

    def _on_commit(self, node_id, new_text):
        if node_id in self.nodes:
            self.nodes[node_id]["text"] = new_text
        self.draw_eap()

    def _on_edit_start(self, node_id):
        if node_id not in self.node_positions:
            return
        nw, nh  = self.node_dimensions[node_id]
        x, y    = self.node_positions[node_id]
        scene_r = QRectF(x - nw / 2, y - nh / 2, nw, nh)
        self._float_editor.open(node_id, self.nodes[node_id]["text"], scene_r, self.view)

    def _on_add_child(self, parent_id):
        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {"text": "", "children": [], "parent": parent_id, "shape": shape}
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_eap()
        QTimer.singleShot(60, lambda n=new_id: self._on_edit_start(n))

    def _on_add_sibling(self, node_id):
        parent_id = self.nodes[node_id]["parent"]
        if parent_id is None: return
        shape = self._choose_shape()
        if not shape: return
        new_id = self.next_id; self.next_id += 1
        self.nodes[new_id] = {"text": "", "children": [], "parent": parent_id, "shape": shape}
        self.nodes[parent_id]["children"].append(new_id)
        self.draw_eap()
        QTimer.singleShot(60, lambda n=new_id: self._on_edit_start(n))

    def _on_delete(self, node_id):
        label = self.nodes[node_id]["text"] or "nó sem nome"
        ans = QMessageBox.question(self, "Excluir",
              f"Excluir '{label}' e todas as suas sub-tarefas?",
              QMessageBox.Yes | QMessageBox.No)
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
        self.wbs_numbers[node_id] = wbs
        for i, cid in enumerate(self.nodes[node_id]["children"]):
            self.calculate_wbs(cid, f"{wbs}.{i+1}")

    def pre_calcular_dimensoes(self):
        self.node_dimensions.clear()
        for nid in self.nodes:
            shape = self.nodes[nid].get("shape", "roundrect")
            tmp = NodeItem(nid, self.wbs_numbers.get(nid, ""),
                           self.nodes[nid]["text"], nid == 1,
                           shape, self.signals, self.zoom)
            self.node_dimensions[nid] = (tmp.width(), tmp.height())

    def calcular_posicoes(self, node_id, nivel):
        filhos = self.nodes[node_id]["children"]
        nw, nh = self.node_dimensions[node_id]
        y = 80 * self.zoom + nivel * (nh + self.pad_y)
        if not filhos:
            x = self.current_leaf_x + nw / 2
            self.current_leaf_x += nw + self.pad_x
        else:
            xs = [self.calcular_posicoes(c, nivel + 1) for c in filhos]
            x  = sum(xs) / len(xs)
        self.node_positions[node_id] = (x, y)
        return x

    def draw_eap(self):
        self._scene_items = []
        self.scene.clear()
        if not self.nodes: return
        self.node_positions.clear()
        self.wbs_numbers.clear()
        self.calculate_wbs(1, "1")
        self.pre_calcular_dimensoes()
        self.current_leaf_x = 80 * self.zoom
        self.calcular_posicoes(1, nivel=0)
        vw       = self.view.viewport().width() or 800
        offset_x = vw / 2 - self.node_positions[1][0]
        min_x    = min(p[0] - self.node_dimensions[n][0] / 2
                       for n, p in self.node_positions.items())
        if min_x + offset_x < 80 * self.zoom:
            offset_x = 80 * self.zoom - min_x
        for n in self.node_positions:
            x, y = self.node_positions[n]
            self.node_positions[n] = (x + offset_x, y)
        # Recursively draw tree connections, and also handle independent roots
        for root_id in [n for n, data in self.nodes.items() if data["parent"] is None]:
            self._draw_connections(root_id)
        self._draw_nodes()
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))

    def _draw_connections(self, node_id):
        px, py = self.node_positions[node_id]
        pw, _  = self.node_dimensions[node_id]
        p1 = QPointF(px + pw / 2, py)
        
        if "cross_links" in self.nodes[node_id]:
            pen_cross = QPen(QColor(T()["accent_bright"]), max(1.5, int(2 * self.zoom)), Qt.DashLine, Qt.RoundCap, Qt.RoundJoin)
            for cid in self.nodes[node_id]["cross_links"]:
                if cid not in self.node_positions: continue
                cx, cy = self.node_positions[cid]
                cw, _  = self.node_dimensions[cid]
                # Distancia entre eles
                p2 = QPointF(cx - cw/2, cy) if cx > px else QPointF(cx + cw/2, cy)
                
                path = QPainterPath()
                path.moveTo(p1)
                mid_x = (p1.x() + p2.x()) / 2
                path.lineTo(mid_x, p1.y())
                path.lineTo(mid_x, p2.y())
                path.lineTo(p2)
                self._scene_items.append(self.scene.addPath(path, pen_cross))

                arrow_size = 8 * self.zoom
                dir_x = -1 if cx > px else 1
                poly = QPolygonF([p2, QPointF(p2.x() + arrow_size*dir_x, p2.y() - arrow_size/2), QPointF(p2.x() + arrow_size*dir_x, p2.y() + arrow_size/2)])
                self._scene_items.append(self.scene.addPolygon(poly, QPen(Qt.NoPen), QBrush(QColor(T()["accent_bright"]))))

        filhos = self.nodes[node_id]["children"]
        if not filhos: return
        _, ph  = self.node_dimensions[node_id]
        py_bot = py + ph / 2
        mid_y  = py_bot + self.pad_y / 2
        t_draw = T(); pen = QPen(QColor(t_draw["line_eap"]), max(1, int(2 * self.zoom)),
                      Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        for cid in filhos:
            cx, cy = self.node_positions[cid]
            cy_top = cy - self.node_dimensions[cid][1] / 2
            for coords in [(px, py_bot, px, mid_y),
                           (px, mid_y,  cx, mid_y),
                           (cx, mid_y,  cx, cy_top)]:
                self._scene_items.append(self.scene.addLine(*coords, pen))
            self._draw_connections(cid)

    def _draw_nodes(self):
        for nid, (x, y) in self.node_positions.items():
            nw, nh = self.node_dimensions[nid]
            shape  = self.nodes[nid].get("shape", "roundrect")
            item = NodeItem(nid, self.wbs_numbers[nid],
                            self.nodes[nid]["text"],
                            nid == 1, shape, self.signals, self.zoom)
            item.setPos(x - nw / 2, y - nh / 2)
            self.scene.addItem(item)
            self._scene_items.append(item)





class _EAPModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = EAPWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Passe o mouse sobre um bloco para ver botões de adicionar Filho (+) ou Irmão (+).\n"
            "• O código WBS (1.1, 1.2...) é gerado e atualizado sozinho.\n"
            "• Clique duplo para renomear os pacotes de trabalho.\n"
            "• Use o menu 'Exibir' para Zoom e ajuste de tela."
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
            "schema": "eap.v1",
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
        self._inner.nodes = nodes if nodes else {1: {"text": "", "children": [], "parent": None, "shape": "roundrect"}}
        self._inner.next_id = state.get("next_id", 2)
        self._inner.draw_eap()

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

