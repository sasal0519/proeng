```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║   ██████╗ ██████╗  ██████╗ ███████╗███╗   ██╗ ██████╗              ║
║   ██╔══██╗██╔══██╗██╔═══██╗██╔════╝████╗  ██║██╔════╝              ║
║   ██████╔╝██████╔╝██║   ██║█████╗  ██╔██╗ ██║██║  ███╗             ║
║   ██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║██║   ██║             ║
║   ██║     ██║  ██║╚██████╔╝███████╗██║ ╚████║╚██████╔╝             ║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝              ║
║                                                                    ║
║             ███████╗██╗   ██╗██╗████████╗███████╗                  ║
║             ██╔════╝██║   ██║██║╚══██╔══╝██╔════╝                  ║
║             ███████╗██║   ██║██║   ██║   █████╗                    ║
║             ╚════██║██║   ██║██║   ██║   ██╔══╝                    ║
║             ███████║╚██████╔╝██║   ██║   ███████╗                  ║
║             ╚══════╝ ╚═════╝ ╚═╝   ╚═╝   ╚══════╝                  ║
║                                                                    ║
║          Industrial Engineering & Project Management               ║
║               Professional Suite  v2.0 — 10 Modules               ║
╚════════════════════════════════════════════════════════════════════╝
```

> **ProEng** é uma plataforma de engenharia industrial de ponta, desenhada para unificar o planejamento técnico, a modelagem de processos e a gestão estratégica em um único ambiente visual de alta fidelidade.

---

────────────────────────────────────────────────────────────────────────
PREFÁCIO E VISÃO GERAL
────────────────────────────────────────────────────────────────────────

O projeto **ProEng** nasceu da necessidade de ferramentas de engenharia que não fossem apenas funcionais, mas também esteticamente superiores e intuitivas. Em um mundo onde softwares técnicos costumam ser cinzas e burocráticos, o ProEng introduz o conceito de **Creative Industrial Engineering** — onde o design auxilia na clareza de pensamento e na detecção de falhas.

Esta suíte foi construída do zero utilizando o framework **PyQt5**, aproveitando o poder da aceleração de hardware para renderizar diagramas vetoriais complexos com suavidade e precisão de pixel.

---

────────────────────────────────────────────────────────────────────────
FILOSOFIA DE DESIGN: MULTI-TEMA NEO-BRUTALISTA
────────────────────────────────────────────────────────────────────────

A estética do ProEng é um dos seus pilares fundamentais. Ela não é puramente decorativa; cada escolha de cor e sombra tem um propósito funcional.

### Neo-Brutalismo Industrial

O ProEng utiliza **13 temas visuais** com linguagem neo-brutalista consistente: bordas sólidas e grossas, sombras duras com offset, tipografia pesada em caixa alta e cores saturadas. Esse estilo prioriza a legibilidade e a hierarquia visual, sendo ideal para engenheiros que preferem interfaces diretas e sem distrações decorativas.

### Sistema Multi-Tema (13 Temas)

O usuário pode alternar entre os temas a qualquer momento via seletor dropdown na barra de navegação:

1. **Neo-Brutal** — Amarelo vibrante sobre fundo claro, bordas pretas grossas
2. **Midnight** — Azul profundo com ciano elétrico
3. **Embers** — Cinza carvão com laranja brasas
4. **Forest** — Verde orgânico escuro
5. **Synthwave** — Roxo neon e magenta retro 80s
6. **Arctic** — Branco-gelo com azul glacial
7. **Solar** — Amarelo-dourado com marrom-terra
8. **Crimson** — Vinho profundo com vermelho escarlate
9. **Ocean** — Azul marinho com espuma branca
10. **Volcano** — Preto basalto com amarelo lava
11. **Mint** — Verde-menta suave com creme
12. **Onyx** — Preto absoluto com acentos brancos
13. **Lilac** — Lavanda com tonalidade delicada

Cada tema atualiza em tempo real todos os módulos, diagramas, barras de ferramentas e diálogos, mantendo paridade funcional completa.

---

╔════════════════════════════════════════════════════════════════════╗
║  ARQUITETURA DO SISTEMA: CORE ENGINE                               ║
╚════════════════════════════════════════════════════════════════════╝

O ProEng utiliza uma arquitetura baseada em **Plugins Modulares**, onde o núcleo do sistema apenas gerencia a navegação e o estado global, enquanto as funcionalidades de engenharia residem em módulos independentes.

