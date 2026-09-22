import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import requests
from pypdf import PdfReader
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="CSA Engenharia | Plataforma de Gestão de Exaustão",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS AVANÇADA (PADRÃO CSA ENGENHARIA) ---
st.markdown("""
    <style>
    /* Estilo Geral */
    .stApp { background-color: #F4F6F9; }
    
    /* Cabeçalho Institucional */
    .csa-header {
        background: linear-gradient(135deg, #0D3B66 0%, #002855 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(13, 59, 102, 0.15);
    }
    .csa-header h1 { color: #FFFFFF !important; margin: 0; font-size: 2.2rem; font-weight: 700; }
    .csa-header p { color: #E2E8F0; margin-top: 5px; font-size: 1.1rem; }

    /* Cartões de Métricas */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-top: 4px solid #0D3B66;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }
    .metric-title { font-size: 0.9rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; color: #0D3B66; font-weight: 800; margin-top: 5px; }

    /* Cartão de Parecer de IA */
    .ia-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #0D3B66;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def carregar_dados():
    response = supabase.table("vistorias_exaustao").select("*").execute()
    return pd.DataFrame(response.data)

# --- CABEÇALHO ---
st.markdown("""
    <div class="csa-header">
        <h1>CSA ENGENHARIA</h1>
        <p>Plataforma Técnica de Auditoria e Diagnóstico de Riscos em Exaustão Mecânica — Shopping Guararapes</p>
    </div>
""", unsafe_allow_html=True)

df = carregar_dados()

if df.empty:
    st.error("Nenhum registro encontrado no Supabase. Execute o script SQL no Supabase para popular os dados das 20 lojas.")
    st.stop()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.image("https://img.icons8.com/color/96/shield.png", width=60)
st.sidebar.title("Painel de Controle")

modulo = st.sidebar.radio("Selecione o Módulo:", [
    "📊 Dashboard de Performance e Riscos",
    "🤖 Agente de IA Técnico (Base44)",
    "📄 Ingestão de Relatórios (PDF/OCR)",
    "📋 Matriz Consolidada de Unidades"
])

# FILTRO GLOBAL DE MÊS
meses_disp = df["mes_referencia"].unique().tolist()
mes_selecionado = st.sidebar.selectbox("Ciclo da Vistoria:", meses_disp)
df_filtrado = df[df["mes_referencia"] == mes_selecionado].copy()

# --- MÓDULO 1: DASHBOARD DE PERFORMANCE E RISCOS ---
if modulo == "📊 Dashboard de Performance e Riscos":
    
    # KPIs Topo
    col1, col2, col3, col4 = st.columns(4)
    
    total_lojas = len(df_filtrado)
    criticas = len(df_filtrado[df_filtrado["criticidade"].isin(["Crítico", "Severo"])])
    perc_eletrica = (df_filtrado["eletrica_exposta"].sum() / total_lojas) * 100 if total_lojas > 0 else 0
    perc_intertrav = ((~df_filtrado["intertravamento_ok"]).sum() / total_lojas) * 100 if total_lojas > 0 else 0

    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Lojas Auditadas</div><div class="metric-value">{total_lojas}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card" style="border-top-color: #EF4444;"><div class="metric-title">Grau Crítico / Severo</div><div class="metric-value" style="color: #EF4444;">{criticas}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card" style="border-top-color: #F97316;"><div class="metric-title">Risco Elétrico (NR-10)</div><div class="metric-value" style="color: #F97316;">{perc_eletrica:.0f}%</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card" style="border-top-color: #3B82F6;"><div class="metric-title">Falha Intertravamento</div><div class="metric-value" style="color: #3B82F6;">{perc_intertrav:.0f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos
    g1, g2 = st.columns([1, 1])

    with g1:
        st.markdown("### 🎯 Distribuição de Criticidade (ICL)")
        fig_pie = px.pie(
            df_filtrado, 
            names="criticidade", 
            color="criticidade",
            hole=0.4,
            color_discrete_map={
                "Controlado": "#22C55E", 
                "Atenção": "#3B82F6", 
                "Relevante": "#F97316", 
                "Crítico": "#EF4444", 
                "Severo": "#0F172A"
            }
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.markdown("### 📈 Ranking de Risco por Loja (ICL %)")
        df_sorted = df_filtrado.sort_values(by="icl_score", ascending=True)
        fig_bar = px.bar(
            df_sorted, 
            y="loja", 
            x="icl_score", 
            orientation="h",
            color="criticidade",
            color_discrete_map={
                "Controlado": "#22C55E", 
                "Atenção": "#3B82F6", 
                "Relevante": "#F97316", 
                "Crítico": "#EF4444", 
                "Severo": "#0F172A"
            }
        )
        fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), xaxis_title="Pontuação ICL", yaxis_title="")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- MÓDULO 2: AGENTE TÉCNICO BASE44 ---
elif modulo == "🤖 Agente de IA Técnico (Base44)":
    st.markdown("### 🤖 Diagnóstico Inteligente por Operação")
    st.write("Selecione uma loja para consultar a análise técnica gerada diretamente pelo **Agente do Base44**.")

    loja_selecionada = st.selectbox("Escolha a Operação Comerciais:", df_filtrado["loja"].unique())
    dados_loja = df_filtrado[df_filtrado["loja"] == loja_selecionada].to_dict(orient="records")[0]

    # Exibição resumida dos dados enviados
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Criticidade:** {dados_loja['criticidade']}")
    c2.warning(f"**Pontuação ICL:** {dados_loja['icl_score']}%")
    c3.error(f"**Fiação Exposta:** {'Sim' if dados_loja['eletrica_exposta'] else 'Não'}")

    if st.button("🚀 Gerar Parecer do Agente Base44", type="primary"):
        with st.spinner("Conectando ao Agente do Base44 e processando diretrizes da ABNT NBR 14518 e NFPA 96..."):
            
            base44_url = st.secrets.get("BASE44_URL", "")
            base44_token = st.secrets.get("BASE44_TOKEN", "")

            headers = {
                "Authorization": f"Bearer {base44_token}",
                "Content-Type": "application/json"
            }
            
            prompt_envio = f"""
            Analise a vistoria técnica da loja '{dados_loja['loja']}' no Shopping Guararapes.
            Dados da vistoria:
            - Criticidade: {dados_loja['criticidade']} (ICL: {dados_loja['icl_score']}%)
            - Fiação Exposta (NR-10): {dados_loja['eletrica_exposta']}
            - Intertravamento de Gás/Exaustão OK: {dados_loja['intertravamento_ok']}
            - Combate a Incêndio Conforme (NFPA 96): {dados_loja['incendio_conforme']}
            - Obstrução na Casa de Máquinas (NR-12): {dados_loja['casa_maquinas_obstruida']}
            - Vazamento de Gordura nos Dutos: {dados_loja['vazamento_dutos']}
            - Observações do Vistoriador: {dados_loja['observacoes']}
            """

            payload = {
                "message": prompt_envio
            }

            try:
                res = requests.post(base44_url, json=payload, headers=headers, timeout=20)
                if res.status_code in [200, 201]:
                    res_json = res.json()
                    parecer = res_json.get("text") or res_json.get("response") or res_json.get("message") or str(res_json)
                else:
                    parecer = f"Erro na requisição ({res.status_code}): {res.text}"
            except Exception as e:
                parecer = f"Falha na conexão com o servidor do Base44: {e}"

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f'<div class="ia-card"><h3>📋 Parecer Técnico — {loja_selecionada}</h3><br>{parecer}</div>', unsafe_allow_html=True)

# --- MÓDULO 3: INGESTÃO DE RELATÓRIOS (PDF/OCR) ---
elif modulo == "📄 Ingestão de Relatórios (PDF/OCR)":
    st.markdown("### 📄 Processamento de Novos Laudos em PDF")
    st.write("Faça o upload do relatório da vistoria em formato PDF para que o sistema extraia as informações e atualize a base de dados do Supabase.")

    uploaded_pdf = st.file_uploader("Arraste ou selecione o arquivo PDF do laudo:", type=["pdf"])

    if uploaded_pdf is not None:
        reader = PdfReader(io.BytesIO(uploaded_pdf.read()))
        texto_completo = ""
        for page in reader.pages:
            texto_completo += page.extract_text() or ""

        st.success("PDF processado com sucesso!")
        
        with st.expander("Ver Texto Extraído do Documento"):
            st.write(texto_completo)

        st.markdown("---")
        st.markdown("#### Confirmar e Salvar no Supabase")
        
        with st.form("form_salvar_pdf"):
            f_loja = st.text_input("Nome da Loja/Operação:")
            f_mes = st.text_input("Mês de Referência:", value="2026-06")
            f_icl = st.slider("Índice de Criticidade (ICL %):", 0, 100, 50)
            f_crit = st.selectbox("Nível de Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
            
            col_a, col_b = st.columns(2)
            f_eletrica = col_a.checkbox("Fiação Elétrica Exposta (NR-10)")
            f_inter = col_b.checkbox("Intertravamento Conforme")
            f_incendio = col_a.checkbox("Combate a Incêndio Conforme (NFPA 96)")
            f_obstrucao = col_b.checkbox("Casa de Máquinas Obstruída")

            f_obs = st.text_area("Observações Técnicas:", value=texto_completo[:300])

            btn_salvar = st.form_submit_button("Salvar no Supabase")

            if btn_salvar:
                novo_registro = {
                    "loja": f_loja,
                    "mes_referencia": f_mes,
                    "icl_score": f_icl,
                    "criticidade": f_crit,
                    "eletrica_exposta": f_eletrica,
                    "intertravamento_ok": f_inter,
                    "incendio_conforme": f_incendio,
                    "casa_maquinas_obstruida": f_obstrucao,
                    "observacoes": f_obs
                }
                supabase.table("vistorias_exaustao").insert(novo_registro).execute()
                st.success(f"Operação {f_loja} registrada com sucesso no banco de dados!")

# --- MÓDULO 4: MATRIZ CONSOLIDADA ---
elif modulo == "📋 Matriz Consolidada de Unidades":
    st.markdown("### 📋 Visão Tabular e Matriz de Riscos")
    st.write("Acompanhamento completo de todas as 20 unidades do Shopping Guararapes.")
    
    st.dataframe(
        df_filtrado[[
            "loja", "criticidade", "icl_score", "incendio_conforme", 
            "intertravamento_ok", "eletrica_exposta", "casa_maquinas_obstruida", "vazamento_dutos", "observacoes"
        ]],
        use_container_width=True
    )
