# Referência de API — ProEng v2.0

Este documento descreve as classes, funções e interfaces principais dos 10 módulos do projeto ProEng.

---

## 1. Sistema de Temas

### 1.1 Singleton `T()`

```python
from proeng.core.themes import T

def T() -> dict:
    """Retorna o dicionário de cores do tema ativo (dark ou light)."""
```

**Propriedades do tema:**

| Chave | Descrição | Exemplo |
|-------|-----------|--------|
| `bg_app` | Fundo principal da aplicação | `#050816` (dark) |
| `bg_card` | Fundo de cartões/caixas | `rgba(15, 23, 42, 210)` |
| `accent` | Cor de acento principal | `#2563EB` |
| `accent_bright` | Cor de acento clara | `#38BDF8` |
| `text` | Cor do texto principal | `#E5E7EB` |
| `text_dim` | Cor do texto secundário | `#9CA3AF` |
| `btn_add` | Cor do botão adicionar | `#22C55E` |
| `btn_del` | Cor do botão excluir | `#EF4444` |
| `line` | Cor das linhas de conexão | `#38BDF8` |
| `toolbar_bg` | Fundo da barra de ferramentas |gradiente |

### 1.2 Funções do Módulo `themes`

```python
from proeng.core.themes import set_theme, THEMES

def set_theme(name: str):
    """Altera o tema ativo para 'dark' ou 'light'."""
```

### 1.3 Tipos 5W2H

```python
from proeng.core.themes import W5H2_TYPES

W5H2_TYPES = {
    "ROOT":  {"t": "PLANO DE AÇÃO", "c": "#E03535"},
    "WHAT":  {"t": "O QUÊ? (Ação)", "c": "#3498DB"},
    "WHY":   {"t": "POR QUÊ? (Justificativa)", "c": "#F1C40F"},
    "WHO":   {"t": "QUEM? (Responsável)", "c": "#9B59B6"},
    "WHERE": {"t": "ONDE? (Local)", "c": "#2ECC71"},
    "WHEN":  {"t": "QUANDO? (Prazo)", "c": "#E67E22"},
    "HOW":   {"t": "COMO? (Método/Etapas)", "c": "#1ABC9C"},
    "COST":  {"t": "QUANTO? (Custo/Orçamento)", "c": "#E74C3C"}
}
```

---

## 2. Módulo Flowsheet (PFD)

### 2.1 Classe `FlowsheetWidget`

Widget principal para diagramas de processo com balanço de massa.

```python
from proeng.modules.flowsheet import FlowsheetWidget
```

**Construtor:**

```python
def __init__(self)
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `solve_mass_balance()` | Executa o algoritmo de Kahn para cálculo de vazões |
| `load_example()` | Carrega um exemplo industrial de processo |
| `get_state()` | Retorna estado serializável `{nodes, edges, streams}` |
| `set_state(state)` | Restaura estado a partir de dicionário |

**Sinais:**

| Sinal | Parâmetros | Descrição |
|-------|------------|-----------|
| `node_added` | `node_id` | Emitido quando novo equipamento é adicionado |
| `connection_made` | `source, target` | Emitido quando conexão é criada |

### 2.2 Classe `ProcessNode`

Nó de equipamento industrial.

```python
class ProcessNode(QGraphicsItem):
    def __init__(self, symbol_type: str, label: str = ""):
```

**Propriedades:**

- `symbol_type`: Tipo de equipamento (ex: "Tanque", "Bomba", "Reator")
- `label`: Nome customizado do equipamento
- `edges`: Lista de conexões (`Stream` objects)
- `split_config`: Dicionário de configuração de fração `{comp: {port: {mode, val}}}`

### 2.3 Classe `Stream` (Edge)

Conexão entre equipamentos com dados de balanço de massa.

```python
class Stream(QGraphicsPathItem):
    def __init__(self, source_node, target_node):
        self.flow_data: dict  # {componente: vazão_kg_h}
        self.pipe_name: str
```

### 2.4 Funções Auxiliares

```python
def draw_equipment(painter, symbol_type, size, is_icon=False, theme=None):
    """Desenha símbolo industrial em QPainter."""
```

---

## 3. Módulo BPMN

### 3.1 Classe `BPMNAutoWidget`

Widget principal do modelador BPMN 2.0.

```python
from proeng.modules.bpmn import BPMNAutoWidget
```

**Construtor:**

```python
def __init__(self)
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `zoom_in()` | Aumenta zoom em 15% |
| `zoom_out()` | Diminui zoom em 15% |
| `update_zoom(z)` | Define zoom específico (0.3 - 3.0) |
| `get_state()` | Retorna `{schema, nodes, lanes, next_id}` |
| `set_state(state)` | Restaura estado BPMN |
| `draw_diagram()` | Redesenha o diagrama completo |

**Propriedades:**

- `nodes`: Dicionário de nós `{id: {text, shape, level, lane, children, parent}}`
- `lanes`: Lista de nomes das raias/pools
- `zoom`: Fator de zoom atual