### A Classe `BaseModule`

Todos os 10 módulos do ProEng (Flowsheet, BPMN, EAP, Canvas, Ishikawa, 5W2H, Gantt, Kanban, Scrum e PDCA) herdam da `BaseModule`. Esta classe define o contrato que todo módulo deve seguir:

- `get_state()`: Serializa todos os objetos do canvas em um dicionário Python (JSON-friendly).
- `set_state(state)`: Reconstitui o ambiente de trabalho a partir de um arquivo salvo.
- `refresh_theme()`: Informa ao módulo que as cores globais mudaram e ele deve se redesenhar.

### Estrutura do Projeto

```
PROENG CORE ARCHITECTURE
┌─────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  main_app.py │  │  welcome.py  │  │   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINE                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐      │
│  │ themes   │ │  utils   │ │ toolbar  │ │  base_module   │      │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘      │
├─────────────────────────────────────────────────────────────────┤
│  MODULE LAYER (10 módulos)                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐      │
│  │flowsheet │ │   bpmn   │ │   eap    │ │    canvas      │      │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐      │
│  │ishikawa  │ │  w5h2    │ │  gantt   │ │    kanban      │      │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘      │
│  ┌──────────┐ ┌──────────┐                                      │
│  │ scrum    │ │  pdca    │                                      │
│  └──────────┘ └──────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Estrutura de Diretórios Detalhada

A organização de arquivos segue os padrões modernos de desenvolvimento Python:

```text
proeng/
│
├── core/                       # O "Cérebro" da Aplicação
│   ├── __init__.py
│   ├── themes.py               # Tema Neo-Brutalista (paleta de cores)
│   ├── utils.py                # Utilitários de desenho, exportação e conversão colorimétrica
│   ├── toolbar.py              # Fábrica de barras de ferramentas customizadas
│   ├── project.py              # Lógica de I/O de arquivos e metadados
│   └── base_module.py          # Interface abstrata para integração de módulos
│
├── modules/                    # Ferramentas Especializadas (10 módulos)
│   ├── __init__.py
│   ├── flowsheet.py            # PFD (Process Flow Diagram)
│   ├── bpmn.py                 # Fluxogramas de Processos de Negócio
│   ├── eap.py                  # WBS (Work Breakdown Structure)
│   ├── canvas.py               # Planejamento visual de projetos
│   ├── ishikawa.py             # Diagramas de Causa e Efeito (6M)
│   ├── w5h2.py                 # Matrizes de Planos de Ação
│   ├── gantt.py                # Cronograma com Caminho Crítico (CPM)
│   ├── kanban.py               # Quadro Kanban com Cards Arrastáveis
│   ├── scrum.py                # Scrum Sprint Board com Backlog
│   └── pdca.py                 # Ciclo PDCA (Plan-Do-Check-Act)
│
├── ui/                         # A "Pele" da Aplicação
│   ├── main_app.py             # Workspace principal, Sidebar e Logic Switcher
│   ├── welcome.py              # Hub de entrada com gallery e carrossel
│   └── selection_screen.py     # Grid visual de escolha de módulos
│
└── resources/                  # Ativos Estáticos
    └── screenshots/            # Capturas de tela para documentação interna
