# Arquitetura do ProEng

## 📋 Visão Geral

**ProEng** é uma suíte modular de ferramentas de engenharia implementada em **Python + PyQt5** com design **Neo-Brutalist**. A aplicação orquestra múltiplos módulos especializados através de uma janela principal central (`MainApp`) com suporte a temas dinâmicos, persistência e export.

### Características Principais

- **11 Módulos Independentes**: Gantt, Flowsheet, BPMN, EAP, Canvas, W5H2, Ishikawa, Kanban, Scrum, PDCA, Script
- **Sistema de Temas**: 13 temas (dark, light, neo-brutalist, solarized, etc.) com propagação automática
- **Persistência**: Salva/carrega projetos em formato JSON (`.proeng`)
- **Export**: Gera PNG (3x supersample) e PDFs (A3 landscape)
- **Empacotável**: Compilável via PyInstaller para distribuição Windows
- **Lazy Loading**: Módulos carregados sob demanda (otimização de memória)

---

## 📁 Estrutura do Repositório

```
proeng/
├── core/                    # Lógica central e orquestração
│   ├── __init__.py
│   ├── base_module.py       # Contrato abstrato para módulos
│   ├── project.py           # Persistência (.proeng JSON)
│   ├── themes.py            # Sistema de temas (T(), cycle_theme())
│   ├── toolbar.py           # Barra de ferramentas
│   └── utils.py             # Utilitários de export (PNG, PDF)
│
├── ui/                      # Interface do usuário
│   ├── __init__.py
│   ├── main_app.py          # Janela principal (orquestração)
│   ├── nav_bar.py           # Barra de navegação + theme toggle
│   └── welcome.py           # Tela inicial (grid de módulos)
│
├── modules/                 # Implementações de ferramentas (11 módulos)
│   ├── __init__.py
│   ├── bpmn.py              # Modelador BPMN (swimlanes, tasks, gateways)
│   ├── canvas.py            # Business Model Canvas
│   ├── eap.py               # EAP / WBS (Work Breakdown Structure)
│   ├── flowsheet.py         # PFD / Process Flow Diagram
│   ├── gantt.py             # Diagrama de Gantt + CPM (Critical Path Method)
│   ├── ishikawa.py          # Fishbone / Causa-Efeito
│   ├── kanban.py            # Quadro Kanban com drag-drop
│   ├── pdca.py              # Ciclo PDCA (Plan-Do-Check-Act)
│   ├── scrum.py             # Sprint Board
│   ├── script_module.py     # Interpretador Python (execução em background)
│   └── w5h2.py              # 5W2H Planner (tabela interativa)
│
└── resources/
    └── screenshots/         # Telas/imagens de exemplo
```

### Arquivos Raiz (Root)

- **`main.py`**: Entrypoint da aplicação (usado por console script `proeng`)
- **`setup.py`**: Configuração de packaging PyPI + console script
- **`ProEng.spec`**: Especificação PyInstaller para build Windows EXE
- **`requirements.txt`**: Dependências Python
- `capture_welcome.py`, `generate_screenshots.py`: Utilitários para documentação

---

## 🏗️ Camadas Arquiteturais

### **Camada 1: Core (Orquestração Central)**

#### `proeng/core/themes.py` — Sistema de Temas

Define o sistema de temas global com suporte a **13 temas distintos** (dark, light, neo-brutalist, solarized, etc).

**Estrutura:**
```python
THEMES = {
    "neo_brutalist": {
        "name": "neo_brutalist",
        "bg_app": "#1A1A1A",
        "bg_card": "#2A2A2A",
        "accent": "#FFE500",
        "text_primary": "#FFFFFF",
        "shadow_offset_x": 8,
        "shadow_offset_y": 8,
        "shadow_hover_offset_x": 0,
        "shadow_hover_offset_y": 0,
        "border_width": 4,
        "border_radius": 0,
        # ... 50+ chaves padronizadas
    },
    "dark": {...},
    "light": {...},
    # ... 10 temas adicionais
}

# API Global
T() → Dict                  # Retorna tema ativo
set_theme(name) → None      # Define tema por nome
cycle_theme() → None        # Avança para próximo tema
validate_theme(name) → bool # Valida integridade
refresh_theme_recursive(widget) → None  # Propaga a filhos
```

**Consumo:**
- Widgets usam `T()` para cores/estilos em `__init__` e `refresh_theme()`
- `MainApp._on_theme_toggle_refresh()` propaga mudanças via `refresh_theme_recursive()`

---

#### `proeng/core/base_module.py` — Contrato de Módulos

Define interface que todo módulo must implementar.

