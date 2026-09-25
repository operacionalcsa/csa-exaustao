-- MIGRAÇÃO ADITIVA. NÃO APAGA NEM ALTERA O CONTEÚDO TÉCNICO EXISTENTE.
alter table public.vistorias_exaustao add column if not exists shopping text default 'Guararapes';
alter table public.vistorias_exaustao add column if not exists ano_referencia text;
alter table public.vistorias_exaustao add column if not exists mes_numero text;
alter table public.vistorias_exaustao add column if not exists data_hora text;

update public.vistorias_exaustao set shopping=coalesce(nullif(shopping,''),'Guararapes') where shopping is null or shopping='';
update public.vistorias_exaustao set ano_referencia=left(mes_referencia,4) where (ano_referencia is null or ano_referencia='') and mes_referencia is not null;
update public.vistorias_exaustao set mes_numero=right(mes_referencia,2) where (mes_numero is null or mes_numero='') and mes_referencia is not null;
update public.vistorias_exaustao set data_hora=coalesce(data_hora,dados->>'data_hora') where data_hora is null or data_hora='';
create index if not exists idx_vistorias_shopping_ano_mes on public.vistorias_exaustao(shopping,ano_referencia,mes_referencia);
