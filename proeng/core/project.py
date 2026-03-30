# -*- coding: utf-8 -*-
"""Gerenciamento de Projeto e Estado Global (Arquivo .proeng)."""

import json
import os

class AppProject:
    """Representa um projeto consolidado, contendo os estados de todos os módulos."""

    def __init__(self):
        self.filename = None
        self.state = {
            "version": "1.0",
            "modules": {}
        }

    def update_module_state(self, module_name: str, state_dict: dict):
        """Atualiza a porção do estado pertencente a um módulo específico."""
        self.state["modules"][module_name] = state_dict

    def get_module_state(self, module_name: str) -> dict:
        """Retorna o estado salvo de um módulo específico."""
        return self.state["modules"].get(module_name, {})

    def save(self, file_path: str):
        """Serializa o estado inteiro da aplicação em um formato JSON."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        self.filename = file_path

    def load(self, file_path: str):
        """Desserializa e carrega um projeto de um arquivo."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        self.filename = file_path

    @property
    def has_file(self) -> bool:
        """Verifica se o projeto atual foi salvo/carregado de um arquivo."""
        return self.filename is not None
