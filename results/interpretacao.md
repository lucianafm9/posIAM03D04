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
| B | 4 de 6 | 1 de 14 | recusa pouco quando deveria: o modelo base tende a "aproveitar" o contexto. A seção 7 mostra que, na A17 e na A18, a busca trouxe trechos com palavras em comum, mas sem a resposta, e o modelo respondeu com eles |
| C | 2 de 6 | 2 de 14 | o pior dos dois lados |
| D | **6 de 6** | **0 de 14** | recusa exatamente quando deve |

O dado mais importante deste critério: **D melhorou os dois lados ao mesmo tempo.** Se o LoRA tivesse só aprendido a "recusar mais", a recusa indevida teria subido. Ela caiu de 1 para 0: a A14, que B recusou mesmo com a resposta no contexto, D respondeu certo. Isso indica que o modelo aprendeu a **verificar se o contexto responde a pergunta**, que é o comportamento treinado: os exemplos de treino trazem o mesmo tipo de contexto da busca, às vezes relevante e às vezes não.

## 3. A relação entre alucinação e precisão

<!-- GRAFICO -->

### A taxa de alucinação sozinha engana

A taxa de alucinação calculada sobre as 20 perguntas mistura **duas decisões** do modelo:

1. **responder ou recusar;**
2. **quando responde, acertar ou errar.**

Um modelo que recusasse tudo teria 0% de alucinação, e também 0% de utilidade: acertaria só as 6 perguntas fora da base e nenhuma das 14 que o funcionário precisa ver respondidas. Por isso a alucinação só tem sentido lida **junto** com a precisão e a cobertura. A tabela abaixo separa as duas decisões:

<!-- TABELA_PRECISAO -->

- **Precisão das respostas dadas:** quando o modo responde, quantas vezes acerta. É o que o funcionário experimenta.
- **Alucinação nas respostas dadas:** quando o modo responde, quantas vezes afirma algo errado (inventa ou usa um trecho que não responde).
- **Cobertura da base:** das 14 perguntas que têm resposta, quantas foram respondidas certo.

A alucinação total é o produto das duas decisões: *proporção de perguntas respondidas × alucinação nas respostas dadas*.

| Modo | Responde | × Erra quando responde | = Erro afirmado no total |
|---|---:|---:|---:|
| A | 60% | 67% | 40% (8/20) |
| B | 75% | 20% | 15% (3/20) |
| C | 80% | 75% | 60% (12/20) |
| D | 70% | 7% | **5% (1/20)** |

### O que a relação mostra em cada modo

- **A e C: precisão e alucinação não estão em equilíbrio, as duas estão no pior ponto.** A precisão é 0% porque o conhecimento não existe no modelo. Nesse cenário, o único jeito de alucinar menos é responder menos: A recusa 8 vezes e erra 8; C recusa só 4 e erra 12. A diferença entre A e C não é de conhecimento (os dois sabem zero), é de **disposição para responder**, e o LoRA aumentou essa disposição sem dar o conhecimento.
- **A → B: o grounding move as duas métricas na direção certa ao mesmo tempo.** A precisão vai de 0% para 80%, e a alucinação nas respostas dadas cai de 67% para 20%. Não há troca entre as duas, porque o que mudou foi a **origem da resposta**: ela deixa de vir da memória do modelo e passa a vir do documento.
- **B → D: o LoRA melhora a calibração, isto é, a decisão de quando responder.** D respondeu exatamente 14 vezes, o mesmo número de perguntas que têm resposta na base, e acertou 13. B errou a decisão nos dois sentidos: respondeu 2 perguntas que deveria recusar e recusou 1 que deveria responder. Com a decisão certa, a precisão sobe para 93% e a alucinação nas respostas dadas cai para 7%.

Em resumo, **o grounding resolve a precisão, e o LoRA resolve a calibração.** As duas camadas juntas levam o erro afirmado de 40% (A) para 5% (D).

### Nem todo erro custa igual: perguntas de risco alto

Das 14 perguntas da base, 5 tratam de temas em que uma resposta errada pode causar acidente, multa ou responsabilização: EPI, velocidade no pátio, carga perigosa, controle de acesso e registro de avaria (campo `risco` em `data/perguntas.json`). A tabela mostra como cada modo respondeu a essas 5; ⚠️ marca as respostas erradas afirmadas como certas.

<!-- TABELA_RISCO -->

- **C** afirma, por exemplo, que carga perigosa pode ficar só 24 horas no pátio IMO e que emprestar a credencial "não traz nenhuma alteração". São erros que levam a uma ação errada.
- **B** acertou as 5.
- **D**, o melhor modo no geral, errou justamente uma delas: na A07, listou o EPI geral e omitiu o protetor auricular exigido no cais.

Isso mostra que **93% de precisão no geral não garante 100% nos temas críticos**. Com 5 perguntas de risco alto, a diferença entre B e D é de uma resposta e não permite dizer que um modo é mais seguro que o outro. A conclusão que vale é que temas de segurança precisam de uma proteção adicional, independente da precisão média (ver seção 4).

### Efeito de cada camada

