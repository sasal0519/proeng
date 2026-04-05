# -*- coding: utf-8 -*-

# Gerenciamento centralizado de temas visuais da aplicação PRO ENG.
#
# Responsabilidade: Centralizar todas as definições de cores, tipografia, dimensões
# e propriedades visuais utilizadas pela interface PyQt5. Fornece mecanismo de
# troca dinâmica de temas através de dicionário global ativo (_ACTIVE).
#
# Temas disponíveis:
# - dark: Tema escuro com acentos roxo (#8B5CF6) e verde-água (#06D6A0)
# - light: Tema claro com paleta terrosa (terracota, azul-marinho, areia)
# - neo_brutalist: Tema neo brutalista com cores vibrantes e bordas grossas
#
# Design system:
# - SEM gradientes, SEM transparência (cores sólidas apenas)
# - Tipografia sans-serif pesada (Arial Black, weight 900)
# - Bordas sólidas com offset de sombra duro (sem blur)
# - Border radius zero em todos os elementos
#
# Outputs:
# - Dicionário tema ativo acessível via T()
# - Constante W5H2_TYPES com cores para nós do diagrama 5W2H

# Dicionário de temas: cada tema mapeia chaves padronizadas para valores de cor/dimensão.
# Chaves esperadas:
# - bg_*: cores de fundo (app, cards, inputs)
# - accent*: cores de destaque (principal, bright, dim)
# - text*: cores de texto (primário, secundário, muted)
# - btn_*: cores específicas para botões de ação
# - shadow*: cor e offsets de sombra (dura, sem blur)
# - border_*: espessura e raio de bordas
# - font_*: famílias tipográficas para títulos e conteúdo

THEMES = {
    # Tema escuro: fundo quase preto com cards em azul-marinho profundo.
    # Acentos: roxo vibrante (principal), verde-água (hover).
    # Sombras roxas criando efeito neon sutil.
    "dark": {
        "name": "dark",
        "bg_app": "#0D0D0D",
        "bg_card": "#1A1A2E",
        "bg_card2": "#16213E",
        "bg_input": "#0F0F1A",
        "glass_border": "#8B5CF6",
        "accent": "#8B5CF6",
        "accent_bright": "#06D6A0",
        "accent_dim": "#6D28D9",
        "text": "#F1F1F1",
        "text_dim": "#A0A0B0",
        "text_muted": "#6B6B80",
        "line": "#8B5CF6",
        "line_eap": "#4A4A5A",
        "btn_add": "#06D6A0",
        "btn_sib": "#00B4D8",
        "btn_del": "#EF476F",
        "node_bg": "#1A1A2E",
        "node_border": "#8B5CF6",
        "node_text": "#F1F1F1",
        "toolbar_bg": "#1A1A2E",
        "toolbar_sep": "#8B5CF6",
        "toolbar_btn": "#16213E",
        "toolbar_btn_h": "#8B5CF6",
        "sig_bg_l": "#0D0D0D",
        "sig_bg_r": "#1A1A2E",
        "sig_border": "#8B5CF6",
        "sig_text": "#F1F1F1",
        "btn_close_h": "#EF476F",
        "btn_win_h": "#F1F1F1",
        "shadow": "#8B5CF6",
        "shadow_offset_x": 6,
        "shadow_offset_y": 6,
        "shadow_hover_offset_x": 3,
        "shadow_hover_offset_y": 3,
        "border_width": 3,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
    },
    # Tema claro: fundo creme quente com cards brancos.
    # Paleta: terracota (#E07A5F), azul-marinho (#3D405B), areia (#F2CC8F).
    # Sombras pretas sólidas, estilo neo brutalista suave.
    "light": {
        "name": "light",
        "bg_app": "#F0E6D3",
        "bg_card": "#FFFFFF",
        "bg_card2": "#E8D5C4",
        "bg_input": "#FFFFFF",
        "glass_border": "#000000",
        "accent": "#E07A5F",
        "accent_bright": "#3D405B",
        "accent_dim": "#F2CC8F",
        "text": "#2D2D2D",
        "text_dim": "#5C5C5C",
        "text_muted": "#8A8A8A",
        "line": "#000000",
        "line_eap": "#000000",
        "btn_add": "#81B29A",
        "btn_sib": "#3D405B",
        "btn_del": "#E07A5F",
        "node_bg": "#FFFFFF",
        "node_border": "#000000",
        "node_text": "#2D2D2D",
        "toolbar_bg": "#F4F1DE",
        "toolbar_sep": "#000000",
        "toolbar_btn": "#FFFFFF",
        "toolbar_btn_h": "#E07A5F",
        "sig_bg_l": "#F0E6D3",
        "sig_bg_r": "#FFFFFF",
        "sig_border": "#000000",
        "sig_text": "#2D2D2D",
        "btn_close_h": "#E07A5F",
        "btn_win_h": "#000000",
        "shadow": "#000000",
        "shadow_offset_x": 6,
        "shadow_offset_y": 6,
        "shadow_hover_offset_x": 3,
        "shadow_hover_offset_y": 3,
        "border_width": 3,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
        "block_yellow": "#F2CC8F",
        "block_green": "#81B29A",
        "block_blue": "#3D405B",
        "block_red": "#E07A5F",
        "block_orange": "#E9C46A",
        "block_purple": "#6A1B9A",
    },
    # Tema neo brutalista: fundo laranja claro com cards brancos.
    # Cores vibrantes e alto contraste: laranja (#FF6D00), vermelho (#FF1744).
    # Bordas grossas (4px) e sombras com offset (8px), sem blur.
    "neo_brutalist": {
        "name": "neo_brutalist",
        "bg_app": "#FFF3E0",
        "bg_card": "#FFFFFF",
        "bg_card2": "#FFE0B2",
        "bg_input": "#FFFFFF",
        "glass_border": "#000000",
        "accent": "#FF6D00",
        "accent_bright": "#FF1744",
        "accent_dim": "#FFB74D",
        "text": "#000000",
        "text_dim": "#37474F",
        "text_muted": "#78909C",
        "line": "#000000",
        "line_eap": "#000000",
        "btn_add": "#00C853",
        "btn_sib": "#2979FF",
        "btn_del": "#FF1744",
        "node_bg": "#FFFFFF",
        "node_border": "#000000",
        "node_text": "#000000",
        "toolbar_bg": "#FFE0B2",
        "toolbar_sep": "#000000",
        "toolbar_btn": "#FFFFFF",
        "toolbar_btn_h": "#FF6D00",
        "sig_bg_l": "#FFF3E0",
        "sig_bg_r": "#FFFFFF",
        "sig_border": "#000000",
        "sig_text": "#000000",
        "btn_close_h": "#FF1744",
        "btn_win_h": "#000000",
        "shadow": "#000000",
        "shadow_offset_x": 8,
        "shadow_offset_y": 8,
        "shadow_hover_offset_x": 4,
        "shadow_hover_offset_y": 4,
        "border_width": 4,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
        "block_yellow": "#FFD600",
        "block_green": "#00C853",
        "block_blue": "#2979FF",
        "block_red": "#FF1744",
        "block_orange": "#FF6D00",
        "block_purple": "#AA00FF",
    },
}