```python
class BaseModule(QFrame):
    def get_state(self) -> Dict:
        """Retornar dict serializável com estado de negócio (sem Qt objects)."""
        
    def set_state(self, state: Dict) -> None:
        """Restaurar estado a partir de dict salvo."""
        
    def refresh_theme(self) -> None:
        """Reaplicar estilos com T() após troca de tema."""
        
    def get_view(self) -> Optional[QGraphicsView]:
        """Retornar QGraphicsView para export, ou None."""
        return None
```

**Responsabilidades:**
- Separar estado de negócio (dados) de UI (Qt objects)
- Serializar em `get_state()` (JSON-compatível)
- Restaurar via `set_state()`
- Suportar refresh dinâmico de temas
- Fornecer vista para export opcionalmente

---

#### `proeng/core/project.py` — Persistência

Gerencia serialização de projeto em disco (formato JSON `.proeng`).

```python
class AppProject:
    def save(path: str) → None  # Serializa estado de todos módulos
    def load(path: str) → None  # Desserializa de disco
    def update_module_state(module_name, state) → None
    def get_module_state(module_name) → Dict
```

**Formato (`.proeng`):**
```json
{
  "schema_version": "1.1",
  "metadata": {"created": "2026-04-08", ...},
  "modules": {
    "gantt": {"tasks": [...], ...},
    "flowsheet": {...},
    ...
  }
}
```

---

#### `proeng/core/utils.py` — Utilitários

Exportação e renderização (PNG, PDF, estilo neo-brutalist).

```python
_export_view(view, fmt: str, parent) → str  # PNG (3x) ou PDF (A3)
_nb_paint_node(...) → None  # Renderiza nó com border 4px, shadow 8x8
_solid_fill(...) → None     # Preenche respeitando tema
```

---

### **Camada 2: UI (Interface do Usuário)**

#### `proeng/ui/main_app.py` — Janela Principal

Orquestra toda a aplicação.

```
MainApp (QMainWindow)
├── NavBar (top)
│   ├── botões navegação (um por módulo)
│   └── ThemeToggle / Dropdown
├── QStackedWidget (central)
│   ├── WelcomeScreen (idx 0)
│   └── módulos carregados (idx 1+)
└── MenuBar (arquivo, edição, export)
```

**Responsabilidades:**
- Orquestração: gerencia estado global (projeto, módulo ativo)
- Lazy loading: cria módulo apenas quando selecionado
- Sincronização: `_sync_all_to_project()` e `_sync_project_to_all()`
- Theme propagation: `refresh_theme_recursive()` após `cycle_theme()`
- Export: usa `get_view()` ou heurísticas para PNG/PDF

**Sinais:**
- `module_changed(str)`, `project_changed()`, `theme_changed()`

**Inicialização:**
1. `__init__()` → cria widgets, restaura último projeto
2. `_setup_palette()` → aplica tema inicial
3. `_setup_ui_connections()` → conecta sinais
4. `show()` → exibe WelcomeScreen ou módulo anterior

---

#### `proeng/ui/nav_bar.py` — Navegação

Barra com botões de módulos e seletor de tema.

```python
NavBar (QFrame)
├── Grid de botões (um por módulo)
└── ThemeToggle / ThemeSelectorDropdown

Sinais:
  - module_requested(str)
  - theme_toggled()
```

---

#### `proeng/ui/welcome.py` — Tela Inicial

Grid de módulos com cards neo-brutalist.

```python
WelcomeScreen (QFrame)
├── Grid de ModuleCardNB (um por módulo)
├── Botão "New Project"
├── Botão "Open Project"
└── Botão "Load Example"

ModuleCardNB (QFrame)
├── Ícone / cor do módulo
├── Título + descrição
└── Hover effect: shadow 8x8 → 0x0

Sinais:
  - new_project(), open_project(), load_example()
  - open_module(str)
```

---

### **Camada 3: Módulos (Ferramentas Especializadas)**

Cada módulo implementa o contrato `BaseModule`:

```python
_XModule (BaseModule)
├── __init__()
├── ._inner: QGraphicsScene / QFrame / widget customizado
├── get_state() → Dict      # Serializable
├── set_state(Dict)         # Restore
├── refresh_theme()         # Apply T()
└── get_view() → Optional[QGraphicsView]
```

#### Módulos Disponíveis

| Módulo | Descrição | Tipo |
|--------|-----------|------|
| **gantt** | Cronograma com CPM, crítico, folga | QGraphicsView |
| **flowsheet** | PFD diagrama com nós/edges, balanços | QGraphicsView |
| **bpmn** | Modelador BPMN (swimlanes, tasks, gateways) | QGraphicsView |
| **eap** | WBS / EAP (Work Breakdown Structure) | QGraphicsView |
| **canvas** | Business Model Canvas + notas | QFrame |
| **w5h2** | 5W2H planner (tabela interativa) | QFrame |
| **ishikawa** | Fishbone / diagrama causa-efeito | QGraphicsView |
| **kanban** | Quadro Kanban com drag-drop | QFrame |
| **scrum** | Sprint board (histórias, tarefas) | QFrame |
| **pdca** | Ciclo PDCA (visualização circular) | QGraphicsView |
| **script** | Interpretador Python + exec background | QFrame |

