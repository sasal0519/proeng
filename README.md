
                                                                                                         
                            🌐 ENGLISH VERSION / VERSÃO EM INGLÊS 🌐                                      

---

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
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

> **ProEng** is a cutting-edge industrial engineering platform designed to unify technical planning, process modeling, and strategic management in a single high-fidelity visual environment.

---

────────────────────────────────────────────────────────────────────────
PREFACE AND OVERVIEW
────────────────────────────────────────────────────────────────────────

The **ProEng** project was born from the need for engineering tools that are not only functional but also aesthetically superior and intuitive. In a world where technical software is often gray and bureaucratic, ProEng introduces the concept of **Creative Industrial Engineering** — where design aids in clarity of thought and failure detection.

This suite was built from scratch using the **PyQt5** framework, leveraging hardware acceleration to render complex vector diagrams smoothly with pixel-perfect precision.

---

────────────────────────────────────────────────────────────────────────
DESIGN PHILOSOPHY: MULTI-THEME NEO-BRUTALISM
────────────────────────────────────────────────────────────────────────

The aesthetics of ProEng is one of its fundamental pillars. It is not purely decorative; every color and shadow choice serves a functional purpose.

### Industrial Neo-Brutalism

ProEng uses **14 visual themes** with consistent neo-brutalist language: thick solid borders, hard drop shadows with offset, heavy typography in uppercase, and saturated colors. This style prioritizes readability and visual hierarchy, making it ideal for engineers who prefer direct interfaces without decorative distractions.

### Multi-Theme System (14 Themes)

Users can switch between themes at any time via dropdown selector in the navigation bar:

1. **Neo-Brutal** — Vibrant yellow on light background, thick black borders
2. **Midnight** — Deep blue with electric cyan
3. **Embers** — Charcoal gray with ember orange
4. **Forest** — Dark organic green
5. **Synthwave** — Neon purple and retro 80s magenta
6. **Arctic** — Ice white with glacial blue
7. **Solar** — Gold-yellow with earth brown
8. **Crimson** — Deep wine with scarlet red
9. **Ocean** — Navy blue with white foam
10. **Volcano** — Basalt black with lava yellow
11. **Mint** — Soft mint-green with cream
12. **Onyx** — Absolute black with white accents
13. **Lilac** — Lavender with delicate undertone
14. **Dracula** — Official Dracula theme palette (100% spec-compliant)

Each theme updates in real-time across all modules, diagrams, toolbars, and dialogs, maintaining complete functional parity.

---

╔════════════════════════════════════════════════════════════════════╗
║  SYSTEM ARCHITECTURE: CORE ENGINE                                  ║
╚════════════════════════════════════════════════════════════════════╝

ProEng uses a **Modular Plugin Architecture**, where the system core only manages navigation and global state, while engineering functionality resides in independent modules.

### The `BaseModule` Class

All 11 modules of ProEng (Flowsheet, BPMN, EAP, Canvas, Ishikawa, 5W2H, Gantt, Kanban, Scrum, PDCA, and Script Engine) inherit from `BaseModule`. This class defines the contract every module must follow:

- `get_state()`: Serializes all canvas objects into a Python dictionary (JSON-friendly).
- `set_state(state)`: Reconstitutes the work environment from a saved file.
- `refresh_theme()`: Informs the module that global colors have changed and it must redraw.

### Detailed Directory Structure

The file organization follows modern Python development standards:

```text
proeng/
│
├── core/                       # The "Brain" of the Application
│   ├── __init__.py
│   ├── themes.py               # Neo-Brutalist Theme (color palette)
│   ├── utils.py                # Drawing utilities, export, colorimetric conversion
│   ├── toolbar.py              # Custom toolbar factory
│   ├── project.py              # File I/O logic and metadata
│   └── base_module.py          # Abstract interface for module integration
│
├── modules/                    # Specialized Tools (11 modules)
│   ├── __init__.py
│   ├── flowsheet.py            # PFD (Process Flow Diagram)
│   ├── bpmn.py                 # Business Process Flow Charts
│   ├── eap.py                  # WBS (Work Breakdown Structure)
│   ├── canvas.py               # Visual Project Planning
│   ├── ishikawa.py             # Cause-Effect Diagrams (6M)
│   ├── w5h2.py                 # Action Plan Matrices
│   ├── gantt.py                # Timeline with Critical Path (CPM)
│   ├── kanban.py               # Kanban Board with Drag-Drop Cards
│   ├── scrum.py                # Scrum Sprint Board with Backlog
│   ├── pdca.py                 # PDCA Cycle (Plan-Do-Check-Act)
│   └── script_module.py         # Python Script Execution Engine
│
├── ui/                         # The "Skin" of the Application
│   ├── main_app.py             # Main workspace, Sidebar, Module Switcher
│   ├── welcome.py              # Entry hub with gallery and carousel
│   └── nav_bar.py              # Navigation bar with theme switcher
│
└── resources/                  # Static Assets
    └── screenshots/            # Screenshots for internal documentation
```

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: PFD FLOWSHEET
────────────────────────────────────────────────────────────────────────

