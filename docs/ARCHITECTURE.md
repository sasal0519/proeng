# Arquitetura do ProEng

## Visão Geral

O ProEng é uma suíte desktop de ferramentas de engenharia construída com **Python 3 + PyQt5**, contendo **10 módulos** independentes e **6 temas visuais**.

```
main.py
└── proeng/
    ├── core/
    │   ├── themes.py        ← Sistema de temas (6 temas) + T() singleton
    │   ├── toolbar.py       ← Toolbar unificada para todos os módulos
    │   ├── base_module.py   ← Interface abstrata (get_state, set_state, refresh_theme)
    │   └── utils.py         ← _export_view, constantes de cor
    │
    ├── modules/             ← Cada módulo é independente e executável
    │   ├── flowsheet.py     ← PFD — Diagrama de processo industrial
    │   ├── eap.py           ← EAP — Estrutura Analítica do Projeto (WBS)
    │   ├── bpmn.py          ← BPMN — Modelagem de processos BPMN 2.0
    │   ├── canvas.py        ← PM Canvas — Grade Finocchio completa
    │   ├── ishikawa.py      ← Ishikawa — Diagrama causa e efeito (6M)
    │   ├── w5h2.py          ← 5W2H — Plano de ação com auto-layout
    │   ├── gantt.py         ← Gantt — Cronograma com Caminho Crítico (CPM)
    │   ├── kanban.py        ← Kanban — Quadro visual com drag-and-drop
    │   ├── scrum.py         ← Scrum — Sprint Board com Backlog e Story Points
    │   └── pdca.py          ← PDCA — Ciclo Plan-Do-Check-Act circular
    │
    └── ui/
        ├── selection_screen.py  ← Tela inicial com os cards dos módulos
        ├── main_app.py          ← Janela principal e roteamento
        └── nav_bar.py           ← Barra de navegação e seletor de temas
```

## Sistema de Temas

O singleton `T()` em `proeng/core/themes.py` retorna o dicionário do tema ativo.  
Todos os métodos `paint()` chamam `T()` para garantir atualização em tempo real.

O ProEng oferece 6 temas: **Dark**, **Light**, **Clássico**, **Neo-Brutalist**, **Solarized** e **High Contrast**.

```python
from proeng.core.themes import T
t = T()
color = t["bg_app"]  # cor de fundo atual
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
# ... etc
```

## Executando a Suíte Completa

```bash
python main.py
```