# Estado global do tema: dicionário mutável que armazena tema ativo.
# Usa dict em vez de variável direta para permitir modificação por referência
# em módulos importados sem necessidade de reimport.
# Tema padrão: neo_brutalist
_ACTIVE = {"theme": THEMES["neo_brutalist"]}

# Sequência de rotação ao ciclar temas: dark -> light -> neo_brutalist -> dark (loop).
_THEME_ORDER = ["dark", "light", "neo_brutalist"]


def T():
    # Retorna dicionário do tema ativo.
    #
    # Função de acesso centralizado ao tema corrente. Todos os módulos de UI
    # chamam T() para obter cores e propriedades visuais atualizadas.
    # Permite trocar tema globalmente sem necessidade de reimport.
    #
    # Retorno: Dict com todas as chaves de cores e propriedades do tema ativo.
    return _ACTIVE["theme"]


def set_theme(name: str):
    # Define tema ativo pelo nome.
    #
    # Parâmetro name: Chave do tema em THEMES ('dark', 'light', 'neo_brutalist').
    #
    # Exceção: KeyError se o nome não existir no dicionário THEMES.
    #
    # Lógica: Atualiza _ACTIVE para apontar para o dicionário do tema solicitado.
    _ACTIVE["theme"] = THEMES[name]


def cycle_theme():
    # Avança para o próximo tema na sequência cíclica.
    #
    # Lógica:
    # 1. Obtém nome do tema atual
    # 2. Encontra seu índice em _THEME_ORDER
    # 3. Calcula próximo índice com módulo (volta ao início se necessário)
    # 4. Atualiza _ACTIVE e retorna o novo nome
    #
    # Retorno: String com nome do tema que foi ativado (dark/light/neo_brutalist).
    #
    # Utilizado por NavBar e MainApp quando usuário clica botão de alternância.
    current = _ACTIVE["theme"]["name"]
    try:
        idx = _THEME_ORDER.index(current)
    except ValueError:
        idx = 0
    next_idx = (idx + 1) % len(_THEME_ORDER)
    _ACTIVE["theme"] = THEMES[_THEME_ORDER[next_idx]]
    return _THEME_ORDER[next_idx]


# Mapeamento de cores para nós do diagrama 5W2H.
# W5H2_TYPES: mapeia cada tipo de nó para rótulo descritivo (t) e cor de fundo (c).
# Utilizado pelo módulo w5h2.py para colorir células da tabela durante renderização.
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
