import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="CSA Engenharia | Gestão de Exaustão",
    page_icon="🛡️",
    layout="wide"
)

# --- IDENTIDADE VISUAL CSA ENGENHARIA (CSS CUSTOMIZADO) ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stAppHeader { background-color: #0D3B66; }
    h1, h2, h3 { color: #0D3B66 !important; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetricValue"] { color: #004B87 !important; font-weight: bold; }
    .stButton>button { background-color: #0D3B66 !important; color: white !important; border-radius: 6px; border: none; }
    .stButton>button:hover { background-color: #002855 !important; }
    .csa-card {
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #0D3B66; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def carregar_vistorias():
    response = supabase.table("vistorias_exaustao").select("*").execute()
    return pd.DataFrame(response.data)

# --- CABEÇALHO DA PLATAFORMA ---
st.markdown("<h1 style='text-align: left;'>CSA ENGENHARIA</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='margin-top: -15px;'>Plataforma Técnica de Riscos — Sistema de Exaustão (Guararapes)</h3>", unsafe_allow_html=True)
st.markdown("---")

df = carregar_vistorias()

if df.empty:
    st.warning("Nenhum dado encontrado no banco de dados Supabase.")
    st.stop()

# --- BARRA LATERAL (NAVEGAÇÃO E FILTROS) ---
st.sidebar.title("Navegação & Filtros")
menu = st.sidebar.radio("Selecione o Módulo:", ["Dashboard Principal", "Agente IA (Base44)", "Cadastrar Novo Relatório"])

meses_disponiveis = df["mes_referencia"].unique().tolist()
mes_filtro = st.sidebar.selectbox("Ciclo de Vistoria:", meses_disponiveis)
df_filtrado = df[df["mes_referencia"] == mes_filtro]

# --- MÓDULO 1: DASHBOARD PRINCIPAL ---
if menu == "Dashboard Principal":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lojas Auditadas", len(df_filtrado))
    col2.metric("Crítico / Severo", len(df_filtrado[df_filtrado["criticidade"].isin(["Crítico", "Severo"])]))
    
    perc_eletrica = (df_filtrado["eletrica_exposta"].sum() / len(df_filtrado)) * 100
    perc_intertravamento = ((~df_filtrado["intertravamento_ok"]).sum() / len(df_filtrado)) * 100
    
    col3.metric("Fiação Exposta", f"{perc_eletrica:.0f}%")
    col4.metric("Falha Intertravamento", f"{perc_intertravamento:.0f}%")

    st.markdown("### 📊 Indicadores Técnicos por Pilar")
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("**Distribuição por Nível de Criticidade**")
        fig_pie = px.pie(
            df_filtrado, names="criticidade", color="criticidade",
            color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.write("**Índice de Criticidade (ICL %) por Loja**")
        fig_bar = px.bar(
            df_filtrado.sort_values(by="icl_score", ascending=False), x="loja", y="icl_score", color="criticidade",
            color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 📋 Tabela Detalhada de Operações")
    st.dataframe(df_filtrado[["loja", "criticidade", "icl_score", "incendio_conforme", "intertravamento_ok", "eletrica_exposta", "casa_maquinas_obstruida", "observacoes"]], use_container_width=True)

# --- MÓDULO 2: INTEGRAÇÃO COM AGENTE BASE44 VIA API ---
elif menu == "Agente IA (Base44)":
    st.markdown("### 🤖 Diagnóstico via Agente IA Base44")
    st.write("Consulta ao Agente Especialista da CSA Engenharia ancorado nas normas ABNT NBR 14518, NFPA 96, NR-10 e NR-12.")
    
    loja_selecionada = st.selectbox("Selecione a Loja para Análise:", df_filtrado["loja"].unique())
    dados_loja = df_filtrado[df_filtrado["loja"] == loja_selecionada].to_dict(orient="records")[0]
    
    if st.button("Consultar Agente Base44"):
        with st.spinner("Conectando ao Agente Base44 e processando normas..."):
            base44_url = st.secrets.get("BASE44_URL", "")
            base44_token = st.secrets.get("BASE44_TOKEN", "")
            
            if base44_url and base44_token:
                try:
                    headers = {
                        "Authorization": f"Bearer {base44_token}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "message": f"Analise a seguinte operação comercial do Shopping Guararapes: {dados_loja}"
                    }
                    
                    response = requests.post(base44_url, json=payload, headers=headers, timeout=15)
                    
                    if response.status_code in [200, 201]:
                        res_json = response.json()
                        parecer = res_json.get("text", res_json.get("response", res_json.get("message", response.text)))
                    else:
                        parecer = f"Erro na requisição (Código {response.status_code}): {response.text}"
                except Exception as e:
                    parecer = f"Falha ao conectar com o serviço do Base44: {e}"
            else:
                # Retorno de segurança/demo caso a chave no secrets ainda não esteja preenchida
                parecer = f"""
                ### 🚨 DIAGNÓSTICO SÍNTESE — {dados_loja['loja']}
                - **Classificação de Risco:** {dados_loja['criticidade']} (ICL: {dados_loja['icl_score']}%)
                
                ### 📜 INFRAÇÕES NORMATIVAS IDENTIFICADAS
                - **ABNT NBR 14518 / NFPA 96:** Pendência nos dispositivos de intertravamento/combate a incêndio.
                - **NR-10:** Risco de fiação exposta e inadequação do quadro elétrico.

                ### 🛠️ PLANO DE AÇÃO IMEDIATO (CSA ENGENHARIA)
                1. **Passo 1 (Até 7 dias):** Intervenção no painel elétrico de acionamento do exaustor.
                2. **Passo 2 (Em até 30 dias):** Teste de estanqueidade de dutos e revisão de vedações.
                3. **Passo 3 (Rotina):** Emissão de ART e agendamento de manutenção preventiva.
                """
            
            st.markdown("<div class='csa-card'>", unsafe_allow_html=True)
            st.markdown(f"#### Parecer do Agente — {loja_selecionada}")
            st.markdown(parecer)
            st.markdown("</div>", unsafe_allow_html=True)

# --- MÓDULO 3: CADASTRAR NOVOS RELATÓRIOS ---
elif menu == "Cadastrar Novo Relatório":
    st.markdown("### 📝 Entrada de Dados — Ciclos Futuros")
    
    with st.form("form_novo_relatorio"):
        nova_loja = st.text_input("Nome da Operação / Loja:")
        novo_mes = st.text_input("Mês de Referência (ex: 2026-07):", value="2026-07")
        
        c1, c2 = st.columns(2)
        incendio = c1.checkbox("Sistema de Combate a Incêndio Conforme", value=True)
        intertravamento = c2.checkbox("Intertravamento Elétrico / Gás OK", value=True)
        eletrica = c1.checkbox("Possui Fiação Elétrica Exposta", value=False)
        obstrucao = c2.checkbox("Casa de Máquinas Obstruída", value=False)
        vazamento = c1.checkbox("Vazamento em Dutos", value=False)
        
        score_icl = st.slider("Pontuação de Risco ICL (0 a 100):", 0, 100, 30)
        criticidade = st.selectbox("Nível de Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
        obs = st.text_area("Observações Técnicas do Vistoriador:")
        
        submitted = st.form_submit_button("Salvar no Supabase")
        
        if submitted:
            dados_novos = {
                "loja": nova_loja, "mes_referencia": novo_mes, "incendio_conforme": incendio,
                "intertravamento_ok": intertravamento, "eletrica_exposta": eletrica,
                "casa_maquinas_obstruida": obstrucao, "vazamento_dutos": vazamento,
                "icl_score": score_icl, "criticidade": criticidade, "observacoes": obs
            }
            supabase.table("vistorias_exaustao").insert(dados_novos).execute()
            st.success(f"Relatório da operação {nova_loja} registrado com sucesso!")