The **Process Flow Diagram** is the most technically complex tool. It uses the `QGraphicsScene` graphics engine to manage interactive objects.

### Equipment Rendering Logic

The `draw_equipment` function centralizes rendering of 50+ types of industrial machines.

- **Vector Mathematics**: Each equipment is drawn using polygons (`QPolygonF`) and paths (`QPainterPath`) based on proportions relative to node size.
- **Dynamic Gradients**: We use `QLinearGradient` to create surfaces that appear metallic or glass-like, reacting dynamically to the theme's accent color.

### Smart Piping

The `Edge` class manages connectivity between equipment.

- **Normal Calculation**: Pipes exit orthogonally from ports (Top, Bottom, Left, Right).
- **Masking Effect**: To prevent pipe lines from crossing identification text (Tag), we implement a label background that assumes the exact canvas color (`bg_app`), creating a professional "cut" technical visual.

### Connection Ports

Each `ProcessNode` has 12 invisible connection ports (3 on each side) that appear only during hover or line creation, reducing visual clutter.

### Automatic Mass Balance

The Flowsheet module implements a mass balance engine:

- **Topological Sorting**: Kahn's algorithm for cycle detection and correct processing.
- **Mixing and Distribution**: For each node, the system sums inputs and distributes to output components per fraction or fixed flow configuration.
- **Global Verification**: At the end, verifies that total input mass equals output + retained.
- **Auto-Calculation**: After diagram changes, balance recalculates automatically with 300ms debounce.
- **Excel Export**: Exports all balance data to formatted spreadsheet.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: BPMN MODELER
────────────────────────────────────────────────────────────────────────

Focused on operational efficiency, ProEng's BPMN modeler rigorously follows international notation standards.

### Swimlane System

Unlike common flowcharts, ProEng's BPMN organizes tasks in **Swimming Lanes**.

- **Pool Management**: Dynamically add or remove lanes.
- **Headers**: Lane headers use the `_glass_grad` system for modern transparent visuals.
- **Multi-Position Text**: Add text labels to elements in 5 directions (inside, above, below, left, right).
- **Recall Arrows**: Automatic orthogonal paths (DOWN→LEFT→UP) with dashed styling for feedback loops.

### Connection Types

- **Hierarchical**: Parent-child connections (solid lines).
- **Cross-Lane**: Manual interconnections (dashed accent-color lines).
- **Recall**: Automatic DOWN→LEFT→UP routing with dashes for returns to previous elements.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: EAP (WORK BREAKDOWN STRUCTURE)
────────────────────────────────────────────────────────────────────────

The Work Breakdown Structure organizes project chaos into logical hierarchy.

### Tree Algorithm

The EAP module automatically generates links between "Work Packages".

- **Visual Hierarchy**: Parent level always highlighted in warmer colors (Gold/Yellow), while lower levels follow the suite's palette.
- **Selection and Editing**: Double-click to edit text, context menu to add sub-tasks.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: PROJECT MODEL CANVAS
────────────────────────────────────────────────────────────────────────

Agile planning tool to align the team before any technical project begins.

### The 15 Planning Blocks

- **External Factors**: Stakeholders, Constraints, Assumptions, Risks.
- **Internal Factors**: Team, Costs, Requirements.
- **Objectives**: Justification, SMART Objective, Benefits.
- **Deliverables**: Deliverable Group and Timeline.

Each block has a rich text editor supporting multiple lines and dynamic resizing.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: 5W2H ACTION PLAN
────────────────────────────────────────────────────────────────────────

