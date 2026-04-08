# -*- coding: utf-8 -*-

# Módulo Gantt Chart — Cronograma de Projetos com Cálculo de Caminho Crítico (CPM).
#
# Responsabilidade: Fornecer widget interativo de cronograma de projeto (Gantt chart)
# com suporte a:
# - Tarefas com datas de início/fim, progresso, marcos (milestones)
# - Predecessoras (dependências entre tarefas)
# - Cálculo automático de Caminho Crítico (CPM) com forward/backward pass
# - Renderização visual com barra de progresso, hoje (today line), zoom infinito
# - Edição inline e exportação PNG/PDF
#
# Visualmente:
#   - Header com calendário (meses/dias)
#   - Linha "today" em cor destaque
#   - Barras coloridas para tarefas (vermelho se crítica, cor tema caso contrário)
#   - Marcos representados por círculos
#   - Setas tracejadas para dependências
#
# Padrões: Command Pattern (sinais), Model-View (tasks dict vs GanttWidget)

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
    QScrollArea,
    QSplitter,
    QGraphicsPathItem,
    QMenu,
    QListView,
    QLineEdit,
    QLabel,
    QStackedWidget,
    QTextEdit,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QInputDialog,
    QFileDialog,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QComboBox,
    QSlider,
    QDialog,
    QCheckBox,
    QGraphicsTextItem,
    QGraphicsLineItem,
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
    QLinearGradient,
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
    QDate,
)

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.utils import _export_view, _c, _nb_paint_node, _is_nb
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class GanttSignals(QObject):
    """
    Sistema de sinais (Command Pattern) para comunicação entre componentes do Gantt.
    
    Emite eventos assíncronos para adição, edição, exclusão e cálculo de tarefas.
    Desacopla o modelo de dados da UI, permitindo reatividade em tempo real.
    
    Sinais:
    - add_task(): Solicita criação de nova tarefa com editor modal
    - delete_task(int): Remove tarefa pelo ID
    - edit_task(int): Abre editor para tarefa existente
    - commit_task(int, dict): Aplica mudanças (nome, datas, progresso)
    - calculate_cpm(): Executa algoritmo CPM forward/backward passes
    """
    add_task = pyqtSignal()
    delete_task = pyqtSignal(int)
    edit_task = pyqtSignal(int)
    commit_task = pyqtSignal(int, dict)
    calculate_cpm = pyqtSignal()


