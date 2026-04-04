# -*- coding: utf-8 -*-
"""Módulo Gantt Chart — Cronograma de Projetos com CPM."""

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
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDateEdit,
    QComboBox,
    QSlider,
    QDialog,
    QCheckBox,
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
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsLineItem
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
from proeng.core.utils import _export_view, _c, _solid_fill
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


class GanttSignals(QObject):
    add_task = pyqtSignal()
    delete_task = pyqtSignal(int)
    edit_task = pyqtSignal(int)
    commit_task = pyqtSignal(int, dict)
    calculate_cpm = pyqtSignal()


class GanttTaskItem(QGraphicsItem):
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
        m = 5 * self.zoom
        return QRectF(-m, -m, self._width + m * 2, self._height + m * 2)

    def paint(self, painter, option, widget=None):
        t = T()
        painter.setRenderHint(QPainter.Antialiasing)

        r = QRectF(0, 0, self._width, self._height)

        is_critical = self.task_data.get("is_critical", False)
        progress = self.task_data.get("progress", 0)

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

        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", int(10 * self.zoom), QFont.Bold)
        painter.setFont(font)

        name = self.task_data.get("name", "Tarefa")
        text_rect = r.adjusted(8, 4, -8, -4)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, name)

        if self.hovered:
            bs = 20 * self.zoom
            hbs = bs / 2

            del_rect = QRectF(self._width - hbs, -hbs, bs, bs)
            painter.setBrush(QBrush(QColor(220, 53, 69)))
            painter.setPen(QPen(Qt.NoPen))
            painter.drawRoundedRect(del_rect, 4, 4)
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(del_rect, Qt.AlignCenter, "×")

    def hoverEnterEvent(self, e):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, e):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
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
        event.accept()
        QTimer.singleShot(0, lambda: self.signals.edit_task.emit(self.task_id))


