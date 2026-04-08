# -*- coding: utf-8 -*-

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║  MÓDULO: Quadro Kanban — Gestão de Tarefas com Cards Arrastáveis           ║
# ╚════════════════════════════════════════════════════════════════════════════╝
#
# Responsabilidade:
#   Quadro Kanban interativo para gestão de tarefas com colunas (A Fazer, Em Andamento,
#   Feito, Cancelado). Cards são arrastáveis entre colunas, editáveis inline,
#   deletáveis, com persistência de estado e suporte a temas dinâmicos.
#
# Padrões de Projeto:
#   - Observer Pattern: SinaisKanban emite sinais (adicionar_card, mover_card, deletar_card)
#   - Factory Pattern: Geração dinâmica de cards baseado em tipo/data
#   - State Pattern: cards dict estruturado {"col_id": [{"id", "titulo", "desc"}]}
#   - Adapter Pattern: _ModuloKanban implementa interface BaseModule
#
# Estructura de Dados (cards):
#   Dict[str, List[Dict]] = {
#     "afazer": [{"id": 1, "titulo": "Tarefa 1", "desc": "Descrição", "prioridade": "ALTA"}],
#     "emandamento": [{"id": 2, "titulo": "Tarefa 2", "desc": "...", "prioridade": "MED"}],
#     "feito": [{"id": 3, "titulo": "Tarefa 3", "desc": "...", "prioridade": "BAIXA"}],
#     "cancelado": [{"id": 4, "titulo": "Tarefa 4", "desc": "...", "prioridade": "BAIXA"}],
#   }
#
# Colunas Padrão:
#   - 📋 A FAZER: Tarefas não iniciadas
#   - 🔄 EM ANDAMENTO: Tarefas em execução
#   - ✅ FEITO: Tarefas completadas
#   - 🚫 CANCELADO: Tarefas canceladas
#
# Layout: 4 colunas horizontais com scroll vertical independente por coluna
# Cards: Retângulos com borda 3px (neo-brutal), clicáveis para editar
# Tema: Neo-Brutalista com cores de prioridade para cards

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QLabel,
    QInputDialog,
    QMessageBox,
    QMenu,
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

from PyQt5.QtCore import (
    Qt,
    QRectF,
    QSize,
    pyqtSignal,
    QObject,
    QMimeData,
    QByteArray,
)

from proeng.core.themes import T
from proeng.core.utils import _c
from proeng.core.toolbar import _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class SinaisKanban(QObject):
    """Sinais do quadro Kanban."""
    adicionar_card = pyqtSignal(str)  # col_id
    mover_card = pyqtSignal(str, str, int)  # from_col, to_col, card_id
    deletar_card = pyqtSignal(str, int)  # col_id, card_id
    editar_card = pyqtSignal(str, int)  # col_id, card_id
    confirmar_card = pyqtSignal(str, int, str, str)  # col_id, card_id, titulo, desc