```

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: PFD FLOWSHEET
────────────────────────────────────────────────────────────────────────

O **Process Flow Diagram** é a ferramenta de maior complexidade técnica. Ele utiliza o motor gráfico `QGraphicsScene` para gerenciar objetos interativos.

### Lógica de Desenho de Equipamentos

A função `draw_equipment` centraliza a renderização de mais de 50 tipos de máquinas industriais.

- **Matemática Vetorial**: Cada equipamento é desenhado usando polígonos (`QPolygonF`) e caminhos (`QPainterPath`) baseados em proporções relativas ao tamanho do nó.
- **Gradientes Dinâmicos**: Utilizamos `QLinearGradient` para criar superfícies que parecem metálicas ou de vidro, reagindo dinamicamente à cor de acento do tema.

### Smart Piping (Tubulação Inteligente)

A classe `Edge` gerencia a conectividade entre equipamentos.

- **Cálculo de Normais**: As tubulações saem ortogonalmente das portas (Top, Bottom, Left, Right).
- **Efeito Máscara (Masking)**: Para evitar que a linha da tubulação cruze o texto de identificação (Tag), implementamos um fundo de rótulo que assume a cor exata do canvas (`bg_app`), criando um visual de "corte" técnico profissional.

### Portas de Conexão

Cada `ProcessNode` possui 12 portas de conexão invisíveis (3 em cada lado) que aparecem apenas durante o "hover" ou durante a criação de uma linha, reduzindo o ruído visual ("clutter").

### Balanço de Massa Automático

O módulo Flowsheet implementa um motor de balanço de massa:

- **Ordenação Topológica**: Algoritmo de Kahn para detecção de ciclos e processamento correto.
- **Mistura e Distribuição**: Para cada nó, o sistema soma as entradas e distribui aos componentes nas saídas conforme configuração de fração ou vazão fixa.
- **Verificação Global**: Ao final, verifica se a massa total de entrada equals a saída + retido.
- **Autocalculação**: Após alterações no diagrama, o balanço recalcula automaticamente com debounce de 300ms.
- **Exportação Excel**: Exporta todos os dados de balanço para planilha formatada.

### Correções Recentes

- **Bug de Pipes Infinitos**: Corrigida criação duplicada de pipes ao criar conexões de saída de equipamentos.
- **Propagação de Dados de Saída**: Agora ao criar uma nova corrente de saída, o sistema pré-preenche automaticamente com os dados do balanço de massa calculado, soma das entradas ou dados existentes.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: BPMN MODELER
────────────────────────────────────────────────────────────────────────

Focado na eficiência operacional, o modelador BPMN do ProEng segue rigorosamente a notação internacional.

### Sistema de Raias (Lanes)

Diferente de fluxogramas comuns, o BPMN do ProEng organiza as tarefas em **Swimming Lanes**.

- **Pool Management**: Você pode adicionar ou remover raias dinamicamente.
- **Headers**: Os cabeçalhos de raia utilizam o sistema `_glass_grad` para um visual moderno e transparente.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: EAP (WORK BREAKDOWN STRUCTURE)
────────────────────────────────────────────────────────────────────────

A Estrutura Analítica do Projeto organiza o caos do escopo em uma hierarquia lógica.

### Algoritmo de Árvore

O módulo EAP gera automaticamente os links entre "Pacotes de Trabalho".

- **Hierarquia Visual**: O nível pai é sempre destacado com cores mais quentes (Dourado/Amarelo), enquanto os níveis inferiores seguem a paleta da suíte.
- **Seleção e Edição**: Clique duplo para editar textos, menu de contexto para adicionar sub-tarefas.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: PROJECT MODEL CANVAS
────────────────────────────────────────────────────────────────────────

Ferramenta de planejamento ágil para alinhar a equipe antes do início de qualquer projeto técnico.

### Os 15 Blocos de Planejamento

- **Fatores Externos**: Stakeholders, Restrições, Premissas, Riscos.
- **Fatores Internos**: Equipe, Custos, Requisitos.
- **Objetivos**: Justificativa, Objetivo SMART, Benefícios.
- **Entregas**: Grupo de Entregas e Linha do Tempo.

Cada bloco possui um editor de texto rico que suporta múltiplas linhas e redimensionamento dinâmico.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: 5W2H ACTION PLAN
────────────────────────────────────────────────────────────────────────

Uma matriz tabular para execução tática, onde cada ação é detalhada em 7 dimensões cruciais.

### Estrutura da Tabela

1. **WHAT**: A tarefa a ser realizada.
2. **WHY**: O propósito da ação.
3. **WHERE**: Local de execução.
4. **WHEN**: Cronograma previsto.
5. **WHO**: Responsável (Owner).
6. **HOW**: Procedimento técnico.
7. **HOW MUCH**: Orçamento financeiro ou de RH.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: ISHIKAWA (6M)
────────────────────────────────────────────────────────────────────────

O diagrama de Ishikawa (ou Espinha de Peixe) permite identificar a causa raiz de problemas em linhas de produção.

### Os 6 Pilares da Qualidade

O ProEng segmenta as causas em 6 categorias pré-definidas:

- **Métodos**: Processos e rotinas operacionais.
- **Máquinas**: Equipamentos, ferramentas e software.
- **Materiais**: Matéria-prima e qualidade de insumos.
- **Mão de Obra**: Habilidades, treinamento e pessoas.
- **Medida**: Dados, métricas e calibração de instrumentos.
- **Meio Ambiente**: Local de trabalho, clima e condições externas.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: GANTT (CRONOGRAMA CPM)
────────────────────────────────────────────────────────────────────────

O módulo **Gantt** oferece um cronograma completo com suporte a caminho crítico (CPM) e marcos (milestones).

### Funcionalidades Principais

- **Tarefas e Dependências**: Criação de tarefas com nome, data de início, data de fim, progresso (%) e predecessora.
- **Milestones**: Marcos visuais representados como círculos no cronograma para datas de referência.
- **Caminho Crítico (CPM)**: Algoritmo que identifica automaticamente as tarefas sem folga, destacando-as em vermelho para priorização de esforço.
- **Visualização Temporal**: Barras horizontais renderizadas sobre uma grade temporal com a data atual marcada por uma linha tracejada.
- **Progresso Visual**: Barras verdes internas indicam o progresso percentual de cada tarefa.

### Controles de Zoom

Use `Ctrl + Scroll` para ajustar a escala temporal. O gráfico se adapta automaticamente mantendo todas as tarefas visíveis.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: KANBAN BOARD
────────────────────────────────────────────────────────────────────────

O módulo **Kanban** implementa um quadro visual de gestão de tarefas com 4 colunas de status.

### Sistema de Colunas

- **A FAZER**: Tarefas planejadas aguardando início.
- **EM ANDAMENTO**: Tarefas atualmente em execução.
- **FEITO**: Tarefas concluídas com sucesso.
- **CANCELADO**: Tarefas descartadas (histórico preservado).

### Cards Interativos

Cada card exibe título, descrição e prioridade (ALTA / MÉDIA / BAIXA) com destaque visual por cor. Os cards suportam **drag-and-drop** entre colunas para atualização rápida de status.

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: SCRUM SPRINT BOARD
────────────────────────────────────────────────────────────────────────

O **Scrum Sprint Board** implementa o framework ágil Scrum com gestão de backlog e sprints.

### Funcionalidades

- **Backlog**: Repositório de user stories aguardando priorização.
- **Sprint Board**: 4 colunas (TODO → IN PROGRESS → REVIEW → DONE) com drag-and-drop.
- **Story Points**: Cada card carrega uma estimativa em pontos (escala Fibonacci recomendada). O total de pontos do Sprint é exibido no cabeçalho.
- **Planejamento de Sprint**: Ferramenta para mover itens do Backlog para a Sprint ativa.
- **Fechamento de Sprint**: Gera métricas de entrega (itens concluídos × pontos entregues).

---

────────────────────────────────────────────────────────────────────────
MÓDULO DETALHADO: PDCA (CICLO DE MELHORIA CONTÍNUA)
────────────────────────────────────────────────────────────────────────

O módulo **PDCA** implementa o ciclo de melhoria contínua de Deming em um layout visual circular.

### Os 4 Quadrantes

O diagrama é renderizado como um círculo dividido em 4 quadrantes coloridos:

- **P (Plan / Planejar)**: Identificar problemas e planejar ações de melhoria.
- **D (Do / Executar)**: Implementar as ações planejadas em escala piloto.
- **C (Check / Verificar)**: Medir resultados e comparar com metas.
- **A (Act / Agir)**: Padronizar ações bem-sucedidas ou corrigir desvios.

### Interação

Cada quadrante aceita cards interativos: clique no botão `(+)` para adicionar etapas, clique duplo para editar, e use `(-)` para excluir. Cada quadrante possui uma cor temática que se adapta automaticamente ao tema ativo.

---

╔════════════════════════════════════════════════════════════════════╗
║  INSTALLATION GUIDE                                           ║
╠═══════════════════════════════════════════════════════════════╣
║  Requirements: Python 3.8+  |  PyQt5  |  1366x768 min         ║
╚═══════════════════════════════════════════════════════════════╝

### Requisitos do Sistema

- **Sistema Operacional**: Windows 10/11, Linux (Ubuntu/Debian) ou macOS.
- **Python**: Versão 3.8 ou superior recomendada.
- **Resolução de Tela**: Mínimo 1366x768 (Otimizado para Full HD 1920x1080).

### Configuração do Ambiente

1. **Download do Código**:
    ```bash
    git clone https://github.com/proeng-systems/proeng-suite.git
    cd proeng-suite
    ```

2. **Preparação do Python** — Crie um ambiente virtual para isolar as dependências:
    ```bash
    python -m venv .venv
    # No Windows:
    .venv\Scripts\activate
    # No Linux/Mac:
    source .venv/bin/activate
    ```

3. **Instalação de Dependências** — O projeto utiliza apenas o **PyQt5** como dependência externa pesada:
    ```bash
    pip install pyqt5
    ```

4. **Execução**:
    ```bash
    python main.py
    ```

---

────────────────────────────────────────────────────────────────────────
MANUAL TÉCNICO: SISTEMA DE TEMAS (themes.py)
────────────────────────────────────────────────────────────────────────

A customização visual é feita através de um dicionário centralizado. Abaixo, a descrição de cada chave de cor:

```
THEME SYSTEM — COLOR KEYS
┌─────────────────┬───────────────────────────┬────────────────────────────┐
│ Key             │ Description               │ Primary Usage              │
├─────────────────┼───────────────────────────┼────────────────────────────┤
│ bg_app          │ Application Background    │ Window canvas base color   │
│ bg_card         │ Card / Glass Surface      │ Sidebars, context menus    │
│ accent          │ Primary Accent            │ Buttons, focus borders     │
│ accent_bright   │ Bright Accent             │ Hover, active selection    │
│ text            │ Primary Text              │ Labels, high-priority      │
│ text_dim        │ Dimmed Text               │ Descriptions, placeholders │
│ line            │ Pipe / Connection Lines   │ Flowsheet tubulation       │
│ toolbar_bg      │ Toolbar Background        │ Top and side toolbars      │
└─────────────────┴───────────────────────────┴────────────────────────────┘
```

---

────────────────────────────────────────────────────────────────────────
ATALHOS DE TECLADO (POWER USER)
────────────────────────────────────────────────────────────────────────

```
KEYBOARD SHORTCUTS
┌───────────────┬────────────────────────────────┬──────────────────┐
│ Shortcut      │ Action                         │ Context          │
├───────────────┼────────────────────────────────┼──────────────────┤
│ Ctrl + N      │ New Project                    │ Global           │
│ Ctrl + S      │ Save Project (.proeng)         │ Global           │
│ Ctrl + L      │ Toggle Dark / Light Theme      │ Global           │
│ Ctrl + B      │ Toggle Sidebar                 │ Global           │
│ Ctrl + E      │ Export Diagram as PNG          │ Graphic Modules  │
│ Delete        │ Remove Selected Object         │ Canvas           │
│ Space         │ Pan Canvas                     │ Canvas           │
│ Esc           │ Cancel Active Tool             │ Global           │
└───────────────┴────────────────────────────────┴──────────────────┘
```

---

────────────────────────────────────────────────────────────────────────
CONTRIBUIÇÃO E FILOSOFIA
────────────────────────────────────────────────────────────────────────

O ProEng é um projeto de **Software Livre** que valoriza a cooperação altruísta. Para contribuir, você não apenas segue um fluxo técnico, mas adere ao compromisso de manter o conhecimento aberto:

1. **Audite o Código**: Como ferramenta de engenharia, a segurança depende da sua revisão.
2. **Melhore e Compartilhe**: Se criou um novo símbolo ou correção, envie-o para que todos se beneficiem.
3. **Respeite a Liberdade**: Qualquer contribuição será licenciada sob os mesmos termos da GPLv3.

- **Fork & Pull Request**: O fluxo clássico de colaboração via GitHub é bem-vindo.
- **Inspirado em Stallman**: Veja nosso [MANIFESTO.md](MANIFESTO.md) para entender nossa visão ética.

---

────────────────────────────────────────────────────────────────────────
LICENÇA DE USO: SOFTWARE LIVRE (GPLv3)
────────────────────────────────────────────────────────────────────────

Este software é um **Free Software** (Software Livre), distribuído sob a licença **GNU General Public License v3.0**.

Diferente de licenças permissivas, a GPLv3 garante que o ProEng permaneça livre para sempre. Isso significa que você tem a liberdade de usar, estudar e modificar o software para qualquer fim, desde que mantenha essas liberdades disponíveis para os outros. Consulte o arquivo [LICENSE](LICENSE) para os termos completos.

---

────────────────────────────────────────────────────────────────────────
CONTATO E SUPORTE
────────────────────────────────────────────────────────────────────────

Para dúvidas técnicas, bugs ou sugestões de novos equipamentos:

- **Issues**: [GitHub Issues Page]

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ProEng Suite v2.0 — Industrial Engineering & Project Management
10 Modules | 6 Themes | GPLv3
License : GNU General Public License v3.0
Built with Python, Qt Framework, and Precision Engineering
(c) 2026 ProEng Systems — Knowledge must remain free.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
