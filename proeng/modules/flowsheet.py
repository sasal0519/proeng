# -*- coding: utf-8 -*-
"""Módulo PFD Flowsheet — Diagrama de processo industrial."""
import sys
import math
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QListWidget, QListWidgetItem, QSplitter, QGraphicsPathItem, QMenu,
    QListView, QLineEdit, QLabel, QStackedWidget, QTextEdit,
    QGraphicsRectItem, QInputDialog, QFileDialog, QSizePolicy, QGraphicsEllipseItem, QToolBox,
    QGraphicsSimpleTextItem, QDialog, QComboBox, QFormLayout, QDialogButtonBox
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
    C_BORDER, C_TEXT_MAIN, C_TEXT, C_PLACEHOLDER, C_BTN_ADD, C_BTN_DEL, C_LINE,
    C_BTN_SIB, C_BG_ROOT, C_BORDER_ROOT, W5H2_TYPES)
from proeng.core.toolbar import _make_toolbar, _hide_inner_toolbar
from proeng.core.base_module import BaseModule


from PyQt5.QtWidgets import QDialog, QComboBox, QFormLayout, QDialogButtonBox

class TerminalConfigDialog(QDialog):
    """Diálogo industrial para escolher Tipo e Nome do fluxo."""
    def __init__(self, parent=None, suggested_type="Saída"):
        super().__init__(parent)
        self.setWindowTitle("Configurar Terminal")
        self.setMinimumWidth(320)
        t = T()
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Entrada", "Saída"])
        self.type_combo.setCurrentText(suggested_type)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Água, Vapor, MP-01...")
        self.name_edit.setFocus()
        
        form.addRow("Tipo de Fluxo:", self.type_combo)
        form.addRow("Nome do Fluxo:", self.name_edit)
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg_app']}; color: {t['text']}; }}
            QLabel {{ color: {t['text']}; font-weight: bold; }}
            QComboBox, QLineEdit {{ 
                background: {t['bg_card']}; 
                border: 1px solid {t['accent']}; 
                border-radius: 4px; 
                padding: 6px; 
                color: {t['text']}; 
            }}
            QPushButton {{ 
                background: {t['bg_card']}; 
                color: {t['text']}; 
                border-radius: 4px; 
                padding: 6px 15px; 
                min-width: 80px;
            }}
            QPushButton:hover {{ background: {t['accent']}; color: white; }}
        """)

    def get_values(self):
        return self.type_combo.currentText(), self.name_edit.text()


EQUIPMENT_ALIASES = {
    "Bomba Centrífuga": "Bomba", "Bomba Volumétrica": "Bomba", "Compressores": "Bomba",
    "Trocador Casco-Tubo": "Trocador", "Reator CSTR": "Reator", "Tanque Aberto": "Tanque", 
    "Vaso Vertical": "Vaso", "Tanque Misturador": "Misturador", "Secador Rotativo": "Secador", 
    "Válvula Globo": "Válvula", "PSV (Alívio)": "PSV", "Válvula de Bloqueio": "Válvula", 
    "Forno": "Forno", "Fornalha": "Forno", "Lavagem": "Lavadora", "Peneira": "Peneira", 
    "Filtro": "Filtro", "Separador Bifásico": "Separador Bifásico", "Vaso Horizontal": "Vaso_H",
    "Esfera de Gás": "Esfera", "Silo": "Silo", "Compressor": "Compressor", "Soprador": "Compressor",
    "Exaustor": "Fan", "Turbina": "Turbina", "Ejetor": "Ejetor", "Trocador de Placas": "Trocador_P",
    "Caldeira": "Caldeira", "Torre de Resfriamento": "Resfriamento", "Evaporador": "Evaporador",
    "Aquecedor Elétrico": "Heat_E", "Reator Tubular (PFR)": "Reator_T", "Moinho": "Moinho",
    "Britador": "Britador", "Válvula Borboleta": "Válvula_B", "Válvula de Controle": "Válvula_C",
    "Válvula de Retenção": "Válvula_R", "Flare": "Flare", "Chaminé": "Chaminé",
    "Correia Transportadora": "Correia", "Rosca Transportadora": "Rosca", "Elevador de Canecas": "Elevador",
    "Refervedor Kettle": "Refervedor", "Condensador de Casco": "Trocador", "Extrusora": "Extrusora",
    "Leito Fluidizado": "Reator_F", "Precipitador Eletrostático": "ESP", "Filtro Rotativo": "Filtro_R",
    "Coluna de Recheio": "Torre_R", "Válvula Solenoide": "Válvula_S", "Tanque de Teto Flutuante": "Tanque_F",
    "LPG Esfera": "Esfera", "Britador de Mandíbula": "Britador", "Peneira Vibratória": "Peneira_V",
    "Transmissor de Pressão": "Inst_P", "Transmissor de Temperatura": "Inst_T", "Transmissor de Vazão": "Inst_V",
    "Transmissor de Nível": "Inst_N", "Analisador": "Inst_A", "Válvula de Segurança (SRV)": "PSV",
    "Secador de Spray": "Spray_D", "Misturador Estático": "Mist_E", "Filtro de Mangas": "Bag_F",
    "Reator de Batelada": "Reator_B", "Cristalizador": "Cristal", "Filtro Prensa": "Filtro_P",
    "Adsorvedor": "Vaso", "Agitador de Pá": "Misturador", "Válvula de Pé": "Válvula",
    "Transportador Pneumático": "Pneum_C", "Válvula de Macho": "Válvula", "Filtro Cartucho": "Filtro",
    "Bomba de Vácuo": "Bomba", "Ejetor de Vapor": "Ejetor", "Resfriador de Filme": "Trocador",
    "Peneira Rotativa": "Peneira", "Hidrociclone": "Ciclone", "Ciclone de Gases": "Ciclone",
    "Talha Elétrica": "Box", "Painel de Controle": "Box", "Válvula de Esfera": "Válvula_B"
}

def draw_equipment(painter, symbol_type, size, is_icon=False, theme=None):
    s = size / 2
    if theme is None:
        try: theme = T()
        except: theme = THEMES["dark"]
    
    pen_color = theme["text"] if is_icon else theme["accent"]
    _bg_node = theme["bg_card"]
    
    # Efeito "Glass Neon" Industrial Dinâmico
    grad = QLinearGradient(QPointF(-size, -size), QPointF(size, size))
    c_base = QColor(theme["accent"])
    
    # Opacidade ajustada para o tema (mais sutil no Light)
    alpha1 = 60 if theme["name"] == "dark" else 40
    alpha2 = 20 if theme["name"] == "dark" else 10
    
    c_fill1 = QColor(c_base.red(), c_base.green(), c_base.blue(), alpha1)
    c_fill2 = QColor(c_base.red(), c_base.green(), c_base.blue(), alpha2)
    grad.setColorAt(0, c_fill1)
    grad.setColorAt(1, c_fill2)

    pw = 1.2 if is_icon else 1.8
    default_pen = QPen(QColor(pen_color), pw, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(default_pen)
    painter.setBrush(QBrush(grad))

    st = EQUIPMENT_ALIASES.get(symbol_type, symbol_type)

    if st == "Vaso":
        painter.drawRoundedRect(QRectF(-s*0.8, -s, s*1.6, s*2), s*0.6, s*0.6)
    elif st == "Vaso Horizontal":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3, s*1.2), s*0.6, s*0.6)
    elif st == "Tanque":
        painter.drawRect(QRectF(-s*0.8, -s*0.5, s*1.6, s*1.5))
        painter.drawArc(QRectF(-s*0.8, -s*1.0, s*1.6, s*1.0), 0, 180 * 16)
    elif st == "Tanque Fechado":
        painter.drawRect(QRectF(-s*0.8, -s, s*1.6, s*2))
        painter.drawArc(QRectF(-s*0.8, -s*1.2, s*1.6, s*0.8), 0, 180 * 16)
        painter.drawArc(QRectF(-s*0.8, s*0.6, s*1.6, s*0.8), 180*16, 180 * 16)
    elif st == "Esfera de Gás":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.6, s*0.8), QPointF(-s*0.8, s*1.5))
        painter.drawLine(QPointF(s*0.6, s*0.8), QPointF(s*0.8, s*1.5))
    elif st == "Silo":
        painter.drawRect(QRectF(-s*0.8, -s*1.5, s*1.6, s*2))
        poly = QPolygonF([QPointF(-s*0.8, s*0.5), QPointF(s*0.8, s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Separador Bifásico":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3.0, s*1.2), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.5, 0), QPointF(s*1.5, 0))
    elif st == "Separador Trifásico":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.6, s*3.0, s*1.2), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.5, -s*0.2), QPointF(s*1.5, -s*0.2))
        painter.drawLine(QPointF(-s*1.5, s*0.2), QPointF(s*1.5, s*0.2))
    elif st == "Bomba":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        poly = QPolygonF([QPointF(-s*0.3, -s*0.7), QPointF(s*0.3, -s*0.7), QPointF(0, -s*1.4)])
        painter.drawPolygon(poly)
    elif st == "Bomba Volumétrica":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawEllipse(QRectF(-s*0.4, -s*0.4, s*0.8, s*0.8))
        painter.drawLine(QPointF(0, -s*0.8), QPointF(0, s*0.8))
    elif st == "Compressor":
        poly = QPolygonF([QPointF(-s*0.8, s*0.8), QPointF(s*0.8, s*0.4),
                          QPointF(s*0.8, -s*0.4), QPointF(-s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif st == "Soprador":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.6, s*1.2, s*1.2))
        painter.drawRect(QRectF(s*0.2, -s*0.6, s*0.5, s*0.5))
    elif st == "Exaustor":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawLine(QPointF(-s*0.6, 0), QPointF(s*0.6, 0))
        painter.drawLine(QPointF(0, -s*0.6), QPointF(0, s*0.6))
    elif st == "Turbina":
        poly = QPolygonF([QPointF(s*0.8, s*0.8), QPointF(-s*0.8, s*0.4),
                          QPointF(-s*0.8, -s*0.4), QPointF(s*0.8, -s*0.8)])
        painter.drawPolygon(poly)
    elif st == "Ejetor":
        poly = QPolygonF([QPointF(-s, -s*0.3), QPointF(-s*0.2, -s*0.1), QPointF(s, -s*0.3),
                          QPointF(s, s*0.3), QPointF(-s*0.2, s*0.1), QPointF(-s, s*0.3)])
        painter.drawPolygon(poly)
    elif st == "Trocador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, 0), QPointF(-s*0.5, -s*0.5))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(0, s*0.5))
        painter.drawLine(QPointF(0, s*0.5), QPointF(s*0.5, -s*0.5))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(s, 0))
    elif st == "Trocador de Placas":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        for i in [-0.8, -0.4, 0, 0.4, 0.8]:
            painter.drawLine(QPointF(s*i, -s*0.8), QPointF(s*i, s*0.8))
    elif st == "Permutador a Ar":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawLine(QPointF(-s*0.5, -s*0.5), QPointF(s*0.5, -s*1.2))
        painter.drawLine(QPointF(s*0.5, -s*0.5), QPointF(-s*0.5, -s*1.2))
        painter.drawEllipse(QRectF(-s*0.6, -s*1.3, s*1.2, s*0.8))
    elif st == "Resfriador de Topo":
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        painter.drawLine(QPointF(-s*0.8, -s*0.8), QPointF(s*0.8, s*0.8))
    elif st == "Fornalha":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s*1.5))
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(0, -s*1.5), QPointF(s, -s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, s*0.2))
        painter.drawLine(QPointF(s*0.6, s*0.2), QPointF(-s*0.6, -0.2))
    elif st == "Caldeira":
        painter.drawRoundedRect(QRectF(-s*1.5, -s*0.8, s*3.0, s*1.6), s*0.4, s*0.4)
        for i in [-0.4, 0, 0.4]:
            painter.drawLine(QPointF(-s*1.5, s*i), QPointF(s*1.5, s*i))
    elif st == "Torre de Resfriamento":
        poly = QPolygonF([QPointF(-s, s*1.5), QPointF(s, s*1.5),
                          QPointF(s*0.6, -s*1.2), QPointF(-s*0.6, -s*1.2)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(-s*0.4, -s*1.4), QPointF(s*0.4, -s*1.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, -s*1.4))
    elif st == "Evaporador":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*1.5, s*1.2, s*2), s*0.6, s*0.6)
        painter.drawRect(QRectF(-s*0.6, s*0.5, s*1.2, s*1.0))
    elif st == "Aquecedor Elétrico":
        painter.drawRect(QRectF(-s*0.6, -s, s*1.2, s*2))
        poly = QPolygonF([QPointF(-s*0.4, 0), QPointF(0, -s*0.6), QPointF(s*0.4, 0), QPointF(0, s*0.6)])
        painter.drawPolygon(poly)
    elif st.startswith("Inst_"):
        painter.drawEllipse(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6))
        txt = st.split("_")[1]
        painter.drawText(QRectF(-s*0.8, -s*0.8, s*1.6, s*1.6), Qt.AlignCenter, txt)
    elif st == "Spray_D":
        painter.drawRect(QRectF(-s, -s*1.2, s*2, s*1.2))
        poly = QPolygonF([QPointF(-s, 0), QPointF(0, s*1.5), QPointF(s, 0)])
        painter.drawPolygon(poly)
    elif st == "Mist_E":
        painter.drawRect(QRectF(-s*2, -s*0.3, s*4, s*0.6))
        for i in range(5): painter.drawLine(QPointF(-s*2+i*s*0.8, -s*0.3), QPointF(-s*1.6+i*s*0.8, s*0.3))
    elif st == "Bag_F":
        painter.drawRect(QRectF(-s, -s, s*2, s*1.5))
        for i in range(3): painter.drawRect(QRectF(-s*0.8+i*s*0.6, -s*0.8, s*0.4, s*2))
    elif st == "Reator_B":
        painter.drawRoundedRect(QRectF(-s, -s, s*2, s*2.5), s*0.4, s*0.4)
        painter.drawLine(QPointF(0, -s*0.5), QPointF(0, s*0.5))
        painter.drawLine(QPointF(-s*0.4, s*0.5), QPointF(s*0.4, s*0.5))
    elif st == "Cristal":
        painter.drawRoundedRect(QRectF(-s, -s*1.5, s*2, s*3), s*0.5, s*0.5)
        for i in range(10): painter.drawPoint(QPointF(random.uniform(-s*0.5, s*0.5), random.uniform(-s, s)))
    elif st == "Filtro_P":
        painter.drawRect(QRectF(-s*1.5, -s, s*3, s*2))
        for i in range(6): painter.drawLine(QPointF(-s*1.5+i*s*0.5, -s), QPointF(-s*1.5+i*s*0.5, s))
    elif st == "Pneum_C":
        painter.drawRect(QRectF(-s*2, -s*0.2, s*4, s*0.4))
        painter.drawEllipse(QRectF(s*1.5, -s*0.5, s, s))
    elif st == "Vaso_H":
        painter.drawRoundedRect(QRectF(-s*1.8, -s*0.8, s*3.6, s*1.6), s*0.6, s*0.6)
        painter.drawLine(QPointF(-s*1.2, s*0.8), QPointF(-s*1.2, s*1.1))
        painter.drawLine(QPointF(s*1.2, s*0.8), QPointF(s*1.2, s*1.1))
    elif st == "Compressor":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawEllipse(QRectF(-s*0.6, -s*0.6, s*1.2, s*1.2))
        painter.drawLine(QPointF(0, -s), QPointF(0, s))
    elif st == "Fan":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        for i in range(4):
            ang = i * 90; painter.drawLine(QPointF(0,0), QPointF(s*math.cos(math.radians(ang)), s*math.sin(math.radians(ang))))
    elif st == "Turbina":
        poly = QPolygonF([QPointF(-s, -s*0.6), QPointF(s, -s), QPointF(s, s), QPointF(-s, s*0.6)])
        painter.drawPolygon(poly)
    elif st == "Ejetor":
        poly = QPolygonF([QPointF(-s, -s*0.3), QPointF(-s*0.2, -s*0.2), QPointF(s*0.2, -s*0.4), QPointF(s, -s*0.4), 
                          QPointF(s, s*0.4), QPointF(s*0.2, s*0.4), QPointF(-s*0.2, s*0.2), QPointF(-s, s*0.3)])
        painter.drawPolygon(poly)
    elif st == "Trocador_P":
        painter.drawRect(QRectF(-s*0.8, -s*1.2, s*1.6, s*2.4))
        for i in range(5): painter.drawLine(QPointF(-s*0.8, -s+i*s*0.5), QPointF(s*0.8, -s+i*s*0.5+0.2))
    elif st == "Resfriamento":
        painter.drawRect(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, -s*0.7), QPointF(s, -s*0.7))
        painter.drawEllipse(QRectF(-s*0.4, -s*1.2, s*0.8, s*0.4))
    elif st == "Evaporador":
        painter.drawRoundedRect(QRectF(-s*0.7, -s*1.5, s*1.4, s*3), s*0.5, s*0.5)
        for i in range(4): painter.drawArc(QRectF(-s*0.4, -s+i*s*0.5, s*0.8, s*0.4), 0, 180*16)
    elif st == "Reator_T":
        painter.drawRect(QRectF(-s*1.6, -s*0.5, s*3.2, s))
        for i in [-1.0, -0.5, 0, 0.5, 1.0]:
            painter.drawEllipse(QRectF(s*i - s*0.2, -s*0.4, s*0.4, s*0.8))
    elif st == "Moinho":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawPoint(0,0); painter.drawEllipse(QRectF(-s*0.5, -s*0.5, s, s))
    elif st == "Britador":
        painter.drawLine(QPointF(-s, -s), QPointF(0, s)); painter.drawLine(QPointF(s, -s), QPointF(0, s))
        painter.drawLine(QPointF(-s*0.5, -s), QPointF(s*0.5, -s))
    elif st == "Válvula_B":
        poly = QPolygonF([QPointF(-s, -s*0.6), QPointF(s, s*0.6), QPointF(s, -s*0.6), QPointF(-s, s*0.6)])
        painter.drawPolygon(poly); painter.drawEllipse(QRectF(-s*0.2, -s*0.2, s*0.4, s*0.4))
    elif st == "Válvula_C":
        poly = QPolygonF([QPointF(-s, -s*0.6), QPointF(s, s*0.6), QPointF(s, -s*0.6), QPointF(-s, s*0.6)])
        painter.drawPolygon(poly); painter.drawArc(QRectF(-s*0.6, -s*1.4, s*1.2, s*0.8), 0, 180*16)
        painter.drawLine(QPointF(0, -s*0.1), QPointF(0, -s*0.6))
    elif st == "Válvula_R":
        poly = QPolygonF([QPointF(-s, -s*0.6), QPointF(s, s*0.6), QPointF(s, -s*0.6), QPointF(-s, s*0.6)])
        painter.drawPolygon(poly); painter.drawLine(QPointF(-s, s*0.6), QPointF(s, -s*0.6))
    elif st == "Chaminé":
        poly = QPolygonF([QPointF(-s*0.5, -s*2), QPointF(s*0.5, -s*2), QPointF(s, s*2), QPointF(-s, s*2)])
        painter.drawPolygon(poly)
    elif st == "Refervedor":
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6), s*0.4, s*0.4)
        painter.drawRect(QRectF(s*0.2, -s*0.4, s*0.8, s*0.8))
    elif st == "Extrusora":
        painter.drawRect(QRectF(-s*2, -s*0.4, s*4, s*0.8))
        painter.drawRect(QRectF(-s*1.8, -s*0.9, s*0.6, s*0.5))
        for i in range(8): painter.drawLine(QPointF(-s*1.5+i*s*0.4, -s*0.4), QPointF(-s*1.3+i*s*0.4, s*0.4))
    elif st == "Reator_F":
        painter.drawRoundedRect(QRectF(-s*0.8, -s*2, s*1.6, s*4), s*0.4, s*0.4)
        for i in range(20): painter.drawPoint(QPointF(random.uniform(-s*0.6, s*0.6), random.uniform(s, s*1.8)))
    elif st == "ESP":
        painter.drawRect(QRectF(-s*1.5, -s, s*3, s*2))
        for i in range(4): painter.drawLine(QPointF(-s*1.2+i*s*0.8, -s), QPointF(-s*1.2+i*s*0.8, s))
        poly = QPolygonF([QPointF(-s*1.5, s), QPointF(-s*0.5, s*1.5), QPointF(0, s), QPointF(0.5*s, s*1.5), QPointF(s*1.5, s)])
        painter.drawPolyline(poly)
    elif st == "Filtro_R":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawRect(QRectF(-s*1.2, s*0.2, s*2.4, s*0.8))
    elif st == "Torre_R":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        for i in range(3):
            y = -s*1.5 + i*s*1.5
            painter.drawRect(QRectF(-s*0.5, y, s, s*0.8))
            for j in range(3): painter.drawLine(QPointF(-s*0.5, y+j*0.2*s), QPointF(s*0.5, y+j*0.2*s+0.1*s))
    elif st == "Válvula_S":
        poly = QPolygonF([QPointF(-s, -s*0.6), QPointF(s, s*0.6), QPointF(s, -s*0.6), QPointF(-s, s*0.6)])
        painter.drawPolygon(poly); painter.drawRect(QRectF(-s*0.3, -s*1.3, s*0.6, s*0.7))
    elif st == "Tanque_F":
        painter.drawRect(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, -s*0.5), QPointF(s, -s*0.5))
    elif st == "Peneira_V":
        painter.drawLine(QPointF(-s*1.5, -s*0.5), QPointF(s*1.5, s*0.5))
        for i in range(10): painter.drawPoint(QPointF(-s*1.3+i*s*0.3, -s*0.4+i*s*0.1))
    elif st == "Esfera":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.7, s), QPointF(-s*0.7, s*1.3))
        painter.drawLine(QPointF(s*0.7, s), QPointF(s*0.7, s*1.3))
    elif st == "Correia":
        painter.drawRoundedRect(QRectF(-s*2, -s*0.2, s*4, s*0.4), s*0.2, s*0.2)
        painter.drawEllipse(QRectF(-s*1.9, -s*0.15, s*0.3, s*0.3))
        painter.drawEllipse(QRectF(s*1.6, -s*0.15, s*0.3, s*0.3))
    elif st == "Rosca":
        painter.drawRect(QRectF(-s*2, -s*0.3, s*4, s*0.6))
        for i in range(10): painter.drawLine(QPointF(-s*2 + i*s*0.4, -s*0.3), QPointF(-s*1.8 + i*s*0.4, s*0.3))
    elif st == "Elevador":
        painter.drawRect(QRectF(-s*0.4, -s*2, s*0.8, s*4))
        for i in range(5): painter.drawRect(QRectF(-s*0.3, -s*1.8 + i*s*0.8, s*0.6, s*0.3))
    elif st == "Heat_E":
        painter.drawRect(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, -s), QPointF(s, s)); painter.drawLine(QPointF(-s, s), QPointF(s, -s))
    elif st == "Flare":
        painter.drawLine(QPointF(-s*0.3, s*2), QPointF(0, -s*2)); painter.drawLine(QPointF(s*0.3, s*2), QPointF(0, -s*2))
        painter.drawEllipse(QRectF(-s*0.4, -s*2.2, s*0.8, s*0.4))
    elif st == "Reator":
        painter.drawRoundedRect(QRectF(-s*0.8, -s*1.2, s*1.6, s*2.4), s*0.4, s*0.4)
        painter.drawRect(QRectF(-s*0.25, -s*1.6, s*0.5, s*0.4))
        painter.drawLine(QPointF(0, -s*1.2), QPointF(0, s*0.6))
        painter.drawLine(QPointF(-s*0.4, s*0.2), QPointF(s*0.4, s*0.6))
        painter.drawLine(QPointF(s*0.4, s*0.2), QPointF(-s*0.4, s*0.6))
    elif st == "Reator Tubular (PFR)":
        painter.drawRect(QRectF(-s*1.6, -s*0.5, s*3.2, s))
        for i in [-1.0, -0.5, 0, 0.5, 1.0]:
            painter.drawEllipse(QRectF(s*i - s*0.2, -s*0.4, s*0.4, s*0.8))
    elif st == "Misturador":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s*0.6, -s*0.6), QPointF(s*0.6, s*0.6))
        painter.drawLine(QPointF(-s*0.6, s*0.6), QPointF(s*0.6, -s*0.6))
    elif st == "Moinho":
        painter.drawRect(QRectF(-s, -s*0.5, s*2, s))
        painter.drawEllipse(QRectF(-s*0.8, -s*0.4, s*0.8, s*0.8))
        painter.drawEllipse(QRectF(0, -s*0.4, s*0.8, s*0.8))
    elif st == "Britador":
        poly = QPolygonF([QPointF(-s*0.8, -s), QPointF(s*0.8, -s), QPointF(s*0.4, s*0.8), QPointF(-s*0.4, s*0.8)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, -s), QPointF(0, s*0.8))
    elif st == "Torre de Destilação":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        for i in range(8):
            y = -s*2 + i*s*0.6
            painter.drawLine(QPointF(-s*0.6, y), QPointF(s*0.6, y))
    elif st == "Coluna de Absorção":
        painter.drawRoundedRect(QRectF(-s*0.6, -s*2.5, s*1.2, s*5), s*0.5, s*0.5)
        for i in [-1.5, -0.75, 0, 0.75, 1.5]:
            painter.drawLine(QPointF(-s*0.6, s*i), QPointF(s*0.6, s*i))
        painter.drawLine(QPointF(-s*0.6, -s*1.5), QPointF(s*0.6, s*1.5))
        painter.drawLine(QPointF(s*0.6, -s*1.5), QPointF(-s*0.6, s*1.5))
    elif st == "Secador":
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.6, s*2.4, s*1.2), s*0.2, s*0.2)
        painter.drawLine(QPointF(-s*1.2, 0), QPointF(s*1.2, 0))
    elif st == "Filtro Prensa":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        for i in [-0.6, 0, 0.6]:
            painter.drawLine(QPointF(s*i, -s*0.8), QPointF(s*i, s*0.8))
    elif st == "Filtro Rotativo":
        painter.drawEllipse(QRectF(-s*1.2, -s*1.2, s*2.4, s*2.4))
        painter.drawRect(QRectF(-s*1.5, s*0.4, s*3, s*0.8))
    elif st == "Filtro":
        painter.drawEllipse(QRectF(-s, -s, s*2, s*2))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s, 0), QPointF(s, 0))
        painter.setPen(default_pen)
    elif st == "Ciclone":
        painter.drawRect(QRectF(-s*0.6, -s*1.5, s*1.2, s))
        poly = QPolygonF([QPointF(-s*0.6, -s*0.5), QPointF(s*0.6, -s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Hidrociclone":
        painter.drawRect(QRectF(-s*0.4, -s*1.5, s*0.8, s))
        poly = QPolygonF([QPointF(-s*0.4, -s*0.5), QPointF(s*0.4, -s*0.5), QPointF(0, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Centrífuga":
        painter.drawEllipse(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        painter.drawLine(QPointF(-s*1.2, 0), QPointF(s*1.2, 0))
    elif st == "Clarificador":
        painter.drawRect(QRectF(-s*1.5, -s*0.5, s*3, s))
        poly = QPolygonF([QPointF(-s*1.5, s*0.5), QPointF(s*1.5, s*0.5), QPointF(s*0.5, s*1.5), QPointF(-s*0.5, s*1.5)])
        painter.drawPolygon(poly)
    elif st == "Peneira Vibratória" or st == "Peneira":
        painter.drawRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6))
        painter.setPen(QPen(QColor(pen_color), 2, Qt.DashLine))
        painter.drawLine(QPointF(-s*1.2, -s*0.4), QPointF(s*1.2, s*0.4))
        painter.setPen(default_pen)
    elif st == "Válvula":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
    elif st == "Válvula Borboleta":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawEllipse(QRectF(-s*0.2, -s*0.2, s*0.4, s*0.4))
    elif st == "Válvula de Controle":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, 0), QPointF(0, -s*1.2))
        painter.drawEllipse(QRectF(-s*0.6, -s*1.8, s*1.2, s*0.6))
    elif st == "Válvula de Retenção":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, -s*0.5), QPointF(0, s*0.5))
    elif st == "PSV":
        poly = QPolygonF([QPointF(-s, -s*0.5), QPointF(-s, s*0.5),
                          QPointF(s, -s*0.5), QPointF(s, s*0.5)])
        painter.drawPolygon(poly)
        painter.drawLine(QPointF(0, 0), QPointF(0, -s))
        painter.drawLine(QPointF(-s*0.4, -s*0.6), QPointF(s*0.4, -s*0.6))
    elif st == "Chaminé":
        poly = QPolygonF([QPointF(-s*0.4, -s*2), QPointF(s*0.4, -s*2), QPointF(s*0.8, s*2), QPointF(-s*0.8, s*2)])
        painter.drawPolygon(poly)
    elif symbol_type == "Forno":
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.drawRoundedRect(QRectF(-s*1.2, -s*0.8, s*2.4, s*1.6), 10, 10)
        path = QPainterPath()
        path.moveTo(-s*0.8, s*0.2)
        for i in range(5):
            path.lineTo(-s*0.6 + i*s*0.3, -s*0.2 if i%2==0 else s*0.2)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
    elif symbol_type == "Lavadora":
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.drawRoundedRect(QRectF(-s*0.7, -s*1.3, s*1.4, s*2.6), 15, 15)
        for i in range(4):
            painter.drawLine(-s*0.5, -s + i*s*0.6, s*0.5, -s + i*s*0.6)
    else:
        painter.setBrush(QBrush(QColor(_bg_node)))
        painter.setPen(QPen(QColor(theme["accent"]), 2, Qt.DashLine))
        painter.drawRect(QRectF(-s, -s, s*2, s*2))
        painter.drawLine(QPointF(-s, -s), QPointF(s, s))
        painter.drawLine(QPointF(-s, s), QPointF(s, -s))


class ConnectorPort(QGraphicsEllipseItem):
    def __init__(self, node, port_id):
        super().__init__(-5, -5, 10, 10, node)
        self.node = node
        self.port_id = port_id
        self.setAcceptHoverEvents(True)
        self.setBrush(QBrush(QColor(0, 150, 255)))
        self.setPen(QPen(QColor(255, 255, 255), 1))
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setZValue(10)
        self.setVisible(False)

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor(0, 255, 255)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor(0, 150, 255)))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            view = self.scene().views()[0]
            if hasattr(view, 'start_connection'):
                view.start_connection(self)
                event.accept()
                return
        super().mousePressEvent(event)


class SourceSinkHandle(QGraphicsItem):
    """Ponta de seta independente (Source/Sink) que não depende de equipamentos."""
    def __init__(self, h_type="Saída", flow_name=""):
        super().__init__()
        self.h_type = h_type
        self.flow_name = flow_name
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.edges = []
        
    def add_edge(self, edge): self.edges.append(edge)
    def boundingRect(self): return QRectF(-20, -20, 40, 40)

    def paint(self, painter, option, widget=None):
        # Tornar o terminal invisível — Queremos apenas a SEÇÃO da seta do Edge
        pass

    def contextMenuEvent(self, event):
        menu = QMenu(); t = T()
        menu.setStyleSheet(f"QMenu{{background:{t['bg_card']};color:{t['text']};border:1px solid {t['accent']};}}")
        name_act = menu.addAction("✏️ Renomear Terminal")
        del_act = menu.addAction("🗑 Excluir Terminal")
        act = menu.exec_(event.screenPos())
        if act == name_act:
            text, ok = QInputDialog.getText(None, "Terminal", "Nome:", QLineEdit.Normal, self.flow_name)
            if ok: self.flow_name = text; self.update()
        elif act == del_act:
            for e in list(self.edges): 
                if e.scene(): self.scene().removeItem(e)
            if self.scene(): self.scene().removeItem(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for e in self.edges: e.adjust()
        return super().itemChange(change, value)


class Edge(QGraphicsPathItem):
    def __init__(self, source_node, dest_node, source_port="right", dest_port="left"):
        super().__init__()
        self.source_node = source_node
        self.dest_node = dest_node
        self.source_port = source_port
        self.dest_port = dest_port
        self.source_node.add_edge(self)
        self.dest_node.add_edge(self)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        try: lc = T()["line"]
        except: lc = "#94a3b8"
        pen = QPen(QColor(lc), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)
        self.setZValue(-1)
        self.is_utility = False
        self.pipe_name = ""
        # Container para o label com fundo para visibilidade
        self.label_bg = QGraphicsRectItem(self)
        self.label_bg.setBrush(QBrush(QColor(T()["bg_app"]))) 
        self.label_bg.setPen(QPen(Qt.NoPen))
        self.label_bg.setVisible(False)
        
        self.label_item = QGraphicsSimpleTextItem(self.label_bg)
        self.label_item.setBrush(QBrush(QColor(T()["text"])))
        self.label_item.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.label_item.setVisible(True)
        
        self.adjust()

    def get_port_normal(self, port_id):
        side = port_id.split('_')[0]
        if side == "top": return (0, -1)
        if side == "bottom": return (0, 1)
        if side == "left": return (-1, 0)
        if side == "right": return (1, 0)
        return (0, 0)

    def get_port_position(self, node, port_id):
        if isinstance(node, SourceSinkHandle): return node.scenePos() 
        if hasattr(node, 'ports') and port_id in node.ports:
            return node.mapToScene(node.ports[port_id].pos())
        return node.sceneBoundingRect().center()

    def adjust(self):
        if not self.source_node or not self.dest_node:
            return
        p1 = self.get_port_position(self.source_node, self.source_port)
        p2 = self.get_port_position(self.dest_node, self.dest_port)
        path = QPainterPath()
        path.moveTo(p1)
        d1 = self.get_port_normal(self.source_port)
        d2 = self.get_port_normal(self.dest_port)
        p1_out = QPointF(p1.x() + d1[0]*25, p1.y() + d1[1]*25)
        p2_in  = QPointF(p2.x() + d2[0]*25, p2.y() + d2[1]*25)
        path.lineTo(p1_out)
        if d1[1] != 0:
            path.lineTo(p1_out.x(), p1_out.y())
            path.lineTo(p2_in.x(), p1_out.y()) 
            path.lineTo(p2_in.x(), p2_in.y())
        else:
            path.lineTo(p1_out.x(), p2_in.y())
            path.lineTo(p2_in.x(), p2_in.y())
        path.lineTo(p2)
        self.setPath(path)
        
        # Posicionamento Robusto do Label
        if self.pipe_name:
            # Encontra o ponto médio do caminho para o label
            mid_p = path.pointAtPercent(0.5)
            self.label_item.setText(self.pipe_name)
            self.label_item.setBrush(QBrush(QColor(T()["text"]))) # Cor dinâmica conforme tema
            self.label_bg.setBrush(QBrush(QColor(T()["bg_app"]))) # "Mask" com a cor do fundo
            br = self.label_item.boundingRect()
            self.label_bg.setRect(0, 0, br.width() + 8, br.height() + 4)
            self.label_item.setPos(4, 2)
            # Posiciona o label ACIMA da linha para maior clareza visual
            self.label_bg.setPos(mid_p.x() - br.width()/2 - 4, mid_p.y() - br.height() - 10)
            self.label_bg.setVisible(True)
            self.label_bg.setZValue(1)
        else:
            self.label_bg.setVisible(False)
        dx, dy = p2.x() - p2_in.x(), p2.y() - p2_in.y()
        self._arrow_dir = math.atan2(dy, dx); self._dest_pos = p2

    def contextMenuEvent(self, event):
        menu = QMenu(); t = T()
        menu.setStyleSheet(f"QMenu{{background:{t['bg_card']};color:{t['text']};border:1px solid {t['accent']};}}")
        name_action = menu.addAction("✏️ Renomear Fluxo")
        del_act = menu.addAction("🗑 Excluir Tubulação")
        action = menu.exec_(event.screenPos())
        if action == del_act:
            for n in [self.source_node, self.dest_node]:
                if isinstance(n, SourceSinkHandle):
                    if n.scene(): self.scene().removeItem(n)
                elif n and self in n.edges: n.edges.remove(self)
            if self.scene(): self.scene().removeItem(self)
        elif action == name_action:
            text, ok = QInputDialog.getText(None, "Piping", "Nome:", QLineEdit.Normal, self.pipe_name)
            if ok: self.pipe_name = text; self.label_item.setText(text); self.adjust()

    def paint(self, painter, option, widget=None):
        try: t = T(); lc = t.get("line", C_LINE)
        except: t = {"accent_bright": "#00E5FF"}; lc = C_LINE
        
        style = Qt.SolidLine
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.isSelected(): 
            painter.setPen(QPen(QColor(t.get("accent_bright", "#00E5FF")), 3, style, Qt.RoundCap, Qt.RoundJoin))
        else: 
            painter.setPen(QPen(QColor(lc), 2.5, style, Qt.RoundCap, Qt.RoundJoin))
            
        painter.drawPath(self.path())
        
        if hasattr(self, '_dest_pos'):
            color = QColor(lc) if not self.isSelected() else QColor(t.get("accent_bright", "#34d399"))
            painter.setPen(QPen(Qt.NoPen))
            painter.setBrush(QBrush(color))
            
            p1, angle = self._dest_pos, self._arrow_dir
            size = 8
            
            # Seta Sólida Industrial (Triângulo)
            p2 = QPointF(p1.x() - size * math.cos(angle - 0.35), p1.y() - size * math.sin(angle - 0.35))
            p3 = QPointF(p1.x() - size * math.cos(angle + 0.35), p1.y() - size * math.sin(angle + 0.35))
            
            arrow_head = QPolygonF([p1, p2, p3])
            painter.drawPolygon(arrow_head)


class ProcessNode(QGraphicsItem):
    def __init__(self, symbol_type):
        super().__init__()
        self.symbol_type = symbol_type
        self.edges = []; self.size = 50
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True); self.setCursor(QCursor(Qt.SizeAllCursor))
        self.ports = {f"{s}_{i}": ConnectorPort(self, f"{s}_{i}") for s in ["top","bottom","left","right"] for i in range(1,4)}
        self.update_ports()
        self.custom_name = ""
        self._hover_bg = QGraphicsRectItem(self)
        self._hover_bg.setBrush(QBrush(QColor(20, 20, 20, 230)))
        self._hover_bg.setPen(QPen(QColor(T()["accent"]), 1))
        self._hover_text = QGraphicsSimpleTextItem(self.symbol_type, self)
        self._hover_text.setBrush(QBrush(QColor("white")))
        self._hover_text.setFont(QFont("Segoe UI", 9, QFont.Bold))
        tw, th = self._hover_text.boundingRect().width(), self._hover_text.boundingRect().height()
        self._hover_bg.setRect(-5, -5, tw + 10, th + 10)
        r = self.boundingRect(); lx, ly = r.center().x() - tw/2, r.top() - th - 15
        self._hover_bg.setPos(lx, ly); self._hover_text.setPos(lx, ly)
        self._hover_bg.setVisible(False); self._hover_text.setVisible(False)
        self._hover_bg.setAcceptHoverEvents(False); self._hover_text.setAcceptHoverEvents(False)
        
        # Rótulo Persistente (Nome do Equipamento) — Sem fundo, cor dinâmica
        self._name_item = QGraphicsSimpleTextItem(self)
        self._name_item.setBrush(QBrush(QColor(T()["text"])))
        self._name_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.update_name_pos()

    def update_name_pos(self):
        r = self.boundingRect()
        tw = self._name_item.boundingRect().width()
        # Centralizado abaixo do equipamento
        self._name_item.setPos(r.center().x() - tw/2, r.bottom() - 15)

    def hoverEnterEvent(self, event):
        for port in self.ports.values(): port.setVisible(True)
        self.prepareGeometryChange()
        r = self.boundingRect(); tw = self._hover_text.boundingRect().width()
        th = self._hover_text.boundingRect().height()
        lx, ly = r.center().x() - tw/2, r.top() + 5
        self._hover_bg.setPos(lx, ly); self._hover_text.setPos(lx, ly)
        self._hover_bg.setVisible(True); self._hover_text.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        for port in self.ports.values(): port.setVisible(False)
        self._hover_bg.setVisible(False); self._hover_text.setVisible(False)
        super().hoverLeaveEvent(event)

    def update_ports(self):
        s = self.size / 2; st = self._get_alias(); m = 0
        if st in ["Torre de Destilação", "Coluna de Absorção", "Flare", "Chaminé"]: r = QRectF(-s*0.8 - m, -s*2.7 - m, s*1.6 + m*2, s*5.4 + m*2)
        elif st in ["Separador Bifásico", "Separador Trifásico", "Caldeira", "Vaso Horizontal", "Clarificador"]: r = QRectF(-s*1.8 - m, -s - m, self.size*1.8 + m*2, self.size + m*2)
        elif st in ["Secador", "Peneira", "Peneira Vibratória", "Filtro Prensa", "Trocador de Placas", "Filtro Rotativo"]: r = QRectF(-s*1.5 - m, -s*1.2 - m, self.size*1.5 + m*2, self.size*1.2 + m*2)
        elif st in ["Reator", "Reator Tubular (PFR)", "Ciclone", "Hidrociclone", "Torre de Resfriamento", "Silo"]: r = QRectF(-s*1.8 - m, -s*1.8 - m, self.size*1.8 + m*2, self.size*1.8 + m*2)
        elif st in ["Evaporador", "Aquecedor Elétrico"]: r = QRectF(-s - m, -s*1.6 - m, self.size + m*2, self.size*1.6 + m*2)
        else: r = QRectF(-s - m, -s - m, self.size + m*2, self.size + m*2)
        if hasattr(self, 'ports'):
            for i in range(1, 4):
                f = i * 0.25
                self.ports[f"top_{i}"].setPos(r.left() + r.width() * f, r.top())
                self.ports[f"bottom_{i}"].setPos(r.left() + r.width() * f, r.bottom())
                self.ports[f"left_{i}"].setPos(r.left(), r.top() + r.height() * f)
                self.ports[f"right_{i}"].setPos(r.right(), r.top() + r.height() * f)

    def _get_alias(self):
        return EQUIPMENT_ALIASES.get(self.symbol_type, self.symbol_type)

    def add_edge(self, edge): self.edges.append(edge)

    def set_name(self, name):
        self.custom_name = name
        self._hover_text.setText(f"{self.symbol_type}: {name}" if name else self.symbol_type)
        self._name_item.setText(name if name else self.symbol_type)
        self.update_name_pos()
        # Re-ajustar fundo do hover
        tw, th = self._hover_text.boundingRect().width(), self._hover_text.boundingRect().height()
        self._hover_bg.setRect(-5, -5, tw + 10, th + 10)
        self.update()

    def set_size(self, new_size):
        self.prepareGeometryChange(); self.size = max(20, min(new_size, 300)); self.update_ports()
        for e in self.edges: e.adjust()
        self.update()

    def contextMenuEvent(self, event):
        menu = QMenu(); t = T()
        menu.setStyleSheet(f"QMenu{{background:{t['bg_card']};color:{t['text']};border:1px solid {t['accent']};}}")
        del_act = menu.addAction("🗑 Excluir Equipamento")
        act = menu.exec_(event.screenPos())
        if act == del_act:
            for e in list(self.edges):
                other = e.source_node if e.dest_node == self else e.dest_node
                if isinstance(other, SourceSinkHandle):
                    if other.scene(): self.scene().removeItem(other)
                if e.scene(): self.scene().removeItem(e)
            if self.scene(): self.scene().removeItem(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for e in self.edges: e.adjust()
        return super().itemChange(change, value)

    def boundingRect(self):
        m, s, st = 5, self.size/2, self._get_alias()
        if st in ["Torre de Destilação", "Coluna de Absorção", "Flare", "Chaminé"]: base = QRectF(-s*0.8 - m, -s*2.7 - m, s*1.6 + m*2, s*5.4 + m*2)
        elif st in ["Separador Bifásico", "Separador Trifásico", "Caldeira", "Vaso Horizontal", "Clarificador"]: base = QRectF(-s*1.8 - m, -s - m, self.size*1.8 + m*2, self.size + m*2)
        else: base = QRectF(-s - m, -s - m, self.size + m*2, self.size + m*2)
        return base.adjusted(-s*2, -60, s*2, s*2)

    def paint(self, painter, option, widget=None):
        t = T(); painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setPen(QPen(QColor(t["accent_bright"]), 2, Qt.DotLine))
            painter.drawRect(self.boundingRect().adjusted(0, 40, 0, 0))
        # Sincroniza cor do texto com o tema no redesenho
        self._name_item.setBrush(QBrush(QColor(t["text"])))
        draw_equipment(painter, self.symbol_type, self.size, False, t)


class SymbolListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setDragDropMode(QListWidget.DragOnly); self.setViewMode(QListWidget.ListMode)
        self.setIconSize(QSize(50, 50)); self.setSpacing(5); self.setWordWrap(True)

    def startDrag(self, actions):
        item = self.currentItem()
        if not item: return
        data = QByteArray(); QDataStream(data, QIODevice.WriteOnly).writeQString(item.text())
        mime = QMimeData(); mime.setData('application/x-pfd-item', data)
        drag = QDrag(self); drag.setMimeData(mime)
        pix = item.icon().pixmap(40, 40); drag.setPixmap(pix)
        drag.setHotSpot(QPoint(20, 20)); drag.exec_(Qt.CopyAction)


class SymbolPalette(QToolBox):
    def __init__(self):
        super().__init__()
        self.categories = {
            "Geral": ["Filtro", "Peneira", "Separador Bifásico", "Clarificador", "Secador Rotativo"],
            "Armazenamento": ["Tanque Aberto", "Tanque Fechado", "Vaso Vertical", "Vaso Horizontal", "Esfera de Gás", "Silo", "Tanque de Teto Flutuante", "LPG Esfera"],
            "Movimentação": ["Bomba Centrífuga", "Bomba Volumétrica", "Compressor", "Soprador", "Exaustor", "Turbina", "Ejetor", "Correia Transportadora", "Rosca Transportadora", "Elevador de Canecas"],
            "Troca Térmica": ["Trocador Casco-Tubo", "Trocador de Placas", "Forno", "Caldeira", "Torre de Resfriamento", "Evaporador", "Aquecedor Elétrico", "Refervedor Kettle", "Condensador de Casco"],
            "Transformação": ["Reator CSTR", "Reator Tubular (PFR)", "Leito Fluidizado", "Lavagem", "Tanque Misturador", "Moinho", "Britador", "Extrusora"],
            "Separação": ["Torre de Destilação", "Coluna de Absorção", "Coluna de Recheio", "Decantador", "Hidrociclone", "Precipitador Eletrostático", "Filtro Rotativo", "Filtro de Mangas", "Filtro Prensa", "Cristalizador"],
            "Instrumentação": ["Transmissor de Pressão", "Transmissor de Temperatura", "Transmissor de Vazão", "Transmissor de Nível", "Analisador"],
            "Controles": ["Válvula Globo", "Válvula Borboleta", "Válvula de Esfera", "Válvula de Controle", "Válvula de Retenção", "PSV (Alívio)", "Válvula Solenoide", "Flare", "Chaminé", "Painel de Controle"]
        }
        for cat, symbols in self.categories.items():
            lw = SymbolListWidget(); self._apply_list_style(lw)
            for sym in symbols:
                item = QListWidgetItem(self._create_icon(sym), sym); 
                item.setToolTip(f"Equipamento: {sym}")
                lw.addItem(item)
            self.addItem(lw, cat)
        self._apply_palette_style()

    def _create_icon(self, sym):
        pix = QPixmap(50, 50); pix.fill(Qt.transparent); p = QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        p.translate(25, 25); draw_equipment(p, sym, 28, True, T()); p.end()
        return QIcon(pix)

    def refresh_theme(self):
        self._apply_palette_style()
        for i in range(self.count()):
            lw = self.widget(i)
            if isinstance(lw, SymbolListWidget):
                self._apply_list_style(lw)
                # Atualiza ícones de cada item
                for row in range(lw.count()):
                    item = lw.item(row)
                    item.setIcon(self._create_icon(item.text()))

    def _apply_palette_style(self):
        t = T()
        self.setStyleSheet(f"QToolBox::tab{{background:{t['bg_card']};color:{t['text']};font-weight:bold;}} QToolBox::tab:selected{{color:{t['accent']};}}")

    def _apply_list_style(self, lw):
        t = T()
        lw.setStyleSheet(f"""
            QListWidget {{ background: {t['bg_app']}; border: none; padding: 5px; }}
            QListWidget::item {{ color: {t['text']}; font-size: 11px; font-weight: bold; border-bottom: 1px solid {t['accent_dim']}; padding: 10px; }}
            QListWidget::item:hover {{ background: {t['bg_card']}; border-radius: 8px; color: {t['accent_bright']}; }}
        """)


class FlowsheetCanvas(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene); self.setRenderHint(QPainter.Antialiasing); self.setAcceptDrops(True)
        self.mode = "Move"; self.temp_line = None; self.zoom_level = 1.0

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('application/x-pfd-item'): e.acceptProposedAction()
    def dragMoveEvent(self, e):
        if e.mimeData().hasFormat('application/x-pfd-item'): e.acceptProposedAction()
    def dropEvent(self, e):
        sym = QDataStream(e.mimeData().data('application/x-pfd-item'), QIODevice.ReadOnly).readQString()
        node = ProcessNode(sym); node.setPos(self.mapToScene(e.pos())); self.scene().addItem(node); e.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for item in self.items(event.pos()):
                if isinstance(item, ConnectorPort):
                    self.mode, self.start_port = "PortConnect", item
                    path = QPainterPath(); path.moveTo(item.scenePos())
                    self.temp_line = self.scene().addPath(path, QPen(QColor(T()["accent"]), 2, Qt.DashLine))
                    for i in self.scene().items():
                        if hasattr(i, "ports"): 
                            for p in i.ports.values(): p.setVisible(True)
                    return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == "PortConnect" and self.temp_line:
            p1, p2 = self.start_port.scenePos(), self.mapToScene(event.pos())
            path = QPainterPath(); path.moveTo(p1); path.lineTo(p2); self.temp_line.setPath(path)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.mode == "PortConnect" and self.temp_line:
            target = None
            for item in self.items(event.pos()):
                if isinstance(item, ConnectorPort) and item.node != self.start_port.node: target = item; break
            if target: self.scene().addItem(Edge(self.start_port.node, target.node, self.start_port.port_id, target.port_id))
            else:
                suggested = "Saída" if "right" in self.start_port.port_id else "Entrada"
                dialog = TerminalConfigDialog(self, suggested)
                if dialog.exec_() == QDialog.Accepted:
                    v_type, v_name = dialog.get_values()
                    if v_name:
                        # Criamos a Ponta de Seta Autônoma (Sem Ghost Nodes)
                        handle = SourceSinkHandle(v_type, v_name)
                        handle.setPos(self.mapToScene(event.pos()))
                        self.scene().addItem(handle)
                        
                        # Conectamos o pipe (Edge)
                        # Entrada: O fluxo flui do Handle para o Equipamento
                        # Saída: O fluxo flui do Equipamento para o Handle
                        if v_type == "Entrada":
                            edge = Edge(handle, self.start_port.node, "tip", self.start_port.port_id)
                        else:
                            edge = Edge(self.start_port.node, handle, self.start_port.port_id, "tip")
                            
                        self.scene().addItem(edge)
                        edge.pipe_name = v_name
                        edge.label_item.setText(v_name)
                        edge.adjust()
                    
            self.scene().removeItem(self.temp_line); self.temp_line = None; self.mode = "Move"
            for i in self.scene().items():
                if hasattr(i, "ports"): 
                    for p in i.ports.values(): p.setVisible(False)
            return
        super().mouseReleaseEvent(event)


class FlowsheetWidget(QWidget):
    def __init__(self):
        super().__init__(); layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        self._tb = QWidget(); self._tb.setFixedHeight(50); tb_lay = QHBoxLayout(self._tb)
        self.btn_pal = QPushButton("☰ Equipamentos"); self.btn_pal.setCheckable(True); self.btn_pal.setChecked(True)
        tb_lay.addWidget(self.btn_pal); tb_lay.addStretch()
        layout.addWidget(self._tb)
        self.scene = QGraphicsScene(); self.scene.setSceneRect(0,0,2000,2000); self.canvas = FlowsheetCanvas(self.scene)
        self.splitter = QSplitter(Qt.Horizontal); self.palette = SymbolPalette()
        self.splitter.addWidget(self.palette)
        self.splitter.addWidget(self.canvas)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([200, 800])
        layout.addWidget(self.splitter)
        self.process_name_input = QLineEdit(self.canvas); self.process_name_input.setPlaceholderText("Processo..."); self.process_name_input.move(15, 15)
    def load_example(self, example_id):
        # 1. Limpar cena
        self.scene.clear()
        self.process_name_input.setText(example_id)
        
        # 2. Dados dos Exemplos
        examples = {
            "Refinaria": {
                "nodes": [
                    ("Vaso Horizontal", 50, 350, "Carga"),
                    ("Bomba Centrífuga", 180, 360, "P-101"),
                    ("Torre de Destilação", 350, 250, "T-101"),
                    ("Condensador de Casco", 550, 150, "E-101"),
                    ("Tanque Fechado", 750, 150, "Destilado")
                ],
                "edges": [
                    (0, 1, "right", "left"), (1, 2, "right", "left"),
                    (2, 3, "top", "left"), (3, 4, "right", "left")
                ]
            },
            "Produção de Amônia": {
                "nodes": [
                    ("Compressor", 80, 300, "C-101"),
                    ("Reator Tubular (PFR)", 300, 300, "R-101"),
                    ("Trocador de Placas", 530, 300, "E-102"),
                    ("Separador Bifásico", 750, 300, "V-102")
                ],
                "edges": [
                    (0, 1, "right", "left"), (1, 2, "right", "left"), (2, 3, "right", "left")
                ]
            },
            "Tratamento de Água (ETA)": {
                "nodes": [
                    ("Clarificador", 100, 250, "Clarificador"),
                    ("Filtro de Mangas", 300, 250, "F-101"),
                    ("Filtro Cartucho", 500, 250, "F-102"),
                    ("Tanque Aberto", 700, 250, "Água Tratada")
                ],
                "edges": [
                    (0, 1, "right", "left"), (1, 2, "right", "left"), (2, 3, "right", "left")
                ]
            },
            "Caldeira Industrial": {
                "nodes": [
                    ("Tanque Aberto", 80, 450, "Água Alimentação"),
                    ("Bomba Centrífuga", 220, 460, "B-201"),
                    ("Caldeira", 420, 380, "Vaporizador"),
                    ("Chaminé", 650, 200, "Exaustão")
                ],
                "edges": [
                    (0, 1, "right", "left"), (1, 2, "right", "left"), (2, 3, "top", "bottom")
                ]
            },
            "Linha de Mineração": {
                "nodes": [
                    ("Britador de Mandíbula", 100, 200, "Britagem"),
                    ("Correia Transportadora", 350, 220, "Transporte"),
                    ("Moinho", 600, 200, "Moagem")
                ],
                "edges": [
                    (0, 1, "right", "left"), (1, 2, "right", "left")
                ]
            }
        }

        if example_id not in examples: return
        ex = examples[example_id]
        
        # 3. Criar Nodes
        created_nodes = []
        for sym, x, y, name in ex["nodes"]:
            node = ProcessNode(sym)
            node.setPos(x, y)
            node.set_name(name)
            self.scene.addItem(node)
            created_nodes.append(node)
            
        # 4. Criar Edges
        for s_idx, t_idx, s_por, t_por in ex["edges"]:
            edge = Edge(created_nodes[s_idx], created_nodes[t_idx], s_por, t_por)
            self.scene.addItem(edge)
            edge.adjust()

        t = T()
        # Estiliza o botão "Equipamentos" para ficar sem fundo e com texto no tema
        self.btn_pal.setStyleSheet(f"""
            QPushButton {{ 
                background: transparent; color: {t['text']}; 
                font-weight: bold; border: none; padding: 5px 15px; 
            }}
            QPushButton:hover {{ color: {t['accent']}; }}
        """)
        self._tb.setStyleSheet(f"background:{t['toolbar_bg']}; border-bottom:2px solid {t['accent']};")
        self.canvas.setBackgroundBrush(QBrush(QColor(t["bg_app"])))
        if hasattr(self, "palette"):
            self.palette.refresh_theme()
        # Força redo em todos os itens da cena para pegar novas cores e máscaras
        for item in self.scene.items():
            if isinstance(item, Edge):
                item.adjust() # Recalcula máscara com nova cor bg_app
            item.update()


class _FlowsheetModule(BaseModule):
    def __init__(self):
        super().__init__(); self._inner = FlowsheetWidget(); layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.addWidget(self._inner)
    # --- BaseModule API -------------------------------------------------
    def get_state(self):
        scene_items = self._inner.scene.items()
        nodes = []
        handles = []
        edges = []
        node_ids = {}
        handle_ids = {}

        # 1) Primeiro coletamos os nós e terminais para criar mapas de ID
        for i in scene_items:
            if isinstance(i, ProcessNode):
                node_id = f"n{len(node_ids) + 1}"
                node_ids[i] = node_id
                nodes.append({
                    "id": node_id,
                    "type": i.symbol_type,
                    "x": i.scenePos().x(),
                    "y": i.scenePos().y(),
                    "name": getattr(i, "custom_name", ""),
                    "size": getattr(i, "size", 50),
                })
            elif isinstance(i, SourceSinkHandle):
                handle_id = f"h{len(handle_ids) + 1}"
                handle_ids[i] = handle_id
                handles.append({
                    "id": handle_id,
                    "h_type": i.h_type,
                    "flow_name": i.flow_name,
                    "x": i.scenePos().x(),
                    "y": i.scenePos().y(),
                })

        # 2) Depois coletamos conexões usando IDs estáveis
        for i in scene_items:
            if not isinstance(i, Edge):
                continue

            source_kind = "node" if isinstance(i.source_node, ProcessNode) else "handle"
            dest_kind = "node" if isinstance(i.dest_node, ProcessNode) else "handle"
            source_ref = node_ids.get(i.source_node) if source_kind == "node" else handle_ids.get(i.source_node)
            dest_ref = node_ids.get(i.dest_node) if dest_kind == "node" else handle_ids.get(i.dest_node)

            # Se algum endpoint não está mapeado, ignora esta aresta para evitar estado inconsistente
            if not source_ref or not dest_ref:
                continue

            edges.append({
                "source_kind": source_kind,
                "source_id": source_ref,
                "source_port": i.source_port,
                "dest_kind": dest_kind,
                "dest_id": dest_ref,
                "dest_port": i.dest_port,
                "pipe_name": i.pipe_name,
                "is_utility": i.is_utility,
            })

        return {
            "schema": "flowsheet.v2",
            "process_name": self._inner.process_name_input.text(),
            "nodes": nodes,
            "handles": handles,
            "edges": edges,
        }

    def set_state(self, state):
        self._inner.scene.clear()

        # Compatibilidade com estado antigo (v1): {"nodes": [{"type","x","y"}]}
        if state.get("schema") != "flowsheet.v2":
            for n in state.get("nodes", []):
                node = ProcessNode(n["type"])
                node.setPos(n["x"], n["y"])
                self._inner.scene.addItem(node)
            self._inner.process_name_input.setText(state.get("process_name", ""))
            return

        created_nodes = {}
        created_handles = {}

        # 1) Recria nós de processo
        for n in state.get("nodes", []):
            node = ProcessNode(n.get("type", ""))
            node.setPos(n.get("x", 0), n.get("y", 0))
            if n.get("name"):
                node.set_name(n.get("name", ""))
            if "size" in n:
                try:
                    node.set_size(int(n["size"]))
                except Exception:
                    pass
            self._inner.scene.addItem(node)
            created_nodes[n.get("id")] = node

        # 2) Recria terminais source/sink
        for h in state.get("handles", []):
            handle = SourceSinkHandle(h.get("h_type", "Saída"), h.get("flow_name", ""))
            handle.setPos(h.get("x", 0), h.get("y", 0))
            self._inner.scene.addItem(handle)
            created_handles[h.get("id")] = handle

        # 3) Recria conexões
        for e in state.get("edges", []):
            src = created_nodes.get(e.get("source_id")) if e.get("source_kind") == "node" else created_handles.get(e.get("source_id"))
            dst = created_nodes.get(e.get("dest_id")) if e.get("dest_kind") == "node" else created_handles.get(e.get("dest_id"))
            if src is None or dst is None:
                continue
            edge = Edge(src, dst, e.get("source_port", "right"), e.get("dest_port", "left"))
            edge.pipe_name = e.get("pipe_name", "")
            edge.is_utility = bool(e.get("is_utility", False))
            if edge.pipe_name:
                edge.label_item.setText(edge.pipe_name)
            edge.adjust()
            self._inner.scene.addItem(edge)

        self._inner.process_name_input.setText(state.get("process_name", ""))
    def refresh_theme(self):
        if hasattr(self._inner, "refresh_theme"):
            self._inner.refresh_theme()
    def get_view(self):
        return getattr(self._inner, "canvas", None)

if __name__ == "__main__":
    app = QApplication(sys.argv); w = _FlowsheetModule(); w.show(); sys.exit(app.exec_())
