import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
import requests
from pypdf import PdfReader
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="CSA Engenharia | Gestão de Risco de Exaustão",
    page_icon="🛡️",
    layout="wide"
)

# --- IDENTIDADE VISUAL CSA ENGENHARIA ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stAppHeader { background-color: #0D3B66; }
    h1, h2, h3 { color: #0D3B66 !important; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetricValue"] { color: #004B87 !important; font-weight: bold; }
    .csa-card {
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #0D3B66; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def carregar_vistorias():
    response = supabase.table("vistorias_exaustao").select("*").execute()
    return pd.DataFrame(response.data)

# --- CABEÇALHO ---
st.markdown("<h1>CSA ENGENHARIA</h1>", unsafe_allow_html=True)
st.markdown("### Auditoria Técnica & Monitoramento de Exaustão Comercial — Shopping Guararapes")
st.markdown("---")

df = carregar_vistorias()

# --- BARRA LATERAL ---
st.sidebar.title("Navegação Estratégica")
menu = st.sidebar.radio("Selecione o Módulo:", [
    "Dashboard Executivo", 
    "Diagnóstico Agente IA (Base44)", 
    "Upload & Leitura de Relatório PDF",
    "Matriz de Riscos & Lojas"
])

# --- MÓDULO 1: DASHBOARD EXECUTIVO ---
if menu == "Dashboard Executivo":
    if df.empty:
        st.info("Nenhum registro encontrado no Supabase. Utilize a aba 'Upload & Leitura de Relatório PDF' para importar os relatórios técnicos.")
    else:
        # Filtro de Mês
        meses = df["mes_referencia"].unique().tolist()
        mes_sel = st.sidebar.selectbox("Ciclo de Vistoria:", meses)
        df_filtrado = df[df["mes_referencia"] == mes_sel]

        # Métricas Principais
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Operações Auditadas", len(df_filtrado))
        c2.metric("Nível Crítico/Severo", len(df_filtrado[df_filtrado["criticidade"].isin(["Crítico", "Severo"])]))
        
        fiacao_exp = (df_filtrado["eletrica_exposta"].sum() / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0
        intertrav = ((~df_filtrado["intertravamento_ok"]).sum() / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0
        
        c3.metric("Risco Elétrico (NR-10)", f"{fiacao_exp:.0f}%")
        c4.metric("Falha Intertravamento", f"{intertrav:.0f}%")

        st.markdown("---")
        st.markdown("### 📊 Indicadores Globais do Sistema de Exaustão")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            fig_pie = px.pie(
                df_filtrado, names="criticidade", title="Distribuição de Criticidade (ICL)",
                color="criticidade",
                color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            fig_bar = px.bar(
                df_filtrado.sort_values("icl_score", ascending=False),
                x="loja", y="icl_score", color="criticidade",
                title="Ranking de Risco por Loja (Pontuação ICL)",
                color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# --- MÓDULO 2: AGENTE BASE44 ---
elif menu == "Diagnóstico Agente IA (Base44)":
    st.markdown("### 🤖 Consulta Técnica ao Agente Especialista (Base44)")
    st.write("Análise automatizada ancorada nas normas **ABNT NBR 14518, NFPA 96, NR-10 e NR-12**.")

    if df.empty:
        st.warning("Cadastre relatórios ou insira dados no banco para habilitar a consulta por loja.")
    else:
        loja_selecionada = st.selectbox("Selecione a Loja para Auditoria:", df["loja"].unique())
        dados_loja = df[df["loja"] == loja_selecionada].to_dict(orient="records")[0]

        if st.button("Gerar Parecer Técnico via Base44"):
            with st.spinner("Consultando normas e processando parecer do Agente..."):
                base44_url = st.secrets.get("BASE44_URL", "")
                base44_token = st.secrets.get("BASE44_TOKEN", "")

                headers = {
                    "Authorization": f"Bearer {base44_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "message": f"Realize um parecer técnico completo para a operação '{dados_loja['loja']}'. Dados da vistoria: {dados_loja}. Destaque as infrações das normas NBR 14518, NFPA 96 e NR-10."
                }

                try:
                    response = requests.post(base44_url, json=payload, headers=headers, timeout=20)
                    if response.status_code in [200, 201]:
                        res_data = response.json()
                        parecer = res_data.get("text") or res_data.get("response") or res_data.get("message") or response.text
                    else:
                        parecer = f"⚠️ Erro ao comunicar com o Base44 (Status {response.status_code}). Verifique a URL do endpoint nas Secrets."
                except Exception as e:
                    parecer = f"Falha na conexão: {e}"

                st.markdown("<div class='csa-card'>", unsafe_allow_html=True)
                st.markdown(f"#### Parecer do Agente IA — {loja_selecionada}")
                st.markdown(parecer)
                st.markdown("</div>", unsafe_allow_html=True)

# --- MÓDULO 3: UPLOAD DE PDF ---
elif menu == "Upload & Leitura de Relatório PDF":
    st.markdown("### 📄 Processamento Automático de Relatórios em PDF")
    st.write("Faça o upload do laudo/relatório técnico em PDF. O sistema extrairá o texto e cadastrará os indicadores no sistema.")

    uploaded_file = st.file_uploader("Selecione o laudo da loja (PDF):", type=["pdf"])

    if uploaded_file is not None:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        texto_extraido = ""
        for page in reader.pages:
            texto_extraido += page.extract_text() or ""

        st.success("PDF lido com sucesso!")
        st.text_area("Prévia do Conteúdo Extraído:", texto_extraido[:1000] + "...", height=150)

        with st.form("confirmar_dados_pdf"):
            st.markdown("#### Confirmar Dados Extraídos para o Banco")
            nome_loja = st.text_input("Nome da Loja / Operação:")
            mes_ref = st.text_input("Mês de Referência:", value="2026-07")
            icl_score = st.slider("Pontuação ICL (0-100):", 0, 100, 50)
            criticidade = st.selectbox("Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
            
            c1, c2 = st.columns(2)
            eletrica = c1.checkbox("Possui Fiação Exposta (NR-10)")
            intertrav = c2.checkbox("Intertravamento Conforme")

            obs = st.text_area("Resumo / Observações Extraídas:", value=texto_extraido[:500])

            if st.form_submit_button("Salvar Vistoria no Supabase"):
                novo_reg = {
                    "loja": nome_loja,
                    "mes_referencia": mes_ref,
                    "icl_score": icl_score,
                    "criticidade": criticidade,
                    "eletrica_exposta": eletrica,
                    "intertravamento_ok": intertrav,
                    "observacoes": obs
                }
                supabase.table("vistorias_exaustao").insert(novo_reg).execute()
                st.success(f"Relatório da {nome_loja} salvo com sucesso!")

# --- MÓDULO 4: TABELA COMPLETA ---
elif menu == "Matriz de Riscos & Lojas":
    st.markdown("### 📋 Matriz Consolidada de Riscos")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado cadastrado.")
