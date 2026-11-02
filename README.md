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

Ajustes que a GPU T4 do Colab exigiu, porque ela não suporta `bfloat16` no treino:

- o modelo é carregado com `dtype=torch.float32`, já que o Qwen vem em `bfloat16` por padrão nas versões atuais do `transformers`;
- o `SFTConfig` usa `bf16=False` e `fp16=False`, porque o `trl` atual liga o `bf16` por padrão.

Sem esses ajustes, o `trainer.train()` falha com `gemm input type at::BFloat16 and output type float is only supported for CUDA devices with compute capability 8.0 or higher`. A aula não teve o problema porque usava versões mais antigas das bibliotecas.

**Dataset.** São 60 perguntas escritas à mão, cada uma com gabarito:

- **treino:** 40 perguntas, sendo 30 na base e 10 fora da base;
- **teste:** 20 perguntas diferentes das de treino, sendo 14 na base e 6 fora da base.

O contexto de cada exemplo de treino vem da mesma busca usada na inferência. Assim, nas perguntas fora da base o modelo vê trechos que parecem relacionados mas não respondem, e aprende a recusar mesmo assim.

**Treino executado.** No Colab, com GPU T4, foram 30 passos em 3 épocas, com 1 min 22 s de treino. O LoRA treinou 2.179.072 parâmetros, 0,14% do modelo. O loss caiu de forma contínua:

| Passo | 5 | 10 | 15 | 20 | 25 | 30 |
|---|---:|---:|---:|---:|---:|---:|
| Training loss | 2,183 | 2,064 | 1,909 | 1,751 | 1,664 | 1,579 |

O valor absoluto é alto porque, como na aula, o loss é calculado sobre a sequência inteira, incluindo o prompt de sistema e os trechos do contexto. Esses tokens são longos e o modelo não tem como prevê-los. O que importa é a tendência de queda e o efeito medido na avaliação: recusa e citação da fonte. Um próximo passo seria calcular o loss só sobre a resposta (`assistant_only_loss=True`).

O notebook executado, com todas as saídas, está em `notebooks/micro_capstone_assistente_executado.ipynb`. As métricas impressas nele são as da primeira versão do avaliador (ver "Revisão do avaliador" em Resultados).

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

Os fatos são trechos curtos com variações aceitas, como `30 minutos|30 min|meia hora`, comparados por palavra inteira. Um teste garante que todo fato do gabarito está escrito no documento-fonte, para o gabarito não ter erro.

Conta como recusa tanto a frase padrão dos modos com contexto quanto as recusas genéricas do modelo sem contexto, como "não tenho informações sobre...". Dizer que não sabe não é alucinação.

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

### Modelo (executado no Colab, GPU T4)

Conjunto de teste: 20 perguntas, sendo 14 na base e 6 fora da base. Geração determinística (`do_sample=False`).

| Métrica | A. Base sem contexto | B. Base com contexto | C. LoRA sem contexto | D. LoRA com contexto |
|---|---:|---:|---:|---:|
| Acerto geral | 20,0% | 80,0% | 10,0% | **85,0%** |
| Acerto (perguntas na base) | 0,0% | **85,7%** | 0,0% | 78,6% |
| Fatos cobertos | 0,0% | **88,2%** | 5,9% | 82,4% |
| Recusa correta (fora da base) | 66,7% | 66,7% | 33,3% | **100,0%** |
| Taxa de alucinação | 60,0% | **15,0%** | 75,0% | **15,0%** |
| Cita a fonte certa | 0,0% | 57,1% | 0,0% | **92,9%** |

> **Relatório detalhado:** [`results/relatorio.md`](results/relatorio.md) organiza as métricas por **critério de aceitação** (baseado na fonte, redução de alucinação, relevância e uso do contexto). Para cada critério, mostra como cada modo se comporta e por quê, com contagens absolutas, revisão manual do tipo de erro, resultado pergunta a pergunta, o que mudou entre os modos e o que a busca entregou nas perguntas fora da base.

Distribuição das respostas:

| Categoria | A | B | C | D |
|---|---:|---:|---:|---:|
| Correta | 0 | 12 | 0 | 11 |
| Incompleta | 0 | 0 | 1 | 0 |
| Incorreta (na base, sem nenhum fato) | 10 | 1 | 11 | 3 |
| Recusa indevida | 4 | 1 | 2 | 0 |
| Recusa correta | 4 | 4 | 2 | 6 |
| Alucinação (fora da base) | 2 | 2 | 4 | 0 |

A taxa de alucinação automática é igual em B e D, mas a revisão manual mostra que o tipo de erro é diferente em cada modo:

| Tipo de erro (revisão manual) | A | B | C | D |
|---|---:|---:|---:|---:|
| Inventou informação que não existe na base | 8 | 0 | 12 | 0 |
| Usou um trecho da base que não responde a pergunta | 0 | 3 | 0 | 1 |
| Resposta vaga, sem fato concreto ou sem a regra | 4 | 0 | 4 | 0 |
| **Respostas úteis** (corretas + recusas corretas) | 4 | 16 | 2 | **19** |

Arquivos: `results/metricas.json`, `results/respostas.json` (as 80 respostas completas), `results/revisao_manual.json` (o rótulo e a justificativa de cada resposta) e `results/relatorio.md`.

**Revisão do avaliador.** Ao ler as 80 respostas, encontrei duas falhas na primeira versão do avaliador automático, a que rodou no Colab:

1. A comparação de fatos era por trecho de texto. Por isso "30 a **45 dias**" contou como acerto do fato "**5 dias**" (A09, modo A). Agora a comparação é por palavra inteira.
2. Só a frase padrão contava como recusa. Por isso "não tenho informações sobre o auxílio-creche" contou como alucinação nos modos sem contexto. Agora as recusas genéricas também contam.

Como o avaliador não depende do modelo, `python scripts/reavaliar.py` reclassifica as respostas salvas sem rodar o Colab de novo. Os modos B e D não mudaram. O modo A foi de 5% de acerto e 95% de alucinação para 20% e 60%, e o modo C de 0% e 95% para 10% e 75%. Com o avaliador antigo, a diferença a favor do grounding parecia maior do que é; os números da tabela acima são os corrigidos. A avaliação original está guardada em `results/colab_original/`, e os dois casos viraram testes em `tests/test_assistente.py`.

## Análise comparativa

### Sem grounding (A): o modelo não sabe e, na maioria das vezes, inventa

Sem contexto, o modelo não acertou nenhuma das 14 perguntas da base. Em 10 delas respondeu sem nenhum fato correto, na maioria **inventando** um prazo ou uma regra plausível:

- "pelo menos 30 dias de antecedência" para o credenciamento (o certo é 3 dias úteis);
- "não pode permanecer por mais de 24 horas" no pátio IMO (o certo é 5 dias);
- "30 a 45 dias" de free time de exportação (o certo é 5 dias);
- "Sim, os funcionários podem realizar seu trabalho em um ambiente híbrido" para quem está em experiência (o certo é não).

Nas outras 4, ele disse que não tinha a informação. Essa honestidade aparece também nas perguntas fora da base (4 de 6 recusadas), mas não ajuda o funcionário: o modo A **não consegue responder nada** sobre a empresa. Quando arrisca, inventa, como em "15 dias de licença-paternidade".

### Grounding (A → B): a maior parte da melhoria vem do contexto

Com os trechos da base no prompt, o mesmo modelo, sem nenhum treino, foi de 0% para **85,7%** de acerto nas perguntas da base. A alucinação caiu de 60% para **15%**. Essa é a evidência central do projeto: **conectar a IA aos documentos é o que traz a precisão**.

As falhas de B são as previstas para um modelo pequeno:

- **Usa contexto que não responde a pergunta.** Na A18 (licença-paternidade), a busca trouxe o trecho de férias, e o modelo respondeu com as regras de férias. Na A17 (devolução de notebook), respondeu com a regra de perda de credencial.
- **Recusa o que está no contexto.** Na A14 (híbrido na experiência), a resposta estava no trecho, e mesmo assim ele recusou.
- **Cita a fonte de forma irregular.** Citou a fonte certa em 57% das respostas da base, e na A07 a resposta estava certa mas citou POL-08 no lugar de POL-03.

