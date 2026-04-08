# -*- coding: utf-8 -*-
# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MÓDULO: Scrum Sprint Board — Gestão de Sprints e Backlog                 ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# Responsabilidade:
#   Quadro Scrum com Backlog, Sprint (To Do / In Progress / Review / Done),
#   suporte a story points, burndown visual e persistência de estado.
#   Cards arrastáveis entre colunas, edição inline, deleção.
#
# Padrões: Observer (sinais), State (cards dict), Factory (card creation)
# Interface: BaseModule (get_state, set_state, refresh_theme)

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QInputDialog,
    QMessageBox,
    QScrollArea,
    QMenu,
    QSpinBox,
    QDialog,
    QTextEdit,
)
from PyQt5.QtGui import (
    QPainter,
    QBrush,
    QColor,
    QFont,
    QPen,
    QFontMetrics,
    QPixmap,
    QDrag,
)
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject, QByteArray, QMimeData

from proeng.core.themes import T
from proeng.core.base_module import BaseModule
from proeng.core.toolbar import _hide_inner_toolbar


class SinaisScrum(QObject):
    add_item_sprint = pyqtSignal()
    add_item_backlog = pyqtSignal()
    mover_item = pyqtSignal(str, str, int)  # from, to, item_id
    deletar_item = pyqtSignal(str, int)  # col_id, item_id
    editar_item = pyqtSignal(str, int)
    planejar_sprint = pyqtSignal()
    fechar_sprint = pyqtSignal()


class ScrumTaskDialog(QDialog):
    """Diálogo para criar/editar item Scrum."""
    def __init__(self, titulo="", desc="", pontos=3, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Item do Sprint")
        self.setMinimumWidth(400)
        t = T()

        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("Título:"))
        self.titulo_edit = QInputDialog()
        self._titulo = titulo
        self._desc = desc
        self._pontos = pontos

        self.text_titulo = QTextEdit(self)
        self.text_titulo.setPlainText(titulo)
        self.text_titulo.setFixedHeight(50)
        lay.addWidget(self.text_titulo)

        lay.addWidget(QLabel("Descrição:"))
        self.text_desc = QTextEdit(self)
        self.text_desc.setPlainText(desc)
        self.text_desc.setFixedHeight(100)
        lay.addWidget(self.text_desc)

        lay.addWidget(QLabel("Story Points:"))
        self.spin_pontos = QSpinBox(self)
        self.spin_pontos.setRange(0, 21)
        self.spin_pontos.setValue(pontos)
        lay.addWidget(self.spin_pontos)

        self.btn_ok = QPushButton("OK")
        self.btn_cancelar = QPushButton("Cancelar")
        btn_lay = QHBoxLayout()
        btn_lay.addWidget(self.btn_ok)
        btn_lay.addWidget(self.btn_cancelar)
        lay.addLayout(btn_lay)

        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancelar.clicked.connect(self.reject)

        self._apply_style()

    def _apply_style(self):
        t = T()
        self.setStyleSheet(f"""
            QDialog {{ background: {t["bg_app"]}; }}
            QLabel {{ color: {t["text"]}; font-weight: bold; font-size: 12px; }}
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["text"]};
                border: 2px solid {t["accent"]}; padding: 6px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {t["accent"]}; color: #FFFFFF; }}
        """)

    def get_data(self):
        return {
            "titulo": self.text_titulo.toPlainText().strip(),
            "descricao": self.text_desc.toPlainText().strip(),
            "pontos": self.spin_pontos.value(),
        }


