# Tutoriais do ProEng

Este documento fornece guias passo a passo para utilizar cada módulo do ProEng.

---

## 1. Flowsheet — Diagrama de Processo (PFD)

O módulo Flowsheet permite criar diagramas de processos industriais com balanço de massa automático.

### 1.1 Interface Principal

```
┌─────────────────────────────────────────────────────────────┐
│  🔀 Flowsheet — PFD com Balanço de Massa     [+Equipamento]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌──────┐         ┌──────┐         ┌──────┐             │
│    │Tanque│────────▶│Bomba │────────▶│Reator│             │
│    └──────┘         └──────┘         └──────┘             │
│                                                             │
│    [Entrada]                        [Saída]               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Adicionando Equipamentos

1. Clique no botão **"+ Equipamento"** na toolbar
2. Selecione o tipo de equipamento na lista:
   - **Tanque**: Reservatórios
   - **Bomba**: Bombas centrífugas
   - **Reator**: Reatores CSTR
   - **Trocador**: Trocadores de calor
   - **Válvula**: Válvulas de controle
   - **Caldeira**: Geradores de vapor
   - **Torre**: Colunas de destilação/absorção
3. O equipamento aparece no canvas. Arraste para posicionar.

### 1.3 Criando Conexões

1. Passe o mouse sobre um equipamento para revelar as **portas de conexão** (pontos azuis)
2. Clique em uma porta e arraste até outra porta
3. Uma seta (Stream) conecta os equipamentos
4. Clique na conexão para editar os dados de vazão

### 1.4 Configurando Dados de Vazão

1. Clique com **botão direito** em uma conexão (seta)
2. Selecione **"Editar Dados da Corrente"**
3. Configure:
   - **Vazão Total**: kg/h total da corrente
   - **Componentes**: Adicione componentes e porcentagens
4. Exemplo de configuração:

| Componente | Porcentagem | Vazão (kg/h) |
|------------|-------------|--------------|
| Água | 70.0 | 700.0 |
| NaOH | 20.0 | 200.0 |
| HCl | 10.0 | 100.0 |

### 1.5 Executando Balanço de Massa

1. Certifique-se de que:
   - Todas as correntes de **entrada** têm dados definidos
   - Os **equipamentos** têm configurações de separação
2. Clique em **"⚙️ Balanço"** na toolbar
3. O algoritmo de Kahn calcula automaticamente:
   - Vazões em todas as correntes
   - Distribuição nos produtos de saída
4. Resultados aparecem nas conexões

### 1.6 Configurando Separação de Equipamentos

1. Clique com botão direito no equipamento
2. Selecione **"Configurar Desempenho"**
3. Para cada componente, defina:
   - **Fração (%)**: Porcentagem que sai em cada porta
   - **Vazão Fixa**: Vazão constante na saída

---

## 2. BPMN — Modelador de Processos

O módulo BPMN permite criar diagramas de processos seguindo o padrão BPMN 2.0.

### 2.1 Conceitos Básicos

- **Pool**: Processo principal ou organização
- **Lane (Raia)**: Setor ou responsável
- **Tarefa**: Atividade a ser executada
- **Evento**: Acontecimento (Início, Intermediário, Fim)
- **Gateway**: Decisão (Exclusivo, Paralelo, Inclusivo)

### 2.2 Criando um Processo

1. O diagrama inicia com um **Evento de Início** padrão
2. Clique no botão **"+"** no final de uma tarefa para adicionar a próxima
3. Use o menu de contexto (botão direito) para:
   - Adicionar filho/irmão
   - Mudar formato (tarefa ↔ gateway ↔ evento)
   - Mover entre raias

### 2.3 Adicionando Raias

1. Clique no botão **"⊞ Adicionar Nova Baia"** abaixo do diagrama
2. Digite o nome do setor (ex: "Produção", "Logística")
3. Arraste elementos entre raias usando o menu de contexto

### 2.4 Tipos de Elementos

**Eventos:**
- ⭕ **Evento de Início**: Início do processo (verde)
- 🔵 **Evento Intermediário**: Acontecimento durante o fluxo
- ❌ **Evento de Fim**: Término do processo (vermelho)
- ⏰ **Evento de Tempo**: Timer/relogio
- 💬 **Evento de Mensagem**: Comunicação

**Gateways:**
- ◆ **Exclusivo (X)**: Apenas um caminho é escolhido
- ⬜ **Paralelo (+)**: Caminhos executam simultaneamente
- 🔘 **Inclusivo (O)**: Um ou mais caminhos podem ser escolhidos

### 2.5 Editando Elementos

1. **Duplo clique** no elemento para editar o nome
2. Ou use **botão direito → Renomear**

---

## 3. EAP — Estrutura Analítica do Projeto

O módulo EAP cria a hierarquia WBS (Work Breakdown Structure) do projeto.

### 3.1 Interface

```
┌─────────────────────────────────────────────────────────────┐
│  📋 EAP — Estrutura Analítica do Projeto         [Zoom +/-] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│        ┌─────────────┐                                     │
│        │  1. Projeto │                                     │
│        └──────┬──────┘                                     │
│               │                                             │
│    ┌──────────┼──────────┐                                 │
│    ▼          ▼          ▼                                 │
│ ┌──────┐  ┌──────┐  ┌──────┐                              │
│ │1.1   │  │1.2   │  │1.3   │                              │
│ │Fase A│  │Fase B│  │Fase C│                              │
│ └──────┘  └──────┘  └──────┘                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Criando a Estrutura

