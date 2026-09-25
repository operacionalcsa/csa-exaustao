# CSA Exaustão — biblioteca atualizada

Alterações:
- removida a aba separada de relatório por loja;
- removida a importação de PDF;
- mantido o formulário manual;
- adicionado Shopping/Ano/Mês;
- mantidos os dados existentes e Guararapes como padrão para registros antigos;
- ICL agora é explicitamente um índice agregado de exposição, não uma certificação de segurança;
- cada loja mostra ICL + não conformidades + itens não informados + achados individuais;
- matriz ampliada para Segurança Contra Incêndio, Desempenho, Integridade Mecânica, Elétrica, Manutenibilidade e Conservação;
- pesos e severidade ficam conceitualmente separados;
- ausência de resposta nunca é convertida em conformidade;
- matriz de risco é separada do ICL;
- estrutura preparada para futura IA redatora sem permitir que a IA escolha criticidade ou pesos.

## Deploy
1. Substitua o `app.py` e `requirements.txt` do GitHub.
2. Execute `supabase_migration.sql` no SQL Editor do Supabase.
3. Mantenha `SUPABASE_URL` e `SUPABASE_KEY` somente nos Secrets do Streamlit, nunca no GitHub.
4. Os registros antigos recebem apenas os metadados de shopping/ano/mês/data; o JSON técnico não é reescrito.

## Observação técnica
A escala 0/25/50/75/100 é uma escala operacional de severidade do motor desta versão. Ela não deve ser apresentada como “nota dada diretamente por uma ABNT”. A etapa seguinte deve transformar cada regra em uma matriz formal de evidência → requisito aplicável → severidade → risco → ação, com rastreabilidade por item.
