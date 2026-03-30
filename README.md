# ⚙️ ProEng — Engenharia & Gestão Industrial

> **ProEng** é uma suíte desktop de alto desempenho construída em **Python 3** e **PyQt5**, projetada especificamente para engenheiros, gestores de projetos e analistas de processos. Uma solução modular que une diagramação técnica, planejamento estratégico e gestão ágil em uma única interface moderna.

---

## 🖼️ Visual Showcase

A interface do ProEng foi desenhada para oferecer máxima clareza e produtividade, com suporte total a temas **Dark Industrial** e **Light Blue**.

| 🌑 Tema Escuro (Focado em Precisão) | ☀️ Tema Claro (Focado em Documentação) |
| :---: | :---: |
| ![Dark Mode](proeng/resources/screenshots/flowsheet_dark.png) | ![Light Mode](proeng/resources/screenshots/flowsheet_light.png) |

---

## 🛠️ Módulos Integrados

### 🏭 PFD Flowsheet (Diagrama de Fluxo de Processo)
A ferramenta mais robusta da suíte, otimizada para modelagem de processos químicos e industriais.
- **Conectividade Multi-Porta**: 12 pontos de conexão por equipamento (3 por lado) para roteamento complexo.
- **Terminais Dinâmicos**: Crie alimentações e saídas instantâneas arrastando tubulações para o vazio.
- **Roteamento Inteligente**: Tubulações ortogonais ("em L") automatizadas para saídas de topo e fundo.
- **Biblioteca de 26+ Ícones**: Bombas, Reatores, Torres de Destilação, Trocadores de Calor, Válvulas e muito mais.
- **Identificação de Correntes**: Rótulos de texto que se mantêm fixos e alinhados às tubulações.

### 🔀 BPMN Modeler (Modelagem de Negócios)
Padronização de processos conforme a norma BPMN 2.0.
- **Pools & Lanes**: Organização de responsabilidades em raias verticais e horizontais.
- **Fluxos Lógicos**: Eventos de início/fim, gateways de decisão e tarefas procedimentais.
- **Exportação Profissional**: Gere diagramas limpos para manuais de SOP (Procedimento Operacional Padrão).

### 📋 Gerador EAP/WBS (Estrutura Analítica do Projeto)
Descomponha o escopo do seu projeto de forma visual e hierárquica.
- **Numeração Automática**: Geração automática de códigos WBS (1.1, 1.1.1, etc.).
- **Layout Inteligente**: Auto-ajuste de nós para manter o diagrama sempre equilibrado.
- **Gestão de Pacotes de Trabalho**: Identificação clara de entregáveis.

### 🐟 Diagrama de Ishikawa (Espinha de Peixe)
Análise estruturada de causa raiz para controle de qualidade.
- **Metodologia 6M**: Categorias pré-definidas (Método, Máquina, Medida, Meio-Ambiente, Mão-de-Obra, Material).
- **Brainstorming Visual**: Adição dinâmica de causas secundárias e terciárias.

### 📝 PM Canvas & 🎯 Plano 5W2H
Ferramentas de planejamento estratégico e execução.
- **Canvas de Projeto**: Grade completa (Finocchio) para visão estratégica em uma página.
- **Matriz 5W2H**: Plano de ação detalhado (Who, What, Where, When, Why, How, How Much).

---

## 🚀 Como Executar (Ambiente de Desenvolvimento)

Para rodar a suíte ProEng em sua máquina local, siga os passos abaixo:

### 1. Pré-requisitos
- **Python 3.9+** instalado.
- Gerenciador de pacotes **pip**.

### 2. Instalação das Dependências
Clone o repositório e instale as bibliotecas necessárias:
```bash
git clone https://github.com/sasal0519/proeng.git
cd proeng
pip install -r requirements.txt
```

### 3. Rodando a Aplicação
```bash
python main.py
```

Você também pode testar módulos específicos individualmente:
```bash
python -m proeng.modules.flowsheet
```

---

## 💎 Diferenciais Técnicos

- **Arquitetura Modular**: Cada módulo funciona de forma independente, facilitando a manutenção e expansão.
- **Renderização Vectorial**: O motor gráfico baseado em `QGraphicsView` garante zoom infinito sem perda de qualidade.
- **Exportação Flexível**: Gere arquivos **PNG** em alta resolução ou documentos **PDF** prontos para impressão em A3/A4.
- **Persistência JSON**: Projetos salvos em formato leve e legível para fácil compartilhamento.

---

## 📜 Licença

Este projeto está licenciado sob a **MIT License** — consulte o arquivo [LICENSE](LICENSE) para mais detalhes.

---

*Desenvolvido com ❤️ pela comunidade ProEng.*