class CardKanban(QWidget):
    """Card individual do Kanban com suporte a drag-drop."""

    selecionado = pyqtSignal(str, int)  # col_id, card_id
    deletar_solicitado = pyqtSignal(str, int)  # col_id, card_id

    def __init__(self, col_id, card_id, titulo, desc):
        super().__init__()
        self.col_id = col_id
        self.card_id = card_id
        self.titulo = titulo
        self.desc = desc
        self._hov = False
        self._dragging = False
        self._drag_threshold = 5
        self._drag_start_pos = None

        self.setMinimumHeight(100)
        self.setStyleSheet("background: transparent; border: none;")
        self.setCursor(Qt.OpenHandCursor)
        self.setAttribute(Qt.WA_Hover)

    def event(self, e):
        """Detecta passagem do mouse."""
        if e.type() == 10:  # QEvent.HoverEnter
            self._hov = True
            self.update()
        elif e.type() == 11:  # QEvent.HoverLeave
            self._hov = False
            self.update()
        return super().event(e)

    def mousePressEvent(self, event):
        """Inicia drag ou abre editor."""
        if event.button() == Qt.RightButton:
            menu = QMenu(self)
            acao_editar = menu.addAction("Editar")
            acao_deletar = menu.addAction("Deletar")

            acao = menu.exec_(self.mapToGlobal(event.pos()))
            if acao == acao_deletar:
                self.deletar_solicitado.emit(self.col_id, self.card_id)
            return
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Detecta inicio de drag."""
        if not self._drag_start_pos:
            return
        if not self._dragging and event.buttons() & Qt.LeftButton:
            dist = (event.pos() - self._drag_start_pos).manhattanLength()
            if dist > self._drag_threshold:
                self._dragging = True
                self.setCursor(Qt.ClosedHandCursor)
                self.start_drag()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Cancela drag ou abre editor se for clique curto."""
        if self._dragging:
            self._dragging = False
            self._drag_start_pos = None
            self.setCursor(Qt.OpenHandCursor)
        elif event.button() == Qt.LeftButton:
            self.selecionado.emit(self.col_id, self.card_id)
        super().mouseReleaseEvent(event)

    def start_drag(self):
        """Inicia operacao de drag-and-drop nativo do Qt."""

        def create_ghost():
            pixmap = QPixmap(self.size())
            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            self.render(p)
            p.end()
            return pixmap

        ghost = create_ghost()
        mime = QMimeData()
        payload = f"{self.col_id},{self.card_id}".encode()
        mime.setData("application/x-kanban-card", QByteArray(payload))

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(ghost)
        drag.setHotSpot(self._drag_start_pos)
        drag.exec_(Qt.MoveAction)

    def paintEvent(self, event):
        """Renderiza card com borda e conteúdo baseado no status da coluna."""
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        # Cor de fundo do card baseada na coluna (status), igual ao Scrum
        mapa_cor_status = {
            "afazer": t.get("accent", "#FFE500"),
            "emandamento": t.get("accent_bright", "#0057FF"),
            "feito": t.get("btn_add", "#00C44F"),
            "cancelado": t.get("error", "#FF0000"),
        }
        cor_status = mapa_cor_status.get(self.col_id, t["bg_card"])

        # Fundo (muda para branco no hover para contraste)
        bg = "#FFFFFF" if self._hov else t["bg_card"]
        txt = "#FFFFFF" if self._hov else t["text"]
        txt_dim = "#FFFFFF" if self._hov else t["text"]
        p.setBrush(QBrush(QColor(bg)))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        # Barra lateral colorida por status da coluna
        p.setBrush(QBrush(QColor(cor_status)))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), 6, r.height()))

        # Sombra se passar mouse
        if self._hov:
            p.setBrush(QBrush(QColor(t.get("shadow", "#000000"))))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(QRectF(r.left() + 4, r.top() + 4, r.width() - 4, r.height() - 4))

        ff = t.get("font_family_content", "'Segoe UI', 'Arial', sans-serif")

        # Título
        p.setFont(QFont(ff, 10, QFont.Bold))
        p.setPen(QColor(txt))
        ret_titulo = QRectF(r.left() + 14, r.top() + 10, r.width() - 50, 24)
        fm = QFontMetrics(p.font())
        titulo_elidido = fm.elidedText(self.titulo, 0, int(ret_titulo.width()))
        p.drawText(ret_titulo, Qt.AlignLeft | Qt.AlignVCenter, titulo_elidido)

        # Badge de status (caixa arredondada, igual ao badge de pontos do Scrum)
        p.setBrush(QBrush(QColor(t["glass_border"])))
        p.setPen(QPen(Qt.NoPen))
        badge_r = QRectF(r.right() - 40, r.top() + 10, 30, 22)
        p.drawEllipse(badge_r.adjusted(4, 0, -4, 0))

        status_abbr = {
            "afazer": "AF",
            "emandamento": "EP",
            "feito": "F",
            "cancelado": "C",
        }
        p.setFont(QFont(ff, 9, QFont.Bold))
        p.setPen(QColor(txt))
        p.drawText(
            badge_r.adjusted(4, 0, -4, 0),
            Qt.AlignCenter,
            status_abbr.get(self.col_id, "?"),
        )

        # Descrição
        p.setFont(QFont(ff, 9))
        p.setPen(QColor(txt_dim))
        ret_desc = QRectF(r.left() + 14, r.top() + 36, r.width() - 28, 50)
        p.drawText(ret_desc, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self.desc)

        # Badge de status texto no rodapé (caixa com fundo visível)
        status_full = {
            "afazer": "A FAZER",
            "emandamento": "WIP",
            "feito": "FEITO",
            "cancelado": "CANCELADO",
        }
        status_label = status_full.get(self.col_id, "")
        p.setFont(QFont(ff, 7, QFont.Bold))

        badge_w = r.width() - 28
        badge_h = 16
        badge_x = r.left() + 14
        badge_y = r.bottom() - badge_h - 4

        bg_card2 = "#000000" if self._hov else t["bg_card2"]
        p.setBrush(QBrush(QColor(bg_card2)))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(badge_x, badge_y, badge_w, badge_h))

        fm_status = QFontMetrics(p.font())
        elidido = fm_status.elidedText(status_label, 0, int(badge_w))
        p.setPen(QColor(txt))
        p.drawText(QRectF(badge_x, badge_y, badge_w, badge_h), Qt.AlignCenter, elidido)

        p.end()


