# -*- coding: utf-8 -*-

# Utilitários globais de interface e renderização.
#
# Responsabilidade: Fornecer funções compartilhadas para:
# - Acesso seguro a cores do tema ativo via chave de dicionário
# - Renderização de nós/retângulos com estilo neo-brutalista (sem gradientes)
# - Exportação de diagramas para PNG/PDF com alta qualidade
#
# Design: SÓLIDO. SEM gradientes, SEM transparência em nenhuma função.
# Todas as cores são RGB sólidas. Sombras renderizadas como deslocamentos
# com cor sólida. Bordas grossas (3-4px) sem arredondamento.
#
# Outputs: QColor(s) com tema ativo, funções de renderização QPainter-based,
# diálogos de arquivo/exportação

from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
    QGraphicsView,
    QGraphicsScene,
    QFileDialog,
)
from PyQt5.QtGui import (
    QPen,
    QBrush,
    QColor,
    QPainter,
    QPixmap,
)
from PyQt5.QtCore import Qt, QRectF

from proeng.core.themes import T, _ACTIVE


def _c(key):
    # Retorna QColor pelo valor de chave do tema ativo.
    #
    # Acesso seguro: Se chave não existir, retorna cor padrão #7367F0 (roxo).
    # Se tema não estiver inicializado ou houver erro, também retorna fallback.
    #
    # Parâmetro key: String com nome de chave no dicionário theme (ex: "accent", "text").
    # Retorno: QColor com valor hexadecimal da cor do tema ativo.
    #
    # Utilizado em toda a aplicação para obter cores dinâmicas sem hardcoding.
    try:
        val = T().get(key, "#7367F0")
        return QColor(val)
    except Exception:
        return QColor("#7367F0")


def _solid_fill(rect, hovered=False):
    # Retorna cor sólida de preenchimento sem gradientes ou transparência.
    #
    # Lógica:
    #   - Se hovered=True: retorna bg_card2 (cor secundária de fundo, geralmente mais clara)
    #   - Caso contrário: retorna bg_card (cor primária de fundo)
    #
    # Parâmetros:
    #   rect: QRectF do objeto sendo preenchido (futuro uso para lógica condicional)
    #   hovered: Boolean indicando estado hover para escolher cor
    #
    # Retorno: QColor do preenchimento sólido.
    return _c("bg_card2") if hovered else _c("bg_card")


def _is_nb(t=None):
    # Verifica se renderização deve usar estilo neo-brutalista.
    #
    # Nota histórica: Anteriormente retornava if t["name"] == "neo_brutalist",
    # mas foi unificado - TODOS os temas agora usam renderização neo-brutalista
    # (bordas duras, sombras sólidas, sem gradientes/transparência).
    #
    # Retorno: Sempre True no presente (função mantida para compatibilidade reversa).
    return True


def _nb_paint_node(
    painter,
    rect,
    hovered=False,
    pressed=False,
    border_color=None,
    bg_color=None,
    shadow=True,
    radius=None,
):
    # Renderiza nó/retângulo com estilo neo-brutalista (sem gradientes/transparência).
    #
    # Responsabilidade: Desenhar elemento de interface com bordas duras, sombra
    # sólida com offset, e cores derivadas do tema ativo. Simula feedback de
    # interação (hover reduz sombra, pressed desloca elemento para baixo-direita).
    #
    # Parâmetros:
    #   painter: QPainter em operação de desenho
    #   rect: QRectF do retângulo a desenhar
    #   hovered: Boolean indicando estado hover (reduz tamanho da sombra)
    #   pressed: Boolean indicando estado pressionado (desloca elemento, sem sombra)
    #   border_color: Cor customizada de borda (hex string). Se None, usa glass_border do tema.
    #   bg_color: Cor customizada de fundo (hex string). Se None, usa bg_card ou bg_card2.
    #   shadow: Boolean indicando se deve desenhar sombra
    #   radius: Raio de arredondamento personalizado. Se None, usa border_radius do tema.
    #
    # Processo de renderização:
    #   1. Obtém propriedades do tema (border_width, shadow_offset_*, border_radius)
    #   2. Calcula offsets de sombra baseado em estado (pressed > hovered > normal)
    #   3. Obtém cores (sombra, borda, preenchimento)
    #   4. Desenha sombra com translação (apenas se shadow=True e pressed=False)
    #   5. Desenha retângulo/rounded_rect com borda e preenchimento
    #   6. Restaura estado do painter após operações
    #
    # Design: Sombras sólidas com offset duro (sem blur). Borders espessas (3-4px).
    # Sem transparência em nenhuma etapa.
    t = T()

    bw = t.get("border_width", 3)
    if pressed:
        sx = t.get("shadow_offset_x", 4)
        sy = t.get("shadow_offset_y", 4)
        shadow = False
    elif hovered:
        sx = t.get("shadow_hover_offset_x", 2)
        sy = t.get("shadow_hover_offset_y", 2)
    else:
        sx = t.get("shadow_offset_x", 4)
        sy = t.get("shadow_offset_y", 4)
    rad = t.get("border_radius", 0) if radius is None else radius
    sh_col = QColor(t.get("shadow", "#000000"))
    bdr_col = QColor(border_color) if border_color else QColor(t["glass_border"])
    fill_col = QColor(bg_color) if bg_color else _solid_fill(rect, hovered)

    if pressed and shadow:
        pass
    elif shadow:
        painter.save()
        painter.setBrush(QBrush(sh_col))
        painter.setPen(QPen(Qt.NoPen))
        shadow_rect = rect.translated(sx, sy)
        painter.drawRect(shadow_rect)
        painter.restore()

    painter.save()
    if pressed:
        painter.translate(sx, sy)
    painter.setBrush(QBrush(fill_col))
    painter.setPen(QPen(bdr_col, bw))
    if rad > 0:
        painter.drawRoundedRect(rect, rad, rad)
    else:
        painter.drawRect(rect)
    painter.restore()


