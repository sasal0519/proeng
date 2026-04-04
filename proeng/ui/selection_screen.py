# -*- coding: utf-8 -*-
"""Tela de seleção dos módulos e card individual."""

import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
    QScrollArea,
    QFrame,
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
)
from PyQt5.QtWidgets import QScrollArea, QFrame

from proeng.core.themes import T, THEMES, _ACTIVE, cycle_theme
from proeng.ui.nav_bar import ThemeToggle


def _draw_icon_arrow(p, x, y, size, col):
    pen = QPen(QColor(col), 2.5, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(x, y + size / 2), QPointF(x + size, y + size / 2))
    p.drawLine(QPointF(x + size - 6, y + size / 2 - 5), QPointF(x + size, y + size / 2))
    p.drawLine(QPointF(x + size - 6, y + size / 2 + 5), QPointF(x + size, y + size / 2))


class ModuleCard(QPushButton):
    def __init__(self, emoji, title, desc, key, callback):
        super().__init__()
        self._emoji = emoji
        self._title = title
        self._desc = desc
        self._hov = False
        self.setMinimumSize(240, 128)
        self.setMaximumHeight(148)
        self.setMinimumHeight(128)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFlat(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.clicked.connect(lambda: callback(key))

    def event(self, e):
        from PyQt5.QtCore import QEvent

        if e.type() == QEvent.HoverEnter:
            self._hov = True
            self.update()
        elif e.type() == QEvent.HoverLeave:
            self._hov = False
            self.update()
        return super().event(e)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)

        bw = t.get("border_width", 3)
        sx = t.get("shadow_offset_x", 6)
        sy = t.get("shadow_offset_y", 6)
        hsx = t.get("shadow_hover_offset_x", 2)
        hsy = t.get("shadow_hover_offset_y", 2)

        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        if self._hov:
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(r.translated(hsx, hsy))
        else:
            p.setBrush(QColor(t["shadow"]))
            p.setPen(QPen(Qt.NoPen))
            p.drawRect(r.translated(sx, sy))

        p.setBrush(QBrush(QColor(t["bg_card"])))
        p.setPen(QPen(QColor(t["glass_border"]), bw))
        p.drawRect(r)

        p.setBrush(QBrush(QColor(t["accent"] if self._hov else t["accent_bright"])))
        p.setPen(QPen(Qt.NoPen))
        p.drawRect(QRectF(r.left(), r.top(), r.width(), 6))

        ff = t.get("font_family", "'Segoe UI', sans-serif").replace("'", "")

        icon_box = QRectF(r.left() + 12, r.top() + 16, 36, 36)
        p.setPen(QPen(QColor(t["glass_border"]), 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(icon_box)
        p.setFont(QFont(ff, 16, QFont.Bold))
        p.setPen(QColor(t["text"]))
        p.drawText(icon_box, Qt.AlignCenter, self._emoji)

        p.setFont(QFont(ff, 12, QFont.Bold))
        p.setPen(QColor(t["text"]))
        title_rect = QRectF(r.left() + 58, r.top() + 14, r.width() - 76, 22)
        fm = QFontMetrics(p.font())
        p.drawText(
            title_rect,
            Qt.AlignLeft | Qt.AlignVCenter,
            fm.elidedText(self._title, Qt.ElideRight, int(title_rect.width())),
        )

        p.setFont(QFont(ff, 9, QFont.Normal))
        p.setPen(QColor(t["text_dim"]))
        desc_top = r.top() + 40
        desc_h = r.bottom() - desc_top - 10
        desc_r = QRectF(r.left() + 58, desc_top, r.width() - 76, max(desc_h, 28))
        p.drawText(desc_r, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._desc)

        if self._hov:
            _draw_icon_arrow(p, r.right() - 28, r.bottom() - 22, 16, t["text"])

        p.end()


# ═══════════════════════════════════════════════════════════════════
#   ASSINATURA FLUTUANTE
# ═══════════════════════════════════════════════════════════════════


class SignatureOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(26)
        self._reposition()

    def _reposition(self):
        p = self.parent()
        if p:
            w = 320
            self.setGeometry(p.width() - w - 10, p.height() - 32, w, 26)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        g.setColorAt(0, QColor(t["sig_bg_l"]))
        g.setColorAt(0.25, QColor(t["sig_bg_r"]))
        g.setColorAt(1, QColor(t["sig_bg_r"]))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor(t["sig_border"]), 1))
        p.drawRoundedRect(r, 13, 13)
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(t["sig_text"]))
        p.drawText(
            QRectF(r.left() + 12, r.top(), r.width() - 16, r.height()),
            Qt.AlignVCenter | Qt.AlignLeft,
            "♥  Desenvolvido com carinho por Salomão Félix",
        )
        p.end()


