```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██████╗ ██████╗  ██████╗ ███████╗███╗   ██╗ ██████╗              ║
║   ██╔══██╗██╔══██╗██╔═══██╗██╔════╝████╗  ██║██╔════╝              ║
║   ██████╔╝██████╔╝██║   ██║█████╗  ██╔██╗ ██║██║  ███╗             ║
║   ██╔═══╝ ██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║██║   ██║             ║
║   ██║     ██║  ██║╚██████╔╝███████╗██║ ╚████║╚██████╔╝             ║
║   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝ ╚═════╝             ║
║                                                                      ║
║             ███████╗██╗   ██╗██╗████████╗███████╗                  ║
║             ██╔════╝██║   ██║██║╚══██╔══╝██╔════╝                  ║
║             ███████╗██║   ██║██║   ██║   █████╗                    ║
║             ╚════██║██║   ██║██║   ██║   ██╔══╝                    ║
║             ███████║╚██████╔╝██║   ██║   ███████╗                  ║
║             ╚══════╝ ╚═════╝ ╚═╝   ╚═╝   ╚══════╝                  ║
║                                                                      ║
║          Industrial Engineering & Project Management                 ║
║                    Professional Suite  v1.0                          ║
╚══════════════════════════════════════════════════════════════════════╝
```

> **ProEng** e uma plataforma de engenharia industrial de ponta, desenhada para unificar o planejamento tecnico, a modelagem de processos e a gestao estrategica em um unico ambiente visual de alta fidelidade.

---

────────────────────────────────────────────────────────────────────────
PREFACIO E VISAO GERAL
────────────────────────────────────────────────────────────────────────

O projeto **ProEng** nasceu da necessidade de ferramentas de engenharia que nao fossem apenas funcionais, mas tambem esteticamente superiores e intuitivas. Em um mundo onde softwares tecnicos costumam ser cinzas e burocraticos, o ProEng introduz o conceito de **Creative Industrial Engineering** — onde o design auxilia na clareza de pensamento e na deteccao de falhas.

Esta suite foi construida do zero utilizando o framework **PyQt5**, aproveitando o poder da aceleracao de hardware para renderizar diagramas vetoriais complexos com suavidade e precisao de pixel.

---

────────────────────────────────────────────────────────────────────────
FILOSOFIA DE DESIGN: INDUSTRIAL GLASSMORPHISM
────────────────────────────────────────────────────────────────────────

A estetica do ProEng e um dos seus pilares fundamentais. Ela nao e puramente decorativa; cada escolha de cor e transparencia tem um proposito funcional.

### O Conceito "Dark Navy & Emerald"

Utilizamos uma paleta baseada em **Azul Marinho Profundo** para o canvas de trabalho. Isso cria um contraste natural com as linhas de processo em verde ou azul brilhante, facilitando a identificacao de conexoes em diagramas densos.

- **Fundo da Aplicacao (`bg_app`)**: `#050816` — Um tom de azul petroleo que absorve o brilho excessivo do monitor.
- **Efeito de Vidro (`bg_card`)**: `rgba(15, 23, 42, 210)` — Elementos de interface que parecem flutuar sobre o diagrama, permitindo ver a estrutura por baixo sem perder o foco na ferramenta ativa.
- **Acento Neon (`accent`)**: `#2563EB` e `#10B981` — Cores vibrantes que indicam interatividade e estados ativos.

### Transicao para o Modo Light

O ProEng oferece paridade total entre temas. No modo **Light**, as cores sao invertidas para tons de cinza suave e azul corporativo, garantindo que o software seja adequado para impressoes tecnicas em papel ou apresentacoes em salas iluminadas.

---

╔════════════════════════════════════════════════════════════════════╗
║  ARQUITETURA DO SISTEMA: CORE ENGINE                               ║
╚════════════════════════════════════════════════════════════════════╝

O ProEng utiliza uma arquitetura baseada em **Plugins Modulares**, onde o nucleo do sistema apenas gerencia a navegacao e o estado global, enquanto as funcionalidades de engenharia residem em modulos independentes.

### A Classe `BaseModule`

Todos os modulos do ProEng (Flowsheet, BPMN, etc.) herdam da `BaseModule`. Esta classe define o contrato que todo modulo deve seguir:

- `get_state()`: Serializa todos os objetos do canvas em um dicionario Python (JSON-friendly).
- `set_state(state)`: Reconstitui o ambiente de trabalho a partir de um arquivo salvo.
- `refresh_theme()`: Informa ao modulo que as cores globais mudaram e ele deve se redesenhar.

