# CSA Exaustão — plataforma técnica

## O que esta versão preserva
- Layout visual baseado no painel anterior: cartões, gráficos simples, acordeões e textos explicativos.
- Dados existentes do Supabase: nenhum registro técnico é atualizado pela migration.
- Guararapes 2026 continua disponível; registros antigos recebem contexto de shopping/ano apenas em memória quando essas colunas não existirem.

## O que foi corrigido
- Formulário manual integral com todos os campos do relatório de input enviado.
- Chaves únicas no Streamlit para eliminar `StreamlitDuplicateElementKey`.
- Metodologia ICL restaurada, com fórmula, pesos, exemplo e explicação.
- Cálculo individual por loja restaurado: cada loja mostra exposição por pilar e contribuição de cada peso para o ICL.
- Achados individuais permanecem visíveis independentemente do ICL.
- Diagnóstico técnico dissertativo e encaminhamentos de mitigação.
- Análise técnica assistida agora apresenta texto para leitura humana; não exibe código Python.
- Referências técnicas aparecem junto aos achados e na metodologia.
- Tabelas foram reduzidas ao mínimo necessário; telas principais priorizam cards, gráficos e acordeões.
- Shopping, ano e mês/ciclo ficam disponíveis para reutilização futura.
- Não há módulo de importação de PDF.

## ICL
O ICL é um índice agregado de exposição. Não é certificado de segurança e não deve ser usado isoladamente para declarar uma loja conforme. A cobertura dos dados, os achados individuais e a severidade são mostrados separadamente.

A fórmula operacional é:
`ICL = Σ(Exposição do Pilar × Peso do Pilar) ÷ Σ Pesos Ativos`

Os valores de severidade usados pelo motor são parâmetros operacionais da plataforma, não percentuais atribuídos pela ABNT. A referência normativa fundamenta a interpretação técnica de cada regra.

## Base técnica
A plataforma usa como referência principal a ABNT NBR 14518 para sistemas de ventilação de cozinhas profissionais, além de projeto, fabricante e requisitos da autoridade competente. A NFPA 96 pode ser utilizada como referência internacional complementar quando aplicável.

## Deploy
1. Substitua `app.py` e `requirements.txt` no GitHub.
2. Faça upload de `README.md` e `supabase_migration.sql` no GitHub.
3. Execute o conteúdo de `supabase_migration.sql` uma única vez no SQL Editor do Supabase.
4. Mantenha `SUPABASE_URL` e `SUPABASE_KEY` somente nos Secrets do Streamlit.

## Segurança de dados
A migration é aditiva: não contém `DELETE`, `TRUNCATE`, `DROP TABLE` nem `UPDATE` dos registros existentes.
