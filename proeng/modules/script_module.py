# -*- coding: utf-8 -*-

"""
Interpretador de Scripts de Engenharia — PRO ENG.

Edicao livre (esquerda) + canvas com animacao leve (direita).
O script roda em QThread separada; plt.pause() usa canvas.draw_idle()
— so redesenha o que mudou, sem custo de re-renderizacao total.
"""

import gc
import io
import math
import sys as _sys
import time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as _plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure as MplFigure

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import (
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

try:
    from scipy import integrate as _scipy_integrate
    from scipy import optimize as _scipy_optimize
    from scipy import constants as _scipy_constants

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from proeng.core.base_module import BaseModule
from proeng.core.themes import T
from proeng.core.toolbar import _make_toolbar


# ═══════════════════════════════════════════════════════════
# Exemplo padrao — Difusao de Calor 1D (FTCS explicito)
# ═══════════════════════════════════════════════════════════
EXAMPLE_PFR = """\
# Difusao de Calor 1D em uma placa — Metodo Explicito (FTCS)

a      = 70   # Difusividade termica
length = 100  # mm
time   = 40   # segundos
nodes  = 50   # numero de malhas

dx = length / (nodes - 1)
dt = 0.5 * dx**2 / a          # criterio de estabilidade
t_nodes = int(time / dt) + 1

u = np.zeros(nodes) + 50       # temperatura inicial: 50 C
u[0]   = 100                   # contorno esquerdo
u[-1]  = 0                     # contorno direito

fig, axis = plt.subplots()

pcm = axis.pcolormesh(u, cmap=plt.cm.jet, vmin=0, vmax=150)
plt.colorbar(pcm, ax=axis)
axis.set_ylim([-1, 2])

counter = 0
for step in range(t_nodes):
    w = u.copy()
    for i in range(1, nodes - 1):
        u[i] = dt * a * (w[i - 1] - 2 * w[i] + w[i + 1]) / dx**2 + w[i]
    counter += dt

    pcm.set_array(u)
    axis.set_title(f"t = {counter:.3f} s  |  T_media = {np.average(u):.2f} C")
    plt.pause(0.01)

print("Simulacao concluida.")
""".lstrip()


# ═══════════════════════════════════════════════════════════
# Worker — executa script em background
# ═══════════════════════════════════════════════════════════
class ScriptWorker(QThread):
    """
    exec() em thread de fundo (NÃO trava Qt).
    plt.pause() → emite sinal leve para canvas.draw_idle() na main thread.
    """

    redraw = pyqtSignal()   # sinal leve: so trigger
    result = pyqtSignal(object, str, str)  # (error, stdout, stderr)

    def __init__(self, codigo, ns, figure, canvas):
        super().__init__()
        self.codigo = codigo
        self.ns = ns
        self.figure = figure
        self.canvas = canvas

        self._orig_newfig   = _plt.figure
        self._orig_subplots = _plt.subplots
        self._orig_pause    = _plt.pause
        self._orig_show     = _plt.show
        self._orig_close    = _plt.close
        self._orig_gcf      = _plt.gcf
        self._orig_draw     = _plt.draw

    # ── mocks ────────────────────────────────────────
    def _w_newfig(self, *a, **kw):
        return self.figure

    def _w_subplots(self, *a, **kw):
        self.figure.clear()
        nrows = a[0] if len(a) > 0 else kw.get("nrows", 1)
        ncols = a[1] if len(a) > 1 else kw.get("ncols", 1)
        if nrows * ncols > 1:
            return self.figure, self.figure.subplots(nrows, ncols)
        return self.figure, self.figure.add_subplot(111)

    def _w_pause(self, interval=0.01):
        self.redraw.emit()
        # Pausa na thread do worker — Qt continua livre
        if interval > 0:
            time.sleep(max(interval, 0.003))

    def _w_show(self, *_a, **_kw):
        pass

    def _w_close(self, *_a, **_kw):
        pass

    def _w_gcf(self, **kw):
        return self.figure

    def _w_draw(self, *_, **__):
        self.redraw.emit()
        self.canvas.draw_idle()

    # ── run ──────────────────────────────────────────
    def run(self):
        _plt.figure   = self._w_newfig
        _plt.subplots = self._w_subplots
        _plt.pause    = self._w_pause
        _plt.show     = self._w_show
        _plt.close    = self._w_close
        _plt.gcf      = self._w_gcf
        _plt.draw     = self._w_draw

        self.figure.set_canvas(self.canvas)

        old_out, old_err = _sys.stdout, _sys.stderr
        out_buf = io.StringIO()
        err_buf = io.StringIO()
        _sys.stdout = out_buf
        _sys.stderr = err_buf

        error = None
        try:
            exec(self.codigo, self.ns)
        except Exception as e:
            error = e
        finally:
            out_text = out_buf.getvalue()
            err_text = err_buf.getvalue()
            _sys.stdout = old_out
            _sys.stderr = old_err

            _plt.figure   = self._orig_newfig
            _plt.subplots = self._orig_subplots
            _plt.pause    = self._orig_pause
            _plt.show     = self._orig_show
            _plt.close    = self._orig_close
            _plt.gcf      = self._orig_gcf
            _plt.draw     = self._orig_draw

            self.redraw.emit()
            self.result.emit(error, out_text, err_text)


# ═══════════════════════════════════════════════════════════
# Editor + Canvas
# ═══════════════════════════════════════════════════════════
class EditorInterpretadorWidget(QWidget):
    """Editor livre + canvas com animacao leve em tempo real."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Toolbar ──────────────────────────────────────
        self._tb, tb_lay = _make_toolbar(self, "Interpretador de Engenharia")
        self.btn_run = QPushButton("▶ Executar e Plotar")
        self.btn_run.clicked.connect(self._executar_codigo)
        tb_lay.addWidget(self.btn_run)
        layout.addWidget(self._tb)

        # ── QSplitter ───────────────────────────────────
        self.splitter = QSplitter(Qt.Vertical)

        # Painel superior: Editor
        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 11))
        self.editor.setPlaceholderText(
            "# Digite seu script Python aqui.\n"
            "# Use 'plt' para plotar → aparece no canvas.\n"
        )
        self.editor.setPlainText(EXAMPLE_PFR)

        # Painel inferior: Canvas
        self.fig = MplFigure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.fig)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.canvas)
        self.splitter.setSizes([350, 650])

        layout.addWidget(self.splitter)

        # Painel de output
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(70)
        self.output.setPlaceholderText("Output do script...")

        # Worker
        self._worker = None

        self.refresh_theme()

    # ──────────────────────────────────────────────────────
    # Execucao
    # ──────────────────────────────────────────────────────
    def _executar_codigo(self):
        self.output.clear()
        self.output.hide()
        self.btn_run.setEnabled(False)

        codigo = self.editor.toPlainText().strip()
        if not codigo:
            self.btn_run.setEnabled(True)
            return

        ns: dict = {"np": np, "math": math, "plt": _plt}
        if SCIPY_AVAILABLE:
            ns["integrate"] = _scipy_integrate
            ns["optimize"]  = _scipy_optimize
            ns["constants"] = _scipy_constants

        self._worker = ScriptWorker(codigo, ns, self.fig, self.canvas)
        self._worker.redraw.connect(self._on_redraw)
        self._worker.result.connect(self._on_result)
        self._worker.start()

    def _on_redraw(self):
        """Atualizacao leve — tema minimo + draw_idle()."""
        theme = T()
        self.fig.patch.set_facecolor(theme["bg_app"])
        for ax in self.fig.get_axes():
            ax.set_facecolor(theme["bg_card"])
            ax.tick_params(colors=theme["text"])
        self.canvas.draw_idle()

    def _on_result(self, error, stdout_text, stderr_text):
        self._apply_theme_full()       # tema completo so ao final

        if stdout_text.strip():
            self.output.setPlainText(stdout_text.rstrip())
            self.output.show()

        if error is not None:
            QMessageBox.critical(self, "Erro de Execucao", str(error)[:2000])
        elif stderr_text.strip():
            QMessageBox.warning(self, "Aviso", stderr_text.strip()[:1000])

        gc.collect()
        self.btn_run.setEnabled(True)
        self._worker = None

    # ──────────────────────────────────────────────────────
    # Temas
    # ──────────────────────────────────────────────────────
    def refresh_theme(self):
        theme = T()

        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme["accent"]};
                color: {theme["text"]};
                font-weight: 900;
                font-size: 13px;
                border: 2px solid {theme["text"]};
                border-radius: 0px;
                padding: 6px 18px;
            }}
            QPushButton:hover {{ background: {theme["accent_bright"]}; color: #FFF; }}
            QPushButton:pressed {{ background: {theme["accent_dim"]}; }}
            QPushButton:disabled {{ background: {theme["text_muted"]}; color: {theme["bg_card"]}; }}
            """
        )

        self.editor.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {theme["bg_card"]};
                color: {theme["text"]};
                border: 3px solid {theme["accent_dim"]};
                font-family: "Consolas", monospace;
                padding: 8px;
            }}
            """
        )

        self.output.setStyleSheet(
            f"QPlainTextEdit {{ background: {theme["bg_card"]}; color: {theme["text_muted"]}; "
            f"border: none; border-top: 1px solid {theme["accent_dim"]}; "
            f"font-family: Consolas, monospace; font-size: 10px; }}"
        )

        self._apply_theme_full()

    def _apply_theme_full(self):
        """Aplica tema completo — chamada apenas ao final ou no init."""
        theme = T()
        self.fig.patch.set_facecolor(theme["bg_app"])
        for ax in self.fig.get_axes():
            ax.set_facecolor(theme["bg_card"])
            for spine in ax.spines.values():
                spine.set_color(theme["accent_dim"])
                spine.set_linewidth(1.5)
            ax.tick_params(colors=theme["text"])
            if ax.xaxis.get_label():
                ax.xaxis.label.set_color(theme["text"])
            if ax.yaxis.get_label():
                ax.yaxis.label.set_color(theme["text"])
            if ax.title:
                ax.title.set_color(theme["text"])
        self.canvas.draw()


# ═══════════════════════════════════════════════════════════
# Wrapper BaseModule
# ═══════════════════════════════════════════════════════════
class _ScriptModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = EditorInterpretadorWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._inner)

    def refresh_theme(self):
        self._inner.refresh_theme()