### Estrutura do Projeto

```
PROENG CORE ARCHITECTURE
┌─────────────────────────────────────────────────────────────────┐
│  APPLICATION LAYER                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  main_app.py │  │  welcome.py  │  │  selection_screen.py │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  CORE ENGINE                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐    │
│  │ themes   │ │  utils   │ │ toolbar  │ │  base_module   │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  MODULE LAYER                                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐    │
│  │flowsheet │ │   bpmn   │ │   eap    │ │    canvas      │    │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘    │
│  ┌──────────┐ ┌──────────┐                                     │
│  │ishikawa  │ │  w5h2    │                                     │
│  └──────────┘ └──────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Estrutura de Diretorios Detalhada

A organizacao de arquivos segue os padroes modernos de desenvolvimento Python:

```text
proeng/
│
├── core/                       # O "Cerebro" da Aplicacao
│   ├── __init__.py
│   ├── themes.py               # Definicao de paletas Light e Dark
│   ├── utils.py                # Utilitarios de desenho, exportacao e conversao colorimetrica
│   ├── toolbar.py              # Fabrica de barras de ferramentas customizadas
│   ├── project.py              # Logica de I/O de arquivos e metadados
│   └── base_module.py          # Interface abstrata para integracao de modulos
│
├── modules/                    # Ferramentas Especializadas
│   ├── __init__.py
│   ├── flowsheet.py            # PFD (Process Flow Diagram)
│   ├── bpmn.py                 # Fluxogramas de Processos de Negocio
│   ├── eap.py                  # WBS (Work Breakdown Structure)
│   ├── canvas.py               # Planejamento visual de projetos
│   ├── ishikawa.py             # Diagramas de Causa e Efeito (6M)
│   └── w5h2.py                 # Matrizes de Planos de Acao
│
├── ui/                         # A "Pele" da Aplicacao
│   ├── main_app.py             # Workspace principal, Sidebar e Logic Switcher
│   ├── welcome.py              # Hub de entrada com gallery e carrossel
│   └── selection_screen.py     # Grid visual de escolha de modulos
│
└── resources/                  # Ativos Estaticos
    └── screenshots/            # Capturas de tela para documentacao interna
