# -*- coding: utf-8 -*-
"""Infraestrutura comum para módulos visuais do PRO ENG.

Esta camada não muda o comportamento atual dos módulos, mas fornece
uma interface clara que pode ser usada pelo app principal e por testes.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QWidget, QGraphicsView


class BaseModule(QWidget):
    """Base simples para todos os módulos embutidos em `MainApp`.

    Convenções:
    - `get_state` / `set_state` devem serializar apenas dados de negócio
      (sem referências a widgets Qt).
    - `refresh_theme` deve reaplicar estilos baseados em `themes.T()`.
    - `get_view` (opcional) retorna a `QGraphicsView` principal usada
      para exportação PNG/PDF. Quando não houver view, pode retornar None.
    """

    # --- State API -------------------------------------------------
    def get_state(self) -> Dict[str, Any]:  # pragma: no cover - padrão
        """Retorna o estado serializável do módulo.

        Implementações concretas devem sobrescrever este método.
        """
        return {}

    def set_state(self, state: Dict[str, Any]) -> None:  # pragma: no cover - padrão
        """Restaura o estado serializável do módulo."""
        _ = state  # apenas para evitar warnings em implementações vazias

    # --- Tema / UI -------------------------------------------------
    def refresh_theme(self) -> None:  # pragma: no cover - padrão
        """Reaplica estilos visuais ligados ao tema."""
        # Implementações concretas podem sobrescrever se necessário.
        pass

    # --- Export / helpers ------------------------------------------
    def get_view(self) -> Optional[QGraphicsView]:  # pragma: no cover - padrão
        """Retorna a `QGraphicsView` principal (se existir) para exportação."""
        return None

