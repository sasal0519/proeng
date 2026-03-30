# Arquitetura do ProEng

## Visão Geral

O ProEng é uma suíte desktop de ferramentas de engenharia construída com **Python 3 + PyQt5**.

```
main.py
└── proeng/
    ├── core/
    │   ├── themes.py        ← Sistema de temas (Dark/Light) + T() singleton
    │   ├── toolbar.py       ← Toolbar unificada para todos os módulos
    │   └── utils.py        ← _export_view, constantes de cor
    │
    ├── modules/             ← Cada módulo é independente e executável
    │   ├── flowsheet.py     ← PFD — Diagrama de processo industrial
    │   ├── eap.py           ← EAP — Estrutura Analítica do Projeto (WBS)
    │   ├── bpmn.py          ← BPMN — Modelagem de processos BPMN 2.0
    │   ├── canvas.py        ← PM Canvas — Grade Finocchio completa
    │   ├── ishikawa.py      ← Ishikawa — Diagrama causa e efeito (6M)
    │   └── w5h2.py          ← 5W2H — Plano de ação com auto-layout
    │
    └── ui/
        ├── selection_screen.py  ← Tela inicial com os cards dos módulos
        ├── main_app.py          ← Janela principal e roteamento
        └── nav_bar.py           ← Barra de navegação e toggle de tema
```

## Sistema de Temas

O singleton `T()` em `proeng/core/themes.py` retorna o dicionário do tema ativo.  
Todos os métodos `paint()` chamam `T()` para garantir atualização em tempo real.

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
# ... etc
```

## Executando a Suíte Completa

```bash
python main.py
```