```

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: PFD FLOWSHEET
────────────────────────────────────────────────────────────────────────

O **Process Flow Diagram** e a ferramenta de maior complexidade tecnica. Ele utiliza o motor grafico `QGraphicsScene` para gerenciar objetos interativos.

### Logica de Desenho de Equipamentos

A funcao `draw_equipment` centraliza a renderizacao de mais de 50 tipos de maquinas industriais.

- **Matematica Vetorial**: Cada equipamento e desenhado usando poligonos (`QPolygonF`) e caminhos (`QPainterPath`) baseados em proporcoes relativas ao tamanho do no.
- **Gradientes Dinamicos**: Utilizamos `QLinearGradient` para criar superficies que parecem metalicas ou de vidro, reagindo dinamicamente a cor de acento do tema.

### Smart Piping (Tubulacao Inteligente)

A classe `Edge` gerencia a conectividade entre equipamentos.

- **Calculo de Normais**: As tubulacoes saem ortogonalmente das portas (Top, Bottom, Left, Right).
- **Efeito Mascara (Masking)**: Para evitar que a linha da tubulacao cruze o texto de identificacao (Tag), implementamos um fundo de rotulo que assume a cor exata do canvas (`bg_app`), criando um visual de "corte" tecnico profissional.

### Portas de Conexao

Cada `ProcessNode` possui 12 portas de conexao invisiveis (3 em cada lado) que aparecem apenas durante o "hover" ou durante a criacao de uma linha, reduzindo o ruido visual ("clutter").

### Balanco de Massa Automatico

O modulo Flowsheet implementa um motor de balanco de massa:

- **Ordenacao Topologica**: Algoritmo de Kahn para deteccao de ciclos e processamento correto.
- **Mistura e Distribuicao**: Para cada no, o sistema soma as entradas e distribui aos componentes nas saidas conforme configuracao de fracao ou vazao fixa.
- **Verificacao Global**: Ao final, verifica se a massa total de entrada equals a saida + retido.
- **Autocalculacao**: Apos alteracoes no diagrama, o balanco recalcula automaticamente com debounce de 300ms.
- **Exportacao Excel**: Exporta todos os dados de balanco para planilha formatada.

### Correcoes Recentes

- **Bug de Pipes Infinitos**: Corrigida criacao duplicada de pipes ao criar conexoes de saida de equipamentos.
- **Propagacao de Dados de Saida**: Agora ao criar uma nova corrente de saida, o sistema pre-preenche automaticamente com os dados do balanco de massa calculado, soma das entradas ou dados existentes.

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: BPMN MODELER
────────────────────────────────────────────────────────────────────────

Focado na eficiencia operacional, o modelador BPMN do ProEng segue rigorosamente a notacao internacional.

### Sistema de Raias (Lanes)

Diferente de fluxogramas comuns, o BPMN do ProEng organiza as tarefas em **Swimming Lanes**.

- **Pool Management**: Voce pode adicionar ou remover raias dinamicamente.
- **Headers**: Os cabecalhos de raia utilizam o sistema `_glass_grad` para um visual moderno e transparente.

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: EAP (WORK BREAKDOWN STRUCTURE)
────────────────────────────────────────────────────────────────────────

A Estrutura Analitica do Projeto organiza o caos do escopo em uma hierarquia logica.

### Algoritmo de Arvore

O modulo EAP gera automaticamente os links entre "Pacotes de Trabalho".

- **Hierarquia Visual**: O nivel pai e sempre destacado com cores mais quentes (Dourado/Amarelo), enquanto os niveis inferiores seguem a paleta da suite.
- **Selecao e Edicao**: Clique duplo para editar textos, menu de contexto para adicionar sub-tarefas.

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: PROJECT MODEL CANVAS
────────────────────────────────────────────────────────────────────────

Ferramenta de planejamento agil para alinhar a equipe antes do inicio de qualquer projeto tecnico.

### Os 15 Blocos de Planejamento

- **Fatores Externos**: Stakeholders, Restricoes, Premissas, Riscos.
- **Fatores Internos**: Equipe, Custos, Requisitos.
- **Objetivos**: Justificativa, Objetivo SMART, Beneficios.
- **Entregas**: Grupo de Entregas e Linha do Tempo.

Cada bloco possui um editor de texto rico que suporta multiplas linhas e redimensionamento dinamico.

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: 5W2H ACTION PLAN
────────────────────────────────────────────────────────────────────────

Uma matriz tabular para execucao tatica, onde cada acao e detalhada em 7 dimensoes cruciais.

### Estrutura da Tabela

1. **WHAT**: A tarefa a ser realizada.
2. **WHY**: O proposito da acao.
3. **WHERE**: Local de execucao.
4. **WHEN**: Cronograma previsto.
5. **WHO**: Responsavel (Owner).
6. **HOW**: Procedimento tecnico.
7. **HOW MUCH**: Orcamento financeiro ou de RH.

---

────────────────────────────────────────────────────────────────────────
MODULO DETALHADO: ISHIKAWA (6M)
────────────────────────────────────────────────────────────────────────

O diagrama de Ishikawa (ou Espinha de Peixe) permite identificar a causa raiz de problemas em linhas de producao.

### Os 6 Pilares da Qualidade

O ProEng segmenta as causas em 6 categorias pre-definidas:

- **Metodos**: Processos e rotinas operacionais.
- **Maquinas**: Equipamentos, ferramentas e software.
- **Materiais**: Materia-prima e qualidade de insumos.
- **Mao de Obra**: Habilidades, treinamento e pessoas.
- **Medida**: Dados, metricas e calibracao de instrumentos.
- **Meio Ambiente**: Local de trabalho, clima e condicoes externas.

---

╔════════════════════════════════════════════════════════════════════╗
║  GALERIA DE INTERFACE                                              ║
╚════════════════════════════════════════════════════════════════════╝

```
┌─────────────────────────────────────────────────────────────────┐
│  INTERFACE GALLERY  —  Dark (Premium)  vs  Light (Corporate)    │
└─────────────────────────────────────────────────────────────────┘
```

| Modulo | Tema Dark (Premium) | Tema Light (Corporativo) |
| :--- | :---: | :---: |
| **Welcome Screen** | ![Welcome Dark](proeng/resources/screenshots/welcome_dark.png) | ![Welcome Light](proeng/resources/screenshots/welcome_light.png) |
| **Flowsheet (PFD)** | ![Flowsheet Dark](proeng/resources/screenshots/flowsheet_dark.png) | ![Flowsheet Light](proeng/resources/screenshots/flowsheet_light.png) |
| **BPMN Modeler** | ![BPMN Dark](proeng/resources/screenshots/bpmn_dark.png) | ![BPMN Light](proeng/resources/screenshots/bpmn_light.png) |
| **EAP / WBS** | ![EAP Dark](proeng/resources/screenshots/eap_dark.png) | ![EAP Light](proeng/resources/screenshots/eap_light.png) |
| **Project Canvas** | ![Canvas Dark](proeng/resources/screenshots/canvas_dark.png) | ![Canvas Light](proeng/resources/screenshots/canvas_light.png) |
| **Plano 5W2H** | ![5W2H Dark](proeng/resources/screenshots/w5h2_dark.png) | ![5W2H Light](proeng/resources/screenshots/w5h2_light.png) |
| **Ishikawa (6M)** | ![Ishikawa Dark](proeng/resources/screenshots/ishikawa_dark.png) | ![Ishikawa Light](proeng/resources/screenshots/ishikawa_light.png) |

```
┌─────────────────────────────────────────────────────────────────┐
│  END OF INTERFACE GALLERY                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