### Fine-tuning com grounding (B → D): o LoRA ensina o comportamento

O LoRA, treinado com os mesmos hiperparâmetros da aula em 40 exemplos, mudou o **comportamento** do modelo:

- **recusa correta** nas perguntas fora da base: de 66,7% para **100%**, com zero alucinações fora da base;
- **citação da fonte certa:** de 57,1% para **92,9%**;
- respostas mais curtas e diretas, no formato do treino.

O custo foi uma pequena queda no acerto automático das perguntas da base: de 85,7% para 78,6%, ou seja, 11 em vez de 12. Revisando as 3 respostas marcadas como incorretas em D:

| Caso | Resposta de D | Revisão manual |
|---|---|---|
| A01 | "Não, ele já foi considerado perdido. Precisa fazer um novo agendamento. [Fonte: POL-01]" | correta, mas não cita os 30 minutos que o gabarito exige |
| A04 | "1 mês. [Fonte: POL-02]" | equivalente aos 30 dias do documento |
| A07 | lista o EPI geral (capacete, colete, botina, óculos) | **errada**: a pergunta era sobre o protetor auricular exigido no cais |

Na revisão manual, D acerta 13 das 14 perguntas da base e recusa as 6 de fora, um acerto de **95%**. A única resposta errada (A07) usou um trecho certo da base para a pergunta errada, sem inventar informação. B, na mesma revisão, continua com as duas alucinações (A17 e A18) e com a resposta contraditória da A01 ("Sim, seu motorista pode entrar. No entanto, ele precisará de um novo agendamento").

### LoRA sem contexto (C): fine-tuning não substitui grounding

C foi o **pior modo**, com 75% de alucinação. O adapter aprendeu a responder de forma curta e confiante, mas não aprendeu os fatos da base: 30 exemplos e 3 épocas não bastam para "decorar" 8 políticas. Sem o contexto, essa confiança vira invenção:

- "o despachante aduaneiro parceiro tem o número de contato 0800 721 3456";
- "o terminal recebe naves com comprimentos entre 105 e 120 metros";
- "Se você emprestar sua credencial, não haverá nenhuma alteração na sua situação".

C também recusou menos que o modelo base (33% contra 67%).

### Conclusão

| Pergunta | Resposta dos dados |
|---|---|
| O grounding reduz a alucinação? | Sim: de 60% (A) para 15% (B e D), e para 0% nas perguntas fora da base com o LoRA (D) |
| O grounding melhora a precisão? | Sim: de 0% para 78,6–85,7% de acerto nas perguntas da base |
| E o fine-tuning? | Ensina o **comportamento** (recusar, citar a fonte, ser objetivo), não o **conhecimento** |
| Fine-tuning sem grounding funciona? | Não: aumenta a alucinação, porque o modelo fica mais confiante sem saber mais |

Para uma empresa, a arquitetura recomendada é a do modo D. A base fica versionada e é recuperada a cada pergunta, o que permite atualizar uma política sem retreinar o modelo. O fine-tuning entra só para padronizar o comportamento.

### Próximos passos identificados na avaliação

- **Validar a citação na saída:** o modelo às vezes coloca uma fonte depois da recusa, inclusive inexistente, como "[Fonte: POL-XX]" e "[Fonte: ADM-05]". Uma guarda de saída removeria a fonte das recusas e só aceitaria IDs que estão nos trechos recuperados.
- **Limiar de relevância na busca não basta sozinho:** a pontuação BM25 do 1º trecho vai de 3,6 a 15,1 nas perguntas da base e de 0 a 11,7 nas de fora. As faixas se sobrepõem: "Qual o valor da diária de armazenagem de um contêiner reefer?" pontua 11,7 porque o documento de armazenagem fala de reefer, mas não traz valores. Por isso a decisão de recusar precisa ficar com o modelo, que é o que o LoRA ensinou. Um limiar baixo serviria só como filtro adicional.
- **Mais exemplos de treino** com perguntas que exigem escolher entre trechos parecidos, como EPI geral × EPI do cais, para corrigir erros como o A07.

## Exemplos de perguntas e respostas

Respostas reais do conjunto de teste (trechos; as respostas completas estão em `results/respostas.json`).

