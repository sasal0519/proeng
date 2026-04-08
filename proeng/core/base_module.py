# -*- coding: utf-8 -*-

# Interface abstrata para todos os módulos visuais de engenharia integrados em MainApp.
#
# Responsabilidade: Definir contrato (interface) que todos os módulos devem implementar,
# permitindo que a aplicação principal orquestre carregamento, sincronização de estado,
# aplicação de temas dinâmicos e exportação de conteúdo de forma uniforme.
#
# Esta camada não altera o comportamento dos módulos, apenas oferece interface clara
# e consistente entre aplicação principal e plugins de módulo.
#
# Convenções implementadas:
# - get_state() / set_state(): Serializar APENAS dados de negócio (sem widgets Qt).
# - refresh_theme(): Reaplicar estilos baseado em tema ativo via T() de themes.
# - get_view(): Retorna QGraphicsView principal para exportação PNG/PDF (opcional).
#
# Padrão Design: Strategy para permitir implementações variadas mantendo
# interface consistente com aplicação.

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QWidget, QGraphicsView


class BaseModule(QWidget):
    # Interface abstrata que define contrato esperado de módulo visual.
    # 
    # Todos os módulos de engenharia (Flowsheet, BPMN, EAP, etc) herdam desta
    # classe e implementam os métodos conforme necessário para sincronização
    # de estado, tema dinâmico e exportação.

    def get_state(self) -> Dict[str, Any]:
        # Retorna dicionário serializável contendo estado completo do módulo.
        # 
        # Implementações devem sobrescrever o método para retornar dict
        # com dados de negócio: nós, propriedades, configurações etc.
        # Não deve incluir referências a widgets Qt ou objetos não-serializáveis.
        #
        # Retorno padrão (vazio): {} . Implementadores sobrescrevem conforme
        # necessário para fornecer estado relevante.
        return {}

    def set_state(self, state: Dict[str, Any]) -> None:
        # Restaura estado do módulo a partir de dicionário serializável.
        #
        # Parâmetro state contém dados anteriormente obtidos via get_state().
        # Implementações devem reconstruir estado visual e lógico do módulo
        # baseado neste dicionário durante restauração de arquivo de projeto.
        #
        # Lógica padrão: Ignora parâmetro (apenas evita warnings).
        # Implementadores sobrescrevem para processar retorno do arquivo.
        _ = state

    def refresh_theme(self) -> None:
        # Reaplica todos os estilos visuais baseado em tema ativo.
        #
        # Chamado quando usuário alterna entre temas (dark/light/neo_brutalist)
        # via cycle_theme(). Implementações devem:
        # 1. Obter referência ao tema via T() de themes
        # 2. Reaplicar cores a todos os widgets (via setStyleSheet)
        # 3. Atualizar pintura de elementos gráficos (QGraphicsItems, canvas)
        # 4. Chamar update() para forçar repintura de todos os componentes
        #
        # Padrão: Método vazio por padrão (no-op). Implementadores sobrescrevem
        # conforme necessário para o módulo específico.
        pass

    def get_view(self) -> Optional[QGraphicsView]:
        # Retorna referência para QGraphicsView principal do módulo.
        #
        # Utilizado por MainApp._on_export() para obter canvas a ser exportado
        # para PNG ou PDF. Se módulo não possui QGraphicsView, retorna None
        # e exportação não será possível.
        #
        # Padrão: Retorna None (módulo não suporta exportação).
        # Implementadores retornam self.view ou similar se aplicável.
        return None

