# -*- coding: utf-8 -*-
"""Tela de seleção dos módulos e card individual."""
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QListWidget, QListWidgetItem, QSplitter, QGraphicsPathItem, QMenu,
    QListView, QLineEdit, QLabel, QStackedWidget, QTextEdit,
    QGraphicsRectItem, QInputDialog, QFileDialog, QSizePolicy,
    QScrollArea, QFrame
)
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainter, QPalette, QCursor, QPolygonF,
    QFont, QFontMetrics, QIcon, QPixmap, QPainterPath, QDrag, QLinearGradient
)
from PyQt5.QtCore import (
    Qt, QRectF, QPointF, QMimeData, QByteArray, QDataStream,
    QIODevice, QSize, QPoint, QTimer, pyqtSignal, QObject, QSizeF
)
from PyQt5.QtWidgets import QScrollArea, QFrame

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.ui.nav_bar import ThemeToggle

class ModuleCard(QPushButton):
    def __init__(self, emoji, title, desc, key, callback):
        super().__init__()
        self._emoji = emoji
        self._title = title
        self._desc  = desc        # já tem \n inseridos pelo chamador
        self._hov   = False
        self.setMinimumSize(240, 128)
        self.setMaximumHeight(148)
        self.setMinimumHeight(128)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFlat(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.clicked.connect(lambda: callback(key))

    def event(self, e):
        from PyQt5.QtCore import QEvent
        if e.type() == QEvent.HoverEnter:  self._hov = True;  self.update()
        elif e.type() == QEvent.HoverLeave: self._hov = False; self.update()
        return super().event(e)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        # Fundo
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        if self._hov:
            g.setColorAt(0, QColor(t["bg_card2"])); g.setColorAt(1, QColor(t["bg_card"]))
        else:
            g.setColorAt(0, QColor(t["bg_card"])); g.setColorAt(1, QColor(t["bg_app"]))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor(t["accent_bright"] if self._hov else t["accent"]), 1.5))
        p.drawRoundedRect(r, 12, 12)

        # Accent strip topo
        sg = QLinearGradient(r.left(), 0, r.right(), 0)
        sg.setColorAt(0, QColor(t["accent_bright"] if self._hov else t["accent"]))
        sg.setColorAt(0.55, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(sg)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(r.left(), r.top(), r.width(), 3), 2, 2)

        # Emoji
        p.setFont(QFont("Segoe UI", 18))
        p.setPen(QColor(t["text"]))
        p.drawText(QRectF(r.left()+14, r.top()+8, 42, 42), Qt.AlignCenter, self._emoji)

        # Título — 1 linha com elide
        p.setFont(QFont("Segoe UI", 12, QFont.Bold))
        p.setPen(QColor(t["accent_bright"] if self._hov else t["text"]))
        title_rect = QRectF(r.left()+64, r.top()+10, r.width()-84, 24)
        fm = QFontMetrics(p.font())
        p.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(self._title, Qt.ElideRight, int(title_rect.width())))

        # Descrição — word-wrap, altura máx controlada
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(t["accent"] if self._hov else t["text_dim"]))
        desc_top = r.top() + 40
        desc_h   = r.bottom() - desc_top - 10
        desc_r   = QRectF(r.left()+64, desc_top, r.width()-82, max(desc_h, 28))
        p.drawText(desc_r, Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap, self._desc)

        # Seta →
        if self._hov:
            p.setPen(QPen(QColor(t["accent_bright"]), 2, Qt.SolidLine, Qt.RoundCap))
            ax = r.right()-16; ay = r.bottom()-18
            p.drawLine(QPointF(ax-8, ay-5), QPointF(ax, ay))
            p.drawLine(QPointF(ax-8, ay+5), QPointF(ax, ay))
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
            self.setGeometry(p.width()-w-10, p.height()-32, w, 26)

    def paintEvent(self, _):
        t = T()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        g = QLinearGradient(r.left(), 0, r.right(), 0)
        g.setColorAt(0, QColor(t["sig_bg_l"]))
        g.setColorAt(0.25, QColor(t["sig_bg_r"]))
        g.setColorAt(1,   QColor(t["sig_bg_r"]))
        p.setBrush(QBrush(g))
        p.setPen(QPen(QColor(t["sig_border"]), 1))
        p.drawRoundedRect(r, 13, 13)
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor(t["sig_text"]))
        p.drawText(QRectF(r.left()+12, r.top(), r.width()-16, r.height()),
                   Qt.AlignVCenter | Qt.AlignLeft,
                   "♥  Desenvolvido com carinho por Salomão Félix")
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
        
        self._title_label.setStyleSheet(f"color: {t['text']}; font-weight: bold; font-size: 11px;")
        self.update_style()

    def update_style(self):
        t = T()
        border = t["accent"] if self._hover else t["accent_dim"]
        bg = t["bg_card2"] if self._hover else t["bg_card"]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 12px;
            }}
        """)

    def enterEvent(self, e): self._hover = True; self.update_style()
    def leaveEvent(self, e): self._hover = False; self.update_style()


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
        self.on_select   = on_select
        self._on_theme   = on_theme_toggle
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
        tl.setContentsMargins(24, 0, 24, 0); tl.setSpacing(12)
        self._brand_lbl = QLabel("⚙  Pro Eng Tools")
        tl.addWidget(self._brand_lbl)
        tl.addStretch()
        tog = ThemeToggle()
        tog.theme_changed.connect(self._refresh)
        tog.theme_changed.connect(self._on_theme)   # propagate to MainApp
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
        br = QHBoxLayout(); br.setAlignment(Qt.AlignCenter)
        self._badge = QLabel("✦Ferramentas de Engenharia e Gestão✦")
        self._badge.setAlignment(Qt.AlignCenter)
        br.addWidget(self._badge); lay.addLayout(br)
        lay.addSpacing(18)

        # Títulos
        self._t1 = QLabel("Pro Eng Tools"); self._t1.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t1)
        self._t2 = QLabel("— "); self._t2.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._t2)
        lay.addSpacing(8)

        self._sub = QLabel(
            "PyQt5  ·  Zoom Infinito  ·  Exportação PDF & PNG")
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

        # Cards 2×2
        modules = [
            ("🏭", "PFD Flowsheet",
             "Diagrama de processo industrial\ncom 26 equipamentos e tubulações", "flowsheet"),
            ("📋", "Gerador EAP",
             "Estrutura Analítica do Projeto\ncom numeração WBS automática", "eap"),
            ("🔀", "BPMN Modeler",
             "Pools, Lanes e fluxos\nde processo BPMN 2.0", "bpmn"),
            ("📝", "PM Canvas",
             "Project Model Canvas\nGrelha Finocchio completa", "canvas"),
            ("🐟", "Ishikawa",
             "Diagrama Espinha de Peixe\nCausa e Efeito (6M)", "ishikawa"),
            ("🎯", "Plano 5W2H",
             "Gestão de Ações (5W2H)\nDistribuição Automática", "w5h2"),
        ]
        self._cards = []
        # Row 1: flowsheet + eap
        row1 = QHBoxLayout(); row1.setSpacing(16)
        for em, ti, de, key in modules[:2]:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c); row1.addWidget(c)
        lay.addLayout(row1)
        lay.addSpacing(14)
        # Row 2: bpmn + canvas
        row2 = QHBoxLayout(); row2.setSpacing(16)
        for em, ti, de, key in modules[2:4]:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c); row2.addWidget(c)
        lay.addLayout(row2)
        lay.addSpacing(14)
        # Row 3: ishikawa + w5h2
        row3 = QHBoxLayout(); row3.setSpacing(16)
        for em, ti, de, key in modules[4:6]:
            c = ModuleCard(em, ti, de, key, self.on_select)
            self._cards.append(c); row3.addWidget(c)
        lay.addLayout(row3)
        lay.addSpacing(14)

        lay.addSpacing(22)

        # Pills
        self._pills_row = QHBoxLayout()
        self._pills_row.setAlignment(Qt.AlignCenter); self._pills_row.setSpacing(8)
        self._pills = []
        for tag in ["Desenvolvido por : Salomão Félix"]:
            lbl = QLabel(tag); self._pills.append(lbl)
            self._pills_row.addWidget(lbl)
        lay.addLayout(self._pills_row)

    def _apply_bg(self):
        self._apply_styles()

    def _apply_styles(self):
        t = T()

        # Root background — WA_StyledBackground + explicit selector ensures paint
        self.setStyleSheet(f"QWidget {{ background-color: {t['bg_app']}; }}")

        # Accent bars
        self._top_bar.setStyleSheet(
            f"QWidget {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {t['accent_bright']}, stop:0.6 {t['accent']}, stop:1 {t['bg_app']}); }}"
        )
        self._bot_bar.setStyleSheet(
            f"QWidget {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {t['bg_app']}, stop:0.5 {t['accent']}, stop:1 {t['accent_bright']}); }}"
        )

        # Topbar
        self._topbar_widget.setStyleSheet(
            f"QWidget {{ background: {t['bg_card']}; border-bottom: 1px solid {t['accent_dim']}; }}"
        )
        self._brand_lbl.setStyleSheet(
            f"QLabel {{ color: {t['accent_bright']}; font-family: 'Consolas';"
            f" font-size: 14px; font-weight: bold; background: transparent; border: none; }}"
        )

        # Content area background
        self._content.setStyleSheet(
            f"QWidget {{ background-color: {t['bg_app']}; }}"
        )

        # Badge
        self._badge.setStyleSheet(
            f"QLabel {{ color: {t['accent_bright']}; font-family: 'Segoe UI';"
            f" font-size: 11px; font-weight: bold;"
            f" background: transparent;"
            f" border: 1px solid {t['accent_dim']}; border-radius: 20px;"
            f" padding: 4px 18px; }}"
        )

        # Título principal
        self._t1.setStyleSheet(
            f"QLabel {{ color: {t['text']}; font-family: 'Segoe UI';"
            f" font-size: 44px; font-weight: 900; background: transparent; }}"
        )

        # Subtítulo accent
        self._t2.setStyleSheet(
            f"QLabel {{ color: {t['accent_bright']}; font-family: 'Segoe UI';"
            f" font-size: 26px; font-weight: 700; background: transparent; }}"
        )

        # Descrição
        self._sub.setStyleSheet(
            f"QLabel {{ color: {t['text_muted']}; font-family: 'Segoe UI';"
            f" font-size: 12px; background: transparent; }}"
        )

        self._gallery_title.setStyleSheet(
            f"QLabel {{ color: {t['accent_bright']}; font-family: 'Consolas';"
            f" font-size: 10px; font-weight: bold; background: transparent; }}"
        )

        # Feature pills
        pill_s = (
            f"QLabel {{ color: {t['text_dim']}; font-family: 'Segoe UI'; font-size: 10px;"
            f" background: {t['bg_card']}; border: 1px solid {t['accent_dim']};"
            f" border-radius: 12px; padding: 3px 10px; }}"
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