class StoryCard(QWidget):
    """Card individual de história no Scrum Board com suporte a drag-drop."""
    selecionado = pyqtSignal(str, int)
    deletar_solicitado = pyqtSignal(str, int)

    def __init__(self, col_id, item_id, titulo, pontos, status="TODO"):
        super().__init__()
        self.col_id = col_id
        self.item_id = item_id
        self.titulo = titulo
        self.pontos = pontos
        self.status = status
        self._hov = False
        self._dragging = False
        self._drag_threshold = 5
        self._drag_start_pos = None

        self.setMinimumHeight(80)
        self.setStyleSheet("background: transparent; border: none;")
        self.setCursor(Qt.OpenHandCursor)
        self.setAttribute(Qt.WA_Hover)

    def event(self, e):
        if e.type() == 10:
            self._hov = True
            self.update()
        elif e.type() == 11:
            self._hov = False
            self.update()
        return super().event(e)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            menu.addAction("Editar").triggered.connect(
                lambda: self.selecionado.emit(self.col_id, self.item_id)
            )
            menu.addAction("Deletar").triggered.connect(
                lambda: self.deletar_solicitado.emit(self.col_id, self.item_id)
            )
            menu.exec_(self.mapToGlobal(event.pos()))
            return
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._drag_start_pos:
            return
        if not self._dragging and event.buttons() & Qt.LeftButton:
            dist = (event.pos() - self._drag_start_pos).manhattanLength()
            if dist > self._drag_threshold:
                self._dragging = True
                self.setCursor(Qt.ClosedHandCursor)
                self._start_drag()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_start_pos = None
            self.setCursor(Qt.OpenHandCursor)
        elif event.button() == Qt.LeftButton:
            self.selecionado.emit(self.col_id, self.item_id)
        super().mouseReleaseEvent(event)

    def _start_drag(self):
        """Inicia operacao de drag-and-drop."""
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        self.render(p)
        p.end()

        mime = QMimeData()
        payload = f"{self.col_id},{self.item_id}".encode()
        mime.setData("application/x-scrum-card", QByteArray(payload))

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pixmap)
        drag.setHotSpot(self._drag_start_pos)
        drag.exec_(Qt.MoveAction)

    def paintEvent(self, event):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        # Fundo escuro + texto branco no hover
        bg = t.get("accent_bright", "#0057FF") if self._hov else t["bg_card"]
        txt = "#FFFFFF" if self._hov else t["text"]

        p.setBrush(QBrush(QColor(bg)))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        # Barra lateral colorida por status
        mapa_cor_status = {
            "TODO": t.get("accent", "#FFE500"),
            "IN_PROGRESS": t.get("accent_bright", "#0057FF"),
            "REVIEW": t.get("block_orange", "#FF6B00"),
            "DONE": t.get("btn_add", "#00C44F"),
        }
        cor_status = mapa_cor_status.get(self.status, t["accent"])

        p.setBrush(QBrush(QColor(cor_status)))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), 6, r.height()))

        # Sombra on hover
        if self._hov:
            p.setBrush(QBrush(QColor(t.get("shadow", "#000000"))))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(QRectF(r.left() + 4, r.top() + 4, r.width() - 4, r.height() - 4))

        # Título
        ff = t.get("font_family_content", "'Segoe UI', 'Arial', sans-serif")
        p.setFont(QFont(ff, 10, QFont.Bold))
        p.setPen(QColor(txt))
        ret_titulo = QRectF(r.left() + 14, r.top() + 10, r.width() - 50, 24)
        fm = QFontMetrics(p.font())
        titulo_elidido = fm.elidedText(self.titulo, 0, int(ret_titulo.width()))
        p.drawText(ret_titulo, Qt.AlignLeft | Qt.AlignVCenter, titulo_elidido)

        # Badge de story points
        p.setBrush(QBrush(QColor(t["glass_border"])))
        p.setPen(QPen(Qt.NoPen))
        badge_r = QRectF(r.right() - 40, r.top() + 10, 30, 22)
        p.drawEllipse(badge_r.adjusted(4, 0, -4, 0))

        p.setFont(QFont(ff, 9, QFont.Bold))
        p.setPen(QColor(txt))
        p.drawText(
            badge_r.adjusted(4, 0, -4, 0),
            Qt.AlignCenter,
            str(self.pontos) if self.pontos > 0 else "?"
        )

        # Status label
        status_labels = {
            "TODO": "TODO",
            "IN_PROGRESS": "WIP",
            "REVIEW": "REVIEW",
            "DONE": "DONE",
        }
        p.setFont(QFont(ff, 7, QFont.Bold))
        p.setPen(QColor(txt))
        p.drawText(
            QRectF(r.left() + 14, r.bottom() - 20, 60, 14),
            Qt.AlignLeft,
            status_labels.get(self.status, ""),
        )

        p.end()


