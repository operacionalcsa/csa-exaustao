import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# -----------------------------------------------------------------------------
# Configuração Inicial da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vistorias ABNT NBR 14518:2019",
    page_icon="🏭",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Conexão com Supabase (.streamlit/secrets.toml)
# -----------------------------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Erro ao conectar com o Supabase: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# Função para Carregar Vistorias
# -----------------------------------------------------------------------------
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        resposta = supabase.table("vistorias_exaustao").select("*").order("created_at", desc=True).execute()
        return pd.DataFrame(resposta.data)
    except Exception as e:
        st.warning(f"Aviso ao consultar Supabase: {e}")
        return pd.DataFrame()

df = carregar_dados()

# -----------------------------------------------------------------------------
# Estrutura do Formulário Padrão (Perguntas)
# -----------------------------------------------------------------------------
SECOES_RELATORIO = {
    "DADOS DA COIFA": [
        "FABRICANTE",
        "TIPO",
        "VAZÃO DE EXAUSTÃO",
        "HÁ LAVADOR DE GASES?",
        "HÁ LUMINÁRIA NA COIFA",
        "MATERIAL DA LUMINÁRIA EM CONFORMIDADE?",
        "HÁ ALÇAPÃO NA COZINHA?",
        "EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)",
        "ELÉTRICA EXPOSTA PRÓXIMO A COIFA?",
        "HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?",
        "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?",
        "EXISTEM FILTROS?",
        "QUAL O TIPO DE FILTROS?",
        "OS FILTROS ESTÃO COMPLETOS?",
        "OS FILTROS ESTÃO DANIFICADOS?",
        "SISTEMA LAVATÓRIO OPERANTE?",
        "QUADRO DE AUTOMAÇÃO COM ACESSO E OPERANTE?",
        "MATERIAIS DA INFRA HIDRÁULICA APROPRIADOS?",
        "A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?",
        "BICOS INJETORES EM CONFORMIDADE?",
        "FLAUTA DA COIFA EM CONFORMIDADE?",
        "BOIA DA COIFA EM CONFORMIDADE?",
        "BOMBA DE ÁGUA ESTÁ OPERANTE?",
        "HÁ PRODUTO NO RESERVATÓRIO?",
        "DOSADOR OPERANTE?"
    ],
    "DADOS DO EXAUSTOR": [
        "CASA DE MÁQUINA DESOBSTRUÍDA?",
        "FABRICANTE DO EXAUSTOR",
        "TIPO",
        "LUBRIFICAÇÃO",
        "ALINHAMENTO",
        "BALACEAMENTO",
        "CORREIAS",
        "REFERÊNCIA DA CORREA",
        "HÁ PROTETOR DE CORREIA?",
        "MANCAIS",
        "REFERÊNCIA DOS MANCAIS",
        "POLIAS",
        "REFERÊNCIA DAS POLIA MOTORA",
        "REFERÊNCIA DAS POLIA MOVIDA",
        "ROLAMENTOS",
        "ELÉTRICA DO EXAUSTOR",
        "ELÉTRICA EXPOSTA?",
        "ACESSO PARA MANUTENÇÃO?",
        "HÁ JANELA DE INSPEÇÃO NO EXAUSTOR?",
        "HÁ DRENO DE OLÉO?",
        "BASE DO EXAUSTOR",
        "VIBRAÇÃO E RUÍDOS NORMAIS?",
        "PINTURA",
        "HÁ LAVADOR DE GASES?",
        "HÁ INTERTRAVAMENTO?",
        "INTERTRAVAMENTO FUNCIONANDO?"
    ],
    "DUTOS DE EXAUSTÃO": [
        "DUTOS EM BOM ESTADO DE CONSERVAÇÃO?",
        "HÁ VAZAMENTO NOS DUTOS?",
        "TIPO DA CHAPA DO DUTO",
        "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? SUCÇÃO",
        "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? DESCARGA",
        "TIPO DO ISOLAMENTO",
        "EXISTE DUTO SEM ACESSO?",
        "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA SUCÇÃO?",
        "QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?",
        "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?",
        "QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?",
        "ONDE NECESSITA DE JANELAS?",
        "HÁ DAMPER CORTA FOGO?",
        "TIPO DO DAMPER (MECÂNICO/ELÉTRICO)",
        "DAMPER EM BOM ESTADO E OPERANTE?",
        "DAMPER ESTÁ ACESSÍVEL?",
        "DAMPER TEM ACESSO PARA LIMPEZA?",
        "HÁ SISTEMA DE COMBATE A INCÊNDIO (CO2)?",
        "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE (CO2)?",
        "HÁ ACESSO AOS DUTOS DA COZINHA?",
        "HÁ LONA DE ACOPLAMENTO?",
        "LONA DE ACOPLAMENTO"
    ]
}

