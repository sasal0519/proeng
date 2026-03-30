# ⚙️ ProEng — Engenharia & Gestão Industrial

> **ProEng** é uma suíte desktop de alto desempenho construída em **Python 3** e **PyQt5**, projetada especificamente para engenheiros, gestores de projetos e analistas de processos. Uma solução modular que une diagramação técnica, planejamento estratégico e gestão ágil em uma única interface moderna.

---

## 📦 Executável (Windows)

Você pode baixar a versão mais recente pronta para uso (sem necessidade de Python instalado):

🚀 **[Baixar ProEng v1.1.0 (Windows)](https://github.com/sasal0519/proeng/releases)**

- ✨ **Portable**: Não requer instalação, basta extrair e rodar.
- 🎨 **Interface Nativa**: Ícone customizado e suporte total a temas.

---

## 🖼️ Galeria de Módulos

Confira a interface de cada ferramenta da suíte em alta definição:

### 🏭 PFD Flowsheet
Diagramas de fluxo de processo com 12 pontos de conexão e tubulações inteligentes.
![Flowsheet](proeng/resources/screenshots/flowsheet_dark.png)

### 📋 Gerador EAP/WBS
Estrutura Analítica do Projeto com numeração automática e layout dinâmico.
![EAP](proeng/resources/screenshots/eap_dark.png)

### 🔀 BPMN Modeler
Modelagem profissional de processos de negócio com Pools e Lanes.
![BPMN](proeng/resources/screenshots/bpmn_dark.png)

### 📝 PM Canvas
Planejamento estratégico de alto nível utilizando a metodologia Finocchio.
![Canvas](proeng/resources/screenshots/canvas_dark.png)

### 🐟 Diagrama de Ishikawa
Análise estruturada de causa e efeito (6M) para resolução de falhas.
![Ishikawa](proeng/resources/screenshots/ishikawa_dark.png)

### 🎯 Plano de Ação 5W2H
Matriz de execução ágil para controle total de prazos e responsáveis.
![5W2H](proeng/resources/screenshots/w5h2_dark.png)

---

## 🛠️ Módulos Detalhados

### 🏭 PFD Flowsheet
A ferramenta mais robusta da suíte, otimizada para modelagem de processos químicos e industriais.
- **Conectividade Multi-Porta**: 12 pontos de conexão por equipamento (3 por lado) para roteamento complexo.
- **Terminais Dinâmicos**: Crie alimentações e saídas instantâneas arrastando tubulações para o vazio.
- **Roteamento Inteligente**: Tubulações ortogonais ("em L") automatizadas para saídas de topo e fundo.
- **Biblioteca de 26+ Ícones**: Bombas, Reatores, Torres de Destilação e Trocadores de Calor.

### 🔀 BPMN Modeler
- **Pools & Lanes**: Organização de responsabilidades em raias configuráveis.
- **Fluxos Lógicos**: Eventos de início/fim, gateways de decisão e tarefas procedimentais.

### 📋 Gerador EAP/WBS
- **Numeração Automática**: Geração de códigos WBS (1.1, 1.1.1, etc.).
- **Layout Inteligente**: Auto-ajuste de nós para diagramas equilibrados.

---

## 🚀 Como Executar (Ambiente de Desenvolvimento)

### 1. Pré-requisitos
- **Python 3.9+** instalado.
- Gerenciador de pacotes **pip**.

### 2. Instalação
```bash
git clone https://github.com/sasal0519/proeng.git
cd proeng
pip install -r requirements.txt
python main.py
```

---

## 💎 Diferenciais Técnicos

- **Arquitetura Modular**: Módulos independentes e independentes.
- **Renderização Vectorial**: `QGraphicsView` para zoom infinito e alta fidelidade.
- **Exportação Profissional**: Gere arquivos **PNG** de alta resolução ou **PDF** em A3/A4.
- **Persistência JSON**: Projetos leves e fáceis de compartilhar.

---

## 📜 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

*Desenvolvido com ❤️ pela comunidade ProEng.*