---

## 🔄 Fluxos Principais

### Fluxo 1: Novo Projeto
```
WelcomeScreen.new_project
  → MainApp._on_new_project()
    → criar AppProject()
    → resetar módulos (set_state({}))
    → ir para primeiro módulo
```

### Fluxo 2: Trocar Módulo
```
NavBar/WelcomeScreen: module_requested(name)
  → MainApp._on_module_requested(name)
    → sync módulo anterior → project
    → criar se não existir (lazy load)
    → restaurar state
    → exibir (QStackedWidget)
    → emitir module_changed
```

### Fluxo 3: Trocar Tema
```
NavBar: cycle_theme()
  → proeng.core.themes.cycle_theme()
  → MainApp._on_theme_toggle_refresh()
    → refresh_theme_recursive(main_app)
    → emitir theme_changed
```

### Fluxo 4: Salvar Projeto
```
MainApp._on_save_project()
  → _sync_all_to_project() ← coleta get_state()
  → AppProject.save(path) ← JSON .proeng
  → exibir "Salvo"
```

### Fluxo 5: Exportar PNG/PDF
```
MainApp._on_export()
  → módulo.get_view() → QGraphicsView
  → utils._export_view(view, fmt, parent)
    → render 3x para PNG ou A3 para PDF
    → salvar arquivo
```

---

## 📦 Dependências

**requirements.txt:**
```
PyQt5>=5.15
numpy
Pillow
```

**Build:**
- PyInstaller (via `ProEng.spec`)
- UPX (opcional, compressão)

---

## ➕ Como Adicionar Novo Módulo

### 1️⃣ Criar arquivo `proeng/modules/my_tool.py`
```python
from proeng.core.base_module import BaseModule
from proeng.core.themes import T
from typing import Dict, Optional

class _MyToolModule(BaseModule):
    def __init__(self):
        super().__init__()
        self._inner = ...  # seu widget/scene
        self.refresh_theme()
    
    def get_state(self) -> Dict:
        return {}
    
    def set_state(self, state: Dict) -> None:
        pass
    
    def refresh_theme(self) -> None:
        bg = T()["bg_card"]
        self.setStyleSheet(f"background: {bg};")
    
    def get_view(self) -> Optional[...]:
        return None  # ou seu QGraphicsView
```

### 2️⃣ Registrar em `MainApp.__init__`
```python
self.builders = {
    "gantt": lambda: _GanttModule(),
    "my_tool": lambda: _MyToolModule(),  # ← ADD
    ...
}
```

### 3️⃣ Adicionar botão em `NavBar`
```python
self.buttons["my_tool"] = QPushButton("My Tool")
self.buttons["my_tool"].clicked.connect(
    lambda: self._on_module_requested("my_tool")
)
```

### 4️⃣ Adicionar card em `WelcomeScreen`
```python
self.cards["my_tool"] = ModuleCardNB(
    "my_tool", "#FF00FF", "My Tool", "Descrição"
)
```

### 5️⃣ Testar
```bash
python main.py
# Clicar em "My Tool"
```

---

## ✅ Checklist para Novo Módulo

- [ ] Herda de `BaseModule`
- [ ] `get_state()` / `set_state()` round-trip OK
- [ ] `refresh_theme()` reaplica estilos
- [ ] `get_view()` consistente
- [ ] Registrado em `MainApp.builders`
- [ ] Botão em `NavBar`
- [ ] Card em `WelcomeScreen`
- [ ] Testado (abrir, salvar, tema, export)

---

## 🧪 Validação & Testes

```bash
# Teste de tema
python -c "
from proeng.core.themes import T, cycle_theme
from proeng.ui.main_app import MainApp
app = MainApp()
print(T()['name'])  # neo_brutalist
cycle_theme()
print(T()['name'])  # dark
"

# Teste de módulo
python main.py
# Abrir projeto → trocar módulo → trocar tema → export
```

---

## 📚 Próximos Passos

1. ✅ Documentação (este arquivo)
2. 📝 Gerar diagrama de componentes (Mermaid)
3. 🔨 Criar exemplo `_example_module.py`
4. 🧪 Testes unitários (round-trip `get_state`)
5. 🔄 CI pipeline (GitHub Actions)
6. 📖 Docstrings Google Style

---

*Última atualização: 2026-04-08*