class GanttTaskItem(QGraphicsItem):
    """
    Elemento visual de tarefa individual no canvas Gantt.
    
    Renderiza como retângulo arredondado (QGraphicsItem) com:
    - Barra de progresso interna (verde)
    - Cor vermelha (#DC3545) se tarefa crítica, tema accent caso contrário
    - Botão delete (×) exibido ao hover
    - Duplo clique abre editor de tarefa
    
    Model-View pattern: task_data é referência ao dict da tarefa, mudanças
    refletem automaticamente na renderização. Zoom ajusta dimensões dinamicamente.
    
    Args:
        task_id (int): Identificador único da tarefa
        task_data (dict): Referência ao dict {name, start_date, end_date, progress, is_critical, ...}
        zoom (float): Fator de zoom (1.0 = normal)
        signals (GanttSignals): Emissor de eventos de edição/exclusão
    """
    def __init__(self, task_id, task_data, zoom, signals):
        super().__init__()
        self.task_id = task_id
        self.task_data = task_data
        self.zoom = zoom
        self.signals = signals
        self.hovered = False
        self._width = 200 * zoom
        self._height = 32 * zoom

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QCursor(Qt.SizeAllCursor))
        self.setZValue(10)

    def boundingRect(self):
        # Define hitbox expandido com margem de 5px para permitir seleção fácil
        m = 5 * self.zoom
        return QRectF(-m, -m, self._width + m * 2, self._height + m * 2)

    def paint(self, painter, option, widget=None):
        # Renderiza barra de tarefa com progresso, cor crítica/tema, delete button se hover
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)

        r = QRectF(0, 0, self._width, self._height)

        is_critical = self.task_data.get("is_critical", False)
        progress = self.task_data.get("progress", 0)

        if is_critical:
            border_color = "#DC3545"
            bg_color = "#DC3545"
        else:
            border_color = t["accent"]
            bg_color = t["accent"]

        # Estilo neo-brutalist
        if _is_nb(t):
            painter.save()
            painter.setClipRect(r)
            _nb_paint_node(painter, r, self.hovered or self.isSelected(),
                           border_color=border_color, shadow=False, radius=5)

            # Barra de progresso sólida (sem transparência)
            if progress > 0:
                prog_rect = QRectF(0, 0, self._width * progress / 100, self._height)
                painter.setBrush(QBrush(QColor(t.get("btn_add", "#22C55E"))))
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRect(prog_rect)

            painter.restore()

            # Re-desenha nome sobre o fundo
            name = self.task_data.get("name", "Tarefa")
            text_rect = r.adjusted(8, 4, -8, -4)
            painter.setFont(QFont(t.get("font_family_content", "'Segoe UI'").replace("'", ""), int(10 * self.zoom), QFont.Bold))
            # Fundo sólido escuro para texto legível
            painter.save()
            painter.setClipRect(text_rect)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, name)
            painter.restore()
        else:
            # Fallback não neo-brutalist
            if is_critical:
                bg_color = QColor(220, 53, 69, 200)
                border_color = QColor(220, 53, 69)
            else:
                bg_color = QColor(t["accent"])
                border_color = QColor(t["accent"])

            painter.setBrush(QBrush(bg_color))
            painter.setPen(QPen(border_color, 2 if self.isSelected() else 1))
            painter.drawRoundedRect(r, 4, 4)

            if progress > 0:
                prog_rect = QRectF(0, 0, self._width * progress / 100, self._height)
                prog_color = QColor(40, 167, 69, 180)
                painter.setBrush(QBrush(prog_color))
                painter.setPen(QPen(Qt.NoPen))
                painter.drawRoundedRect(prog_rect, 4, 4)

            painter.setPen(QColor(t.get("node_text", "#FFFFFF")))
            font = QFont(t.get("font_family_content", "'Segoe UI', 'Arial', sans-serif").replace("'", ""), int(10 * self.zoom), QFont.Bold)
            painter.setFont(font)

            name = self.task_data.get("name", "Tarefa")
            text_rect = r.adjusted(8, 4, -8, -4)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, name)

        # Se hover, renderiza botão delete (×) no canto superior direito
        if self.hovered:
            bs = 20 * self.zoom
            hbs = bs / 2

            del_rect = QRectF(self._width - hbs, -hbs, bs, bs)
            painter.setBrush(QBrush(QColor(220, 53, 69)))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(del_rect, 4, 4)
            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(QFont("Consolas", int(14 * self.zoom), QFont.Bold))
            painter.drawText(del_rect, Qt.AlignCenter, "×")

    def hoverEnterEvent(self, e):
        # Ativa flag hover para renderizar botão delete + atualiza visualização
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        # Desativa hover e remove botão delete da visualização
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        # Detecta clique no botão delete (durante hover) e emite sinal assíncrono
        # Usa QTimer.singleShot para garantir que sinal é processado após evento
        if event.button() == Qt.LeftButton and self.hovered:
            bs = 20 * self.zoom
            hbs = bs / 2
            del_rect = QRectF(self._width - hbs, -hbs, bs, bs)
            if del_rect.contains(event.pos()):
                QTimer.singleShot(
                    0, lambda: self.signals.delete_task.emit(self.task_id)
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        # Duplo clique abre editor modal da tarefa através de sinal assíncrono
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_task.emit(self.task_id))


