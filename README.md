# posIAM03D04 - Assistente de Conhecimento Interno Corporativo

Micro-capstone da Pós em IA, módulo 3. Um assistente que responde às perguntas dos funcionários usando **somente** as políticas internas de uma empresa de logística portuária, e a comparação do comportamento do modelo **com e sem grounding**.

A empresa, o **Porto Ventura Terminais**, é **fictícia**. Todas as políticas, prazos, valores, ramais e e-mails da base foram criados para este trabalho.

O modelo e o fine-tuning seguem o que foi feito em sala na aula M3D4: Qwen2.5-1.5B-Instruct quantizado em 4 bits, LoRA com `r=16` e `alpha=32` em `q_proj` e `v_proj`, e `SFTTrainer` com 3 épocas. O que muda é a tarefa: em vez de classificar sentimento, o modelo aprende a responder a partir do contexto, citar a fonte e recusar quando a informação não está na base.

## Sumário

- [Como executar](#como-executar)
- [Arquitetura](#arquitetura)
- [Base de conhecimento](#base-de-conhecimento)
- [Estrutura de contexto](#estrutura-de-contexto)
- [Fine-tuning a partir do exemplo da aula](#fine-tuning-a-partir-do-exemplo-da-aula)
- [Avaliação](#avaliação)
- [Resultados](#resultados)
- [Análise comparativa](#análise-comparativa)
- [Exemplos de perguntas e respostas](#exemplos-de-perguntas-e-respostas)
- [Tratamento de erros](#tratamento-de-erros)
- [Critérios de aceitação e evidências](#critérios-de-aceitação-e-evidências)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Limitações](#limitações)

## Como executar

### Sem GPU (base, busca, contexto e testes)

Só precisa de Python 3.10 ou mais recente, sem nenhuma biblioteca externa.

```bash
python scripts/demo_contexto.py
```

```bash
python scripts/demo_contexto.py "Qual o free time para contêiner de importação?"
```

```bash
python scripts/avaliar_busca.py
```

```bash
python scripts/gerar_dataset.py
```

```bash
python -m unittest discover -s tests -v
```

### Com GPU (modelo, fine-tuning e comparação)

1. Abra `notebooks/micro_capstone_assistente.ipynb` no Google Colab e escolha uma GPU T4 (Runtime → Change runtime type).
2. Execute todas as células. O notebook clona este repositório, treina o adapter LoRA e avalia os 4 modos.
3. Ao final, ele baixa `resultados-d04.zip` (pasta `results/`) e `lora-adapter-conhecimento.zip`.

Nenhuma chave de API é necessária: o modelo é aberto e roda no próprio Colab.

## Arquitetura

```
pergunta do funcionário
        │
        ▼
 Busca BM25 (assistente/busca.py) ──► top 3 trechos da base (seção de política + ID POL-NN)
        │
        ▼
 Montagem do contexto (assistente/prompts.py)
   system: regras de grounding (só o CONTEXTO, citar fonte, frase fixa de recusa)
   user:   CONTEXTO com os trechos + PERGUNTA
        │
        ▼
 Qwen2.5-1.5B-Instruct (4 bits) + adapter LoRA treinado nesse formato
        │
        ▼
 resposta com [Fonte: POL-NN]  ou  "Não encontrei essa informação na base de conhecimento..."
        │
        ▼
 Avaliação automática contra o gabarito (assistente/avaliacao.py)
```

## Base de conhecimento

Oito políticas em Markdown, na pasta `base_conhecimento/`. Cada documento tem um ID (`POL-NN`), a área responsável, a versão e seções `##`. Cada seção vira um trecho da base; a seção "Objetivo" fica de fora porque não tem regras.

| ID | Documento | Área | Exemplos de regras |
|---|---|---|---|
| POL-01 | Agendamento de veículos no gate | Operações de Gate | antecedência de 24 h, tolerância de 30 min, no-show |
| POL-02 | Credenciamento e controle de acesso | Segurança Patrimonial | validade das credenciais, integração, perda |
| POL-03 | Segurança no pátio e EPI | SSMA | EPIs obrigatórios, 20 km/h, comunicação em 2 h |
| POL-04 | Armazenagem e free time | Comercial e Faturamento | free time de importação, exportação e vazios, contestação |
| POL-05 | Registro de avarias | Qualidade Operacional | fotos, FR-AV-01, lacre rompido, reclamação |
| POL-06 | Cargas perigosas | SSMA | notificação em 48 h, classes 1 e 7, pátio IMO |
| POL-07 | Viagens e reembolso | Financeiro e RH | limites, comprovantes, adiantamento |
| POL-08 | Jornada, banco de horas e trabalho híbrido | RH | turnos, banco de horas, híbrido, férias |

A base mistura temas operacionais (gate, pátio, cargas) e de RH (reembolso, jornada), como numa intranet real, para que a busca precise separar assuntos parecidos. Exemplo: "prazo de 7 dias" aparece no free time e na reclamação de avaria.

## Estrutura de contexto

O prompt de sistema do modo com grounding (`SISTEMA_COM_CONTEXTO` em `assistente/prompts.py`) define quatro regras:

1. responder usando somente as informações do CONTEXTO;
2. não usar conhecimento externo nem inventar prazos, valores ou regras;
3. se a resposta não estiver no CONTEXTO, responder exatamente a frase de recusa;
4. responder em até 3 frases e terminar com `[Fonte: POL-NN]`.

A mensagem do usuário leva os trechos identificados e, depois, a pergunta:

```
CONTEXTO:
[POL-01 — Agendamento de veículos no gate — Tolerância e atrasos]
O motorista tem tolerância de 30 minutos após o fim da janela agendada. ...

[POL-01 — Agendamento de veículos no gate — Janelas de agendamento]
...

PERGUNTA: Meu motorista chegou 40 minutos depois do fim da janela. Ele ainda pode entrar?
```

O modo sem grounding (`SISTEMA_SEM_CONTEXTO`) só diz que o modelo é o assistente interno do terminal: é o "chatbot genérico" que a empresa teria sem conectar a IA aos documentos.

**Por que BM25 e não embeddings:** com 8 documentos e 34 trechos, uma busca lexical resolve, não precisa baixar outro modelo e é fácil de explicar e testar. A busca recuperou o documento certo no 1º lugar em 100% das 44 perguntas que estão na base (`results/avaliacao_busca.json`). Com uma base maior, o próximo passo seria uma busca híbrida (BM25 + embeddings).

## Fine-tuning a partir do exemplo da aula

| | Aula M3D4 (`aula/`) | Este projeto |
|---|---|---|
| Modelo | Qwen2.5-1.5B-Instruct, 4 bits nf4 | igual |
| LoRA | r=16, alpha=32, dropout 0.05, `q_proj` e `v_proj` | igual |
| Treino | `SFTTrainer`, 3 épocas, batch 4, lr 2e-4 | igual |
| Dataset | `reviews.parquet`: avaliação → `{"sentiment": ...}` | `data/perguntas.json`: contexto + pergunta → resposta com fonte ou recusa |
| Formato | `messages` com system, user e assistant | igual |
| Comparação | `compare()` e `evaluate()` com `disable_adapter()` | igual, com 4 modos e métricas de alucinação |

O material da aula está em `aula/`: o notebook original, o `reviews.parquet` e o adapter de sentimento que eu treinei em sala (`aula/lora-adapter-sentimento/`).

Ajustes feitos na função `ask` da aula:

- o papel `"sytem"` foi corrigido para `"system"`, porque com o erro de digitação o modelo não recebia a instrução de sistema como tal;
- os tensores de entrada passam a ir para `model.device`, o que elimina o aviso de `input_ids` na CPU com o modelo na GPU.

**Dataset.** São 60 perguntas escritas à mão, cada uma com gabarito:

- **treino:** 40 perguntas, sendo 30 na base e 10 fora da base;
- **teste:** 20 perguntas diferentes das de treino, sendo 14 na base e 6 fora da base.

O contexto de cada exemplo de treino vem da mesma busca usada na inferência. Assim, nas perguntas fora da base o modelo vê trechos que parecem relacionados mas não respondem, e aprende a recusar mesmo assim.

## Avaliação

Cada resposta do teste é classificada automaticamente (`assistente/avaliacao.py`):

| Pergunta | Resultado | Categoria |
|---|---|---|
| Na base | traz todos os fatos do gabarito | correta |
| Na base | traz parte dos fatos | incompleta |
| Na base | não traz nenhum fato | incorreta (provável alucinação) |
| Na base | recusou | recusa indevida |
| Fora da base | recusou | recusa correta |
| Fora da base | inventou uma resposta | alucinação |

Os fatos são trechos curtos com variações aceitas, como `30 minutos|30 min|meia hora`. Um teste garante que todo fato do gabarito está escrito no documento-fonte, para o gabarito não ter erro.

Métricas por modo:

- **acerto geral:** respostas corretas + recusas corretas, sobre o total;
- **acerto na base:** respostas corretas nas perguntas que estão na base;
- **fatos cobertos:** proporção dos fatos do gabarito que aparecem nas respostas;
- **recusa correta:** perguntas fora da base que foram recusadas;
- **taxa de alucinação:** respostas inventadas para perguntas fora da base + respostas sem nenhum fato correto, sobre o total;
- **cita a fonte:** respostas a perguntas da base que citam o documento certo.

Os quatro modos comparados:

| Modo | Modelo | Contexto | O que mostra |
|---|---|---|---|
| A | base | não | o chatbot genérico, sem conhecer a empresa |
| B | base | sim | o efeito só do grounding |
| C | base + LoRA | não | se o fine-tuning sozinho "ensina" a base |
| D | base + LoRA | sim | grounding + modelo treinado para usar o contexto e recusar |

## Resultados

### Busca (executada localmente)

| Conjunto | Perguntas na base | Documento certo em 1º | Documento certo no top 3 |
|---|---:|---:|---:|
| Treino | 30 | 100% | 100% |
| Teste | 14 | 100% | 100% |

### Modelo (executado no Colab)

> **Pendente:** executar `notebooks/micro_capstone_assistente.ipynb` no Colab e copiar a pasta `results/` gerada para o repositório. O notebook gera `results/relatorio.md` com a tabela de métricas dos 4 modos e exemplos de respostas reais.

## Análise comparativa

> **Pendente:** esta seção será escrita com os números reais de `results/relatorio.md`, depois da execução no Colab.

Hipóteses que a avaliação vai confirmar ou refutar:

- **A (sem grounding):** o modelo não conhece prazos, valores e ramais da empresa fictícia. A expectativa é que invente respostas plausíveis, como "a tolerância é de 15 minutos", e quase nunca recuse. É a alucinação que o projeto quer reduzir.
- **A → B (só grounding):** a expectativa é que o acerto nas perguntas da base suba bastante, porque a resposta passa a estar no prompt. As recusas devem melhorar menos: modelos pequenos tendem a "aproveitar" algum trecho do contexto mesmo quando ele não responde a pergunta.
- **B → D (grounding + LoRA):** o treino com exemplos de recusa e a citação no formato `[Fonte: POL-NN]` deve aumentar a recusa correta e a citação da fonte.
- **C (LoRA sem contexto):** 30 exemplos e 3 épocas não bastam para o modelo "decorar" a base. A expectativa é que C fique perto de A nas perguntas novas do teste, mostrando que o fine-tuning ensina o **comportamento** e o grounding fornece o **conhecimento**.

## Exemplos de perguntas e respostas

Perguntas do conjunto de teste com a resposta esperada do gabarito. As respostas reais de cada modo ficam em `results/relatorio.md` depois da execução.

| ID | Pergunta | Resposta esperada | Fonte |
|---|---|---|---|
| A01 | Meu motorista chegou 40 minutos depois do fim da janela. Ele ainda pode entrar? | Não. A tolerância é de 30 minutos após o fim da janela; depois disso é preciso um novo agendamento. | POL-01 |
| A03 | O que acontece com a transportadora que falta aos agendamentos sem cancelar? | A partir da 3ª ocorrência de no-show no mês, bloqueio de 48 horas para novos agendamentos. | POL-01 |
| A09 | Quantos dias de free time tem um contêiner de exportação? | 5 dias corridos antes da data prevista de atracação. | POL-04 |
| A12 | Por quanto tempo uma carga perigosa pode ficar no pátio IMO? | 5 dias corridos; depois o cliente é notificado para retirada imediata. | POL-06 |
| A14 | Funcionário em período de experiência pode fazer trabalho híbrido? | Não; o híbrido não se aplica aos primeiros 90 dias. | POL-08 |
| A15 | Qual o valor do auxílio-creche pago pela empresa? | Recusa: a informação não está na base. | — |
| A18 | Quantos dias de licença-paternidade a empresa concede? | Recusa: a informação não está na base. | — |

## Tratamento de erros

| Situação | Como é tratada | O que o usuário vê |
|---|---|---|
| Pergunta sem relação com a base | a busca devolve trechos fracos ou nenhum; o prompt e o treino mandam recusar | "Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto." |
| Nenhum trecho com pontuação > 0 | o contexto vai como "(nenhum trecho encontrado)" | a mesma frase de recusa |
| Documento da base fora do padrão `# POL-NN — Nome` | `carregar_base()` lança `ValueError` com o nome do arquivo | erro na carga, antes de qualquer resposta |
| Fato do gabarito que não está no documento-fonte | o teste `test_todo_fato_esperado_esta_no_documento_fonte` falha | erro nos testes, antes do treino |
| Repositório privado no Colab | o `git clone` falha na célula 1 | instrução no notebook para subir o zip do projeto |
| Resposta longa ou cortada | `max_new_tokens=150` e limite de 3 frases no prompt | resposta curta; se cortada, a avaliação ainda procura os fatos |

## Critérios de aceitação e evidências

| Critério | Como o projeto atende | Evidência |
|---|---|---|
| Respostas baseadas na fonte fornecida | o contexto vem só da base e a resposta cita `[Fonte: POL-NN]` | métrica "cita a fonte"; `results/relatorio.md` |
| Redução clara de alucinação | comparação A × B × D com a taxa de alucinação e a recusa correta | tabela de métricas dos 4 modos |
| Relevância das respostas | busca com 100% de acerto no 1º trecho; gabarito por fatos | `results/avaliacao_busca.json`; "fatos cobertos" |
| Uso correto do contexto | prompt com regras explícitas e LoRA treinado no mesmo formato | `assistente/prompts.py`; `data/treino.jsonl` |
| Conectar IA com dados reais | os documentos da empresa entram no prompt a cada pergunta | `scripts/demo_contexto.py` |
| Melhoria de precisão | acerto na base do modo A comparado com B e D | tabela de métricas |
| Visão de sistema aplicável em empresas | base em Markdown versionada, ID por política, recusa padronizada e encaminhamento à área responsável | seções Arquitetura e Limitações |

## Estrutura do projeto

```
base_conhecimento/        8 políticas internas da empresa fictícia (POL-01 a POL-08)
assistente/
  base.py                 carga dos documentos e divisão em trechos por seção
  texto.py                normalização (acentos, stopwords, plural)
  busca.py                BM25 sem dependências
  prompts.py              estrutura de contexto: prompts de sistema, trechos, recusa
  dataset.py              gera treino.jsonl (formato chat da aula) e teste.jsonl
  avaliacao.py            classificação das respostas e métricas
  relatorio.py            tabela comparativa e exemplos em results/relatorio.md
data/
  perguntas.json          60 perguntas com gabarito (fonte e fatos), divididas em treino e teste
  treino.jsonl, teste.jsonl
notebooks/
  micro_capstone_assistente.ipynb   Colab: baseline, fine-tuning LoRA e avaliação dos 4 modos
scripts/                  demo do contexto, avaliação da busca e geração do dataset
tests/                    testes sem modelo (unittest)
results/                  avaliação da busca e, após o Colab, métricas, respostas e relatório
aula/                     material da aula M3D4 e o adapter de sentimento treinado em sala
```

## Limitações

- **Base pequena e fictícia:** 8 documentos e 34 trechos. Numa empresa real, a base teria centenas de documentos com versões, e seria preciso controlar a vigência e quem pode ver cada um.
- **Avaliação por fatos:** a métrica procura os fatos do gabarito no texto. Uma resposta certa com outras palavras, como "uma hora e meia" em vez de "90 minutos", pode contar como incompleta. Por isso o relatório mostra as respostas completas para conferência manual.
- **Modelo pequeno:** o Qwen 1.5B em 4 bits pode juntar trechos de documentos diferentes ou seguir mal a instrução de recusa. O LoRA melhora esse comportamento, mas não o garante.
- **Busca lexical:** perguntas com sinônimos que não estão nos documentos, como "carreta" em vez de "caminhão", podem recuperar o trecho errado.
- **Dataset pequeno:** 40 exemplos de treino escritos à mão. Em produção, os pares seriam gerados a partir dos documentos e revisados pelas áreas responsáveis.
