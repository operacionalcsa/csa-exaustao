import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from datetime import datetime

# -----------------------------------------------------------------------------
# Configuração Inicial da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CSA EXHAUST INTELLIGENCE | ABNT NBR 14518:2019",
    page_icon="🏭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Conexão com Supabase
# -----------------------------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Erro de conexão com o Supabase: {e}")
    st.stop()

@st.cache_data(ttl=5)
def carregar_dados():
    try:
        resposta = supabase.table("vistorias_exaustao").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        st.warning(f"Erro ao carregar dados do Supabase: {e}")
        return pd.DataFrame()

df_raw = carregar_dados()

# -----------------------------------------------------------------------------
# Dicionário de Perguntas do Formulário
# -----------------------------------------------------------------------------
SECOES_RELATORIO = {
    "DADOS DA COIFA": [
        "FABRICANTE", "TIPO", "VAZÃO DE EXAUSTÃO", "HÁ LAVADOR DE GASES?",
        "HÁ LUMINÁRIA NA COIFA", "MATERIAL DA LUMINÁRIA EM CONFORMIDADE?",
        "HÁ ALÇAPÃO NA COZINHA?", "EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)",
        "ELÉTRICA EXPOSTA PRÓXIMO A COIFA?", "HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?",
        "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?", "EXISTEM FILTROS?",
        "QUAL O TIPO DE FILTROS?", "OS FILTROS ESTÃO COMPLETOS?", "OS FILTROS ESTÃO DANIFICADOS?",
        "SISTEMA LAVATÓRIO OPERANTE?", "QUADRO DE AUTOMAÇÃO COM ACESSO E OPERANTE?",
        "MATERIAIS DA INFRA HIDRÁULICA APROPRIADOS?", "A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?",
        "BICOS INJETORES EM CONFORMIDADE?", "FLAUTA DA COIFA EM CONFORMIDADE?",
        "BOIA DA COIFA EM CONFORMIDADE?", "BOMBA DE ÁGUA ESTÁ OPERANTE?",
        "HÁ PRODUTO NO RESERVATÓRIO?", "DOSADOR OPERANTE?"
    ],
    "DADOS DO EXAUSTOR": [
        "CASA DE MÁQUINA DESOBSTRUÍDA?", "FABRICANTE DO EXAUSTOR", "TIPO",
        "LUBRIFICAÇÃO", "ALINHAMENTO", "BALACEAMENTO", "CORREIAS", "REFERÊNCIA DA CORREA",
        "HÁ PROTETOR DE CORREIA?", "MANCAIS", "REFERÊNCIA DOS MANCAIS", "POLIAS",
        "REFERÊNCIA DAS POLIA MOTORA", "REFERÊNCIA DAS POLIA MOVIDA", "ROLAMENTOS",
        "ELÉTRICA DO EXAUSTOR", "ELÉTRICA EXPOSTA?", "ACESSO PARA MANUTENÇÃO?",
        "HÁ JANELA DE INSPEÇÃO NO EXAUSTOR?", "HÁ DRENO DE OLÉO?", "BASE DO EXAUSTOR",
        "VIBRAÇÃO E RUÍDOS NORMAIS?", "PINTURA", "HÁ LAVADOR DE GASES?",
        "HÁ INTERTRAVAMENTO?", "INTERTRAVAMENTO FUNCIONANDO?"
    ],
    "DUTOS DE EXAUSTÃO": [
        "DUTOS EM BOM ESTADO DE CONSERVAÇÃO?", "HÁ VAZAMENTO NOS DUTOS?", "TIPO DA CHAPA DO DUTO",
        "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? SUCÇÃO",
        "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? DESCARGA", "TIPO DO ISOLAMENTO",
        "EXISTE DUTO SEM ACESSO?", "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA SUCÇÃO?",
        "QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?", "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?",
        "QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?", "ONDE NECESSITA DE JANELAS?",
        "HÁ DAMPER CORTA FOGO?", "TIPO DO DAMPER (MECÂNICO/ELÉTRICO)",
        "DAMPER EM BOM ESTADO E OPERANTE?", "DAMPER ESTÁ ACESSÍVEL?",
        "DAMPER TEM ACESSO PARA LIMPEZA?", "HÁ SISTEMA DE COMBATE A INCÊNDIO (CO2)?",
        "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE (CO2)?", "HÁ ACESSO AOS DUTOS DA COZINHA?",
        "HÁ LONA DE ACOPLAMENTO?", "LONA DE ACOPLAMENTO"
    ]
}

