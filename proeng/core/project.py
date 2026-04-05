# -*- coding: utf-8 -*-

# Gerenciamento centralizado de projeto e persistência de estado global.
#
# Responsabilidade: Armazenar, serializar e desserializar estado de todos os módulos
# da aplicação em arquivo .proeng (JSON). Implementa padrão de schema versionado
# para retrocompatibilidade futura.
#
# Formato de arquivo: JSON com estrutura {version, modules: {module_id: state_dict, ...}}
# Extensão padrão: .proeng
#
# Convenções:
# - SCHEMA_VERSION: Versão atual do formato (1.1)
# - _upgrade_state_if_needed(): Migrações automáticas ao carregar versões antigas
# - Cada módulo armazena seu estado sob chave no dicionário modules
#
# Inputs: Arquivo .proeng (JSON), dicts de estado dos módulos
# Outputs: Arquivo .proeng serializado, dicts de estado recuperados

from __future__ import annotations

import json
import os
from typing import Any, Dict


class AppProject:
    # Representa um projeto consolidado contendo estados de todos os módulos.
    #
    # Atributos:
    # - filename: Caminho do arquivo .proeng atualmente carregado (None se novo)
    # - state: Dict estruturado com {version, modules: {...}}
    #
    # Responsabilidade: Fornecer API simples para sincronização bidirecional
    # de estado entre módulos individuais e arquivo persistido.

    SCHEMA_VERSION = "1.1"

    def __init__(self):
        # Inicializa novo projeto em memória com estado vazio.
        # Schema padrão: versão 1.1 com dicionário modules vazio.
        super().__init__()
        self.filename = None
        self.state = {
            "version": self.SCHEMA_VERSION,
            "modules": {}
        }

    def update_module_state(self, module_name: str, state_dict: Dict[str, Any]):
        # Atualiza porção do estado pertencente a um módulo específico.
        #
        # Parâmetro module_name: chave do módulo (ex: "flowsheet", "bpmn").
        # Parâmetro state_dict: dict completo com estado serial do módulo.
        #
        # Lógica: Sobrescreve entrada anterior, permitindo sincronização
        # após modificações no módulo (antes de salvar arquivo).
        self.state["modules"][module_name] = state_dict

    def get_module_state(self, module_name: str) -> Dict[str, Any]:
        # Retorna estado salvo de um módulo específico pela chave.
        #
        # Parâmetro module_name: chave do módulo.
        # Retorno: Dict com estado anterior (vazio {} se não existe).
        #
        # Utilizado por MainApp para restaurar estado ao carregar projeto
        # ou ao criar novo módulo usando lazy loading.
        return self.state["modules"].get(module_name, {})

    def _upgrade_state_if_needed(self) -> None:
        # Aplica migrações de schema automáticas para retrocompatibilidade.
        #
        # Lógica:
        # 1. Normaliza estrutura: garante modules dict existe
        # 2. Obtém versão atual (default 1.0)
        # 3. Aplica migração 1.0 -> 1.1 (atualmente no-op)
        # 4. Garante campo version existe
        #
        # Permite carregar projetos antigos e altern atualizar formato
        # sem perda de dados.
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

        # Qualquer versão desconhecida: mantém estado mas normaliza campos.
        if "version" not in self.state:
            self.state["version"] = self.SCHEMA_VERSION

    def save(self, file_path: str):
        # Serializa estado inteiro em arquivo JSON.
        #
        # Parâmetro file_path: Caminho completo do arquivo (ex: ~/projeto.proeng).
        #
        # Lógica:
        # 1. Atualiza schema se necessário via _upgrade_state_if_needed()
        # 2. Define versão para SCHEMA_VERSION atual
        # 3. Serializa state como formatted JSON (indent=2)
        # 4. Atualiza filename para referência futura
        #
        # Exceções: Pode lançar IOError se sem permissões de escrita.
        self._upgrade_state_if_needed()
        self.state["version"] = self.SCHEMA_VERSION
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        self.filename = file_path

    def load(self, file_path: str):
        # Desserializa e carrega projeto de arquivo JSON.
        #
        # Parâmetro file_path: Caminho completo do arquivo .proeng.
        #
        # Lógica:
        # 1. Valida que arquivo existe (FileNotFoundError se não)
        # 2. Deserializa JSON para dict state
        # 3. Aplica upgrade automático via _upgrade_state_if_needed()
        # 4. Armazena filename para save() futuro
        #
        # Exceções: FileNotFoundError se arquivo não existe, JSONError se inválido.
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            self.state = json.load(f)
        self._upgrade_state_if_needed()
        self.filename = file_path

    @property
    def has_file(self) -> bool:
        # Verifica se projeto atual foi salvo/carregado de arquivo.
        #
        # Retorno: True se filename não é None (arquivo persistido).
        # Utilizado para determinar se save() ou save_as() deve ser chamado.
        return self.filename is not None