# -----------------------------------------------------------------------------
# Navegação / Barra Lateral
# -----------------------------------------------------------------------------
st.sidebar.title("Navegação")
menu = st.sidebar.radio(
    "Selecione o Módulo:",
    [
        "📋 Novo Relatório (Formulário)",
        "📊 Visão Geral / Métricas",
        "🔍 Análise Detalhada das Lojas",
        "📄 Diagnósticos e Laudos Técnicos",
        "⚙️ Configurações"
    ]
)

st.title("🏭 Gestão de Vistorias em Sistemas de Exaustão")
st.caption("Norma ABNT NBR 14518:2019 — Cozinhas Profissionais")

# -----------------------------------------------------------------------------
# MÓDULO 1: Novo Relatório Manual
# -----------------------------------------------------------------------------
if menu == "📋 Novo Relatório (Formulário)":
    st.header("Preenchimento de Relatório de Vistoria")
    st.info("Apenas Nome da Loja, Mês de Referência e Data/Hora são obrigatórios. Os demais campos do relatório são opcionais.")

    with st.form("form_vistoria", clear_on_submit=True):
        st.subheader("📍 Identificação Geral")
        col_loja, col_mes, col_data = st.columns(3)
        loja_nome = col_loja.text_input("LOJA *", placeholder="Ex: McDonalds - Shopping")
        mes_ref = col_mes.text_input("MÊS DE REFERÊNCIA *", placeholder="Ex: 2026-06 ou Junho/2026")
        data_hora = col_data.text_input("DATA/HORA *", placeholder="Ex: 15/06/2026 14:30")

        respostas_coletadas = {}

        for secao_nome, perguntas in SECOES_RELATORIO.items():
            st.divider()
            st.markdown(f"### 🔽 {secao_nome}")
            
            for index, pergunta in enumerate(perguntas):
                st.markdown(f"**{pergunta}**")
                col_resp, col_obs = st.columns([1, 2])
                
                resp = col_resp.text_input(
                    label=f"Resposta para '{pergunta}'",
                    key=f"resp_{secao_nome}_{index}",
                    placeholder="Resposta (Opcional - até 2 palavras)",
                    max_chars=25,
                    label_visibility="collapsed"
                )
                
                obs = col_obs.text_input(
                    label=f"Anotação para '{pergunta}'",
                    key=f"obs_{secao_nome}_{index}",
                    placeholder="Anotações / Observações (Opcional)",
                    label_visibility="collapsed"
                )
                
                respostas_coletadas[pergunta] = {
                    "resposta": resp.strip() if resp.strip() else "(Sem preenchimento)",
                    "observacao": obs.strip() if obs.strip() else ""
                }

        st.divider()
        st.markdown("### 🔽 OBSERVAÇÕES GERAIS")
        obs_gerais = st.text_area("OBSERVAÇÕES GERAIS (Opcional)", placeholder="Digite considerações gerais caso haja...")

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

                    st.success(f"Relatório da loja {loja_nome} salvo com sucesso!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")

# -----------------------------------------------------------------------------
# MÓDULO 2: Visão Geral / Métricas
# -----------------------------------------------------------------------------
elif menu == "📊 Visão Geral / Métricas":
    st.header("Visão Geral das Vistorias")

    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Vistorias", len(df))
        
        if "loja" in df.columns:
            lojas_unicas = df["loja"].dropna().nunique()
            c2.metric("Lojas Únicas", lojas_unicas)
        
        c3.metric("Norma Base", "ABNT NBR 14518:2019")

        st.divider()
        st.subheader("Registros Salvos")
        
        col_tabela, col_grafico = st.columns([2, 1])
        with col_tabela:
            colunas_exibir = [c for c in ["loja", "mes_referencia", "data_hora", "status", "created_at"] if c in df.columns]
            st.dataframe(df[colunas_exibir], use_container_width=True)

        with col_grafico:
            if "loja" in df.columns and not df["loja"].isnull().all():
                fig = px.bar(df, x="loja", title="Vistorias por Loja", color="loja")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum registro encontrado. Acesse o menu 'Novo Relatório' para começar a alimentar o sistema.")