**A09 — Quantos dias de free time tem um contêiner de exportação?** Esperado: 5 dias corridos (POL-04).

| Modo | Resposta | Avaliação |
|---|---|---|
| A | "Um contêiner de exportação geralmente possui uma duração de 30 a 45 dias para ser liberado..." | incorreta (inventou) |
| B | "5 dias corridos sem cobrança antes da data prevista de atracação do navio." | correta, sem fonte |
| C | "Um contêiner de exportação geralmente possui 30 dias de free time..." | incorreta (inventou) |
| D | "5 dias corridos sem cobrança antes da data prevista de atracação do navio." | correta, sem fonte |

**A14 — Funcionário em período de experiência pode fazer trabalho híbrido?** Esperado: não, primeiros 90 dias (POL-08).

| Modo | Resposta | Avaliação |
|---|---|---|
| A | "Sim, os funcionários podem realizar seu trabalho em um ambiente híbrido..." | incorreta (inventou) |
| B | "Não encontrei essa informação na base de conhecimento..." | recusa indevida |
| C | "Não, a experiência não permite trabalhar em horários flexíveis ou híbridos..." | incorreta (não cita os 90 dias) |
| D | "Não. O trabalho híbrido não se aplica às áreas operacionais nem ao período de experiência (primeiros 90 dias). [Fonte: POL-08]" | correta |

**A03 — O que acontece com a transportadora que falta aos agendamentos sem cancelar?** Esperado: bloqueio de 48 h a partir da 3ª ocorrência no mês (POL-01).

| Modo | Resposta | Avaliação |
|---|---|---|
| A | "...geralmente ocorre uma situação de sobrecarga na área de operações. Para resolver isso, os seguintes passos..." | incorreta (inventou) |
| B | "...geram bloqueio do terminal por 48 horas a partir da terceira ocorrência no mesmo mês. [Fonte: POL-01]" | correta |
| D | "...geram bloqueio do portal do transportador por 48 horas a partir da terceira ocorrência no mesmo mês. [Fonte: POL-01]" | correta |

**A18 — Quantos dias de licença-paternidade a empresa concede?** Fora da base: o certo é recusar.

| Modo | Resposta | Avaliação |
|---|---|---|
| A | "A empresa concede 15 dias de licença-paternidade para os empregados..." | alucinação |
| B | "As férias podem ser divididas em até 3 períodos..." (usou um trecho que não responde) | alucinação |
| C | "A empresa concedeu 15 dias de licença-paternidade para os empregados." | alucinação |
| D | "Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto." | recusa correta |

**A19 — Qual o telefone do despachante aduaneiro parceiro do terminal?** Fora da base.

| Modo | Resposta | Avaliação |
|---|---|---|
| A | "Desculpe, mas não tenho informações sobre a localização exata ou contato específico..." | recusa correta |
| B | "Não encontrei essa informação na base de conhecimento..." | recusa correta |
| C | "O despachante aduaneiro parceiro do Terminal do Porto Ventura tem o número de contato 0800 721 3456." | alucinação |
| D | "Não encontrei essa informação na base de conhecimento..." | recusa correta |

## Tratamento de erros

| Situação | Como é tratada | O que o usuário vê |
|---|---|---|
| Pergunta sem relação com a base | a busca devolve trechos fracos ou nenhum; o prompt e o treino mandam recusar | "Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto." |
| Nenhum trecho com pontuação > 0 | o contexto vai como "(nenhum trecho encontrado)" | a mesma frase de recusa |
| Documento da base fora do padrão `# POL-NN — Nome` | `carregar_base()` lança `ValueError` com o nome do arquivo | erro na carga, antes de qualquer resposta |
| Fato do gabarito que não está no documento-fonte | o teste `test_todo_fato_esperado_esta_no_documento_fonte` falha | erro nos testes, antes do treino |
| Repositório privado no Colab | o `git clone` falha na célula 1 | instrução no notebook para subir o zip do projeto |
| Resposta longa ou cortada | `max_new_tokens=150` e limite de 3 frases no prompt | resposta curta; se cortada, a avaliação ainda procura os fatos |
| GPU sem suporte a `bfloat16` (T4) | modelo carregado em `float32` e `bf16=False` no `SFTConfig` | o treino roda; sem o ajuste, `RuntimeError` no `trainer.train()` |
| Erro no avaliador descoberto depois da execução | `scripts/reavaliar.py` reclassifica as respostas salvas | métricas atualizadas sem rodar o modelo de novo; original em `results/colab_original/` |