class ScrumColumn(QWidget):
    """Coluna individual do Scrum Board com suporte a drop."""
    card_selecionado = pyqtSignal(str, int)
    card_deletar_solicitado = pyqtSignal(str, int)
    card_dropped = pyqtSignal(str, int)  # col_id, item_id

    def __init__(self, col_id, col_titulo, col_key):
        super().__init__()
        self.col_id = col_id
        self.col_titulo = col_titulo
        self.col_key = col_key
        self.cards = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        # Header
        self.header = QLabel(col_titulo)
        self.header.setFixedHeight(40)
        layout.addWidget(self.header)

        # Scroll area para cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.widget_cards = QWidget()
        self.layout_cards = QVBoxLayout(self.widget_cards)
        self.layout_cards.setContentsMargins(0, 0, 0, 0)
        self.layout_cards.setSpacing(8)
        self.scroll.setWidget(self.widget_cards)
        layout.addWidget(self.scroll)

        # Botao add
        self.btn_add = QPushButton("+")
        self.btn_add.setFixedHeight(34)
        layout.addWidget(self.btn_add)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-scrum-card") or \
           event.mimeData().hasFormat("application/x-kanban-card"):
            event.acceptProposedAction()

    def dropEvent(self, event):
        raw = event.mimeData().data("application/x-scrum-card")
        if raw.isEmpty():
            raw = event.mimeData().data("application/x-kanban-card")
        if raw.isEmpty():
            return
        parts = bytes(raw).split(b",")
        if len(parts) == 2:
            try:
                card_id = int(parts[1].decode())
                self.card_dropped.emit(self.col_key, card_id)
            except Exception:
                pass

    def refresh_theme(self):
        t = T()
        self.header.setStyleSheet(f"""
            font-weight: 900; font-size: 13px; color: {t["accent"]};
            font-family: {t.get("font_family", "Arial")};
            background: {t["bg_card"]}; border: {t.get("border_width", 3)}px solid {t["glass_border"]};
            padding: 6px 12px;
        """)
        self.btn_add.setStyleSheet(f"""
            QPushButton {{
                background: {t["bg_card"]}; color: {t["text"]};
                border: {t.get("border_width", 3)}px solid {t["glass_border"]};
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {t["accent"]}; color: #FFFFFF;
                border-color: {t["accent_bright"]};
            }}
        """)
        self.scroll.setStyleSheet(f"border: none; background: {t['bg_card']};")
        for card in self.cards:
            card.update()


