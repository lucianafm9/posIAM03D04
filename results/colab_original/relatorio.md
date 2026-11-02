# Resultado da avaliação

Gerado automaticamente pelo notebook a partir de `results/metricas.json` e `results/respostas.json`.

## Métricas por modo

| Métrica | A. Base sem contexto | B. Base com contexto (grounding) | C. LoRA sem contexto | D. LoRA com contexto |
|---|---:|---:|---:|---:|
| Acerto geral | 5.0% | 80.0% | 0.0% | 85.0% |
| Acerto (perguntas na base) | 7.1% | 85.7% | 0.0% | 78.6% |
| Fatos cobertos | 5.9% | 88.2% | 5.9% | 82.4% |
| Recusa correta (fora da base) | 0.0% | 66.7% | 0.0% | 100.0% |
| Taxa de alucinação | 95.0% | 15.0% | 95.0% | 15.0% |
| Cita a fonte | 0.0% | 64.3% | 0.0% | 92.9% |

## Exemplos de respostas

### A01 — Meu motorista chegou 40 minutos depois do fim da janela. Ele ainda pode entrar?

- **A. Base sem contexto** (incorreta): Desculpe, mas não posso fornecer informações sobre a situação do seu motorista ou verificar se ele pode entrar no terminal. Por favor, entre em contato diretamente com o seu motorista para obter mais detalhes. Se precisar de ajuda, você pode ligar para o nosso serviço de suporte ao cliente.
- **B. Base com contexto (grounding)** (incorreta): Sim, seu motorista pode entrar. No entanto, ele precisará de um novo agendamento, já que o agendamento original foi considerado perdido por excesso de tempo. [Fonte: POL-01]
- **C. LoRA sem contexto** (incorreta): Desculpe, mas não podemos permitir que ele entre no terminal. Por favor, informe a gerência imediatamente para que possamos resolver isso.
- **D. LoRA com contexto** (incorreta): Não, ele já foi considerado perdido. Precisa fazer um novo agendamento. [Fonte: POL-01]

### A03 — O que acontece com a transportadora que falta aos agendamentos sem cancelar?

- **A. Base sem contexto** (incorreta): No Porto Ventura Terminais, quando uma transportadora não pode realizar um agendamento, geralmente ocorre uma situação de sobrecarga na área de operações. Para resolver isso, os seguintes passos são realizados:  1. **Reposição da Transportadora**: A transportadora que estava programada para realizar o agendamento é reprogramada para outro dia ou horário.  2. **Cancelamento do Agendamento**: O agendamento original é cancelado e não será realizado no dia previsto.  3. **Aguarda Reativação**: Se a transportadora estiver disponível novamente, ela pode ser reprogramada para substituir a outra transportadora.  4. **Monitoramento Continuo**: As oper
- **B. Base com contexto (grounding)** (correta): As transportadoras que não comparecem aos agendamentos sem cancelar geram bloqueio do terminal por 48 horas a partir da terceira ocorrência no mesmo mês. [Fonte: POL-01]
- **C. LoRA sem contexto** (incorreta): A transportadora que não atende os agendamentos sem cancelar deve ser informada pelo gerente de operações ou pela central de agendamento. A transportadora deverá se comunicar para confirmar a data e horário da viagem e realizar as alterações necessárias no seu plano de carga. Se a transportadora não concluir as alterações dentro do prazo estipulado, o agendamento será cancelado automaticamente.
- **D. LoRA com contexto** (correta): As transportadoras que não comparecem sem cancelamento geram bloqueio do portal do transportador por 48 horas a partir da terceira ocorrência no mesmo mês. [Fonte: POL-01]

### A09 — Quantos dias de free time tem um contêiner de exportação?

- **A. Base sem contexto** (correta): Um contêiner de exportação geralmente possui uma duração de 30 a 45 dias para ser liberado após a sua chegada ao terminal. Este período pode variar dependendo da demanda e das operações no terminal. A liberação exata varia entre os diferentes terminais portuários.
- **B. Base com contexto (grounding)** (correta): 5 dias corridos sem cobrança antes da data prevista de atracação do navio.
- **C. LoRA sem contexto** (incorreta): Um contêiner de exportação geralmente possui 30 dias de free time. No entanto, isso pode variar dependendo da situação específica e das políticas do seu terminal. Por favor, consulte as regras específicas do seu terminal para obter informações mais precisas.
- **D. LoRA com contexto** (correta): 5 dias corridos sem cobrança antes da data prevista de atracação do navio.

### A14 — Funcionário em período de experiência pode fazer trabalho híbrido?

- **A. Base sem contexto** (incorreta): Sim, os funcionários podem realizar seu trabalho em um ambiente híbrido, combinando a presença física no local com atividades remotas ou online. Isso pode incluir aulas virtuais, consultas remotas, e até mesmo algumas tarefas que não exigem contato direto com o pessoal do estabelecimento. No entanto, a natureza exata desses trabalhos depende da função específica do cargo.
- **B. Base com contexto (grounding)** (recusa_indevida): Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto. [Fonte: POL-08]
- **C. LoRA sem contexto** (incorreta): Não, a experiência não permite trabalhar em horários flexíveis ou híbridos. O funcionamento no Porto Ventura terminais é rotativo e estágio dependendo da demanda.
- **D. LoRA com contexto** (correta): Não. O trabalho híbrido não se aplica às áreas operacionais nem ao período de experiência (primeiros 90 dias). [Fonte: POL-08]

### A15 — Qual o valor do auxílio-creche pago pela empresa?

- **A. Base sem contexto** (alucinacao): Desculpe, mas não tenho informações específicas sobre o valor do auxílio-criança no Porto Ventura Terminais. O melhor modo de obter essa informação seria por meio da própria empresa ou através de uma consulta direta ao seu departamento de recursos humanos. Se você tiver mais detalhes sobre a situação específica, como o nome da empresa ou o local onde ela está localizada, posso tentar buscar essas informações para você.
- **B. Base com contexto (grounding)** (recusa_correta): Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto. [Fonte: POL-XX]
- **C. LoRA sem contexto** (alucinacao): Desculpe, mas não tenho informações sobre esse benefício específico. O Auxílio-Creche é uma política que cada empresa pode adotar e pagar a seus empregados conforme sua situação financeira. Se você está interessado nesse benefício, recomendo entrar em contato com a empresa para obter mais detalhes.
- **D. LoRA com contexto** (recusa_correta): Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto. [Fonte: POL-XX]

### A18 — Quantos dias de licença-paternidade a empresa concede?

- **A. Base sem contexto** (alucinacao): A empresa concede 15 dias de licença-paternidade para os empregados que estejam à espera da chegada de uma criança.
- **B. Base com contexto (grounding)** (alucinacao): As férias podem ser divididas em até 3 períodos, sendo um deles de no mínimo 14 dias e os demais de no mínimo 5 dias cada. O pedido deve ser feito no Portal do Colaborador com 30 dias de antecedência. [Fonte: POL-08]
- **C. LoRA sem contexto** (alucinacao): A empresa concedeu 15 dias de licença-paternidade para os empregados.
- **D. LoRA com contexto** (recusa_correta): Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto. [Fonte: POL-XX]
