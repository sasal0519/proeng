# ⚙️ ProEng — Engenharia & Gestão Industrial

> **ProEng** é uma suíte desktop de alto desempenho construída em **Python 3** e **PyQt5**, projetada especificamente para engenheiros, gestores de projetos e analistas de processos. Uma solução modular que une diagramação técnica, planejamento estratégico e gestão ágil em uma única interface moderna.

---

## 🖥️ Workspace Overview

O ProEng oferece uma experiência de trabalho fluida com temas dinâmicos e navegação integrada entre múltiplos módulos técnicos em resolução **Full HD**.

| 🌑 Dark Industrial (Padrão) | ☀️ Light Blue (Clássico) |
| :---: | :---: |
| ![Dark Theme](proeng/resources/screenshots/welcome_dark.png) | ![Light Theme](proeng/resources/screenshots/welcome_light.png) |

---

## 📦 Executável (Windows)

Você pode baixar a versão mais recente pronta para uso (sem necessidade de Python instalado):

🚀 **[Baixar ProEng v1.1.0 (Windows)](https://github.com/sasal0519/proeng/releases)**

- ✨ **Portable**: Não requer instalação, basta extrair e rodar.
- 🎨 **Interface Nativa**: Ícone customizado e suporte total a temas.

---

## 🖼️ Galeria Técnica de Módulos

| Módulo | 🌑 Tema Escuro | ☀️ Tema Claro |
| :--- | :---: | :---: |
| **🏭 PFD Flowsheet** | ![F_Dark](proeng/resources/screenshots/flowsheet_dark.png) | ![F_Light](proeng/resources/screenshots/flowsheet_light.png) |
| **📋 Gerador EAP/WBS** | ![E_Dark](proeng/resources/screenshots/eap_dark.png) | ![E_Light](proeng/resources/screenshots/eap_light.png) |
| **🔀 BPMN Modeler** | ![B_Dark](proeng/resources/screenshots/bpmn_dark.png) | ![B_Light](proeng/resources/screenshots/bpmn_light.png) |
| **📝 PM Canvas**    | ![C_Dark](proeng/resources/screenshots/canvas_dark.png) | ![C_Light](proeng/resources/screenshots/canvas_light.png) |
| **🐟 Ishikawa**     | ![I_Dark](proeng/resources/screenshots/ishikawa_dark.png) | ![I_Light](proeng/resources/screenshots/ishikawa_light.png) |
| **🎯 Plano 5W2H**   | ![W_Dark](proeng/resources/screenshots/w5h2_dark.png) | ![W_Light](proeng/resources/screenshots/w5h2_light.png) |

---

## 🛠️ Funcionalidades Detalhadas

### 🏭 PFD Flowsheet (Diagrama de Fluxo)
A ferramenta mais robusta da suíte, otimizada para modelagem de processos industriais.
- **Conectividade Profissional**: 12 portas por equipamento (3 por lado) para roteamento de alta densidade.
- **Terminais Dinâmicos**: Crie alimentações e saídas instantâneas arrastando tubulações para o vazio.
- **Roteamento Inteligente**: Tubulações ortogonais ("em L") automatizadas para saídas de topo e fundo.
- **Aesthetics**: Cabeças de seta afiadas e identificação de correntes coladas rente aos tubos.

### 🔀 BPMN Modeler & 📋 Gerador EAP
- **BPMN**: Modelagem de processos com Pools, Lanes, Eventos e Gateways lógicos profissionais.
- **EAP/WBS**: Estrutura Analítica com numeração automática de níveis e layout dinâmico balanceado.

### 📝 Project Model Canvas (PM Canvas)
Planejamento estratégico de alto nível utilizando a metodologia de José Finocchio Jr.
- **Gestão de Stakeholders**: Blocos dedicados para Clientes, Equipe e Fatores Externos.
- **Cronograma & Custos**: Definição rápida de marcos temporais e restrições financeiras.
- **Interface Intuitiva**: Adição de cartões (Post-its digitais) com cores dinâmicas por seção.

### 🐟 Diagrama de Ishikawa (6M)
Análise estruturada de causa raiz utilizando a metodologia Espinha de Peixe.
- **Categorização 6M**: Método, Máquina, Medida, Meio-Ambiente, Mão-de-Obra e Material.
- **Detalhamento Hierárquico**: Suporte nativo para causas secundárias e terciárias organizadas visualmente.
- **Visualização de Problema**: Foco centralizado na definição clara do efeito a ser analisado.

### 🎯 Plano de Ação 5W2H
Matriz de execução ágil para controle total de projetos e ações corretivas.
- **Checklist 5W2H**: O Que, Por Que, Quem, Onde, Quando, Como e Quanto Custa.
- **Hierarquia de Ações**: Organização de ações em árvore para visualização de dependências.
- **Gestão de Responsáveis**: Atribuição clara de tarefas e prazos em cada bloco do plano.

---

## 🚀 Como Executar (Ambiente de Desenvolvimento)

### 1. Pré-requisitos
- **Python 3.9+** e **pip**.

### 2. Instalação
```bash
git clone https://github.com/sasal0519/proeng.git
cd proeng
pip install -r requirements.txt
python main.py
```

---

## 💎 Diferenciais Técnicos

- **Arquitetura Modular**: Módulos desacoplados que facilitam a escala e manutenção.
- **Renderização Vectorial**: Motor `QGraphicsView` para zoom infinito e alta fidelidade.
- **Exportação Industrial**: Gere arquivos **PNG** em alta resolução (3x scale) ou **PDF** em A3/A4.

---

## 📜 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

*Desenvolvido com ❤️ pela comunidade ProEng.*