A tabular matrix for tactical execution, where each action is detailed in 7 critical dimensions.

### Table Structure

1. **WHAT**: The task to be performed.
2. **WHY**: The purpose of the action.
3. **WHERE**: Execution location.
4. **WHEN**: Planned schedule.
5. **WHO**: Responsible owner.
6. **HOW**: Technical procedure.
7. **HOW MUCH**: Financial or HR budget.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: ISHIKAWA (6M)
────────────────────────────────────────────────────────────────────────

The Ishikawa (Fishbone) diagram identifies root causes of production line problems.

### The 6 Quality Pillars

ProEng segments causes into 6 pre-defined categories:

- **Methods**: Operational processes and routines.
- **Machines**: Equipment, tools, and software.
- **Materials**: Raw materials and input quality.
- **Manpower**: Skills, training, and personnel.
- **Measurement**: Data, metrics, and instrument calibration.
- **Environment**: Workplace, climate, and external conditions.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: GANTT (TIMELINE CPM)
────────────────────────────────────────────────────────────────────────

The **Gantt** module offers a complete timeline with Critical Path Method (CPM) and milestone support.

### Main Features

- **Tasks and Dependencies**: Create tasks with name, start date, end date, progress (%), and predecessor.
- **Milestones**: Visual reference markers as circles on the timeline for key dates.
- **Critical Path (CPM)**: Algorithm that automatically identifies tasks with zero slack, highlighting them in red for effort prioritization.
- **Time Visualization**: Horizontal bars rendered on temporal grid with current date marked by dashed line.
- **Visual Progress**: Green interior bars indicate percentage progress for each task.

### Zoom Controls

Use `Ctrl + Scroll` to adjust time scale. The graph automatically adapts keeping all tasks visible.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: KANBAN BOARD
────────────────────────────────────────────────────────────────────────

The **Kanban** module implements a visual task management board with 4 status columns.

### Column System

- **TO DO**: Planned tasks awaiting start.
- **IN PROGRESS**: Currently executing tasks.
- **DONE**: Successfully completed tasks.
- **CANCELED**: Discarded tasks (history preserved).

### Interactive Cards

Each card displays title, description, and priority (HIGH / MEDIUM / LOW) with visual color emphasis. Cards support **drag-and-drop** between columns for quick status updates.

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: SCRUM SPRINT BOARD
────────────────────────────────────────────────────────────────────────

The **Scrum Sprint Board** implements the Scrum agile framework with backlog and sprint management.

### Features

- **Backlog**: Repository of user stories awaiting prioritization.
- **Sprint Board**: 4 columns (TODO → IN PROGRESS → REVIEW → DONE) with drag-and-drop.
- **Story Points**: Each card carries a points estimate (Fibonacci scale recommended). Total sprint points displayed in header.
- **Sprint Planning**: Tool to move items from Backlog to active Sprint.
- **Sprint Closure**: Generates delivery metrics (items completed × points delivered).

---

────────────────────────────────────────────────────────────────────────
DETAILED MODULE: PDCA (CONTINUOUS IMPROVEMENT CYCLE)
────────────────────────────────────────────────────────────────────────

The **PDCA** module implements Deming's continuous improvement cycle in a visual circular layout.

### The 4 Quadrants

The diagram is rendered as a circle divided into 4 colored quadrants:

- **P (Plan)**: Identify problems and plan improvement actions.
- **D (Do)**: Implement planned actions at pilot scale.
- **C (Check)**: Measure results and compare against targets.
- **A (Act)**: Standardize successful actions or correct deviations.

### Interaction

Each quadrant accepts interactive cards: click `(+)` to add steps, double-click to edit, use `(-)` to delete. Each quadrant has a thematic color that automatically adapts to the active theme.

---

╔════════════════════════════════════════════════════════════════════╗
║  INSTALLATION GUIDE                                                 ║
╠═══════════════════════════════════════════════════════════════╣
║  Requirements: Python 3.8+  |  PyQt5  |  1366x768 minimum    ║
╚═══════════════════════════════════════════════════════════════╝

### System Requirements

- **Operating System**: Windows 10/11, Linux (Ubuntu/Debian), or macOS.
- **Python**: Version 3.8 or higher recommended.
- **Screen Resolution**: Minimum 1366x768 (Optimized for Full HD 1920x1080).

### Environment Setup

