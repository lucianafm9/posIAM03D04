## 2. Como cada modo se comporta em cada critério, e por quê

Antes dos números, um ponto de leitura: com 20 perguntas, cada pergunta vale 5 pontos percentuais no geral e 7 pontos nas 14 perguntas da base. Por isso as conclusões abaixo se apoiam nas diferenças grandes e no **tipo de erro** de cada modo, identificado na revisão manual, mais do que em diferenças de uma pergunta.

### Critério 1 — Respostas baseadas na fonte

| Modo | Comportamento | Por quê |
|---|---|---|
| A e C | nunca citam fonte | sem contexto não há documento para citar, e o prompt sem grounding não pede citação |
| B | cita a fonte certa em 8 de 14; responde sem fonte 4 vezes e cita a fonte errada 1 vez (A07, POL-08 no lugar de POL-03) | a regra de citar está só no prompt de sistema, e o modelo base a segue de forma irregular. Na A07, a resposta veio do 1º trecho (POL-03, EPI), mas ele citou o 2º (POL-08, banco de horas), que não tinha relação com a pergunta |
| D | cita a fonte certa em 13 de 14 | os 30 exemplos de treino com resposta terminam em `[Fonte: POL-NN]`; o LoRA fixou o formato |

**Efeito colateral nos dois modos com contexto:** todas as recusas de B e D vêm com uma fonte anexada que não faz sentido, como `[Fonte: POL-XX]` ou `[Fonte: ADM-05]` (documento que não existe). A causa é o prompt de sistema, que manda *sempre* terminar com a fonte, inclusive quando a resposta é a recusa. O LoRA não corrigiu isso porque o prompt continuou o mesmo. A correção proposta é uma guarda de saída que remove a fonte das recusas e só aceita IDs presentes nos trechos recuperados.

### Critério 2 — Redução de alucinação

A taxa automática de alucinação é igual em B e D (15%), mas a revisão manual mostra que **a natureza do erro é diferente** em cada modo:

| Tipo de erro (revisão manual) | A | B | C | D |
|---|---:|---:|---:|---:|
| Inventou informação que não existe na base | 8 | 0 | 12 | 0 |
| Usou um trecho da base que não responde a pergunta | 0 | 3 | 0 | 1 |
| Resposta vaga, sem fato concreto | 4 | 0 | 2 | 0 |

- **Grounding zera a invenção (A → B: de 8 para 0).** Quando a resposta está no contexto, o modelo copia o trecho em vez de gerar a partir da memória paramétrica. Como a empresa é fictícia, essa memória não tem nada de verdadeiro sobre ela, e tudo o que o modelo "lembra" é invenção plausível: 24 horas no pátio IMO, 30 a 45 dias de free time, 15 dias de licença-paternidade.
- **O erro que sobra com grounding é usar mal o contexto.** B não inventa números, mas responde com o trecho errado: na A18 (licença-paternidade), a busca trouxe três trechos fracos (pontuação 3,6 ou menos), e o modelo respondeu com o 3º, as regras de férias do POL-08. Na A17 (devolução de notebook), o 1º trecho fala do notebook fornecido no trabalho híbrido, e o modelo respondeu com o 2º, o prazo de 24 horas para comunicar a perda da credencial (POL-02).
- **O LoRA reduz esse uso indevido (B → D: de 3 para 1)** porque foi treinado com 10 exemplos em que o contexto recuperado *não* respondia a pergunta e o alvo era a recusa.
- **O LoRA sem contexto aumenta a invenção (A → C: de 8 para 12).** O adapter aprendeu um estilo: respostas curtas, afirmativas e com um fato concreto, porque todo alvo de treino era assim. Sem contexto, não há fato para copiar, e o modelo preenche o formato com fatos plausíveis: "0800 721 3456", "navios entre 105 e 120 metros", "R$ 20,00 no Rio Grande do Sul". Ao mesmo tempo, ele perdeu metade das recusas genéricas que o modelo base fazia (de 8 para 4), porque a única recusa que aprendeu está ligada ao formato com contexto.