# ═══════════════════════════════════════════════════════════════════
#   BOTÃO DE TEMA (toggle dark ↔ light)
# ═══════════════════════════════════════════════════════════════════


class GalleryItem(QFrame):
    def __init__(self, title, module_key):
        super().__init__()
        self.title = title
        self.module_key = module_key
        self.setFixedSize(280, 180)
        self._hover = False
        self.setCursor(Qt.PointingHandCursor)
        self._img_label = QLabel(self)
        self._img_label.setScaledContents(True)
        self._img_label.setFixedSize(240, 130)
        self._img_label.move(20, 10)

        self._title_label = QLabel(title, self)
        self._title_label.setAlignment(Qt.AlignCenter)
        self._title_label.setFixedWidth(280)
        self._title_label.move(0, 150)
        self._refresh_img()

    def _refresh_img(self):
        t = T()
        theme_name = t["name"]
        img_path = f"proeng/resources/screenshots/{self.module_key}_{theme_name}.png"
        import os

        if os.path.exists(img_path):
            self._img_label.setPixmap(QPixmap(img_path))
        else:
            self._img_label.setText("No Preview")

        self._title_label.setStyleSheet(
            f"color: {t['text']}; font-weight: bold; font-size: 11px;"
        )
        self.update_style()

    def update_style(self):
        t = T()
        border = "#000000" if self._hover else t.get("glass_border", "#000000")
        bg = t["bg_card2"] if self._hover else t["bg_card"]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 3px solid {border};
                border-radius: 0px;
            }}
        """)

    def enterEvent(self, e):
        self._hover = True
        self.update_style()

    def leaveEvent(self, e):
        self._hover = False
        self.update_style()


class ScreenshotGallery(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFixedHeight(190)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent;")

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout_g = QHBoxLayout(self.container)
        self.layout_g.setContentsMargins(10, 0, 10, 0)
        self.layout_g.setSpacing(20)

        self.items = [
            GalleryItem("Cronograma Gantt", "gantt"),
            GalleryItem("Fluxograma PFD", "flowsheet"),
            GalleryItem("EAP do Projeto", "eap"),
            GalleryItem("Processo BPMN", "bpmn"),
            GalleryItem("Project Canvas", "canvas"),
            GalleryItem("Ishikawa (6M)", "ishikawa"),
            GalleryItem("Plano 5W2H", "w5h2"),
        ]
        for item in self.items:
            self.layout_g.addWidget(item)

        self.setWidget(self.container)

    def refresh(self):
        for item in self.items:
            item._refresh_img()


class SelectionScreen(QWidget):
    def __init__(self, on_select, on_theme_toggle):
        super().__init__()
        self.on_select = on_select
        self._on_theme = on_theme_toggle
        # Needed for setStyleSheet background to actually paint
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Accent bar topo
        self._top_bar = QWidget()
        self._top_bar.setFixedHeight(4)
        self._top_bar.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._top_bar)

        # ── Topbar com brand + toggle
        self._topbar_widget = QWidget()
        self._topbar_widget.setFixedHeight(48)
        self._topbar_widget.setAttribute(Qt.WA_StyledBackground, True)
        tl = QHBoxLayout(self._topbar_widget)
        tl.setContentsMargins(24, 0, 24, 0)
        tl.setSpacing(12)
        self._brand_lbl = QLabel("⚙  PRO ENG")
        tl.addWidget(self._brand_lbl)
        tl.addStretch()
        tog = ThemeToggle()
        tog.theme_changed.connect(self._refresh)
        tog.theme_changed.connect(self._on_theme)  # propagate to MainApp
        tl.addWidget(tog)
        outer.addWidget(self._topbar_widget)

        # ── Conteúdo central
        self._content = QWidget()
        self._content.setAttribute(Qt.WA_StyledBackground, True)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setAlignment(Qt.AlignHCenter)
        self._content_layout.setContentsMargins(80, 36, 80, 36)
        self._content_layout.setSpacing(0)
        outer.addWidget(self._content, 1)

        self._populate_content()

        # ── Accent bar fundo
        self._bot_bar = QWidget()
        self._bot_bar.setFixedHeight(4)
        self._bot_bar.setAttribute(Qt.WA_StyledBackground, True)
        outer.addWidget(self._bot_bar)

        self._apply_styles()

    def _populate_content(self):
        lay = self._content_layout

        # Badge
        br = QHBoxLayout()
        br.setAlignment(Qt.AlignCenter)
        self._badge = QLabel("✦Ferramentas de Engenharia e Gestão✦")
        self._badge.setAlignment(Qt.AlignCenter)
        br.addWidget(self._badge)
        lay.addLayout(br)
        lay.addSpacing(18)

        # Títulos
        self._t1 = QLabel("PRO ENG")
        self._t1.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t1)
        self._t2 = QLabel("— ")
        self._t2.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t2)
        lay.addSpacing(8)

        self._sub = QLabel("PyQt5  ·  Zoom Infinito  ·  Exportação PDF & PNG")
        self._sub.setAlignment(Qt.AlignCenter)
        self._sub.setWordWrap(True)
        lay.addWidget(self._sub)
        lay.addSpacing(24)

        # Galeria de Screenshots
        self._gallery_title = QLabel("✦ GALERIA DE EXEMPLOS REAIS ✦")
        self._gallery_title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._gallery_title)
        lay.addSpacing(8)

        self._gallery = ScreenshotGallery()
        lay.addWidget(self._gallery)
        lay.addSpacing(32)

        # Containers principais: Engenharia | Gestão de Projetos
        main_row = QHBoxLayout()
        main_row.setSpacing(24)
        main_row.setAlignment(Qt.AlignHCenter)

        # Container Engenharia (1x1) - lado esquerdo
        eng_wrapper = QWidget()
        eng_wrapper.setFixedWidth(280)
        eng_layout = QVBoxLayout(eng_wrapper)
        eng_layout.setSpacing(12)
        eng_layout.setContentsMargins(0, 0, 0, 0)
        eng_label = QLabel("🔧 ENGENHARIA")
        eng_label.setAlignment(Qt.AlignCenter)
        eng_layout.addWidget(eng_label)
        eng_modules = [
            (
                "🏭",
                "PFD Flowsheet",
                "Diagrama de processo industrial\ncom 26 equipamentos e tubulações",
                "flowsheet",
            ),
        ]
        for em, ti, de, key in eng_modules:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c)
            eng_layout.addWidget(c)
        main_row.addWidget(eng_wrapper)

        # Container Gestão de Projetos (2x3) - lado direito
        gp_wrapper = QWidget()
        gp_wrapper.setFixedWidth(600)
        gp_layout = QVBoxLayout(gp_wrapper)
        gp_layout.setSpacing(12)
        gp_layout.setContentsMargins(0, 0, 0, 0)
        gp_label = QLabel("📁 GESTÃO DE PROJETOS")
        gp_label.setAlignment(Qt.AlignCenter)
        gp_layout.addWidget(gp_label)
        gp_modules = [
            (
                "📊",
                "Cronograma Gantt",
                "Cronograma com CPM\nCaminho Crítico Automático",
                "gantt",
            ),
            (
                "📋",
                "Gerador EAP",
                "Estrutura Analítica do Projeto\ncom numeração WBS automática",
                "eap",
            ),
            (
                "🔀",
                "BPMN Modeler",
                "Pools, Lanes e fluxos\nde processo BPMN 2.0",
                "bpmn",
            ),
            (
                "📝",
                "PM Canvas",
                "Project Model Canvas\nGrelha Finocchio completa",
                "canvas",
            ),
            (
                "🐟",
                "Ishikawa",
                "Diagrama Espinha de Peixe\nCausa e Efeito (6M)",
                "ishikawa",
            ),
            (
                "🎯",
                "Plano 5W2H",
                "Gestão de Ações (5W2H)\nDistribuição Automática",
                "w5h2",
            ),
        ]
        gp_grid = QGridLayout()
        gp_grid.setSpacing(12)
        gp_grid.setContentsMargins(0, 0, 0, 0)
        row, col = 0, 0
        for em, ti, de, key in gp_modules:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c)
            gp_grid.addWidget(c, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1
        gp_layout.addLayout(gp_grid)
        main_row.addWidget(gp_wrapper)

        lay.addLayout(main_row)
        lay.addSpacing(22)

        lay.addSpacing(22)

        # Pills
        self._pills_row = QHBoxLayout()
        self._pills_row.setAlignment(Qt.AlignCenter)
        self._pills_row.setSpacing(8)
        self._pills = []
        for tag in ["Desenvolvido por : Salomão Félix"]:
            lbl = QLabel(tag)
            self._pills.append(lbl)
            self._pills_row.addWidget(lbl)
        lay.addLayout(self._pills_row)

    def _apply_bg(self):
        self._apply_styles()

    def _apply_styles(self):
        t = T()
        bw = t.get("border_width", 3)
        ff = t.get("font_family", "'Segoe UI', 'Arial', sans-serif")

        self.setStyleSheet(f"QWidget {{ background-color: {t['bg_app']}; }}")

        self._top_bar.setStyleSheet(f"QWidget {{ background: {t['accent']}; }}")
        self._bot_bar.setStyleSheet(f"QWidget {{ background: {t['accent']}; }}")

        self._topbar_widget.setStyleSheet(
            f"QWidget {{ background: {t['bg_card']}; border-bottom: {bw}px solid {t['glass_border']}; }}"
        )
        self._brand_lbl.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 16px; font-weight: 900; background: {t['bg_app']}; border: {bw}px solid {t['glass_border']}; padding: 5px 10px; }}"
        )

        self._content.setStyleSheet(f"QWidget {{ background-color: {t['bg_app']}; }}")

        self._badge.setStyleSheet(
            f"QLabel {{ color: #FFFFFF; font-family: {ff};"
            f" font-size: 11px; font-weight: 900;"
            f" background: {t['accent']}; border: {bw}px solid {t['glass_border']};"
            f" padding: 4px 18px; }}"
        )

        self._t1.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 48px; font-weight: 900; background: transparent; letter-spacing: 2px; }}"
        )

        self._t2.setStyleSheet(
            f"QLabel {{ color: {t['accent']}; font-family: {ff};"
            f" font-size: 28px; font-weight: 900; background: transparent; }}"
        )

        self._sub.setStyleSheet(
            f"QLabel {{ color: {t['text_dim']}; font-family: {ff};"
            f" font-size: 12px; font-weight: bold; background: transparent; }}"
        )

        self._gallery_title.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: {ff};"
            f" font-size: 12px; font-weight: 900; background: {t['bg_card']}; border: {bw}px solid {t['glass_border']}; padding: 5px; }}"
        )

        pill_s = (
            f"QLabel {{ color: {t['text']}; font-family: {ff}; font-size: 11px;"
            f" background: {t['bg_card']}; border: {bw}px solid {t['glass_border']};"
            f" padding: 4px 14px; font-weight: bold; }}"
        )
        for p in self._pills:
            p.setStyleSheet(pill_s)

    def _refresh(self):
        self._apply_styles()
        self._gallery.refresh()
        for c in self._cards:
            c.update()
        # Force full repaint of the whole widget tree
        self.update()
        self.repaint()

    def paintEvent(self, event):
        # Fill background explicitly so theme change is always visible
        t = T()
        from PyQt5.QtGui import QColor

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(t["bg_app"]))
        painter.end()
        super().paintEvent(event)


# ═══════════════════════════════════════════════════════════════════
#   JANELA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════