# -----------------------------------------------------------------------------
# Processamento de Métricas e Fórmulas de Criticidade (ICL)
# -----------------------------------------------------------------------------
def processar_dataframe(df):
    if df.empty:
        return df
    
    # Garantir colunas essenciais
    if "icl_score" not in df.columns:
        df["icl_score"] = 0.0
    if "nivel_criticidade" not in df.columns:
        df["nivel_criticidade"] = "Não Calculado"
        
    # Tratamento caso os dados venham das colunas tradicionais ou do JSON
    for idx, row in df.iterrows():
        dados_json = row.get("dados", {})
        if isinstance(dados_json, dict) and "questoes" in dados_json:
            questoes = dados_json.get("questoes", {})
            total_perguntas = len(questoes)
            conformes = 0
            
            for q, v in questoes.items():
                resp = str(v.get("resposta", "")).upper()
                if resp in ["SIM", "OK", "CONFORME", "OPERANTE", "BOM"]:
                    conformes += 1
            
            if total_perguntas > 0:
                score = round((conformes / total_perguntas) * 100, 1)
                df.at[idx, "icl_score"] = score
                if score >= 80:
                    df.at[idx, "nivel_criticidade"] = "Baixa (Conforme)"
                elif score >= 50:
                    df.at[idx, "nivel_criticidade"] = "Média (Atenção)"
                else:
                    df.at[idx, "nivel_criticidade"] = "Alta (Crítico)"
    return df

df = processar_dataframe(df_raw)

# -----------------------------------------------------------------------------
# Navegação
# -----------------------------------------------------------------------------
st.sidebar.title("🏭 CSA INTELLIGENCE")
st.sidebar.caption("Sistemas de Exaustão NBR 14518:2019")

menu = st.sidebar.radio(
    "Módulos do Sistema:",
    [
        "📊 Visão Geral / Dashboard Executivo",
        "🔍 Análise Detalhada & Criticidade",
        "📄 Diagnósticos e Laudos Técnicos",
        "📋 Novo Relatório (Formulário)",
        "⚙️ Configurações & Banco de Dados"
    ]
)