# -----------------------------------------------------------------------------
# MÓDULO 3: Análise Detalhada das Lojas
# -----------------------------------------------------------------------------
elif menu == "🔍 Análise Detalhada das Lojas":
    st.header("Análise Detalhada")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas_validas = df["loja"].dropna().unique()
        loja_sel = st.selectbox("Selecione a Loja para consultar:", lojas_validas)
        
        registros_loja = df[df["loja"] == loja_sel]
        
        for idx, registro in registros_loja.iterrows():
            dados_json = registro.get("dados", {})
            st.subheader(f"Vistoria: {registro.get('loja')} — {registro.get('mes_referencia', 'N/A')}")
            st.write(f"**Data/Hora do Registro:** {registro.get('data_hora', 'N/A')}")

            if isinstance(dados_json, dict) and "questoes" in dados_json:
                questoes = dados_json["questoes"]
                
                itens = []
                for q, val in questoes.items():
                    itens.append({
                        "Pergunta / Item": q,
                        "Resposta": val.get("resposta", "(Sem preenchimento)"),
                        "Observações": val.get("observacao", "")
                    })
                
                st.dataframe(pd.DataFrame(itens), use_container_width=True)
                
                if dados_json.get("observacoes_gerais"):
                    st.markdown("**Observações Gerais:**")
                    st.info(dados_json["observacoes_gerais"])
                st.divider()
            else:
                st.warning("Este registro não possui dados em formato JSON padronizado.")
    else:
        st.info("Nenhuma loja cadastrada até o momento.")

# -----------------------------------------------------------------------------
# MÓDULO 4: Diagnósticos e Laudos Técnicos
# -----------------------------------------------------------------------------
elif menu == "📄 Diagnósticos e Laudos Técnicos":
    st.header("Diagnósticos e Pareceres Dissertativos")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas_validas = df["loja"].dropna().unique()
        loja_laudo = st.selectbox("Selecione a Loja para Gerar o Laudo:", lojas_validas)
        
        if st.button("📄 Gerar Laudo Técnico Completo"):
            registro = df[df["loja"] == loja_laudo].iloc[0]
            dados_json = registro.get("dados", {})
            questoes = dados_json.get("questoes", {}) if isinstance(dados_json, dict) else {}

            st.markdown(f"## 📋 PARECER TÉCNICO DE VISTORIA - {str(loja_laudo).upper()}")
            st.markdown(f"**Norma de Referência:** ABNT NBR 14518:2019")
            st.markdown(f"**Mês de Referência:** {registro.get('mes_referencia', 'N/A')}")
            st.markdown(f"**Data/Hora da Inspeção:** {registro.get('data_hora', 'N/A')}")
            st.divider()

            st.markdown("### 1. DADOS DA COIFA")
            for p in SECOES_RELATORIO["DADOS DA COIFA"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "(Sem preenchimento)")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Obs: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.markdown("### 2. DADOS DO EXAUSTOR")
            for p in SECOES_RELATORIO["DADOS DO EXAUSTOR"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "(Sem preenchimento)")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Obs: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.markdown("### 3. DUTOS DE EXAUSTÃO")
            for p in SECOES_RELATORIO["DUTOS DE EXAUSTÃO"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "(Sem preenchimento)")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Obs: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.divider()
            st.markdown("### 4. OBSERVAÇÕES GERAIS E CONCLUIMENTO")
            obs_g = dados_json.get("observacoes_gerais", "(Sem observações gerais)") if isinstance(dados_json, dict) else ""
            st.write(obs_g)
    else:
        st.info("Nenhuma loja disponível para geração de laudos.")

# -----------------------------------------------------------------------------
# MÓDULO 5: Configurações
# -----------------------------------------------------------------------------
elif menu == "⚙️ Configurações":
    st.header("Configurações do Sistema")
    st.success("Conexão ativa com o Supabase (Tabela: vistorias_exaustao).")
    if st.button("🔄 Recarregar Dados do Banco"):
        st.cache_data.clear()
        st.success("Cache limpo! Dados recarregados.")