class ScrumWidget(QWidget):
    """Widget principal do Scrum Sprint Board."""
    def __init__(self):
        super().__init__()
        self.sinais = SinaisScrum()
        self.sinais.add_item_sprint.connect(self._ao_adicionar_sprint)
        self.sinais.add_item_backlog.connect(self._ao_adicionar_backlog)
        self.sinais.mover_item.connect(self._ao_mover_item)
        self.sinais.deletar_item.connect(self._ao_deletar_item)
        self.sinais.editar_item.connect(self._ao_editar_item)
        self.sinais.planejar_sprint.connect(self._ao_planejar_sprint)
        self.sinais.fechar_sprint.connect(self._ao_fechar_sprint)

        self.proximo_id = 1

        # Dados: sprints e backlog
        self.backlog = []  # [{id, titulo, desc, pontos}]
        self.sprint_cols = {
            "todo": [],
            "in_progress": [],
            "review": [],
            "done": [],
        }
        self.sprint_name = "Sprint 1"

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        self.lbl_sprint_name = QLabel("SPRINT")
        self.btn_backlog = QPushButton("BACKLOG")
        self.btn_planejar = QPushButton("PLANEJAR SPRINT")
        self.btn_fechar = QPushButton("FECHAR SPRINT")
        self.btn_add_sprint = QPushButton("+ SPRINT ITEM")

        for btn in [self.btn_backlog, self.btn_planejar, self.btn_fechar, self.btn_add_sprint]:
            toolbar.addWidget(btn)

        toolbar.addStretch()
        toolbar.addWidget(self.lbl_sprint_name)
        layout.addLayout(toolbar)

        # Colunas do Sprint
        colunas_sprint = QHBoxLayout()
        colunas_sprint.setSpacing(12)

        self.colunas_sprint = {}
        dados_colunas = [
            ("todo", "TODO"),
            ("in_progress", "IN PROGRESS"),
            ("review", "REVIEW"),
            ("done", "DONE"),
        ]

        for col_key, col_titulo in dados_colunas:
            col = ScrumColumn(col_key, col_titulo, col_key)
            col.btn_add.clicked.connect(lambda _, ck=col_key: self._add_card_dialog(ck))
            self.colunas_sprint[col_key] = col
            colunas_sprint.addWidget(col)

        layout.addLayout(colunas_sprint, stretch=1)

        # Conexoes de sinais das colunas
        for col in self.colunas_sprint.values():
            col.card_selecionado.connect(self._ao_card_selecionado)
            col.card_deletar_solicitado.connect(self._ao_card_deletar_solicitado)
            col.card_dropped.connect(self._ao_card_dropped)

        # Botão Backlog
        self.btn_backlog.clicked.connect(self._ao_abrir_backlog)
        self.btn_planejar.clicked.connect(lambda: self.sinais.planejar_sprint.emit())
        self.btn_fechar.clicked.connect(lambda: self.sinais.fechar_sprint.emit())
        self.btn_add_sprint.clicked.connect(lambda: self.sinais.add_item_sprint.emit())

        # Exemplo inicial
        self._adicionar_exemplos()
        self.refresh_theme()

    def _adicionar_exemplos(self):
        """Adiciona cards de exemplo."""
        exemplos = [
            ("todo", "Configurar ambiente", 2),
            ("todo", "Escrever user stories", 3),
            ("in_progress", "Implementar login", 5),
            ("review", "Design da API", 3),
            ("done", "Definir arquitetura", 2),
        ]
        for col_key, titulo, pontos in exemplos:
            item_id = self.proximo_id
            self.proximo_id += 1
            self.sprint_cols[col_key].append({
                "id": item_id,
                "titulo": titulo,
                "descricao": "",
                "pontos": pontos,
            })
            widget_card = StoryCard(col_key, item_id, titulo, pontos, self._status_from_col(col_key))
            self.colunas_sprint[col_key].cards.append(widget_card)
            self.colunas_sprint[col_key].layout_cards.insertWidget(
                self.colunas_sprint[col_key].layout_cards.count(), widget_card
            )
            widget_card.selecionado.connect(self._ao_card_selecionado)
            widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)

    def _status_from_col(self, col_key):
        map_status = {
            "todo": "TODO",
            "in_progress": "IN_PROGRESS",
            "review": "REVIEW",
            "done": "DONE",
        }
        return map_status.get(col_key, "TODO")

    def _add_card_dialog(self, col_key):
        dialog = ScrumTaskDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["titulo"]:
                return
            item_id = self.proximo_id
            self.proximo_id += 1
            self.sprint_cols[col_key].append({
                "id": item_id,
                "titulo": data["titulo"],
                "descricao": data["descricao"],
                "pontos": data["pontos"],
            })
            status = self._status_from_col(col_key)
            widget_card = StoryCard(
                col_key, item_id, data["titulo"], data["pontos"], status
            )
            widget_card.selecionado.connect(self._ao_card_selecionado)
            widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)
            self.colunas_sprint[col_key].cards.append(widget_card)
            self.colunas_sprint[col_key].layout_cards.insertWidget(
                self.colunas_sprint[col_key].layout_cards.count(), widget_card
            )
            self._atualizar_label_sprint()

    def _ao_adicionar_sprint(self):
        """Adiciona item ao Sprint (coluna TODO por padrão)."""
        self._add_card_dialog("todo")

    def _ao_adicionar_backlog(self):
        """Adiciona item ao Backlog."""
        dialog = ScrumTaskDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["titulo"]:
                return
            item_id = self.proximo_id
            self.proximo_id += 1
            self.backlog.append({
                "id": item_id,
                "titulo": data["titulo"],
                "descricao": data["descricao"],
                "pontos": data["pontos"],
            })
            QMessageBox.information(self, "Backlog", f"'{data['titulo']}' adicionado ao Backlog.")

    def _ao_mover_item(self, from_col, to_col, item_id):
        """Move item entre colunas."""
        pass  # Implementado via UI interativa

    def _ao_deletar_item(self, col_key, item_id):
        """Deleta item da coluna."""
        if item_id in self._find_item(col_key, item_id):
            self.sprint_cols[col_key] = [
                i for i in self.sprint_cols[col_key] if i["id"] != item_id
            ]
            for card in self.colunas_sprint[col_key].cards[:]:
                if card.item_id == item_id:
                    self.colunas_sprint[col_key].cards.remove(card)
                    self.colunas_sprint[col_key].layout_cards.removeWidget(card)
                    card.deleteLater()
                    break

    def _find_item(self, col_key, item_id):
        """Encontra item na coluna."""
        for item in self.sprint_cols.get(col_key, []):
            if item["id"] == item_id:
                return {item_id: item}
        return {}

    def _ao_editar_item(self, col_key, _item_id):
        """N/A placeholder."""
        pass

    def _ao_card_selecionado(self, col_key, item_id):
        """Card clicado para edição."""
        for card_data in self.sprint_cols.get(col_key, []):
            if card_data["id"] == item_id:
                dialog = ScrumTaskDialog(
                    titulo=card_data["titulo"],
                    desc=card_data["descricao"],
                    pontos=card_data["pontos"],
                    parent=self,
                )
                if dialog.exec_() == QDialog.Accepted:
                    data = dialog.get_data()
                    card_data["titulo"] = data["titulo"]
                    card_data["descricao"] = data["descricao"]
                    card_data["pontos"] = data["pontos"]
                    # Atualiza visual
                    for widget_card in self.colunas_sprint[col_key].cards:
                        if widget_card.item_id == item_id:
                            widget_card.titulo = data["titulo"]
                            widget_card.pontos = data["pontos"]
                            widget_card.update()
                    self._atualizar_label_sprint()
                break

    def _ao_card_deletar_solicitado(self, col_key, item_id):
        """Solicitação de deletar card."""
        resposta = QMessageBox.question(
            self, "Confirmar", "Deletar este item?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            self._ao_deletar_item(col_key, item_id)

    def _ao_card_dropped(self, to_col_key, item_id):
        """Handler para card solto em coluna por drag-and-drop."""
        # Encontra coluna de origem
        from_col_key = None
        card_data = None
        for ck, items in self.sprint_cols.items():
            for item in items:
                if item["id"] == item_id:
                    from_col_key = ck
                    card_data = item
                    break
            if from_col_key:
                break

        if not card_data or not from_col_key:
            return

        if from_col_key == to_col_key:
            return

        # Remove dados da origem
        self.sprint_cols[from_col_key] = [
            i for i in self.sprint_cols[from_col_key] if i["id"] != item_id
        ]

        # Adiciona na coluna destino
        self.sprint_cols[to_col_key].append(card_data)

        # Remove widget visual da origem
        src_col = self.colunas_sprint.get(from_col_key)
        if src_col:
            for w in src_col.cards[:]:
                if w.item_id == item_id:
                    src_col.cards.remove(w)
                    src_col.layout_cards.removeWidget(w)
                    w.deleteLater()
                    break

        # Cria novo widget na coluna destino
        status = self._status_from_col(to_col_key)
        widget_card = StoryCard(
            to_col_key, item_id, card_data["titulo"], card_data["pontos"], status
        )
        widget_card.selecionado.connect(self._ao_card_selecionado)
        widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)
        self.colunas_sprint[to_col_key].cards.append(widget_card)
        self.colunas_sprint[to_col_key].layout_cards.insertWidget(
            self.colunas_sprint[to_col_key].layout_cards.count(), widget_card
        )
        self._atualizar_label_sprint()

    def _ao_planejar_sprint(self):
        """Planejar Sprint: mover itens do Backlog para Sprint TODO."""
        if not self.backlog:
            QMessageBox.information(self, "Backlog", "Backlog está vazio.")
            return

        nomes = [f"{i['titulo']} ({i['pontos']}pts)" for i in self.backlog]
        item, ok = QInputDialog.getItem(
            self, "Backlog", "Selecione itens para mover ao Sprint:",
            nomes, 0, False
        )
        if ok and item:
            idx = nomes.index(item)
            movido = self.backlog.pop(idx)
            item_id = self.proximo_id
            self.proximo_id += 1
            self.sprint_cols["todo"].append({
                "id": item_id,
                "titulo": movido["titulo"],
                "descricao": movido["descricao"],
                "pontos": movido["pontos"],
            })
            status = self._status_from_col("todo")
            widget_card = StoryCard(
                "todo", item_id, movido["titulo"], movido["pontos"], status
            )
            widget_card.selecionado.connect(self._ao_card_selecionado)
            widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)
            self.colunas_sprint["todo"].cards.append(widget_card)
            self.colunas_sprint["todo"].layout_cards.insertWidget(
                self.colunas_sprint["todo"].layout_cards.count(), widget_card
            )
            self._atualizar_label_sprint()

    def _ao_fechar_sprint(self):
        """Fechar Sprint atual."""
        done_items = self.sprint_cols.get("done", [])
        total_points = sum(i["pontos"] for i in done_items)
        all_sprint = sum(len(v) for v in self.sprint_cols.values())

        QMessageBox.information(
            self, "Sprint Fechada",
            f"Sprint encerrada com:\n"
            f"• {len(done_items)} itens concluídos\n"
            f"• {total_points} story points entregues\n"
            f"• {all_sprint - len(done_items)} itens não concluídos"
        )

    def _ao_abrir_backlog(self):
        """Mostra diálogo do Backlog."""
        if not self.backlog:
            QMessageBox.information(self, "Backlog", "Backlog está vazio.\nAdicione itens com o botão '+'.")
            return

        texto = "\n".join(
            f"• {i['titulo']} ({i['pontos']}pts)" for i in self.backlog
        )
        QMessageBox.information(self, "Backlog", f"Backlog:\n\n{texto}")

    def refresh_theme(self):
        """Reaplica tema."""
        t = T()
        self.lbl_sprint_name.setStyleSheet(f"""
            color: {t["accent"]}; font-weight: 900; font-size: 16px;
            font-family: {t.get("font_family", "Arial")};
        """)
        for col in self.colunas_sprint.values():
            col.refresh_theme()

    def get_state(self):
        """Retorna estado do Scrum."""
        return {
            "schema": "scrum.v1",
            "sprint_name": self.sprint_name,
            "sprint_cols": self.sprint_cols,
            "backlog": self.backlog,
            "proximo_id": self.proximo_id,
        }

    def set_state(self, state):
        """Restaura estado do Scrum."""
        if not state:
            return
        if state.get("schema") == "scrum.v1":
            self.sprint_cols = state.get("sprint_cols", self.sprint_cols)
            self.backlog = state.get("backlog", self.backlog)
            self.sprint_name = state.get("sprint_name", "Sprint 1")
            self.proximo_id = state.get("proximo_id", 1)
            # Reconstruir visuais
            for col_key, col in self.colunas_sprint.items():
                # Limpar widgets existentes
                for card in col.cards:
                    col.layout_cards.removeWidget(card)
                    card.deleteLater()
                col.cards.clear()
                # Recriar
                for item_data in self.sprint_cols.get(col_key, []):
                    status = self._status_from_col(col_key)
                    widget_card = StoryCard(
                        col_key, item_data["id"], item_data["titulo"],
                        item_data["pontos"], status
                    )
                    widget_card.selecionado.connect(self._ao_card_selecionado)
                    widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)
                    col.cards.append(widget_card)
                    col.layout_cards.insertWidget(col.layout_cards.count(), widget_card)

    def _atualizar_label_sprint(self):
        """Atualiza etiqueta do sprint com total de pontos."""
        total = sum(
            i["pontos"] for items in self.sprint_cols.values() for i in items
        )
        self.lbl_sprint_name.setText(
            f"{self.sprint_name} — {total}pts"
        )