# -----------------------------------------------------------------------------
# MÓDULO 1: Dashboard Executivo / Métricas
# -----------------------------------------------------------------------------
if menu == "📊 Visão Geral / Dashboard Executivo":
    st.title("📊 Painel Executivo de Vistorias Técnicas")
    st.caption("Visão macro do estado de conformidade dos sistemas de exaustão das unidades")

    if not df.empty:
        total_vistorias = len(df)
        lojas_unicas = df["loja"].dropna().nunique() if "loja" in df.columns else 0
        media_icl = df["icl_score"].mean() if "icl_score" in df.columns else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Vistorias", total_vistorias)
        m2.metric("Lojas Monitoradas", lojas_unicas)
        m3.metric("Índice Médio de Conformidade (ICL)", f"{media_icl:.1f}%")
        m4.metric("Norma Técnica Base", "ABNT NBR 14518")

        st.divider()

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("Nível de Criticidade por Loja")
            if "nivel_criticidade" in df.columns and "loja" in df.columns:
                fig_crit = px.pie(
                    df, 
                    names="nivel_criticidade", 
                    title="Distribuição do Nível de Risco",
                    color="nivel_criticidade",
                    color_discrete_map={
                        "Baixa (Conforme)": "#2ecc71",
                        "Média (Atenção)": "#f1c40f",
                        "Alta (Crítico)": "#e74c3c"
                    }
                )
                st.plotly_chart(fig_crit, use_container_width=True)

        with col_right:
            st.subheader("Índice de Conformidade por Loja (ICL)")
            if "loja" in df.columns and "icl_score" in df.columns:
                fig_bar = px.bar(
                    df, 
                    x="loja", 
                    y="icl_score", 
                    color="icl_score",
                    title="Score de Conformidade (%) por Unidade",
                    color_continuous_scale="RdYlGn"
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("📋 Tabela Geral de Vistorias")
        colunas_grid = [c for c in ["loja", "mes_referencia", "data_hora", "icl_score", "nivel_criticidade", "status"] if c in df.columns]
        st.dataframe(df[colunas_grid], use_container_width=True)

    else:
        st.info("Nenhuma vistoria encontrada no banco de dados. Acesse o menu 'Novo Relatório' para registrar.")

# -----------------------------------------------------------------------------
# MÓDULO 2: Análise Detalhada das Lojas
# -----------------------------------------------------------------------------
elif menu == "🔍 Análise Detalhada & Criticidade":
    st.header("🔍 Análise Detalhada de Conformidade e Criticidade")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas = df["loja"].dropna().unique()
        loja_sel = st.selectbox("Selecione a Loja para detalhar:", lojas)

        reg = df[df["loja"] == loja_sel].iloc[0]
        dados_json = reg.get("dados", {})

        c1, c2, c3 = st.columns(3)
        c1.metric("Loja Selecionada", reg.get("loja"))
        c2.metric("Mês de Referência", reg.get("mes_referencia", "N/A"))
        c3.metric("Data/Hora da Vistoria", reg.get("data_hora", "N/A"))

        st.divider()

        if isinstance(dados_json, dict) and "questoes" in dados_json:
            questoes = dados_json["questoes"]
            
            lista_tabela = []
            for q, v in questoes.items():
                lista_tabela.append({
                    "Item Inspecionado": q,
                    "Resposta": v.get("resposta", "(Sem preenchimento)"),
                    "Anotações / Observações": v.get("observacao", "")
                })

            df_items = pd.DataFrame(lista_tabela)
            st.dataframe(df_items, use_container_width=True)

            if dados_json.get("observacoes_gerais"):
                st.subheader("Observações Gerais da Inspeção")
                st.info(dados_json["observacoes_gerais"])
        else:
            st.warning("Este registro possui formato antigo. Preencha um novo formulário para ver o detalhamento completo.")
    else:
        st.info("Nenhuma loja cadastrada para análise.")

# -----------------------------------------------------------------------------
# MÓDULO 3: Diagnósticos e Laudos Técnicos
# -----------------------------------------------------------------------------
elif menu == "📄 Diagnósticos e Laudos Técnicos":
    st.header("📄 Emissão de Laudos Técnicos e Pareceres")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas = df["loja"].dropna().unique()
        loja_laudo = st.selectbox("Selecione a Loja para a Geração do Laudo:", lojas)

        if st.button("📄 Gerar Laudo Técnico Completo"):
            reg = df[df["loja"] == loja_laudo].iloc[0]
            dados_json = reg.get("dados", {})
            questoes = dados_json.get("questoes", {}) if isinstance(dados_json, dict) else {}

            st.markdown(f"## 📋 LAUDO TÉCNICO DE INSPEÇÃO — {str(loja_laudo).upper()}")
            st.markdown(f"**Referência Normativa:** ABNT NBR 14518:2019 — Sistemas de Exaustão para Cozinhas Profissionais")
            st.markdown(f"**Data da Inspecão:** {reg.get('data_hora', 'N/A')} | **Mês Ref:** {reg.get('mes_referencia', 'N/A')}")
            st.divider()

            for secao, perguntas in SECOES_RELATORIO.items():
                st.markdown(f"### 🔽 {secao}")
                for p in perguntas:
                    if p in questoes:
                        r = questoes[p].get("resposta", "(Não Informado)")
                        o = questoes[p].get("observacao", "")
                        obs_str = f" _(Obs: {o})_" if o else ""
                        st.markdown(f"- **{p}:** {r}{obs_str}")

            st.divider()
            st.markdown("### 📝 Parecer Técnico Final")
            obs_g = dados_json.get("observacoes_gerais", "Sem observações gerais registradas.") if isinstance(dados_json, dict) else ""
            st.write(obs_g)
    else:
        st.info("Não há vistorias registradas para gerar laudos.")

# -----------------------------------------------------------------------------
# MÓDULO 4: Novo Relatório Manual (Formulário)
# -----------------------------------------------------------------------------
elif menu == "📋 Novo Relatório (Formulário)":
    st.header("📋 Preenchimento de Relatório de Vistoria")
    st.info("Apenas Nome da Loja, Mês de Referência e Data/Hora são obrigatórios. Todos os outros itens são opcionais.")

    with st.form("form_vistoria", clear_on_submit=True):
        st.subheader("📍 Dados de Identificação")
        c1, c2, c3 = st.columns(3)
        loja_nome = c1.text_input("LOJA *", placeholder="Ex: McDonalds - Shopping")
        mes_ref = c2.text_input("MÊS DE REFERÊNCIA *", placeholder="Ex: 2026-06")
        data_hora = c3.text_input("DATA/HORA *", placeholder="Ex: 15/06/2026 14:30")

        respostas_coletadas = {}

        for secao_nome, perguntas in SECOES_RELATORIO.items():
            st.divider()
            st.markdown(f"### 🔽 {secao_nome}")
            
            for index, pergunta in enumerate(perguntas):
                st.markdown(f"**{pergunta}**")
                col_resp, col_obs = st.columns([1, 2])
                
                resp = col_resp.text_input(
                    label=f"Resposta_{secao_nome}_{index}",
                    key=f"resp_{secao_nome}_{index}",
                    placeholder="Resposta (Opcional - até 2 palavras)",
                    max_chars=25,
                    label_visibility="collapsed"
                )
                
                obs = col_obs.text_input(
                    label=f"Obs_{secao_nome}_{index}",
                    key=f"obs_{secao_nome}_{index}",
                    placeholder="Anotação / Observação (Opcional)",
                    label_visibility="collapsed"
                )
                
                respostas_coletadas[pergunta] = {
                    "resposta": resp.strip() if resp.strip() else "(Sem preenchimento)",
                    "observacao": obs.strip() if obs.strip() else ""
                }

        st.divider()
        st.markdown("### 🔽 OBSERVAÇÕES GERAIS")
        obs_gerais = st.text_area("OBSERVAÇÕES GERAIS (Opcional)", placeholder="Digite considerações adicionais caso existam...")

        submetido = st.form_submit_button("💾 Salvar Relatório de Vistoria")

        if submetido:
            if not loja_nome or not mes_ref or not data_hora:
                st.error("Por favor, preencha os campos obrigatórios: LOJA, MÊS DE REFERÊNCIA e DATA/HORA.")
            else:
                dados_payload = {
                    "loja": loja_nome,
                    "mes_referencia": mes_ref,
                    "data_hora": data_hora,
                    "status": "Concluída",
                    "observacoes_gerais": obs_gerais if obs_gerais else "(Sem observações gerais)",
                    "questoes": respostas_coletadas
                }

                try:
                    supabase.table("vistorias_exaustao").insert({
                        "loja": loja_nome,
                        "mes_referencia": mes_ref,
                        "data_hora": data_hora,
                        "status": "Concluída",
                        "dados": dados_payload
                    }).execute()

                    st.success(f"Relatório da {loja_nome} salvo com sucesso!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")

# -----------------------------------------------------------------------------
# MÓDULO 5: Configurações & Banco
# -----------------------------------------------------------------------------
elif menu == "⚙️ Configurações & Banco de Dados":
    st.header("⚙️ Configurações do Sistema")
    st.success("Conexão com o Supabase ativa (Tabela: vistorias_exaustao).")
    
    if st.button("🔄 Recarregar Dados do Banco"):
        st.cache_data.clear()
        st.success("Cache limpo! Os gráficos e métricas foram atualizados.")
