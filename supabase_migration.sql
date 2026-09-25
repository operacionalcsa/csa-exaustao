-- MIGRAÇÃO ADITIVA E NÃO DESTRUTIVA.
-- Não apaga, regrava, recalcula ou modifica os registros existentes.
-- Apenas cria colunas de metadados necessárias para novas vistorias.

alter table public.vistorias_exaustao add column if not exists shopping text;
alter table public.vistorias_exaustao add column if not exists ano_referencia text;
alter table public.vistorias_exaustao add column if not exists mes_numero text;
alter table public.vistorias_exaustao add column if not exists data_hora text;

create index if not exists idx_vistorias_exaustao_shopping_ano_mes
on public.vistorias_exaustao(shopping, ano_referencia, mes_referencia);