╔═══════════════════════════════════════════════════════════════╗
║  INSTALLATION GUIDE                                           ║
╠═══════════════════════════════════════════════════════════════╣
║  Requirements: Python 3.8+  |  PyQt5  |  1366x768 min        ║
╚═══════════════════════════════════════════════════════════════╝

### Requisitos do Sistema

- **Sistema Operacional**: Windows 10/11, Linux (Ubuntu/Debian) ou macOS.
- **Python**: Versao 3.8 ou superior recomendada.
- **Resolucao de Tela**: Minimo 1366x768 (Otimizado para Full HD 1920x1080).

### Configuracao do Ambiente

1. **Download do Codigo**:
    ```bash
    git clone https://github.com/proeng-systems/proeng-suite.git
    cd proeng-suite
    ```

2. **Preparacao do Python** — Crie um ambiente virtual para isolar as dependencias:
    ```bash
    python -m venv .venv
    # No Windows:
    .venv\Scripts\activate
    # No Linux/Mac:
    source .venv/bin/activate
    ```

3. **Instalacao de Dependencias** — O projeto utiliza apenas o **PyQt5** como dependencia externa pesada:
    ```bash
    pip install pyqt5
    ```

4. **Execucao**:
    ```bash
    python main.py
    ```

---

────────────────────────────────────────────────────────────────────────
MANUAL TECNICO: SISTEMA DE TEMAS (themes.py)
────────────────────────────────────────────────────────────────────────

A customizacao visual e feita atraves de um dicionario centralizado. Abaixo, a descricao de cada chave de cor:

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
CONTRIBUICAO E FILOSOFIA
────────────────────────────────────────────────────────────────────────

O ProEng e um projeto de **Software Livre** que valoriza a cooperacao altruista. Para contribuir, voce nao apenas segue um fluxo tecnico, mas adere ao compromisso de manter o conhecimento aberto:

1. **Audite o Codigo**: Como ferramenta de engenharia, a seguranca depende da sua revisao.
2. **Melhore e Compartilhe**: Se criou um novo simbolo ou correcao, envie-o para que todos se beneficiem.
3. **Respeite a Liberdade**: Qualquer contribuicao sera licenciada sob os mesmos termos da GPLv3.

- **Fork & Pull Request**: O fluxo classico de colaboracao via GitHub e bem-vindo.
- **Inspirado em Stallman**: Veja nosso [MANIFESTO.md](MANIFESTO.md) para entender nossa visao etica.

---

────────────────────────────────────────────────────────────────────────
LICENCA DE USO: SOFTWARE LIVRE (GPLv3)
────────────────────────────────────────────────────────────────────────

Este software e um **Free Software** (Software Livre), distribuido sob a licenca **GNU General Public License v3.0**.

Diferente de licencas permissivas, a GPLv3 garante que o ProEng permaneca livre para sempre. Isso significa que voce tem a liberdade de usar, estudar e modificar o software para qualquer fim, desde que mantenha essas liberdades disponiveis para os outros. Consulte o arquivo [LICENSE](LICENSE) para os termos completos.

---

────────────────────────────────────────────────────────────────────────
CONTATO E SUPORTE
────────────────────────────────────────────────────────────────────────

Para duvidas tecnicas, bugs ou sugestoes de novos equipamentos:

- **Issues**: [GitHub Issues Page]

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ProEng Suite — Industrial Engineering & Project Management
License : GNU General Public License v3.0
Built with Python, Qt Framework, and Precision Engineering
(c) 2026 ProEng Systems — Knowledge must remain free.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