class GanttCanvas(QGraphicsView):
    """
    Canvas/view para renderização do cronograma Gantt.
    
    QGraphicsView observa QGraphicsScene que contém:
    - Header com calendário (nomes meses/dias)
    - Linha "today" de referência (tracejada, cor accent bright)
    - Barras de tarefas com progresso interno
    - Símbolos de marcos (círculos)
    - Setas de dependência (linhas tracejadas entre sucessoras)
    
    Suporta zoom infinito via Ctrl+MouseWheel (escala 0.3x-3.0x).
    Herda do QGraphicsView para suportar pan/zoom eficiente em grandes diagramas.
    
    Args:
        scene (QGraphicsScene): Cena já criada onde itens serão adicionados
        parent: Widget pai (None por padrão)
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.zoom_level = 1.0
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        t = T()
        self.setBackgroundBrush(QBrush(QColor(t["bg_app"])))

    def wheelEvent(self, event):
        # Implementa zoom infinito: Ctrl+ScrollUp = 1.1x, Ctrl+ScrollDown = 0.9x
        # Limita zoom entre 0.3x (muito distante) e 3.0x (muito perto)
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            self.zoom_level = max(0.3, min(self.zoom_level, 3.0))
            self.scale(
                1.1 if event.angleDelta().y() > 0 else 0.9,
                1.1 if event.angleDelta().y() > 0 else 0.9,
            )
        else:
            super().wheelEvent(event)


class TaskEditorDialog(QDialog):
    """
    Modal dialog para edição de tarefa individual.
    
    Campos:
    - name (QLineEdit): Nome/descrição da tarefa
    - start_date (QDateEdit): Data de início com calendário popup
    - end_date (QDateEdit): Data de término
    - progress_slider (QSlider): 0-100% com indicador visual
    - predecessor_combo (QComboBox): Seleção de tarefa predecessora (-1 = nenhuma)
    - is_milestone_check (QCheckBox): Marca tarefa como marco (sem duration)
    
    Retorna dict com campos editados em get_data() se dialog aceito.
    
    Args:
        task_data (dict ou None): Dados da tarefa para populate. Se None, cria nova.
        parent: Widget pai para posicionamento modal
    """
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setWindowTitle("Editar Tarefa")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        # Constrói formulário modal com campos de edição para tarefa
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome da tarefa")
        layout.addWidget(QLabel("Nome:"))
        layout.addWidget(self.name_input)

        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("Início:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addDays(7))
        date_layout.addWidget(QLabel("Fim:"))
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        layout.addWidget(QLabel("Progresso (%):"))
        layout.addWidget(self.progress_slider)

        self.predecessor_combo = QComboBox()
        self.predecessor_combo.addItem("Nenhuma", -1)
        layout.addWidget(QLabel("Predecessora:"))
        layout.addWidget(self.predecessor_combo)

        self.is_milestone_check = QCheckBox("Marco (Milestone)")
        layout.addWidget(self.is_milestone_check)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Salvar")
        self.btn_cancel = QPushButton("Cancelar")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        if self.task_data:
            self.name_input.setText(self.task_data.get("name", ""))
            self.start_date.setDate(
                self.task_data.get("start_date", QDate.currentDate())
            )
            self.end_date.setDate(
                self.task_data.get("end_date", QDate.currentDate().addDays(7))
            )
            self.progress_slider.setValue(self.task_data.get("progress", 0))
            self.is_milestone_check.setChecked(
                self.task_data.get("is_milestone", False)
            )

    def get_data(self):
        # Coleta dados do formulário em dict para aplicação na tarefa
        return {
            "name": self.name_input.text(),
            "start_date": self.start_date.date(),
            "end_date": self.end_date.date(),
            "progress": self.progress_slider.value(),
            "is_milestone": self.is_milestone_check.isChecked(),
            "predecessor": self.predecessor_combo.currentData(),
        }


class GanttWidget(QWidget):
    """
    Widget principal do Gantt: modelo + visão de cronograma com CPM.
    
    Estrutura:
    - tasks dict: {task_id -> {name, start_date, end_date, progress, is_milestone,
                               predecessor, is_critical, es/ef/ls/lf/slack}}
    - GanttSignals: Emite add_task, delete_task, edit_task, commit_task, calculate_cpm
    - _draw_gantt(): Renderiza modelo em scene gráfica
    - _calculate_cpm(): Forward/backward pass para encontrar caminho crítico
    
    Model-View: tasks é modelo, scene renderiza. Zoom escalado por fator 0.3-3.0x.
    Zoom afeta dimensões de barras, fonts, espacamentos mas não o algoritmo CPM.
    
    CPM (Critical Path Method):
    1. Forward pass: Calcula ES (Early Start) e EF (Early Finish) ordenando por datas
    2. Backward pass: Calcula LS (Late Start) e LF (Late Finish) de trás para frente
    3. Slack = LS - ES. Se slack <= 0, tarefa é crítica (no caminho crítico)
    
    Padrões: Factory (task rendering), Observer (signals/slots), Model-View (tasks dict)
    """
    def __init__(self):
        super().__init__()
        self.zoom = 1.0
        self.next_task_id = 1
        self.tasks = {}
        self.signals = GanttSignals()
        self.signals.add_task.connect(self._on_add_task)
        self.signals.delete_task.connect(self._on_delete_task)
        self.signals.edit_task.connect(self._on_edit_task)
        self.signals.commit_task.connect(self._on_commit_task)
        self.signals.calculate_cpm.connect(self._calculate_cpm)

        self._setup_ui()
        self._create_sample_tasks()
        self.refresh_theme()

    def _setup_ui(self):
        # Constrói UI: painel esquerdo (botões + lista) | gantt_canvas via splitter
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        # Painel esquerdo: container com botões acima da lista
        left_panel = QWidget()
        left_widget_layout = QVBoxLayout(left_panel)
        left_widget_layout.setContentsMargins(0, 0, 0, 0)
        left_widget_layout.setSpacing(0)
        left_panel.setFixedWidth(250)

        # Botões de ação como quadros quadrados
        self.btn_add = QPushButton("＋\nNova Tarefa")
        self.btn_add.setFixedSize(250, 80)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        self.btn_add.clicked.connect(lambda: self.signals.add_task.emit())
        left_widget_layout.addWidget(self.btn_add)

        self.btn_cpm = QPushButton("Calcular\nCPM")
        self.btn_cpm.setFixedSize(250, 80)
        self.btn_cpm.setCursor(Qt.PointingHandCursor)
        self.btn_cpm.clicked.connect(lambda: self.signals.calculate_cpm.emit())
        left_widget_layout.addWidget(self.btn_cpm)

        # Layout de tarefas (scrollável)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.setContentsMargins(0, 4, 0, 4)
        self.task_layout.setSpacing(6)
        self.task_layout.addStretch()

        task_scroll = QScrollArea()
        task_scroll.setWidget(self.task_container)
        task_scroll.setWidgetResizable(True)
        task_scroll.setMinimumHeight(200)
        task_scroll.setStyleSheet("border: none; background: transparent;")
        left_widget_layout.addWidget(task_scroll)

        self.splitter.addWidget(left_panel)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 1500)
        t = T()
        self.scene.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
        self.canvas = GanttCanvas(self.scene)
        self.splitter.addWidget(self.canvas)

        layout.addWidget(self.splitter)

    def _create_sample_tasks(self):
        # Popula com 6 tarefas de exemplo para demonstração
        today = QDate.currentDate()
        self.add_task("Inicio do Projeto", today, today, is_milestone=True)
        self.add_task("Planejamento", today.addDays(1), today.addDays(10))
        self.add_task("Design", today.addDays(11), today.addDays(30))
        self.add_task("Desenvolvimento", today.addDays(31), today.addDays(60))
        self.add_task("Testes", today.addDays(61), today.addDays(75))
        self.add_task(
            "Implantação", today.addDays(76), today.addDays(90), is_milestone=True
        )

    def add_task(
        self, name, start_date, end_date, progress=0, is_milestone=False, predecessor=-1
    ):
        # Adiciona tarefa ao modelo com inicialização de CPM values (es/ef/ls/lf/slack)
        task_id = self.next_task_id
        self.next_task_id += 1

        self.tasks[task_id] = {
            "name": name,
            "start_date": start_date,
            "end_date": end_date,
            "progress": progress,
            "is_milestone": is_milestone,
            "predecessor": predecessor,
            "is_critical": False,
            "es": 0,
            "ef": 0,
            "ls": 0,
            "lf": 0,
            "slack": 0,
        }

        self._update_task_list()
        self._draw_gantt()

    def _update_task_list(self):
        # Limpa todas as task buttons existentes
        for i in reversed(range(self.task_layout.count())):
            w = self.task_layout.itemAt(i).widget()
            if w is not None:
                w.deleteLater()

        # Cria botões quadrados para cada tarefa
        for task_id, data in sorted(
            self.tasks.items(), key=lambda x: x[1]["start_date"]
        ):
            is_critical = data.get("is_critical", False)
            is_milestone = data.get("is_milestone", False)
            btn = QPushButton(f"{data['name']}")
            btn.setFixedHeight(72)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, tid=task_id: self._on_edit_task(tid))
            self._task_btn_style(btn, is_critical, is_milestone)
            self.task_layout.insertWidget(self.task_layout.count() - 1, btn)

    def _draw_gantt(self):
        # Renderiza cronograma Gantt completo em QGraphicsScene:
        # 1. Header com calendário simplificado (apenas meses)
        # 2. Painel esquerco com nomes de tarefas (220px fixo)
        # 3. Painel direito com barras de progresso e marcos (escalado por zoom)
        self.scene.clear()
        t = T()

        LEFT_W = 220  # Largura da coluna esquerda

        if not self.tasks:
            return

        # Calcula intervalo de datas e dimensões escaladas
        min_date = min(task["start_date"] for task in self.tasks.values())
        max_date = max(task["end_date"] for task in self.tasks.values())
        days_range = min_date.daysTo(max_date) + 30

        day_width = 30 * self.zoom
        row_height = 55 * self.zoom
        header_height = 45 * self.zoom

        # ── Header: fundo sólido com borda do tema ──
        hdr_border = t.get("sig_border", t["line"])
        header_bg = QGraphicsRectItem(0, 0, 250 + days_range * day_width, header_height)
        header_bg.setBrush(QBrush(QColor(t["accent"])))
        header_bg.setPen(QPen(QColor(hdr_border), 2))
        self.scene.addItem(header_bg)

        # Título da coluna esquerda (centralizado no header)
        title_fs = 17
        title_font = QFont(
            t.get("font_family_content", "'Segoe UI'").replace("'", ""),
            title_fs,
            QFont.Bold,
        )
        title_h = QFontMetrics(title_font).height()
        title_text = QGraphicsTextItem("TAREFA")
        title_text.setFont(title_font)
        title_text.setDefaultTextColor(QColor(t["text"]))
        title_text.setPos(14, (header_height - title_h) / 2)
        self.scene.addItem(title_text)

        month_names_pt = [
            "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        ]

        # ── Calendário: apenas nomes dos meses (centralizados no header) ──
        current_date = min_date
        for i in range(days_range + 1):
            x = 250 + i * day_width
            # Primeiro de cada mês → nome do mês (centralizado no header)
            if current_date.day() == 1:
                month_fs = 12
                month_font = QFont(
                    t.get("font_family_content", "'Segoe UI'").replace("'", ""),
                    month_fs,
                    QFont.Bold,
                )
                month_h = QFontMetrics(month_font).height()
                month_text = QGraphicsTextItem(
                    month_names_pt[current_date.month() - 1].upper()
                )
                month_text.setFont(month_font)
                month_text.setDefaultTextColor(QColor(t["text"]))
                month_text.setPos(x + 6, (header_height - month_h) / 2)
                self.scene.addItem(month_text)

            # Linhas verticais de grade: apenas para 1º do mês (divisões limpas)
            if current_date.day() == 1 and i > 0:
                vline = QGraphicsLineItem(x, header_height, x, header_height + len(self.tasks) * row_height)
                vline.setPen(QPen(QColor(t.get("shadow", "#000000")), 1))
                self.scene.addItem(vline)

            current_date = current_date.addDays(1)

        # ── Linha "hoje" (vertical tracejada) ──
        today = QDate.currentDate()
        if min_date <= today <= max_date:
            today_x = 250 + min_date.daysTo(today) * day_width
            today_line = QGraphicsLineItem(
                today_x,
                header_height,
                today_x,
                header_height + len(self.tasks) * row_height + 50,
            )
            today_line.setPen(QPen(QColor(t["btn_del"]), 3, Qt.DashLine))
            self.scene.addItem(today_line)

        # ── Linhas de tarefas + barras/marcos ──
        y_offset = header_height + 10
        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])

        for idx, (task_id, task_data) in enumerate(sorted_tasks):
            # Fundo alternado sutil para cada linha
            task_bg = QGraphicsRectItem(0, y_offset, 250 + days_range * day_width, row_height)
            bg_color = QColor(t["bg_card"]) if idx % 2 == 0 else QColor(t["bg_app"])
            task_bg.setBrush(QBrush(bg_color))
            task_bg.setPen(QPen(Qt.NoPen))
            self.scene.addItem(task_bg)

            # Borda inferior da linha
            sep = QGraphicsLineItem(0, y_offset + row_height, 250 + days_range * day_width, y_offset + row_height)
            sep.setPen(QPen(QColor(t.get("glass_border", "rgba(255,255,255,20)")), 1))
            self.scene.addItem(sep)

            # Nome da tarefa na coluna esquerda (centralizado verticalmente)
            name_fs = 15
            name_font = QFont(
                t.get("font_family_content", "'Segoe UI'").replace("'", ""),
                name_fs,
                QFont.Bold,
            )
            name_fm = QFontMetrics(name_font)
            name_h = name_fm.height()
            name_y = y_offset + (row_height - name_h) / 2
            elided_name = name_fm.elidedText(task_data["name"], Qt.ElideRight, 230)
            name_text = QGraphicsTextItem(elided_name)
            name_text.setFont(name_font)
            name_text.setDefaultTextColor(QColor(t["text"]))
            name_text.setPos(14, name_y)
            name_text.setFlag(QGraphicsItem.ItemIsSelectable, False)
            name_text.setFlag(QGraphicsItem.ItemIsMovable, False)
            self.scene.addItem(name_text)

            # Calcula posição e largura da barra
            start_x = 250 + min_date.daysTo(task_data["start_date"]) * day_width
            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1
            bar_width = duration * day_width

            if task_data.get("is_milestone"):
                # Marco: círculo centralizado verticalmente no row
                ms_h = 14 * self.zoom
                ms_x = start_x + bar_width / 2 - ms_h / 2
                ms_y = y_offset + (row_height - ms_h) / 2
                milestone = QGraphicsEllipseItem(ms_x, ms_y, ms_h, ms_h)
                milestone.setBrush(QBrush(QColor(t.get("btn_del", "#DC3545"))))
                milestone.setPen(QPen(QColor("#000000"), 2))
                self.scene.addItem(milestone)
            else:
                # Barra de tarefa: centralizada verticalmente no row
                bar_h = max(28, 36 * self.zoom)
                bar_y = y_offset + (row_height - bar_h) / 2
                bar_rect = QRectF(start_x, bar_y, bar_width, bar_h)

                is_critical = task_data.get("is_critical", False)
                bar_color = t.get("btn_del") if is_critical else t["accent"]
                bw = t.get("border_width", 3)

                # Fundo sólido
                bg_bar = QGraphicsRectItem(bar_rect)
                bg_bar.setBrush(QBrush(QColor(bar_color)))
                bg_bar.setPen(QPen(QColor(t["line"]), bw))
                self.scene.addItem(bg_bar)

                # Barra de progresso sólida
                progress = task_data.get("progress", 0)
                if progress > 0:
                    prog_w = max(bar_width * progress / 100, 2)
                    prog_bar = QGraphicsRectItem(
                        QRectF(start_x, bar_y, prog_w, bar_h)
                    )
                    prog_bar.setBrush(QBrush(QColor(t.get("btn_add", "#22C55E"))))
                    prog_bar.setPen(QPen(Qt.NoPen))
                    self.scene.addItem(prog_bar)

                # Texto branco sobre a barra (centralizado verticalmente, elidado)
                bar_fs = max(11, int(13 * self.zoom))
                bar_font = QFont(
                    t.get("font_family_content", "'Segoe UI'").replace("'", ""),
                    bar_fs,
                    QFont.Bold,
                )
                bar_fm = QFontMetrics(bar_font)
                bar_label = bar_fm.elidedText(
                    task_data.get("name", ""), Qt.ElideRight, max(0, int(bar_width - 16))
                )
                bar_text_h = bar_fm.height()
                text_y = bar_y + (bar_h - bar_text_h) / 2
                text_bar = QGraphicsTextItem(bar_label)
                text_bar.setFont(bar_font)
                text_bar.setDefaultTextColor(QColor("#FFFFFF"))
                text_bar.setPos(start_x + 8, text_y)
                self.scene.addItem(text_bar)

            # Setas de dependência
            for dep_id, dep_data in self.tasks.items():
                if dep_data.get("predecessor") == task_id:
                    dep_start_x = (
                        250 + min_date.daysTo(dep_data["start_date"]) * day_width
                    )
                    arrow_line = QGraphicsLineItem(
                        start_x + bar_width,
                        y_offset + row_height / 2,
                        dep_start_x,
                        y_offset + row_height / 2,
                    )
                    arrow_line.setPen(QPen(QColor(t.get("text_dim", "#888888")), 2, Qt.DashLine))
                    self.scene.addItem(arrow_line)

            y_offset += row_height

        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(-50, -50, 100, 100)
        )

    def _task_btn_style(self, btn, is_critical, is_milestone):
        """Aplica estilo neo-brutalista ao botão de tarefa com cores do tema."""
        t = T()
        bw = t.get("border_width", 3)
        if is_critical:
            bg = t.get("btn_del", "#DC3545")
        elif is_milestone:
            bg = t.get("accent_bright", "#0057FF")
        else:
            bg = t.get("btn_add", "#22C55E")
        txt_color = t.get("node_text", "#FFFFFF")
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg}; color: {txt_color};
                border: {bw}px solid #000000; border-radius: 0px;
                padding: 8px 12px; font-weight: bold; font-size: 14px;
                text-align: left;
            }}
            QPushButton:hover {{ filter: brightness(1.1); }}
        """)

    def _on_add_task(self):
        # Slot: abre editor modal para criar nova tarefa e adiciona ao modelo
        dialog = TaskEditorDialog(None, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            self.add_task(
                data["name"],
                data["start_date"],
                data["end_date"],
                data["progress"],
                data["is_milestone"],
                data["predecessor"],
            )

    def _on_delete_task(self, task_id):
        # Slot: remove tarefa e limpa referências em sucessoras (predecessor = -1)
        if task_id in self.tasks:
            del self.tasks[task_id]
            # Remove dependências de tarefas que apontavam para esta
            for tid, tdata in self.tasks.items():
                if tdata.get("predecessor") == task_id:
                    tdata["predecessor"] = -1
            self._update_task_list()
            self._draw_gantt()

    def _on_edit_task(self, task_id):
        # Slot: abre editor modal para editar tarefa existente
        if task_id not in self.tasks:
            return
        dialog = TaskEditorDialog(self.tasks[task_id], self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            # Atualiza apenas campos editáveis (preserva CPM values: es/ef/ls/lf/slack/is_critical)
            self.tasks[task_id].update(
                {
                    "name": data["name"],
                    "start_date": data["start_date"],
                    "end_date": data["end_date"],
                    "progress": data["progress"],
                    "is_milestone": data["is_milestone"],
                    "predecessor": data["predecessor"],
                }
            )
            self._update_task_list()
            self._draw_gantt()

    def _on_commit_task(self, task_id, data):
        # Slot: aplica mudanças diretas ao modelo (não usado atualmente, extensível)
        self.tasks[task_id].update(data)
        self._update_task_list()
        self._draw_gantt()

    def _on_task_list_click(self, item):
        # Slot: clique na lista de tarefas abre editor (duplo clique simulado)
        row = self.task_list.row(item)
        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])
        if row < len(sorted_tasks):
            task_id = sorted_tasks[row][0]
            self._on_edit_task(task_id)

    def _calculate_cpm(self):
        # Implementa algoritmo CPM (Critical Path Method) para identificar tarefas críticas
        # Slack <= 0 indica que tarefa está no caminho crítico (sem margem)
        if not self.tasks:
            return

        # Inicializa valores CPM para todas as tarefas
        for tid in self.tasks:
            self.tasks[tid]["es"] = 0    # Early Start
            self.tasks[tid]["ef"] = 0    # Early Finish
            self.tasks[tid]["ls"] = 0    # Late Start
            self.tasks[tid]["lf"] = 0    # Late Finish
            self.tasks[tid]["slack"] = 0 # Float/Slack
            self.tasks[tid]["is_critical"] = False

        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])

        # FORWARD PASS: Calcula ES/EF (caminhos mais cedo possíveis)
        # ES = max(EF de predecessora), EF = ES + duration
        forward_pass = {}
        for task_id, task_data in sorted_tasks:
            pred_id = task_data.get("predecessor", -1)
            if pred_id == -1 or pred_id not in self.tasks:
                task_data["es"] = 0  # Tarefa inicial começa em 0
            else:
                pred_data = self.tasks[pred_id]
                task_data["es"] = pred_data["ef"]  # Começa quando predecessora termina

            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1
            task_data["ef"] = task_data["es"] + duration
            forward_pass[task_id] = task_data["es"]

        # Duração total do projeto = maior EF
        project_duration = max(t["ef"] for t in self.tasks.values())

        # BACKWARD PASS: Calcula LS/LF (caminhos mais tarde permitidos)
        # LF = min(LS de sucessoras), LS = LF - duration
        reverse_tasks = sorted(
            self.tasks.items(), key=lambda x: x[1]["ef"], reverse=True
        )

        for task_id, task_data in reverse_tasks:
            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1

            # Encontra sucessoras (tarefas que têm esta como predecessora)
            successors = [
                sid
                for sid, sd in self.tasks.items()
                if sd.get("predecessor") == task_id
            ]

            if not successors:  # Tarefa final
                task_data["lf"] = project_duration
            else:  # LF = min(LS de todas as sucessoras)
                task_data["lf"] = min(self.tasks[sid]["es"] for sid in successors)

            task_data["ls"] = task_data["lf"] - duration
            task_data["slack"] = task_data["ls"] - task_data["es"]  # Float livre

            # Marca crítica se slack <= 0 (no tempo limite)
            if task_data["slack"] <= 0:
                task_data["is_critical"] = True

        # Atualiza visualização e mostra resumo do CPM
        self._update_task_list()
        self._draw_gantt()

        critical_path = [tid for tid, td in self.tasks.items() if td.get("is_critical")]
        QMessageBox.information(
            self,
            "CPM Calculado",
            f"Caminho crítico identificado:\n"
            + "\n".join(f"• {self.tasks[tid]['name']}" for tid in critical_path)
            + f"\n\nDuração total do projeto: {project_duration} dias",
        )

    def zoom_in(self):
        # Aumenta zoom para 1.2x (máx 3.0x) e renderiza novamente
        self.zoom = min(self.zoom * 1.2, 3.0)
        self._draw_gantt()

    def zoom_out(self):
        # Diminui zoom para 0.833x (mín 0.3x) e renderiza novamente
        self.zoom = max(self.zoom / 1.2, 0.3)
        self._draw_gantt()

    def reset_zoom(self):
        # Retorna zoom para 1.0x (100%)
        self.zoom = 1.0
        self._draw_gantt()

    def wheelEvent(self, event):
        # Integra zoom infinito via Ctrl+MouseWheel (redireciona para zoom_in/out)
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def _export_scene(self, fmt):
        # Exporta cronograma Gantt para PDF ou PNG usando utilitário _export_view
        _export_view(self.canvas, fmt, self)

    def refresh_theme(self):
        # Aplica tema ativo a todos os componentes (botões, lista, canvas, backgrounds)
        t = T()
        bw = t.get("border_width", 3)

        # Estilo neo-brutalista para todos os botões
        for btn in [self.btn_add, self.btn_cpm]:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {t["accent"]}; color: #FFFFFF;
                    border: {bw}px solid #000000; border-radius: 0px;
                    padding: 0px; font-weight: bold; font-size: 15px;
                    font-family: {t.get("font_family_content", "'Segoe UI'")};
                }}
                QPushButton:hover {{ background: {t["accent_bright"]}; }}
            """)

        # Reaplica estilos aos botões existentes
        self._update_task_list()

        # Atualiza background do canvas e renderiza novamente
        self.canvas.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
        self._draw_gantt()


class _GanttModule(BaseModule):
    """
    Wrapper que implementa interface BaseModule para o widget Gantt.
    
    Responsável por:
    - Encapsular GanttWidget com interface padrão de módulo (get_state/set_state)
    - Persistência: Serializa tasks para JSON com schema "gantt.v1"
    - Tema: Aplica refresh_theme() ao mudar tema ativo
    - Zoom: Expõe zoom_in/out/reset como métodos públicos
    - Help: Texto de ajuda sobre controles do módulo
    
    Padrão Adapter: Adapta GanttWidget (domínio específico) para interface
    BaseModule (framework ProEng). Desacopla visão de negócio do framework.
    """
    def __init__(self):
        super().__init__()
        self._inner = GanttWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "CRONOGRAMA GANTT — Guia Rapido\n\n"
            "O grafico de Gantt e uma ferramenta de planejamento que exibe "
            "as tarefas do projeto como barras horizontais ao longo de uma "
            "linha do tempo, permitindo visualizar duracoes, dependencias "
            "e o progresso de cada atividade.\n\n"
            "COMO USAR:\n"
            "• Clique em 'Nova Tarefa' no painel esquerdo para criar uma "
            "nova atividade com nome, datas de inicio/fim e progresso.\n"
            "• Clique sobre uma tarefa na lista para editar seus dados, "
            "incluindo nome, datas, progresso (%) e tarefa predecessora.\n"
            "• Marque 'Marco (Milestone)' para criar pontos de referencia "
            "importantes no cronograma (exibidos como circulos).\n\n"
            "CAMINHO CRITICO (CPM):\n"
            "• Clique em 'Calcular CPM' para identificar automaticamente "
            "as tarefas criticas (sem folga) que determinam a duracao "
            "total do projeto. Tarefas criticas sao destacadas em vermelho.\n\n"
            "NAVEGACAO:\n"
            "• Use Ctrl + Scroll do mouse para aplicar zoom no grafico.\n"
            "• A linha tracejada vermelha indica a data de hoje.\n"
            "• Barras verdes dentro das tarefas indicam o progresso atual."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def zoom_in(self):
        # Delega zoom_in para widget interno (1.2x escalão)
        self._inner.zoom_in()

    def zoom_out(self):
        # Delega zoom_out para widget interno (0.833x escalão)
        self._inner.zoom_out()

    def reset_zoom(self):
        # Delega reset_zoom para widget interno (volta a 1.0x)
        self._inner.reset_zoom()

    def get_state(self):
        # Serializa modelo para JSON compatível (QDate convert para string ISO 8601)
        # Schema "gantt.v1": permite versionamento de formato no futuro
        # Omite valores calculados CPM (es/ef/ls/lf/slack) pois são recalculados ao carregar
        tasks_state = {}
        for tid, tdata in self._inner.tasks.items():
            tasks_state[str(tid)] = {
                "name": tdata["name"],
                "start_date": tdata["start_date"].toString("yyyy-MM-dd"),
                "end_date": tdata["end_date"].toString("yyyy-MM-dd"),
                "progress": tdata["progress"],
                "is_milestone": tdata["is_milestone"],
                "predecessor": tdata["predecessor"],
            }
        return {
            "schema": "gantt.v1",
            "next_task_id": self._inner.next_task_id,
            "tasks": tasks_state,
        }

    def set_state(self, state):
        # Desserializa JSON para modelo Python: converte strings ISO 8601 para QDate
        # Reinicializa valores CPM (serão recalculados se botão CPM for clicado)
        if not state:
            return
        self._inner.tasks.clear()
        self._inner.next_task_id = state.get("next_task_id", 1)

        for tid_str, tdata in state.get("tasks", {}).items():
            tid = int(tid_str)
            self._inner.tasks[tid] = {
                "name": tdata.get("name", ""),
                # Converte string "YYYY-MM-DD" para QDate, com fallbacks
                "start_date": QDate.fromString(
                    tdata.get("start_date", QDate.currentDate().toString("yyyy-MM-dd")),
                    "yyyy-MM-dd",
                ),
                "end_date": QDate.fromString(
                    tdata.get(
                        "end_date",
                        QDate.currentDate().addDays(7).toString("yyyy-MM-dd"),
                    ),
                    "yyyy-MM-dd",
                ),
                "progress": tdata.get("progress", 0),
                "is_milestone": tdata.get("is_milestone", False),
                "predecessor": tdata.get("predecessor", -1),
                # CPM values zerados (recalculados quando necessário)
                "is_critical": False,
                "es": 0,
                "ef": 0,
                "ls": 0,
                "lf": 0,
                "slack": 0,
            }

        self._inner._update_task_list()
        self._inner._draw_gantt()

    def refresh_theme(self):
        # Delega refresh_theme para widget interno (atualiza cores com tema ativo)
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        # Retorna canvas (QGraphicsView) para exibição em tela de seleção
        return getattr(self._inner, "canvas", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _GanttModule()
    w.setWindowTitle("Gantt Chart — PRO ENG")
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec_())