### 3.2 Classe `BPMNAutoNode`

Item gráfico para elementos BPMN.

```python
class BPMNAutoNode(QGraphicsItem):
    def __init__(self, node_id, text, shape, lane, signals, zoom):
```

**Shapes suportados:**

- Eventos: "Evento Início", "Evento Intermediário", "Evento Fim", "Evento de Tempo", "Evento de Mensagem"
- Tarefas: "Tarefa", "Tarefa de Usuário", "Tarefa de Serviço", "Subprocesso"
- Gateways: "Gateway Exclusivo (X)", "Gateway Paralelo (+)", "Gateway Inclusivo (O)"
- Artefatos: "Objeto de Dados", "Base de Dados"

---

## 4. Módulo EAP (WBS)

### 4.1 Classe `EAPWidget`

Widget da Estrutura Analítica do Projeto.

```python
from proeng.modules.eap import EAPWidget
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `zoom_in()` | Aumenta zoom |
| `zoom_out()` | Diminui zoom |
| `update_zoom(z)` | Define zoom específico |
| `get_state()` | Retorna `{schema, nodes, next_id}` |
| `set_state(state)` | Restaura estado EAP |
| `draw_eap()` | Redesenha estrutura hierárquica |

**Estrutura de nós:**

```python
nodes = {
    id: {
        "text": "Nome do pacote",
        "children": [id_filho1, id_filho2],
        "parent": id_pai,
        "shape": "roundrect" | "ellipse" | "diamond"
    }
}
```

### 4.2 Geração WBS

O código WBS (1, 1.1, 1.1.1) é gerado automaticamente pelo método:

```python
def calculate_wbs(self, node_id: int, wbs: str):
    """Gera numeração WBS recursiva."""
```

---

## 5. Módulo PM Canvas

### 5.1 Classe `PMCanvasWidget`

Widget do Project Model Canvas com 15 blocos.

```python
from proeng.modules.canvas import PMCanvasWidget
```

**Seções disponíveis:**

| ID | Título | Subtítulo |
|----|--------|-----------|
| `just` | JUSTIFICATIVAS | Passado |
| `obj` | OBJ SMART | |
| `ben` | BENEFÍCIOS | Futuro |
| `prod` | PRODUTO | |
| `req` | REQUISITOS | |
| `stk` | STAKEHOLDERS EXTERNOS | & Fatores externos |
| `eqp` | EQUIPE | |
| `prem` | PREMISSAS | |
| `ent` | GRUPO DE ENTREGAS | |
| `rest` | RESTRIÇÕES | |
| `risc` | RISCOS | |
| `tmp` | LINHA DO TEMPO | |
| `cst` | CUSTOS | |

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `zoom_in()` | Aumenta zoom |
| `zoom_out()` | Diminui zoom |
| `reset_zoom()` | Reseta para 0.6 |
| `get_state()` | Retorna `{schema, sections, next_pid}` |
| `set_state(state)` | Restaura estado |

---

## 6. Módulo Ishikawa

### 6.1 Classe `IshikawaWidget`

Widget do Diagrama Espinha de Peixe (6M).

```python
from proeng.modules.ishikawa import IshikawaWidget
```

**Categorias 6M (iniciais):**

1. **Método** — Procedimentos e processos
2. **Máquina** — Equipamentos e ferramentas
3. **Material** — Matérias-primas e insumos
4. **Mão de Obra** — Recursos humanos
5. **Meio Ambiente** — Condições ambientais
6. **Medição** — Sistemas de medição e controle

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `zoom_in()` | Aumenta zoom |
| `zoom_out()` | Diminui zoom |
| `reset_zoom()` | Reseta para 1.0 |
| `get_state()` | Retorna `{schema, nodes, next_id}` |
| `set_state(state)` | Restaura estado |

---

## 7. Módulo 5W2H

### 7.1 Classe `W5H2Widget`

Widget do plano de ação 5W2H.

```python
from proeng.modules.w5h2 import W5H2Widget
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `zoom_in()` | Aumenta zoom |
| `zoom_out()` | Diminui zoom |
| `reset_zoom()` | Reseta para 1.0 |
| `get_state()` | Retorna `{schema, nodes, next_id}` |
| `set_state(state)` | Restaura estado |

**Estrutura de nós:**

```python
nodes = {
    1: {"text": "Projeto/Meta", "type": "ROOT", "parent": None, "children": [id_what]},
    id_what: {"text": "Ação", "type": "WHAT", "parent": 1, "children": [id_why, id_who, ...]},
    id_why: {"text": "Justificativa", "type": "WHY", ...},
    # ...
}
```

---

## 8. Módulo Gantt (Cronograma CPM)

### 8.1 Classe `GanttWidget`

Widget principal do cronograma Gantt com caminho crítico.

