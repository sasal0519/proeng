# 🏭 ProEng Suite — Industrial Engineering Suite

Ferramenta de engenharia industrial unificada com modelagem de processos, planejamento e gestão estratégica em ambiente visual de alta fidelidade.

---

## 🎨 Design: Industrial Glassmorphism

Paleta **Dark Navy & Emerald** com transição completa para modo **Light**. O design prioriza clareza técnica: fundo escuro cria contraste natural com tubulações verdes/azuis brilhantes.

---

## 🏗️ Arquitetura

```
proeng/
├── core/           # BaseModule, themes, toolbar, utils, project
├── modules/        # flowheet, bpmn, eap, canvas, ishikawa, w5h2
├── ui/             # main_app, welcome, selection_screen
└── resources/      # screenshots
```

Todos os módulos herdam de `BaseModule` → `get_state()`, `set_state(state)`, `refresh_theme()`.

---

## 🏭 PFD Flowsheet

- **50+ Equipamentos**: Renderização vetorial com `QPainterPath` e gradientes dinâmicos.
- **Smart Piping**: Tubulações ortogonais com efeito máscara para labels.
- **12 Portas de Conexão**: Invisíveis até hover (3 por lado).
- **Balanço de Massa**: Kahn topsort, mistura/distribuição, autocalculação (300ms debounce), Excel export.

---

## 🔀 BPMN Modeler

Swimming Lanes com glassmorphism, pools dinâmicos, Conforme notação internacional.

---

## 📋 EAP (WBS)

Hierarquia visual automática: pais em dourado, filhos na paleta da suite. Duplo clique editar, menu contexto para sub-tarefas.

---

## 📝 Project Canvas

15 blocos de planejamento (Stakeholders, Restrições, Premissas, Riscos, Equipe, Custos, Requisitos, Justificativa, SMART, Benefícios, Entregas, Timeline). Editor rico multilinha.

---

## 🎯 5W2H Action Plan

Matriz tabular: WHAT, WHY, WHERE, WHEN, WHO, HOW, HOW MUCH.

---

## 🐟 Ishikawa (6M)

6 pilares: Métodos, Máquinas, Materiais, Mão de Obra, Medida, Meio Ambiente.

---

## 📸 Galeria

| Módulo | Dark | Light |
| :--- | :---: | :---: |
| Welcome | ![Welcome Dark](proeng/resources/screenshots/welcome_dark.png) | ![Welcome Light](proeng/resources/screenshots/welcome_light.png) |
| Flowsheet | ![Flowsheet Dark](proeng/resources/screenshots/flowsheet_dark.png) | ![Flowsheet Light](proeng/resources/screenshots/flowsheet_light.png) |
| BPMN | ![BPMN Dark](proeng/resources/screenshots/bpmn_dark.png) | ![BPMN Light](proeng/resources/screenshots/bpmn_light.png) |
| EAP/WBS | ![EAP Dark](proeng/resources/screenshots/eap_dark.png) | ![EAP Light](proeng/resources/screenshots/eap_light.png) |
| Canvas | ![Canvas Dark](proeng/resources/screenshots/canvas_dark.png) | ![Canvas Light](proeng/resources/screenshots/canvas_light.png) |
| 5W2H | ![5W2H Dark](proeng/resources/screenshots/w5h2_dark.png) | ![5W2H Light](proeng/resources/screenshots/w5h2_light.png) |
| Ishikawa | ![Ishikawa Dark](proeng/resources/screenshots/ishikawa_dark.png) | ![Ishikawa Light](proeng/resources/screenshots/ishikawa_light.png) |

---

## 🚀 Instalação

```bash
git clone https://github.com/proeng-systems/proeng-suite.git
cd proeng-suite
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/Mac: source .venv/bin/activate
pip install pyqt5
python main.py
```

---

## ⌨️ Atalhos

`Ctrl+N` Novo | `Ctrl+S` Salvar | `Ctrl+L` Tema | `Ctrl+B` Sidebar | `Ctrl+E` Exportar PNG | `Delete` Remover | `Esc` Cancelar

---

## 📄 Licença

GPLv3 — Software livre para sempre.

---

*© 2026 ProEng Suite — Python + Qt + Passion for Engineering*