class GanttCanvas(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.zoom_level = 1.0
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def wheelEvent(self, event):
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
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.setWindowTitle("Editar Tarefa")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
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
        return {
            "name": self.name_input.text(),
            "start_date": self.start_date.date(),
            "end_date": self.end_date.date(),
            "progress": self.progress_slider.value(),
            "is_milestone": self.is_milestone_check.isChecked(),
            "predecessor": self.predecessor_combo.currentData(),
        }


class GanttWidget(QWidget):
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QWidget()
        self.toolbar.setFixedHeight(50)
        tb = QHBoxLayout(self.toolbar)
        tb.setContentsMargins(10, 5, 10, 5)

        self.title_lbl = QLabel("📊 Gantt Chart — Cronograma do Projeto")
        tb.addWidget(self.title_lbl)

        tb.addSpacing(20)

        self.btn_add = QPushButton("➕ Nova Tarefa")
        self.btn_add.clicked.connect(lambda: self.signals.add_task.emit())
        tb.addWidget(self.btn_add)

        self.btn_cpm = QPushButton("🔢 Calcular CPM")
        self.btn_cpm.clicked.connect(lambda: self.signals.calculate_cpm.emit())
        tb.addWidget(self.btn_cpm)

        tb.addStretch()

        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        tb.addWidget(self.btn_zoom_in)

        self.btn_zoom_out = QPushButton("🔍−")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        tb.addWidget(self.btn_zoom_out)

        self.btn_reset = QPushButton("⟳ 100%")
        self.btn_reset.clicked.connect(self.reset_zoom)
        tb.addWidget(self.btn_reset)

        for lbl, key in [("📄 PDF", "pdf"), ("🖼 PNG", "png")]:
            btn = QPushButton(lbl)
            btn.clicked.connect(lambda _, k=key: self._export_scene(k))
            tb.addWidget(btn)

        layout.addWidget(self.toolbar)

        self.splitter = QSplitter(Qt.Horizontal)

        self.task_list = QListWidget()
        self.task_list.setFixedWidth(250)
        self.task_list.itemClicked.connect(self._on_task_list_click)
        self.splitter.addWidget(self.task_list)

        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 1500)
        self.canvas = GanttCanvas(self.scene)
        self.splitter.addWidget(self.canvas)

        layout.addWidget(self.splitter)

    def _create_sample_tasks(self):
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
        self.task_list.clear()
        for task_id, data in sorted(
            self.tasks.items(), key=lambda x: x[1]["start_date"]
        ):
            item = QListWidgetItem(f"{data['name']}")
            if data.get("is_critical"):
                item.setForeground(QColor(220, 53, 69))
            self.task_list.addItem(item)

    def _draw_gantt(self):
        self.scene.clear()
        t = T()

        if not self.tasks:
            return

        min_date = min(task["start_date"] for task in self.tasks.values())
        max_date = max(task["end_date"] for task in self.tasks.values())
        days_range = min_date.daysTo(max_date) + 30

        day_width = 30 * self.zoom
        row_height = 40 * self.zoom
        header_height = 50 * self.zoom

        header_bg = QGraphicsRectItem(0, 0, 250 + days_range * day_width, header_height)
        header_bg.setBrush(QBrush(QColor(t["toolbar_bg"])))
        self.scene.addItem(header_bg)

        title_font = QFont("Segoe UI", 12, QFont.Bold)
        title_text = QGraphicsTextItem("Tarefa")
        title_text.setFont(title_font)
        title_text.setDefaultTextColor(QColor(t["text"]))
        title_text.setPos(10, 15)
        self.scene.addItem(title_text)

        current_date = min_date
        for i in range(days_range + 1):
            x = 250 + i * day_width
            if current_date.dayOfWeek() <= 5:
                day_rect = QGraphicsRectItem(x, header_height - 25, day_width, 25)
                day_rect.setBrush(QBrush(QColor(t["bg_card"])))
                self.scene.addItem(day_rect)

            day_text = QGraphicsTextItem(str(current_date.day()))
            day_text.setFont(QFont("Segoe UI", 8))
            day_text.setDefaultTextColor(QColor(t["text_dim"]))
            day_text.setPos(x + day_width / 2 - 5, header_height - 20)
            self.scene.addItem(day_text)

            if current_date.day() == 1:
                month_text = QGraphicsTextItem(current_date.shortMonthName())
                month_text.setFont(QFont("Segoe UI", 9, QFont.Bold))
                month_text.setDefaultTextColor(QColor(t["accent_bright"]))
                month_text.setPos(x, 5)
                self.scene.addItem(month_text)

            current_date = current_date.addDays(1)

        today = QDate.currentDate()
        if min_date <= today <= max_date:
            today_x = 250 + min_date.daysTo(today) * day_width
            today_line = QGraphicsLineItem(
                today_x,
                header_height,
                today_x,
                header_height + len(self.tasks) * row_height,
            )
            today_line.setPen(QPen(QColor(t["accent_bright"]), 2, Qt.DashLine))
            self.scene.addItem(today_line)

        y_offset = header_height + 10
        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])

        for idx, (task_id, task_data) in enumerate(sorted_tasks):
            task_bg = QGraphicsRectItem(0, y_offset - 5, 250, row_height)
            task_bg.setBrush(
                QBrush(QColor(t["bg_card"]) if idx % 2 == 0 else QColor(t["bg_app"]))
            )
            self.scene.addItem(task_bg)

            name_text = QGraphicsTextItem(task_data["name"])
            name_text.setFont(QFont("Segoe UI", 10))
            name_text.setDefaultTextColor(QColor(t["text"]))
            name_text.setPos(10, y_offset + 10)
            self.scene.addItem(name_text)

            start_x = 250 + min_date.daysTo(task_data["start_date"]) * day_width
            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1
            bar_width = duration * day_width

            if task_data.get("is_milestone"):
                milestone = QGraphicsRectItem(
                    start_x + bar_width / 2 - 8, y_offset + 8, 16, 24
                )
                milestone.setBrush(QBrush(QColor(t["accent_bright"])))
                milestone.setPen(QPen(QColor(t["accent"]), 2))
                self.scene.addItem(milestone)
            else:
                task_item = QGraphicsItem(
                    task_id, task_data.copy(), self.zoom, self.signals
                )
                task_item.setPos(start_x, y_offset + 4)
                self.scene.addItem(task_item)

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
                    arrow_line.setPen(QPen(QColor(t["line"]), 1, Qt.DashLine))
                    self.scene.addItem(arrow_line)

            y_offset += row_height

        self.scene.setSceneRect(
            self.scene.itemsBoundingRect().adjusted(-50, -50, 100, 100)
        )

    def _on_add_task(self):
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
        if task_id in self.tasks:
            del self.tasks[task_id]
            for tid, tdata in self.tasks.items():
                if tdata.get("predecessor") == task_id:
                    tdata["predecessor"] = -1
            self._update_task_list()
            self._draw_gantt()

    def _on_edit_task(self, task_id):
        if task_id not in self.tasks:
            return
        dialog = TaskEditorDialog(self.tasks[task_id], self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
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
        self.tasks[task_id].update(data)
        self._update_task_list()
        self._draw_gantt()

    def _on_task_list_click(self, item):
        row = self.task_list.row(item)
        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])
        if row < len(sorted_tasks):
            task_id = sorted_tasks[row][0]
            self._on_edit_task(task_id)

    def _calculate_cpm(self):
        if not self.tasks:
            return

        for tid in self.tasks:
            self.tasks[tid]["es"] = 0
            self.tasks[tid]["ef"] = 0
            self.tasks[tid]["ls"] = 0
            self.tasks[tid]["lf"] = 0
            self.tasks[tid]["slack"] = 0
            self.tasks[tid]["is_critical"] = False

        sorted_tasks = sorted(self.tasks.items(), key=lambda x: x[1]["start_date"])

        forward_pass = {}
        for task_id, task_data in sorted_tasks:
            pred_id = task_data.get("predecessor", -1)
            if pred_id == -1 or pred_id not in self.tasks:
                task_data["es"] = 0
            else:
                pred_data = self.tasks[pred_id]
                task_data["es"] = pred_data["ef"]

            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1
            task_data["ef"] = task_data["es"] + duration
            forward_pass[task_id] = task_data["es"]

        project_duration = max(t["ef"] for t in self.tasks.values())

        reverse_tasks = sorted(
            self.tasks.items(), key=lambda x: x[1]["ef"], reverse=True
        )

        for task_id, task_data in reverse_tasks:
            duration = task_data["start_date"].daysTo(task_data["end_date"]) + 1

            successors = [
                sid
                for sid, sd in self.tasks.items()
                if sd.get("predecessor") == task_id
            ]

            if not successors:
                task_data["lf"] = project_duration
            else:
                task_data["lf"] = min(self.tasks[sid]["es"] for sid in successors)

            task_data["ls"] = task_data["lf"] - duration
            task_data["slack"] = task_data["ls"] - task_data["es"]

            if task_data["slack"] <= 0:
                task_data["is_critical"] = True

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
        self.zoom = min(self.zoom * 1.2, 3.0)
        self._draw_gantt()

    def zoom_out(self):
        self.zoom = max(self.zoom / 1.2, 0.3)
        self._draw_gantt()

    def reset_zoom(self):
        self.zoom = 1.0
        self._draw_gantt()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def _export_scene(self, fmt):
        _export_view(self.canvas, fmt, self)

    def refresh_theme(self):
        t = T()
        self.toolbar.setStyleSheet(f"""
            QWidget {{ background: {t["toolbar_bg"]}; border-bottom: 1px solid {t["accent"]}; }}
        """)
        self.title_lbl.setStyleSheet(f"""
            color: {t["accent_bright"]}; font-family: 'Segoe UI';
            font-size: 14px; font-weight: bold; background: transparent;
        """)

        btn_style = f"""
            QPushButton {{
                background: {t["toolbar_btn"]}; color: {t["text"]};
                border: 1px solid {t["accent_dim"]}; border-radius: 5px;
                padding: 5px 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {t["toolbar_btn_h"]}; color: {t["accent_bright"]}; }}
        """
        for btn in [
            self.btn_add,
            self.btn_cpm,
            self.btn_zoom_in,
            self.btn_zoom_out,
            self.btn_reset,
        ]:
            btn.setStyleSheet(btn_style)

        self.task_list.setStyleSheet(f"""
            QListWidget {{
                background: {t["bg_app"]}; color: {t["text"]};
                border: none; font-size: 12px;
            }}
            QListWidget::item:selected {{
                background: {t["accent"]}; color: white;
            }}
        """)

        self.canvas.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
        self._draw_gantt()


class _GanttModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = GanttWidget()
        _hide_inner_toolbar(self._inner)
        self.help_text = (
            "• Clique em '➕ Nova Tarefa' para adicionar tarefas.\n"
            "• Clique em 'Calcular CPM' para encontrar o caminho crítico.\n"
            "• Clique duplo numa tarefa na lista para editar.\n"
            "• Use Ctrl+Scroll para zoom no gráfico.\n"
            "• Arraste as barras para mover no tempo."
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._inner)

    def zoom_in(self):
        self._inner.zoom_in()

    def zoom_out(self):
        self._inner.zoom_out()

    def reset_zoom(self):
        self._inner.reset_zoom()

    def get_state(self):
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
        if not state:
            return
        self._inner.tasks.clear()
        self._inner.next_task_id = state.get("next_task_id", 1)

        for tid_str, tdata in state.get("tasks", {}).items():
            tid = int(tid_str)
            self._inner.tasks[tid] = {
                "name": tdata.get("name", ""),
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
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()

    def get_view(self):
        return getattr(self._inner, "canvas", None)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = _GanttModule()
    w.setWindowTitle("Gantt Chart — PRO ENG")
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec_())