1. **Download Code**:
    ```bash
    git clone https://github.com/username/proeng-suite.git
    cd proeng-suite
    ```

2. **Prepare Python** — Create a virtual environment to isolate dependencies:
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On Linux/Mac:
    source .venv/bin/activate
    ```

3. **Install Dependencies** — The project uses only **PyQt5** as a major external dependency:
    ```bash
    pip install -r requirements.txt
    ```

4. **Run**:
    ```bash
    python main.py
    ```

---

────────────────────────────────────────────────────────────────────────
TECHNICAL MANUAL: THEME SYSTEM (themes.py)
────────────────────────────────────────────────────────────────────────

Visual customization is done through a centralized dictionary. Below, description of each color key:

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
│ border_width    │ Border Thickness          │ Neo-brutal 4px solid       │
│ shadow_offset   │ Shadow Offset             │ Hard 8x8 drop shadow       │
└─────────────────┴───────────────────────────┴────────────────────────────┘
```

---

────────────────────────────────────────────────────────────────────────
KEYBOARD SHORTCUTS (POWER USER)
────────────────────────────────────────────────────────────────────────

```
KEYBOARD SHORTCUTS
┌───────────────┬────────────────────────────────┬──────────────────┐
│ Shortcut      │ Action                         │ Context          │
├───────────────┼────────────────────────────────┼──────────────────┤
│ Ctrl + N      │ New Project                    │ Global           │
│ Ctrl + S      │ Save Project (.proeng)         │ Global           │
│ Ctrl + L      │ Cycle Themes                   │ Global           │
│ Ctrl + B      │ Toggle Sidebar                 │ Global           │
│ Ctrl + E      │ Export Diagram as PNG          │ Graphic Modules  │
│ Ctrl + Shift+P│ Export Diagram as PDF          │ Graphic Modules  │
│ Delete        │ Remove Selected Object         │ Canvas           │
│ Space         │ Pan Canvas                     │ Canvas           │
│ Esc           │ Cancel Active Tool             │ Global           │
└───────────────┴────────────────────────────────┴──────────────────┘
```

---

────────────────────────────────────────────────────────────────────────
CONTRIBUTION AND PHILOSOPHY
────────────────────────────────────────────────────────────────────────

ProEng is a **Free Software** project that values altruistic cooperation. To contribute, you not only follow a technical workflow but also commit to keeping knowledge open:

1. **Audit the Code**: As an engineering tool, security depends on your review.
2. **Improve and Share**: If you created a new symbol or fix, submit it so everyone benefits.
3. **Respect Freedom**: Any contribution will be licensed under the same GPL v3 terms.

- **Fork & Pull Request**: The classic GitHub collaboration flow is welcome.
- **Inspired by Stallman**: See our [MANIFESTO.md](MANIFESTO.md) to understand our ethical vision.

---

────────────────────────────────────────────────────────────────────────
LICENSE: FREE SOFTWARE (GPLv3)
────────────────────────────────────────────────────────────────────────

This software is **Free Software** (Libre Software), distributed under the **GNU General Public License v3.0**.

Unlike permissive licenses, GPL v3 ensures ProEng remains free forever. This means you have the freedom to use, study, and modify the software for any purpose, provided you keep these freedoms available to others. See [LICENSE](LICENSE) for complete terms.

---

────────────────────────────────────────────────────────────────────────
CONTACT AND SUPPORT
────────────────────────────────────────────────────────────────────────

For technical questions, bug reports, or suggestions for new equipment:

