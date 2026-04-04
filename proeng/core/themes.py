# -*- coding: utf-8 -*-
"""Sistema de temas — Dark, Light e Neo Brutalist.

Regras: SEM gradientes, SEM transparencia. Cores solidas apenas.
Tipografia: sans-serif pesada, geometrica, bold.
"""

THEMES = {
    "dark": {
        "name": "dark",
        "bg_app": "#0a0a0a",
        "bg_card": "#1a1a1a",
        "bg_card2": "#2a2a2a",
        "bg_input": "#111111",
        "glass_border": "#00ff88",
        "accent": "#00ff88",
        "accent_bright": "#00ccff",
        "accent_dim": "#00aa55",
        "text": "#ffffff",
        "text_dim": "#cccccc",
        "text_muted": "#888888",
        "line": "#00ff88",
        "line_eap": "#666666",
        "btn_add": "#00ff88",
        "btn_sib": "#00ccff",
        "btn_del": "#ff4444",
        "node_bg": "#1a1a1a",
        "node_border": "#00ff88",
        "node_text": "#ffffff",
        "toolbar_bg": "#1a1a1a",
        "toolbar_sep": "#00ff88",
        "toolbar_btn": "#2a2a2a",
        "toolbar_btn_h": "#00ff88",
        "sig_bg_l": "#0a0a0a",
        "sig_bg_r": "#1a1a1a",
        "sig_border": "#00ff88",
        "sig_text": "#ffffff",
        "btn_close_h": "#ff4444",
        "btn_win_h": "#ffffff",
        "shadow": "#00ff88",
        "shadow_offset_x": 6,
        "shadow_offset_y": 6,
        "shadow_hover_offset_x": 2,
        "shadow_hover_offset_y": 2,
        "border_width": 3,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
    },
    "light": {
        "name": "light",
        "bg_app": "#F3F4F6",
        "bg_card": "#FFFFFF",
        "bg_card2": "#E5E7EB",
        "bg_input": "#FFFFFF",
        "glass_border": "#000000",
        "accent": "#2563EB",
        "accent_bright": "#1D4ED8",
        "accent_dim": "#93C5FD",
        "text": "#000000",
        "text_dim": "#374151",
        "text_muted": "#6B7280",
        "line": "#000000",
        "line_eap": "#000000",
        "btn_add": "#16A34A",
        "btn_sib": "#2563EB",
        "btn_del": "#DC2626",
        "node_bg": "#FFFFFF",
        "node_border": "#000000",
        "node_text": "#000000",
        "toolbar_bg": "#F3F4F6",
        "toolbar_sep": "#000000",
        "toolbar_btn": "#FFFFFF",
        "toolbar_btn_h": "#2563EB",
        "sig_bg_l": "#F3F4F6",
        "sig_bg_r": "#FFFFFF",
        "sig_border": "#000000",
        "sig_text": "#000000",
        "btn_close_h": "#EF4444",
        "btn_win_h": "#000000",
        "shadow": "#000000",
        "shadow_offset_x": 6,
        "shadow_offset_y": 6,
        "shadow_hover_offset_x": 2,
        "shadow_hover_offset_y": 2,
        "border_width": 3,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
        "block_yellow": "#FFD600",
        "block_green": "#2E7D32",
        "block_blue": "#1565C0",
        "block_red": "#C62828",
        "block_orange": "#E65100",
        "block_purple": "#6A1B9A",
    },
    "neo_brutalist": {
        "name": "neo_brutalist",
        "bg_app": "#FFF9C4",
        "bg_card": "#FFFFFF",
        "bg_card2": "#FFEB3B",
        "bg_input": "#FFFFFF",
        "glass_border": "#000000",
        "accent": "#FF5722",
        "accent_bright": "#E91E63",
        "accent_dim": "#FF8A65",
        "text": "#000000",
        "text_dim": "#424242",
        "text_muted": "#757575",
        "line": "#000000",
        "line_eap": "#000000",
        "btn_add": "#4CAF50",
        "btn_sib": "#2196F3",
        "btn_del": "#F44336",
        "node_bg": "#FFFFFF",
        "node_border": "#000000",
        "node_text": "#000000",
        "toolbar_bg": "#FFEB3B",
        "toolbar_sep": "#000000",
        "toolbar_btn": "#FFFFFF",
        "toolbar_btn_h": "#FF5722",
        "sig_bg_l": "#FFF9C4",
        "sig_bg_r": "#FFFFFF",
        "sig_border": "#000000",
        "sig_text": "#000000",
        "btn_close_h": "#F44336",
        "btn_win_h": "#000000",
        "shadow": "#000000",
        "shadow_offset_x": 8,
        "shadow_offset_y": 8,
        "shadow_hover_offset_x": 3,
        "shadow_hover_offset_y": 3,
        "border_width": 4,
        "border_radius": 0,
        "font_family": "'Arial Black', 'Segoe UI', 'Arial', sans-serif",
        "font_family_content": "'Segoe UI', 'Arial', sans-serif",
        "block_yellow": "#FFD600",
        "block_green": "#2E7D32",
        "block_blue": "#1565C0",
        "block_red": "#C62828",
        "block_orange": "#E65100",
        "block_purple": "#6A1B9A",
    },
}

_ACTIVE = {"theme": THEMES["neo_brutalist"]}

_THEME_ORDER = ["dark", "light", "neo_brutalist"]


def T():
    """Retorna o dicionario do tema ativo."""
    return _ACTIVE["theme"]


def set_theme(name: str):
    _ACTIVE["theme"] = THEMES[name]


def cycle_theme():
    """Ciclo through all 3 themes: dark -> light -> neo_brutalist -> dark."""
    current = _ACTIVE["theme"]["name"]
    try:
        idx = _THEME_ORDER.index(current)
    except ValueError:
        idx = 0
    next_idx = (idx + 1) % len(_THEME_ORDER)
    _ACTIVE["theme"] = THEMES[_THEME_ORDER[next_idx]]
    return _THEME_ORDER[next_idx]


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
