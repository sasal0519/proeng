# -*- coding: utf-8 -*-
"""Gerenciamento de Projeto e Estado Global (Arquivo .proeng)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

class AppProject:
    """Representa um projeto consolidado, contendo os estados de todos os módulos."""

    SCHEMA_VERSION = "1.1"

    def __init__(self):
        self.filename = None
        self.state = {
            "version": self.SCHEMA_VERSION,
            "modules": {}
        }

    def update_module_state(self, module_name: str, state_dict: Dict[str, Any]):
        """Atualiza a porção do estado pertencente a um módulo específico."""
        self.state["modules"][module_name] = state_dict

    def get_module_state(self, module_name: str) -> Dict[str, Any]:
        """Retorna o estado salvo de um módulo específico."""
        return self.state["modules"].get(module_name, {})

    def _upgrade_state_if_needed(self) -> None:
        """Aplica migrações de schema para manter retrocompatibilidade."""
        if not isinstance(self.state, dict):
            self.state = {"version": self.SCHEMA_VERSION, "modules": {}}
            return

        if "modules" not in self.state or not isinstance(self.state.get("modules"), dict):
            self.state["modules"] = {}

        current_version = str(self.state.get("version", "1.0"))

        # Migração 1.0 -> 1.1: apenas normalização estrutural e versionamento.
        if current_version == "1.0":
            self.state["version"] = "1.1"
            current_version = "1.1"

        # Qualquer versão desconhecida é mantida, mas normalizamos campos mínimos.
        if "version" not in self.state:
            self.state["version"] = self.SCHEMA_VERSION

    def save(self, file_path: str):
        """Serializa o estado inteiro da aplicação em um formato JSON."""
        self._upgrade_state_if_needed()
        self.state["version"] = self.SCHEMA_VERSION
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        self.filename = file_path

    def load(self, file_path: str):
        """Desserializa e carrega um projeto de um arquivo."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        self._upgrade_state_if_needed()
        self.filename = file_path

    @property
    def has_file(self) -> bool:
        """Verifica se o projeto atual foi salvo/carregado de um arquivo."""
        return self.filename is not None