class ColunaKanban(QWidget):
    """Coluna individual do Kanban com suporte a drop."""

    card_selecionado = pyqtSignal(str, int)
    card_deletar_solicitado = pyqtSignal(str, int)
    card_dropped = pyqtSignal(str, int)  # col_id, card_id

    def __init__(self, col_id, col_titulo):
        super().__init__()
        self.col_id = col_id
        self.col_titulo = col_titulo
        self.cards = []
        self._highlighted = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header com título
        header = QLabel(col_titulo)
        header.setObjectName(f"colHeader_{col_id}")
        layout.addWidget(header)

        # Scroll area para cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName(f"colScroll_{col_id}")
        self.scroll.setStyleSheet("border: none;")

        self.widget_cards = QWidget()
        self.layout_cards = QVBoxLayout(self.widget_cards)
        self.layout_cards.setContentsMargins(0, 0, 0, 0)
        self.layout_cards.setSpacing(8)

        self.scroll.setWidget(self.widget_cards)
        layout.addWidget(self.scroll)

        # Botão para adicionar card
        btn_add = QPushButton("+")
        btn_add.setObjectName(f"colAdd_{col_id}")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(lambda: self._solicitar_adicionar_card())
        layout.addWidget(btn_add)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-kanban-card") or \
           event.mimeData().hasFormat("application/x-scrum-card"):
            event.acceptProposedAction()
            self._highlighted = True
            self.update()

    def dragLeaveEvent(self, event):
        self._highlighted = False
        self.update()

    def dropEvent(self, event):
        self._highlighted = False
        self.update()
        raw = event.mimeData().data("application/x-kanban-card")
        if raw.isEmpty():
            raw = event.mimeData().data("application/x-scrum-card")
        if raw.isEmpty():
            return
        # Parse: "col_id,card_id"
        parts = bytes(raw).split(b",")
        if len(parts) == 2:
            try:
                src_col = parts[0].decode()
                card_id = int(parts[1].decode())
                self.card_dropped.emit(self.col_id, card_id)
            except Exception:
                pass
    
    def _solicitar_adicionar_card(self):
        """Solicita adição de novo card a esta coluna."""
        titulo, ok = QInputDialog.getText(self, "Novo Card", "Título:")
        if ok and titulo:
            desc, ok_desc = QInputDialog.getText(self, "Novo Card", "Descrição:")
            if ok_desc:
                from proeng.modules.kanban import SinaisKanban
                # Será conectado pela classe pai
    
    def adicionar_card_visual(self, card):
        """Adiciona card visual à coluna."""
        self.layout_cards.insertWidget(
            self.layout_cards.count() - 1,
            card
        )
        self.cards.append(card)
        card.selecionado.connect(self.card_selecionado.emit)
        card.deletar_solicitado.connect(self.card_deletar_solicitado.emit)


