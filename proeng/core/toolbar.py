# -*- coding: utf-8 -*-
"""Utilitários para criação e manipulação de barras de ferramentas (Toolbars)."""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLayout
from PyQt5.QtCore import Qt
from proeng.core.themes import T


def _make_toolbar(parent: QWidget, title: str):
    """Cria uma barra de ferramentas padronizada para os módulos.

    Retorna (toolbar_widget, layout_da_toolbar).
    """
    t = T()
    tb = QWidget(parent)
    tb.setFixedHeight(50)
    tb.setObjectName("module_toolbar")

    # Neo-Brutalist style
    tb.setStyleSheet(f"""
        QWidget#module_toolbar {{
            background: {t["toolbar_bg"]};
            border-bottom: 4px solid #000000;
        }}
    """)

    lay = QHBoxLayout(tb)
    lay.setContentsMargins(15, 0, 15, 0)
    lay.setSpacing(10)

    lbl = QLabel(title)
    lbl.setStyleSheet(
        f"color: #000000; font-weight: 900; font-size: 16px; font-family: 'Courier New'; background: #FFFFFF; border: 2px solid #000000; padding: 4px 12px;"
    )
    lay.addWidget(lbl)
    lay.addStretch()

    return tb, lay


def _hide_inner_toolbar(parent_widget: QWidget):
    """Localiza e oculta barras de ferramentas internas redundantes.

    Utilizado para garantir que apenas a toolbar unificada do workspace seja visível.
    """
    # Procura por widgets que se comportem como cabeçalhos ou toolbars locais
    for child in parent_widget.findChildren(QWidget):
        name = child.objectName().lower()
        # Se for um widget de toolbar interna (estratégia de nomenclatura)
        if "toolbar" in name or "header" in name:
            child.hide()