- **Issues**: [GitHub Issues Page](https://github.com/username/proeng-suite/issues)
- **Discussions**: [GitHub Discussions](https://github.com/username/proeng-suite/discussions)

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ProEng Suite v2.0 — Industrial Engineering & Project Management
11 Modules | 14 Themes | GPLv3
License: GNU General Public License v3.0
Built with Python, Qt Framework, and Precision Engineering
(c) 2026 ProEng Systems — Knowledge must remain free.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---


                          🌐 VERSÃO EM PORTUGUÊS / PORTUGUESE VERSION 🌐                                     
                                                                                                            

---

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
║          Engenharia Industrial & Gestão de Projeto                  ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

> **ProEng** é uma plataforma de engenharia industrial de ponta projetada para unificar planejamento técnico, modelagem de processos e gestão estratégica em um único ambiente visual de alta fidelidade.

---

────────────────────────────────────────────────────────────────────────
PREFÁCIO E VISÃO GERAL
────────────────────────────────────────────────────────────────────────

O projeto **ProEng** nasceu da necessidade de ferramentas de engenharia que não fossem apenas funcionais, mas também esteticamente superiores e intuitivas. Em um mundo onde softwares técnicos são frequentemente cinzas e burocráticos, ProEng introduz o conceito de **Engenharia Industrial Criativa** — onde o design auxilia na clareza de pensamento e na detecção de falhas.

Esta suíte foi construída do zero utilizando o framework **PyQt5**, aproveitando a aceleração de hardware para renderizar diagramas vetoriais complexos com suavidade e precisão de pixel.

---

────────────────────────────────────────────────────────────────────────
FILOSOFIA DE DESIGN: MULTI-TEMA NEO-BRUTALISTA
────────────────────────────────────────────────────────────────────────

A estética do ProEng é um dos seus pilares fundamentais. Ela não é puramente decorativa; cada escolha de cor e sombra tem um propósito funcional.

### Neo-Brutalismo Industrial

O ProEng utiliza **14 temas visuais** com linguagem neo-brutalista consistente: bordas sólidas e grossas, sombras duras com offset, tipografia pesada em caixa alta e cores saturadas. Esse estilo prioriza a legibilidade e a hierarquia visual, sendo ideal para engenheiros que preferem interfaces diretas e sem distrações decorativas.

### Sistema Multi-Tema (14 Temas)

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
14. **Dracula** — Paleta oficial do tema Dracula (100% em conformidade com especificação)

Cada tema atualiza em tempo real todos os módulos, diagramas, barras de ferramentas e diálogos, mantendo paridade funcional completa.

---

╔════════════════════════════════════════════════════════════════════╗
║  ARQUITETURA DO SISTEMA: CORE ENGINE                               ║
╚════════════════════════════════════════════════════════════════════╝

O ProEng utiliza uma arquitetura baseada em **Plugins Modulares**, onde o núcleo do sistema apenas gerencia a navegação e o estado global, enquanto as funcionalidades de engenharia residem em módulos independentes.

### A Classe `BaseModule`

Todos os 11 módulos do ProEng (Flowsheet, BPMN, EAP, Canvas, Ishikawa, 5W2H, Gantt, Kanban, Scrum, PDCA e Script Engine) herdam da `BaseModule`. Esta classe define o contrato que todo módulo deve seguir:

- `get_state()`: Serializa todos os objetos do canvas em um dicionário Python (JSON-friendly).
- `set_state(state)`: Reconstitui o ambiente de trabalho a partir de um arquivo salvo.
- `refresh_theme()`: Informa ao módulo que as cores globais mudaram e ele deve se redesenhar.


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
├── modules/                    # Ferramentas Especializadas (11 módulos)
│   ├── __init__.py
│   ├── flowsheet.py            # PFD (Diagrama de Fluxo de Processo)
│   ├── bpmn.py                 # Modelos de Fluxo de Processos de Negócio
│   ├── eap.py                  # EAP (Estrutura Analítica do Projeto)
│   ├── canvas.py               # Planejamento Visual de Projetos
│   ├── ishikawa.py             # Diagramas de Causa e Efeito (6M)
│   ├── w5h2.py                 # Matrizes de Planos de Ação
│   ├── gantt.py                # Cronograma com Caminho Crítico (CPM)
│   ├── kanban.py               # Quadro Kanban com Cards Arrastáveis
│   ├── scrum.py                # Quadro Scrum Sprint com Backlog
│   ├── pdca.py                 # Ciclo PDCA (Plan-Do-Check-Act)
│   └── script_module.py         # Mecanismo de Execução de Scripts Python
│
├── ui/                         # A "Pele" da Aplicação
│   ├── main_app.py             # Workspace principal, Sidebar e Seletor de Módulos
│   ├── welcome.py              # Hub de entrada com galeria e carrossel
│   └── nav_bar.py              # Barra de navegação com seletor de tema
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
ProEng Suite v2.0 — Engenharia Industrial & Gestão de Projeto
11 Módulos | 14 Temas | GPLv3
Licença: GNU General Public License v3.0
Construído com Python, Framework Qt e Engenharia de Precisão
(c) 2026 ProEng Systems — O conhecimento deve permanecer livre.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