class WidgetKanban(QWidget):
    """Widget principal do quadro Kanban."""
    
    def __init__(self):
        super().__init__()
        self.sinais = SinaisKanban()
        self.sinais.adicionar_card.connect(self._ao_adicionar_card)
        self.sinais.mover_card.connect(self._ao_mover_card)
        self.sinais.deletar_card.connect(self._ao_deletar_card)
        self.sinais.editar_card.connect(self._ao_editar_card)
        self.sinais.confirmar_card.connect(self._ao_confirmar_card)
        
        self.proximo_id = 1
        
        # Estrutura de dados
        self.cards = {
            "afazer": [],
            "emandamento": [],
            "feito": [],
            "cancelado": [],
        }
        
        # Mapa de IDs para localização
        self.mapa_id = {}  # {card_id: (col_id, index)}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura interface do Kanban."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Cria 4 colunas
        self.colunas = {}
        dados_colunas = [
            ("afazer", "A FAZER"),
            ("emandamento", "EM ANDAMENTO"),
            ("feito", "FEITO"),
            ("cancelado", "CANCELADO"),
        ]
        
        for col_id, col_titulo in dados_colunas:
            col = ColunaKanban(col_id, col_titulo)
            col.card_selecionado.connect(self._ao_card_selecionado)
            col.card_deletar_solicitado.connect(self._ao_card_deletar_solicitado)
            col.card_dropped.connect(self._ao_card_mover_drop)
            self.colunas[col_id] = col
            layout.addWidget(col)
        
        # Inicializa com alguns cards de exemplo
        self._adicionar_cards_exemplo()
    
    def _adicionar_cards_exemplo(self):
        """Adiciona cards de exemplo iniciais."""
        cards_exemplo = [
            ("afazer", "Analisar Requisitos", "Coletar e documentar requisitos do cliente"),
            ("afazer", "Design da Interface", "Criar prototipos de wireframes"),
            ("emandamento", "Implementar Backend", "Criar APIs REST"),
            ("feito", "Setup do Projeto", "Configurar repositorio e CI/CD"),
        ]

        for col_id, titulo, desc in cards_exemplo:
            card_id = self.proximo_id
            self.proximo_id += 1

            self.cards[col_id].append({
                "id": card_id,
                "titulo": titulo,
                "desc": desc,
            })

            self.mapa_id[card_id] = (col_id, len(self.cards[col_id]) - 1)

            widget_card = CardKanban(col_id, card_id, titulo, desc)
            self.colunas[col_id].adicionar_card_visual(widget_card)
    
    def _ao_adicionar_card(self, col_id):
        """Adiciona novo card à coluna."""
        titulo, ok = QInputDialog.getText(self, "Novo Card", "Título:")
        if ok and titulo:
            desc, ok_desc = QInputDialog.getText(self, "Novo Card", "Descrição:")
            if ok_desc:
                card_id = self.proximo_id
                self.proximo_id += 1

                self.cards[col_id].append({
                    "id": card_id,
                    "titulo": titulo,
                    "desc": desc,
                })

                self.mapa_id[card_id] = (col_id, len(self.cards[col_id]) - 1)

                widget_card = CardKanban(col_id, card_id, titulo, desc)
                self.colunas[col_id].adicionar_card_visual(widget_card)
    
    def _ao_mover_card(self, from_col, to_col, card_id):
        """Move card entre colunas."""
        if card_id in self.mapa_id:
            col_antiga, idx = self.mapa_id[card_id]
            dados_card = self.cards[col_antiga][idx]
            
            # Remove de coluna anterior
            self.cards[col_antiga].pop(idx)
            
            # Adiciona em coluna nova
            self.cards[to_col].append(dados_card)
            
            # Atualiza mapa
            self.mapa_id[card_id] = (to_col, len(self.cards[to_col]) - 1)
            
            # Atualiza visual
            for widget_card in self.colunas[col_antiga].cards:
                if widget_card.card_id == card_id:
                    self.colunas[col_antiga].cards.remove(widget_card)
                    self.colunas[col_antiga].layout_cards.removeWidget(widget_card)
                    widget_card.deleteLater()
                    break
            
            widget_card = CardKanban(
                to_col,
                dados_card["id"],
                dados_card["titulo"],
                dados_card["desc"],
            )
            self.colunas[to_col].adicionar_card_visual(widget_card)
    
    def _ao_deletar_card(self, col_id, card_id):
        """Deleta card da coluna."""
        if card_id in self.mapa_id:
            _, idx = self.mapa_id[card_id]
            self.cards[col_id].pop(idx)
            del self.mapa_id[card_id]
            
            # Remove visual
            for widget_card in self.colunas[col_id].cards[:]:
                if widget_card.card_id == card_id:
                    self.colunas[col_id].cards.remove(widget_card)
                    self.colunas[col_id].layout_cards.removeWidget(widget_card)
                    widget_card.deleteLater()
                    break
    
    def _ao_card_selecionado(self, col_id, card_id):
        """Card foi selecionado para edição."""
        if col_id in self.cards:
            for card in self.cards[col_id]:
                if card["id"] == card_id:
                    titulo, ok = QInputDialog.getText(
                        self, "Editar Card", "Título:",
                        text=card["titulo"]
                    )
                    if ok and titulo:
                        desc, ok_desc = QInputDialog.getText(
                            self, "Editar Card", "Descrição:",
                            text=card["desc"]
                        )
                        if ok_desc:
                            self.sinais.confirmar_card.emit(col_id, card_id, titulo, desc)
    
    def _ao_card_deletar_solicitado(self, col_id, card_id):
        """Deleta card."""
        resposta = QMessageBox.question(
            self, "Confirmar", "Deletar este card?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            self.sinais.deletar_card.emit(col_id, card_id)
    
    def _ao_editar_card(self, col_id, card_id):
        """Edita card."""
        pass
    
    def _ao_confirmar_card(self, col_id, card_id, titulo, desc):
        """Confirma mudanças do card."""
        if col_id in self.cards:
            for card in self.cards[col_id]:
                if card["id"] == card_id:
                    card["titulo"] = titulo
                    card["desc"] = desc

                    # Atualiza visual
                    for widget_card in self.colunas[col_id].cards:
                        if widget_card.card_id == card_id:
                            widget_card.titulo = titulo
                            widget_card.desc = desc
                            widget_card.update()
                            break

    def _mover_card_visual(self, from_col_id, to_col_id, card_id):
        """Move card de uma coluna para outra (visual + dados)."""
        # Encontra os dados do card
        card_data = None
        if from_col_id in self.cards:
            for c in self.cards[from_col_id]:
                if c["id"] == card_id:
                    card_data = c
                    self.cards[from_col_id].remove(c)
                    break
        if card_data is None:
            return

        # Adiciona na coluna destino
        if to_col_id not in self.cards:
            return
        self.cards[to_col_id].append(card_data)

        # Atualiza mapa de IDs
        self.mapa_id[card_id] = (to_col_id, len(self.cards[to_col_id]) - 1)

        # Remove widget da coluna antiga
        src_col = self.colunas.get(from_col_id)
        if src_col:
            for widget_card in src_col.cards[:]:
                if widget_card.card_id == card_id:
                    src_col.cards.remove(widget_card)
                    src_col.layout_cards.removeWidget(widget_card)
                    widget_card.deleteLater()
                    break

        # Cria novo widget na coluna destino
        widget_card = CardKanban(
            to_col_id, card_data["id"], card_data["titulo"],
            card_data["desc"],
        )
        widget_card.selecionado.connect(self._ao_card_selecionado)
        widget_card.deletar_solicitado.connect(self._ao_card_deletar_solicitado)
        self.colunas[to_col_id].adicionar_card_visual(widget_card)

    def _ao_card_mover_drop(self, to_col_id, card_id):
        """Handler para card solto em coluna por drag-and-drop."""
        if card_id in self.mapa_id:
            from_col_id, _ = self.mapa_id[card_id]
            if from_col_id == to_col_id:
                return  # mesma coluna
            self._mover_card_visual(from_col_id, to_col_id, card_id)

    def refresh_theme(self):
        """Reaplica tema apos mudanca de tema global."""
        for col_id in self.colunas:
            for widget_card in self.colunas[col_id].cards:
                widget_card.update()
    
    def get_state(self):
        """Retorna estado persistível do Kanban."""
        return {
            "schema": "kanban.v1",
            "cards": self.cards,
            "proximo_id": self.proximo_id,
        }
    
    def set_state(self, state):
        """Restaura estado do Kanban."""
        if not state:
            return
        
        if state.get("schema") == "kanban.v1":
            self.cards = state.get("cards", self.cards)
            self.proximo_id = state.get("proximo_id", self.proximo_id)


class _ModuloKanban(BaseModule):
    """Adaptador que implementa interface BaseModule para Kanban."""
    
    def __init__(self):
        super().__init__()
        
        # Cria widget interno Kanban
        self._interno = WidgetKanban()
        
        # Oculta toolbar interna
        _hide_inner_toolbar(self._interno)
        
        # Texto de ajuda
        self.help_text = (
            "KANBAN BOARD — Guia Rapido\n\n"
            "O Kanban e um sistema visual de gestao de tarefas que "
            "organiza o trabalho em colunas representando os estagios "
            "do fluxo: A FAZER, EM ANDAMENTO, FEITO e CANCELADO. "
            "Permite limitar o trabalho em progresso e identificar "
            "gargalos rapidamente.\n\n"
            "COMO USAR:\n"
            "• Clique no botao (+) na parte inferior de cada coluna "
            "para adicionar um novo card de tarefa.\n"
            "• Clique em um card para editar seu titulo, descricao "
            "e nivel de prioridade.\n"
            "• Clique com o botao direito sobre um card para acessar "
            "opcoes de edicao ou exclusao.\n"
            "• Arraste os cards entre colunas para atualizar o status "
            "da tarefa (drag-and-drop).\n\n"
            "PRIORIDADES:\n"
            "• ALTA: destaque visual em cor quente (urgente)\n"
            "• MEDIA: destaque intermediario (padrao)\n"
            "• BAIXA: destaque sutil (pode aguardar)\n\n"
            "DICAS:\n"
            "• Mantenha poucas tarefas em 'EM ANDAMENTO' para "
            "focar no que realmente importa.\n"
            "• Mova para 'CANCELADO' ao inves de excluir, para "
            "manter o historico de decisoes."
        )
        
        # Layout padrão
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._interno)
    
    def get_state(self):
        """Retorna estado persistível."""
        return self._interno.get_state()
    
    def set_state(self, state):
        """Restaura estado."""
        self._interno.set_state(state)
    
    def refresh_theme(self):
        """Reaplica tema ao mudar tema global."""
        self._interno.refresh_theme()
    
    def get_view(self):
        """Retorna view gráfica (não aplicável para Kanban)."""
        return None
    
    def zoom_in(self):
        """Zoom in (não aplicável para Kanban)."""
        pass
    
    def zoom_out(self):
        """Zoom out (não aplicável para Kanban)."""
        pass
    
    def reset_zoom(self):
        """Reset zoom (não aplicável para Kanban)."""
        pass