class _ScrumModule(BaseModule):
    """Adaptador que implementa BaseModule para Scrum."""
    def __init__(self):
        super().__init__()
        self._inner = ScrumWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "SCRUM SPRINT BOARD — Guia Rapido\n\n"
            "O Scrum e um framework agil para gestao de projetos "
            "iterativos. O Sprint Board organiza as historias de "
            "usuario (user stories) em 4 colunas: TODO, IN PROGRESS, "
            "REVIEW e DONE, com suporte a story points para "
            "estimativa de esforco.\n\n"
            "COMO USAR:\n"
            "• Clique em '+ SPRINT ITEM' para adicionar uma nova "
            "historia diretamente na coluna TODO.\n"
            "• Clique no botao (+) em cada coluna para adicionar "
            "um item naquela etapa especifica.\n"
            "• Clique em um card para editar titulo, descricao e "
            "story points. Botao direito para deletar.\n"
            "• Arraste os cards entre colunas (drag-and-drop) para "
            "atualizar o progresso da historia.\n\n"
            "BACKLOG E SPRINTS:\n"
            "• Use 'BACKLOG' para visualizar itens em espera.\n"
            "• Use 'PLANEJAR SPRINT' para mover itens do Backlog "
            "para a Sprint ativa (coluna TODO).\n"
            "• Use 'FECHAR SPRINT' para encerrar o ciclo e ver "
            "metricas de entrega (itens concluidos, pontos).\n\n"
            "STORY POINTS:\n"
            "• Cada card exibe seu valor em story points no badge.\n"
            "• O total de pontos do Sprint aparece no cabecalho.\n"
            "• Use a escala Fibonacci (1, 2, 3, 5, 8, 13, 21) "
            "para estimativas consistentes."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def get_state(self):
        return self._inner.get_state()

    def set_state(self, state):
        self._inner.set_state(state)

    def refresh_theme(self):
        self._inner.refresh_theme()

    def get_view(self):
        return None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _ScrumModule()
    w.setWindowTitle("Scrum Sprint Board — PRO ENG")
    w.resize(1400, 800)
    w.show()
    sys.exit(app.exec_())