```python
from proeng.modules.gantt import GanttWidget
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `add_task(name, start, end, progress, predecessor)` | Adiciona tarefa ao cronograma |
| `calculate_cpm()` | Calcula caminho crítico (Critical Path Method) |
| `get_state()` | Retorna `{schema, tasks, next_id}` |
| `set_state(state)` | Restaura estado Gantt |

**Estrutura de tarefas:**

```python
tasks = [
    {
        "id": 1,
        "name": "Nome da Tarefa",
        "start": "2026-04-01",
        "end": "2026-04-15",
        "progress": 50,  # percentual 0-100
        "predecessor": None,  # ou id da predecessora
        "milestone": False,
        "critical": False  # preenchido pelo CPM
    }
]
```

---

## 9. Módulo Kanban

### 9.1 Classe `WidgetKanban`

Widget do quadro Kanban com drag-and-drop.

```python
from proeng.modules.kanban import WidgetKanban
```

**Colunas de status:**

| ID | Título |
|----|--------|
| `afazer` | A FAZER |
| `emandamento` | EM ANDAMENTO |
| `feito` | FEITO |
| `cancelado` | CANCELADO |

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `get_state()` | Retorna `{schema, cards, proximo_id}` |
| `set_state(state)` | Restaura estado Kanban |
| `refresh_theme()` | Reaplica tema visual |

**Estrutura de cards:**

```python
cards = {
    "afazer": [{"id": 1, "titulo": "...", "desc": "...", "prioridade": "alta"}],
    "emandamento": [...],
    "feito": [...],
    "cancelado": [...]
}
```

---

## 10. Módulo Scrum

### 10.1 Classe `ScrumWidget`

Widget do Sprint Board com backlog e story points.

```python
from proeng.modules.scrum import ScrumWidget
```

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `get_state()` | Retorna `{schema, sprint_name, sprint_cols, backlog, proximo_id}` |
| `set_state(state)` | Restaura estado Scrum |
| `refresh_theme()` | Reaplica tema visual |

**Colunas do Sprint:**

| Chave | Título | Status |
|-------|--------|--------|
| `todo` | TODO | Aguardando |
| `in_progress` | IN PROGRESS | Em execução |
| `review` | REVIEW | Em revisão |
| `done` | DONE | Concluído |

**Sinais:**

| Sinal | Descrição |
|-------|-----------|
| `add_item_sprint` | Novo item adicionado ao Sprint |
| `add_item_backlog` | Novo item adicionado ao Backlog |
| `mover_item(from, to, id)` | Card movido entre colunas |
| `planejar_sprint` | Iniciou planejamento de Sprint |
| `fechar_sprint` | Sprint encerrada |

---

## 11. Módulo PDCA

### 11.1 Classe `PDCAWidget`

Widget do ciclo PDCA com layout circular e 4 quadrantes.

```python
from proeng.modules.pdca import PDCAWidget
```

**Quadrantes:**

| Chave | Título | Descrição |
|-------|--------|-----------|
| `P` | PLAN | Planejar ações de melhoria |
| `D` | DO | Executar ações planejadas |
| `C` | CHECK | Verificar resultados obtidos |
| `A` | ACT | Padronizar ou corrigir desvios |

**Métodos:**

| Método | Descrição |
|--------|-----------|
| `get_state()` | Retorna `{schema, quadrants, proximo_id}` |
| `set_state(state)` | Restaura estado PDCA |
| `refresh_theme()` | Reaplica tema visual e cores dos quadrantes |

---

## 12. Classe Base

### 12.1 `BaseModule`

Classe base que todos os módulos implementam.

```python
from proeng.core.base_module import BaseModule

class BaseModule(QWidget):
    def get_state(self) -> Dict[str, Any]:
        """Retorna estado serializável."""

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restaura estado."""

    def refresh_theme(self) -> None:
        """Reaplica tema visual."""

    def get_view(self) -> Optional[QGraphicsView]:
        """Retorna QGraphicsView para exportação."""
```

---

## 13. Utilitários de Exportação

### 13.1 Função `_export_view`

```python
from proeng.core.utils import _export_view

def _export_view(view: QGraphicsView, fmt: str, parent=None):
    """Exporta cena gráfica para PNG ou PDF.
    
    Args:
        view: QGraphicsView contendo a cena
        fmt: "png" ou "pdf"
        parent: Widget pai para dialogs
    """
```

---

## 14. Componentes Industriais

### 14.1 Lista de Componentes

O módulo Flowsheet inclui ~300 componentes industriais:

```python
from proeng.modules.flowsheet import INDUSTRIAL_COMPONENTS

# Exemplos:
# "Água", "Vapor", "NaOH", "HCl", "H₂SO₄"
# "Metanol", "Etanol", "Benzeno"
# "NPK", "Urea", "MAP"
```

### 14.2 Equipamentos

```python
from proeng.modules.flowsheet import EQUIPMENT_ALIASES

# Mapeamento de nomes completos para símbolos:
# "Bomba Centrífuga" -> "Bomba"
# "Trocador Casco-Tubo" -> "Trocador"
# "Reator CSTR" -> "Reator"
```
