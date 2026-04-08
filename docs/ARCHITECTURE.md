# Arquitetura do ProEng

## Visão Geral

O ProEng é uma suíte desktop de ferramentas de engenharia construída com Python 3 + PyQt5, contendo 11 módulos independentes e 14 temas visuais com design neo-brutalista. Sistema completo de persistência, export e tema dinâmico.

```
main.py
└── proeng/
    ├── core/
    │   ├── themes.py        ← Sistema de 14 temas + T() singleton + refresh_theme_recursive()
    │   ├── project.py       ← Persistência em JSON (.proeng) e controle de estado
    │   ├── toolbar.py       ← Toolbar unificada para todos os módulos
    │   ├── base_module.py   ← Interface abstrata (get_state, set_state, refresh_theme, get_view)
    │   └── utils.py         ← Utilitários de export (PNG, PDF) e constantes
    │
    ├── modules/             ← 11 módulos independentes, cada um implementa BaseModule
    │   ├── flowsheet.py     ← Flowsheet - Diagrama de fluxo de processo (PFD)
    │   ├── eap.py           ← EAP - Estrutura Analítica do Projeto (WBS)
    │   ├── bpmn.py          ← BPMN - Modelagem de processos com swimlanes
    │   ├── canvas.py        ← Canvas - Modelo de negócios visual
    │   ├── ishikawa.py      ← Ishikawa - Diagrama causa e efeito (6M)
    │   ├── w5h2.py          ← 5W2H - Plano de ação estruturado
    │   ├── gantt.py         ← Gantt - Cronograma com Caminho Crítico (CPM)
    │   ├── kanban.py        ← Kanban - Quadro visual com drag-and-drop
    │   ├── scrum.py         ← Scrum - Sprint Board com Backlog e Story Points
    │   ├── pdca.py          ← PDCA - Ciclo Plan-Do-Check-Act circular
    │   └── script_module.py ← Script - Interpretador Python para automação
    │
    └── ui/
        ├── main_app.py      ← Janela principal, orquestração e lazy-loading
        ├── nav_bar.py       ← Barra de navegação com seletor de temas
        └── welcome.py       ← Tela inicial com grid de módulos
```

## Sistema de Temas

O ProEng oferece 14 temas com design neo-brutalista consistente: bordas 4px sólidas, sombras 8x8 offset, tipografia Merriweather 900 UPPERCASE.

Temas: neo_brutalist, midnight, embers, forest, synthwave, arctic, solar, crimson, ocean, volcano, mint, onyx, lilac, dracula.

API de temas:

```python
from proeng.core.themes import T, set_theme, cycle_theme, refresh_theme_recursive

# Acessar tema ativo
color = T()["accent"]

# Trocar tema
set_theme("solar")

# Ciclar through themes
cycle_theme()

# Atualizar UI
refresh_theme_recursive(widget)
```

## Executando um Módulo de Forma Independente

```bash
python -m proeng.modules.eap
python -m proeng.modules.bpmn
python -m proeng.modules.flowsheet
python -m proeng.modules.gantt
python -m proeng.modules.kanban
python -m proeng.modules.scrum
python -m proeng.modules.pdca
python -m proeng.modules.ishikawa
python -m proeng.modules.w5h2
python -m proeng.modules.canvas
python -m proeng.modules.script_module
```

## Executando a Suíte Completa

```bash
python main.py
```

## Padrão de Desenvolvimento - BaseModule

Todos os 11 módulos implementam a interface BaseModule:

```python
class BaseModule:
    def get_state(self) -> dict:
        """Retorna estado serializável para persistência"""
        
    def set_state(self, state: dict):
        """Restaura estado do dicionário"""
        
    def refresh_theme(self):
        """Atualiza cores usando T() - chamado ao trocar tema"""
        
    def get_view(self) -> QWidget:
        """Retorna widget para exibição na MainApp"""
```

## Persistência

O sistema de projeto permite salvar/carregar estado completo:

```python
from proeng.core.project import AppProject

project = AppProject("meu_projeto.proeng")
project.save()  # Salva em JSON
project.load()  # Carrega estado anterior
```

## Export

Exporte diagramas em alta resolução:

```python
from proeng.core.utils import export_view

export_view(widget, "diagrama.png", 3)  # 3x supersample
export_view(widget, "diagrama.pdf")     # PDF A3 landscape
```