## Critérios de aceitação e evidências

| Critério | Como o projeto atende | Evidência |
|---|---|---|
| Respostas baseadas na fonte fornecida | o contexto vem só da base e a resposta cita `[Fonte: POL-NN]` | cita a fonte certa em 92,9% das respostas da base (modo D) |
| Redução clara de alucinação | comparação dos 4 modos com e sem grounding | alucinação de 60% (A) para 15% (D); 0 alucinações fora da base em D |
| Relevância das respostas | busca com 100% de acerto no 1º trecho; gabarito por fatos | `results/avaliacao_busca.json`; fatos cobertos de 0% (A) para 82–88% (B e D) |
| Uso correto do contexto | prompt com regras explícitas e LoRA treinado no mesmo formato | recusa correta de 100% em D; revisão manual dos erros na Análise comparativa |
| Conectar IA com dados reais | os documentos da empresa entram no prompt a cada pergunta | `scripts/demo_contexto.py` |
| Melhoria de precisão | acerto na base do modo A comparado com B e D | de 0% (A) para 85,7% (B) e 78,6% (D); 95% na revisão manual de D |
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
  relatorio.py            relatório por critério: matriz critério × modo, revisão manual, transições
data/
  perguntas.json          60 perguntas com gabarito (fonte e fatos), divididas em treino e teste
  treino.jsonl, teste.jsonl
notebooks/
  micro_capstone_assistente.ipynb             Colab: baseline, fine-tuning LoRA e avaliação dos 4 modos
  micro_capstone_assistente_executado.ipynb   o mesmo notebook com as saídas da execução na T4
scripts/                  demo do contexto, avaliação da busca, geração do dataset e reavaliação
tests/                    testes sem modelo (unittest)
results/
  avaliacao_busca.json    acerto da busca (local)
  respostas.json          as 80 respostas do Colab (20 perguntas x 4 modos) com a avaliação
  metricas.json           métricas por modo
  relatorio.md            relatório detalhado por critério de avaliação (gerado)
  revisao_manual.json     rótulo manual e justificativa de cada uma das 80 respostas
  interpretacao.md        análise escrita, incluída no relatorio.md
  colab_original/         avaliação original do Colab, antes da correção do avaliador
aula/                     material da aula M3D4 e o adapter de sentimento treinado em sala
```

## Limitações

- **Base pequena e fictícia:** 8 documentos e 34 trechos. Numa empresa real, a base teria centenas de documentos com versões, e seria preciso controlar a vigência e quem pode ver cada um.
- **Avaliação por fatos:** a métrica procura os fatos do gabarito no texto. Uma resposta certa com outras palavras pode contar como incorreta: foi o caso de "1 mês" no lugar de "30 dias" (A04, modo D). Por isso o README traz a revisão manual dos erros, e as respostas completas ficam em `results/respostas.json`.
- **Conjunto de teste pequeno:** com 20 perguntas, cada resposta vale 5 pontos percentuais. A diferença entre B e D no acerto da base (85,7% contra 78,6%) é de uma única pergunta. Já as diferenças de recusa e de alucinação entre A, B e D são grandes e consistentes.
- **Uma execução:** a geração é determinística, mas o treino do LoRA não foi repetido com outras sementes.
- **Modelo pequeno:** o Qwen 1.5B em 4 bits pode juntar trechos de documentos diferentes ou seguir mal a instrução de recusa. O LoRA melhora esse comportamento, mas não o garante.
- **Busca lexical:** perguntas com sinônimos que não estão nos documentos, como "carreta" em vez de "caminhão", podem recuperar o trecho errado.
- **Dataset pequeno:** 40 exemplos de treino escritos à mão. Em produção, os pares seriam gerados a partir dos documentos e revisados pelas áreas responsáveis.