### Critério 3 — Relevância e precisão

| Modo | Acerto na base (automático → manual) | Por quê |
|---|---|---|
| A e C | 0 de 14 → 0 de 14 | o conhecimento não existe nos pesos do modelo. 30 exemplos e 3 épocas de LoRA não bastam para "decorar" 8 políticas, e as perguntas de teste são diferentes das de treino |
| B | 12 de 14 → 12 de 14 | a busca pôs o documento certo no contexto em 14 de 14 perguntas (`results/avaliacao_busca.json`). Por isso **todo erro de B e D na base é de geração, não de recuperação** |
| D | 11 de 14 → 13 de 14 | as respostas de D são as mais curtas (17 palavras em média). A01 ("Não, ele já foi considerado perdido") e A04 ("1 mês") estão certas, mas sem o fato literal do gabarito, e o avaliador automático as marca como erradas |

O único erro real de D é a A07: a pergunta era sobre a proteção **extra** do cais (protetor auricular), e D listou o EPI geral do pátio. Os dois estão na mesma seção do POL-03, e o modelo pegou a lista errada. É um erro de precisão entre trechos vizinhos, não de invenção.

### Critério 4 — Uso correto do contexto

O uso correto do contexto tem dois lados: **recusar o que não está lá** e **não recusar o que está lá**.

| Modo | Recusa correta (fora da base) | Recusa indevida (na base) | Leitura |
|---|---:|---:|---|
| A | 4 de 6 | 4 de 14 | recusa muito, dos dois lados. As recusas são genéricas ("não tenho informações") e às vezes vêm com contatos inventados, como o site da A19 |
| B | 4 de 6 | 1 de 14 | recusa pouco quando deveria: o modelo base tende a "aproveitar" o contexto. A seção 5 mostra que, na A17 e na A18, a busca trouxe trechos com palavras em comum, mas sem a resposta, e o modelo respondeu com eles |
| C | 2 de 6 | 2 de 14 | o pior dos dois lados |
| D | **6 de 6** | **0 de 14** | recusa exatamente quando deve |

O dado mais importante deste critério: **D melhorou os dois lados ao mesmo tempo.** Se o LoRA tivesse só aprendido a "recusar mais", a recusa indevida teria subido. Ela caiu de 1 para 0: a A14, que B recusou mesmo com a resposta no contexto, D respondeu certo. Isso indica que o modelo aprendeu a **verificar se o contexto responde a pergunta**, que é o comportamento treinado: os exemplos de treino trazem o mesmo tipo de contexto da busca, às vezes relevante e às vezes não.

### Acerto × alucinação: amarrando os resultados

| Modo | Respostas úteis (manual) | Invenção + uso indevido do contexto | Leitura |
|---|---:|---:|---|
| A | 4/20 | 8/20 | não sabe nada da empresa; quando responde, inventa |
| C | 2/20 | 12/20 | o fine-tuning deixou o modelo mais confiante, não mais informado |
| B | 16/20 | 3/20 | o grounding traz o conhecimento; sobra o erro de usar trecho irrelevante |
| D | **19/20** | **1/20** | o LoRA ensina a usar o contexto: citar, recusar e não recusar à toa |

A seção 4 resume o efeito de cada camada em número de perguntas: **o grounding vale +12 respostas úteis, o LoRA sobre o grounding vale +3, e o LoRA sem grounding vale −2.** Ou seja:

1. **Grounding é o que traz a precisão e elimina a invenção.** É a camada que conecta a IA aos dados da empresa.
2. **O fine-tuning é um ajuste de comportamento, e só ajuda em cima do grounding.** Sozinho, piora a alucinação.
3. **Na arquitetura recomendada (D), os erros restantes não são invenções.** São uma escolha errada entre trechos parecidos (A07) e fontes anexadas às recusas, ambos tratáveis com mais exemplos de treino e uma guarda de saída.
