# -*- coding: utf-8 -*-
"""Janela principal da aplicação ProEng."""
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
import os

from proeng.core.themes import T, THEMES, _ACTIVE
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar

from proeng.ui.nav_bar import NavBar, ThemeToggle
from proeng.ui.selection_screen import SelectionScreen, ModuleCard
from proeng.modules.flowsheet import _FlowsheetModule
from proeng.modules.eap       import _EAPModule
from proeng.modules.bpmn      import _BPMNModule
from proeng.modules.canvas    import _CanvasModule
from proeng.modules.ishikawa  import _IshikawaModule
from proeng.modules.w5h2      import _W5H2Module

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



class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Eng Tools")
        self.setGeometry(80, 60, 1440, 880)
        
        # Define o ícone do programa
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self._setup_palette()

        root = QWidget()
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        self._stack = QStackedWidget()
        rl.addWidget(self._stack)
        self.setCentralWidget(root)

        self._selection = SelectionScreen(self._open_module, self._on_theme_toggle)
        self._stack.addWidget(self._selection)
        self._modules = {}
        self._stack.setCurrentIndex(0)

        self._sig = SignatureOverlay(self)
        self._sig.raise_(); self._sig.show()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_sig'):
            self._sig._reposition()

    def _on_theme_toggle(self):
        """Propaga mudança de tema para todos os módulos abertos."""
        self._setup_palette()
        t = T()
        # Refresh every wrapped module
        for mod in self._modules.values():
            mod.setStyleSheet(f"background:{t['bg_app']};")
            # Refresh NavBar
            nav = mod.findChild(NavBar)
            if nav:
                nav._apply_style()
                nav.update()
            # Call refresh_theme on every inner widget that has it
            for w in mod.findChildren(QWidget):
                if hasattr(w, "refresh_theme"):
                    try:
                        w.refresh_theme()
                    except Exception:
                        pass
            # Refresh all canvas backgrounds
            for gv in mod.findChildren(QGraphicsView):
                try:
                    gv.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
                    if gv.scene():
                        gv.scene().update()
                except Exception:
                    pass
            # Refresh symbol palette style
            for sp in mod.findChildren(QListWidget):
                if hasattr(sp, "_apply_palette_style"):
                    try:
                        sp._apply_palette_style()
                    except Exception:
                        pass
        # Refresh signature overlay
        self._sig.update()
        # Refresh selection screen fully
        if hasattr(self._selection, "_refresh"):
            self._selection._refresh()
        # Update the app palette so native widgets also switch
        self._setup_palette()

    def _setup_palette(self):
        t = T()
        p = QPalette()
        p.setColor(QPalette.Window,          QColor(t["bg_app"]))
        p.setColor(QPalette.WindowText,      QColor(t["text"]))
        p.setColor(QPalette.Base,            QColor(t["bg_card"]))
        p.setColor(QPalette.AlternateBase,   QColor(t["bg_card2"]))
        p.setColor(QPalette.Text,            QColor(t["text"]))
        p.setColor(QPalette.Button,          QColor(t["bg_card"]))
        p.setColor(QPalette.ButtonText,      QColor(t["text"]))
        p.setColor(QPalette.Highlight,       QColor(t["accent"]))
        p.setColor(QPalette.HighlightedText, QColor(t["bg_app"]))
        QApplication.instance().setPalette(p)

    def _open_module(self, module_name):
        titles = {
            "flowsheet": "🏭  PFD Flowsheet",
            "eap":       "📋  Gerador EAP",
            "bpmn":      "🔀  BPMN Modeler",
            "canvas":    "📝  PM Canvas",
            "ishikawa":  "🐟  Ishikawa — Causa e Efeito",
            "w5h2":      "🎯  Plano de Ação 5W2H",
        }
        builders = {
            "flowsheet": _FlowsheetModule,
            "eap":       _EAPModule,
            "bpmn":      _BPMNModule,
            "canvas":    _CanvasModule,
            "ishikawa":  _IshikawaModule,
            "w5h2":      _W5H2Module,
        }
    
        if module_name not in self._modules:
            w       = builders[module_name]()
            wrapped = self._wrap_module(w, titles[module_name])
            self._stack.addWidget(wrapped)
            self._modules[module_name] = wrapped

        self._stack.setCurrentWidget(self._modules[module_name])
        nav = self._modules[module_name].findChild(NavBar)
        if nav:
            nav.set_module(titles[module_name])
        self.setWindowTitle(f"Pro Eng Tools  —  {titles[module_name]}")
        self._sig.raise_()

    def _wrap_module(self, module_widget, title):
        t = T()
        container = QWidget()
        container.setStyleSheet(f"background:{t['bg_app']};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        nav = NavBar(self._go_home, self._on_theme_toggle)
        nav.set_module(title)
        nav._toggle.theme_changed.connect(self._on_theme_toggle)
        lay.addWidget(nav)
        lay.addWidget(module_widget)
        # Apply theme immediately on first creation
        if hasattr(module_widget, "refresh_theme"):
            try:
                module_widget.refresh_theme()
            except Exception:
                pass
        return container

    def _go_home(self):
        self._stack.setCurrentIndex(0)
        self.setWindowTitle("Pro Eng Tools")
        self._sig.raise_()
        # Ensure selection screen reflects current theme when returning
        if hasattr(self._selection, "_refresh"):
            self._selection._refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