A seção 6 conta as perguntas que passaram a ter (ou deixaram de ter) resposta útil: **o grounding vale +12, o LoRA sobre o grounding vale +3 e o LoRA sem grounding vale −2.**

1. **Grounding é o que traz a precisão e elimina a invenção.** É a camada que conecta a IA aos dados da empresa.
2. **O fine-tuning ajusta o comportamento (calibração, citação, formato) e só ajuda em cima do grounding.** Sozinho, aumenta a disposição de responder sem dar o conhecimento, e por isso piora a alucinação.
3. **Na arquitetura recomendada (D), os erros restantes não são invenções.** São uma escolha errada entre trechos parecidos (A07) e fontes anexadas às recusas, ambos tratáveis com mais exemplos de treino e uma guarda de saída.

## 4. Implicações para um ambiente corporativo

**1. A arquitetura: grounding é obrigatório; fine-tuning é opcional e vem depois.**
O conhecimento da empresa deve ficar na base de documentos, não nos pesos do modelo. O modo C mostra o risco do caminho contrário: um modelo treinado com exemplos da empresa, mas sem acesso aos documentos, responde com a confiança de quem conhece a empresa e com a precisão de quem não conhece. O fine-tuning se justifica para padronizar o comportamento (citar, recusar, ser objetivo), sempre sobre o grounding.

**2. O indicador certo não é só a taxa de alucinação.**
Um painel de produção precisa de, no mínimo, quatro números lidos juntos:
- **precisão das respostas dadas:** a confiança do funcionário no que lê;
- **cobertura:** quanto da base o assistente consegue responder;
- **taxa de recusa:** quanto o funcionário fica sem resposta;
- **erro afirmado em temas críticos:** o risco operacional.

Como a seção anterior mostrou, cortar a alucinação recusando tudo melhora um indicador e destrói os outros.

**3. Errar custa mais do que recusar, e o custo depende do tema.**
- Uma **recusa** custa tempo: o funcionário pergunta à área responsável.
- Uma **resposta errada afirmada como certa** pode virar ação: um caminhão que perde a janela, um contêiner de carga perigosa fora do prazo, alguém sem protetor auricular no cais.

Por isso, num ambiente real, os temas devem ser classificados por risco. Nos de risco alto (SSMA, carga perigosa, acesso, aduaneiro), a resposta deve mostrar o trecho literal da política com o link para o documento e indicar a área responsável. Se a guarda de saída não validar a fonte, o assistente recusa e encaminha.

**4. As recusas são um sinal de lacuna na documentação.**
As 6 perguntas fora da base (auxílio-creche, licença-paternidade, devolução de notebook, telefone do despachante) são dúvidas plausíveis de funcionários para as quais não existe política escrita. Em produção, registrar as perguntas recusadas gera uma lista priorizada do que o RH e as áreas precisam documentar. O assistente passa a melhorar a própria base.

**5. Manutenção sem retreino, com teste de regressão.**
Uma política alterada exige só editar o documento e reindexar a busca. Não é preciso retreinar o modelo. O conjunto de teste com gabarito e os scripts deste projeto (`avaliar_busca.py`, `reavaliar.py`) funcionam como teste de regressão: antes de publicar uma versão nova da base ou do modelo, roda-se a avaliação e compara-se com a anterior, como foi feito aqui ao corrigir o avaliador.

**6. Rastreabilidade: a citação precisa ser verificada, não só exibida.**
Citar a fonte é o que permite ao funcionário e à auditoria conferir a resposta. Mas o modelo também anexou fontes inexistentes às recusas (ADM-05, POL-XX). Num sistema real, a citação só pode ser mostrada se o ID estiver entre os trechos efetivamente recuperados. Caso contrário, uma citação falsa dá credibilidade a uma resposta errada.

**7. Invenções podem virar risco de segurança da informação.**
Sem grounding, o modelo inventou um telefone ("0800 721 3456") e sites ("www.portoventura.pt", "www.portoventura.com.br"). Num assistente interno, um contato inventado pode levar um funcionário a ligar ou entrar num site que não pertence à empresa, uma porta para fraude e engenharia social. É mais um motivo para não colocar um modelo sem grounding diante dos funcionários.

**8. Custo e privacidade.**
O modelo usado tem 1,5 bilhão de parâmetros, roda quantizado em 4 bits numa GPU T4 de 15 GB e responde em segundos. Isso permite hospedar o assistente na infraestrutura da própria empresa, sem enviar documentos internos a serviços externos, o que importa para a LGPD e para informações comerciais. Em produção, a busca também precisaria filtrar os documentos pelo perfil de quem pergunta, porque nem toda política pode ser vista por todos.

**9. O que este teste ainda não garante.**
São 20 perguntas, 5 delas de risco alto, numa base de 8 documentos. Os resultados indicam a direção com segurança: grounding × sem grounding é uma diferença grande e consistente. As diferenças pequenas, como B × D na base, ainda não estão comprovadas. Antes de uma implantação, o conjunto de teste deveria crescer por área, com perguntas reais de funcionários e uma amostra das respostas revisada por pessoas a cada nova versão.