# CONSTANTES DE CORES (LEGADO)
# Estas constantes foram utilizadas em versões antigas da aplicação.
# Mantidas aqui por compatibilidade reversa, mas NÃO devem ser usadas em novo código.
# Usar T() + _c(chave) em vez disso para cores dinâmicas baseadas no tema.

C_BG_APP = "transparent"
C_BG_NODE = "transparent"
C_BORDER = "rgba(0,0,0,0)"
C_TEXT_MAIN = "white"
C_TEXT = "white"
C_PLACEHOLDER = "grey"
C_BTN_ADD = "#22C55E"
C_BTN_DEL = "#EF4444"
C_LINE = "#7367F0"
C_BTN_SIB = "#0EA5E9"
C_BG_ROOT = "#5E50EF"
C_BORDER_ROOT = "white"


def _export_view(view, fmt, parent=None):
    # Exporta vista gráfica para arquivo PNG ou PDF.
    #
    # Responsabilidade: Abrir diálogo de salvamento, renderizar cena QGraphicsView
    # em alta qualidade (supersample 3x para PNG, A3 landscape para PDF), e salvar.
    #
    # Parâmetros:
    #   view: QGraphicsView contendo a cena a exportar
    #   fmt: Formato de arquivo ("png" ou "pdf")
    #   parent: Widget pai para diálogos modais (opcional)
    #
    # Exportação PNG:
    #   - Escala: 3x (resulta em imagem 3x maior para melhor qualidade)
    #   - Algoritmo: Renderiza cena em QPixmap, salva como PNG
    #   - Fundo: Usa cor bg_app do tema ativo
    #
    # Exportação PDF:
    #   - Requer módulo PyQt5.QtPrintSupport (QPrinter)
    #   - Tamanho: A3 landscape para diagramas complexos
    #   - Resolução: HighResolution
    #   - Aspect ratio: Mantém proporções do diagrama
    #
    # Fluxo:
    #   1. Obtém bounding rect da cena (com padding de 150px)
    #   2. Verifica se cena está vazia (mostra aviso e retorna)
    #   3. Abre diálogo QFileDialog para usuário escolher local/nome do arquivo
    #   4. Se fmt=="png": renderiza em QPixmap e salva
    #   5. Se fmt=="pdf": cria QPrinter com configurações, renderiza e salva
    #   6. Mostra diálogo de confirmação com caminho do arquivo salvo
    t = T()
    scene = view.scene()
    rect = scene.itemsBoundingRect().adjusted(-150, -150, 150, 150)
    if rect.isEmpty():
        QMessageBox.warning(parent, "Nada para exportar", "A cena está vazia.")
        return

    if fmt == "png":
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PNG", "diagrama.png", "Imagem PNG (*.png)"
        )
        if not path:
            return
        scale = 3
        target_w = max(1, int(rect.width() * scale))
        target_h = max(1, int(rect.height() * scale))
        img = QPixmap(target_w, target_h)
        img.fill(QColor(t["bg_app"]))
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        target_rect = QRectF(0, 0, target_w, target_h)
        scene.render(p, target=target_rect, source=rect)
        p.end()
        img.save(path, "PNG")
        QMessageBox.information(parent, "PNG Exportado", f"Arquivo salvo em:\n{path}")

    elif fmt == "pdf":
        try:
            from PyQt5.QtPrintSupport import QPrinter

            HAS_PRINT = True
        except ImportError:
            HAS_PRINT = False

        if not HAS_PRINT:
            QMessageBox.warning(
                parent,
                "Módulo ausente",
                "QPrintSupport não encontrado.\nExecute: pip install PyQt5 --upgrade",
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            parent, "Exportar como PDF", "diagrama.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPrinter.A3)
        printer.setOrientation(QPrinter.Landscape)
        p = QPainter(printer)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        target_rect = QRectF(0, 0, printer.width(), printer.height())
        scene.render(
            p, target=target_rect, source=rect, aspectRatioMode=Qt.KeepAspectRatio
        )
        p.end()
        QMessageBox.information(parent, "PDF Exportado", f"Arquivo salvo em:\n{path}")


# Mapeamento de tipos de nós do diagrama 5W2H com rótulos e cores.
# Legado: Este dicionário também está definido em themes.py.
# Mantido aqui por compatibilidade com código antigo usando utils.W5H2_TYPES.
# Novo código deve importar de themes.py: from proeng.core.themes import W5H2_TYPES
#
# Estrutura:
#   - Chave: tipo de nó (ROOT, WHAT, WHY, WHO, WHERE, WHEN, HOW, COST)
#   - Valor: dict com "t" (texto/rótulo) e "c" (cor de fundo em hex)

W5H2_TYPES = {
    "ROOT": {"t": "PLANO DE ACAO", "c": "#E03535"},
    "WHAT": {"t": "O QUE? (Acao)", "c": "#3498DB"},
    "WHY": {"t": "POR QUE? (Justificativa)", "c": "#F1C40F"},
    "WHO": {"t": "QUEM? (Responsavel)", "c": "#9B59B6"},
    "WHERE": {"t": "ONDE? (Local)", "c": "#2ECC71"},
    "WHEN": {"t": "QUANDO? (Prazo)", "c": "#E67E22"},
    "HOW": {"t": "COMO? (Metodo/Etapas)", "c": "#1ABC9C"},
    "COST": {"t": "QUANTO? (Custo/Orcamento)", "c": "#E74C3C"},
}