1. O nó raiz (1) é criado automaticamente
2. **Passe o mouse** sobre um nó para revelar botões:
   - **(+)** inferior: Adicionar filho
   - **(+)**: Adicionar irmão
   - **(-)**: Excluir nó
3. Clique no botão **(+)** para adicionar sub-pacotes

### 3.3 Editando Pacotes

1. **Duplo clique** no nó para editar o nome
2. Digite o nome do pacote de trabalho

### 3.4 Formatos de Nós

Ao adicionar um nó, escolha o formato:
- **Retângulo Arredondado**: Pacote de trabalho normal
- **Elipse**: Marco (milestone)
- **Losango**: Decisão

### 3.5 Numeração WBS

O código WBS é gerado automaticamente:
- Nível 1: `1`
- Nível 2: `1.1`, `1.2`, `1.3`
- Nível 3: `1.1.1`, `1.1.2`

---

## 4. PM Canvas — Project Model Canvas

O PM Canvas contém 15 blocos para planejamento de projetos.

### 4.1 Estrutura do Canvas

```
┌───────────┬───────────┬───────────┬───────────┬───────────┐
│ JUSTIFIC. │   OBJ     │  BENEF.   │  PRODUTO  │   RISCOS  │
│  (Grupo)  │  SMART    │  (Grupo)  │           │           │
├───────────┼───────────┼───────────┼───────────┼───────────┤
│           │           │           │           │           │
│  REQ      │  STAKEH   │  EQUIPE   │   PREM    │    TMP    │
│           │  HOLDERS  │           │           │           │
├───────────┼───────────┴───────────┼───────────┴───────────┤
│                    │   RESTRIÇÕES  │            CUSTOS      │
└────────────────────┴──────────────┴─────────────────────────┘
```

### 4.2 Preenchendo Blocos

1. **Duplo clique** no centro de um bloco amarelo para editar
2. Digite o conteúdo (aceita múltiplas linhas)
3. Pressione **Enter** para confirmar

### 4.3 Adicionando Anotações

1. Passe o mouse sobre uma seção
2. Clique no botão **(+)** que aparece no centro
3. Um novo bloco amarelo é criado dentro da seção
4. Duplo clique para editar

### 4.4 Excluindo Anotações

1. Passe o mouse sobre um bloco
2. Clique no botão **(-)** no canto superior direito

---

## 5. Ishikawa — Diagrama de Causa e Efeito

O diagrama de Ishikawa (espinha de peixe) análise causas de problemas usando as 6 categorias M.

### 5.1 Estrutura Inicial

```
        Método
           │
    ┌──────┼──────┐
    │      │      │
 Máq  Material  Mão de Obra
    │      │      │
    └──────┼──────┘
           │
    ┌──────┼──────┐
    │      │      │
  Meio   Medição  │
    │      │      │
    └──────┼──────┘
           │
        [EFEITO]
```

### 5.2 Editando o Efeito

1. **Duplo clique** no retângulo "EFEITO / PROBLEMA"
2. Digite o problema ou efeito a ser analisado

### 5.3 Adicionando Causas

1. Passe o mouse sobre uma categoria (Método, Máquina, etc.)
2. Clique no botão **(+)** para adicionar sub-causas
3. Duplo clique na causa para nomeá-la

### 5.4 Hierarquia de Causas

- **Nível 0**: Cabeça (Efeito/Problema)
- **Nível 1**: Categorias 6M
- **Nível 2**: Causas específicas

Você pode adicionar causas em até 2 níveis de profundidade.

---

## 6. 5W2H — Plano de Ação

O módulo 5W2H cria planos de ação estruturados.

### 6.1 Estrutura

```
┌─────────────────┐
│ PLANO DE AÇÃO   │  ← ROOT
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ O QUÊ? │ │ O QUÊ? │   ← WHAT (Ação)
└───┬────┘ └───┬────┘
    │         │
 ┌──┼──┐  ┌──┼──┐
 │  │  │  │  │  │
 ▼  ▼  ▼  ▼  ▼  ▼
WHY WHO WHEN WHERE HOW COST
```

### 6.2 Adicionando Nova Ação

1. Clique no botão **(+)** vermelho no nó raiz
2. Uma nova ação é criada com todos os campos 5W2H

### 6.3 Preenchendo os Campos

1. **Duplo clique** em qualquer caixa colorida
2. Digite o conteúdo:
   - **WHAT (O QUÊ?)**: Ação a ser realizada
   - **WHY (POR QUÊ?)**: Justificativa
   - **WHO (QUEM?)**: Responsável
   - **WHERE (ONDE?)**: Local
   - **WHEN (QUANDO?)**: Prazo
   - **HOW (COMO?)**: Método/etapas
   - **COST (QUANTO?)**: Custo/orçamento

### 6.4 Excluindo Ação

1. Passe o mouse sobre uma ação WHAT
2. Clique no botão **(-)** vermelho

---

## 7. Atalhos e Dicas

### 7.1 Zoom

| Ação | Atalho |
|------|--------|
| Aumentar zoom | `Ctrl + +` ou scroll cima |
| Diminuir zoom | `Ctrl + -` ou scroll baixo |
| Reset zoom | Botão na toolbar |

### 7.2 Exportação

Todos os módulos suportam exportação:
- **PNG**: Imagem de alta resolução
- **PDF**: Documento para impressão

Clique nos botões de exportação na toolbar de cada módulo.

### 7.3 Persistência

Os projetos são salvos automaticamente em formato `.proeng` (JSON), incluindo:
- Estado de todos os módulos
- Configurações de tema
- Zoom e posição da visualização
