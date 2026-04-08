# -*- coding: utf-8 -*-

# Funções utilitárias para criação e gerenciamento de barras de ferramentas (toolbars).
#
# Responsabilidade: Fornecer factory functions padronizadas para criar toolbars
# em módulos, garantindo estilo uniforme e ocultamento de barras redundantes.
#
# Padrão: Factory pattern para criar elementos de toolbar com styling consistente
# baseado no tema ativo.

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLayout
from PyQt5.QtCore import Qt
from proeng.core.themes import T


def _make_toolbar(parent: QWidget, title: str):
    # Factory function que cria toolbar padronizada para módulos.
    #
    # Parâmetros:
    # - parent: Widget pai que conterá a toolbar (geralmente o módulo)
    # - title: Texto a exibir no label esquerdo da toolbar (ex: "FLOWSHEET")
    #
    # Retorno: Tupla (toolbar_widget, layout_da_toolbar) para adicionar botões
    #
    # Lógica:
    # 1. Obtém tema ativo via T()
    # 2. Cria QWidget com altura fixa (50px) e estilo Neo-Brutalist
    # 3. Cria layout horizontal com label esquerdo (título) e stretch
    # 4. Retorna widget e layout para que caller adicione botões
    #
    # Estilo: Background toolbar_bg, borda preta 4px, título em Courier New.
    t = T()
    tb = QWidget(parent)
    tb.setFixedHeight(50)
    tb.setObjectName("module_toolbar")

    tb.setStyleSheet(f"""
        QWidget#module_toolbar {{
            background: {t["toolbar_bg"]};
            border-bottom: 4px solid #000000;
        }}
    """)

    lay = QHBoxLayout(tb)
    lay.setContentsMargins(15, 0, 15, 0)
    lay.setSpacing(10)

    # Label de título: background branco, borda preta, peso 900
    lbl = QLabel(title)
    lbl.setStyleSheet(
        f"color: #000000; font-weight: 900; font-size: 16px; font-family: 'Courier New'; background: #FFFFFF; border: 2px solid #000000; padding: 4px 12px;"
    )
    lay.addWidget(lbl)
    lay.addStretch()

    return tb, lay


def _hide_inner_toolbar(parent_widget: QWidget):
    # Localiza e oculta barras de ferramentas internas redundantes.
    #
    # Parâmetro parent_widget: Widget raiz do módulo contendo potenciais
    # toolbars internas que devem ser ocultadas.
    #
    # Lógica:
    # 1. Itera por todos os children widgets via findChildren()
    # 2. Obtém objectName em minúsculas
    # 3. Se nome contém "toolbar" ou "header", chama hide()
    # 4. Impede exibição de barras redundantes/padronizadas
    #
    # Utilizado ao construir módulo para garantir que apenas
    # toolbar unificada de MainApp seja visível.
    for child in parent_widget.findChildren(QWidget):
        name = child.objectName().lower()
        if "toolbar" in name or "header" in name:
            child.hide()
