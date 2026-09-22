import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from pypdf import PdfReader
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="CSA Engenharia | Gestão de Riscos em Exaustão",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO (PADRÃO CSA ENGENHARIA) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC; }
    
    .csa-header {
        background: linear-gradient(135deg, #0D3B66 0%, #002855 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(13, 59, 102, 0.15);
    }
    .csa-header h1 { color: #FFFFFF !important; margin: 0; font-size: 2rem; font-weight: 700; }
    .csa-header p { color: #E2E8F0; margin-top: 5px; font-size: 1rem; }

    .metric-card {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border-top: 4px solid #0D3B66;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        text-align: center;
    }
    .metric-title { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.7rem; color: #0D3B66; font-weight: 800; margin-top: 5px; }

    .ia-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 6px solid #0D3B66;
        padding: 20px;
        border-radius: 8px;
        margin-top: 15px;
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

# --- MOTOR DE IA LOCAL (GERADOR DE PARECER TÉCNICO) ---
def gerar_parecer_ia_local(row):
    loja = row['loja']
    icl = row['icl_score']
    criticidade = row['criticidade']
    
    infracoes = []
    recomendacoes = []

    if not row['incendio_conforme']:
        infracoes.append("• **NFPA 96 / ABNT NBR 14518:** Inconformidade no sistema de combate/extinção fixa ou acúmulo severo de gordura nos dutos.")
        recomendacoes.append("• Realizar higienização química/mecânica imediata nos dutos e revisar o acionamento do saponificante.")

    if not row['intertravamento_ok']:
        infracoes.append("• **ABNT NBR 14518 (Item 5.4):** Ausência ou falha no sistema de intertravamento automático entre a exaustão e a linha de gás/energia das cocções.")
        recomendacoes.append("• Adequar o painel de intertravamento solenoide para corte automático de combustível em caso de desarmamento da exaustão.")

    if row['eletrica_exposta']:
        infracoes.append("• **NR-10 (Segurança em Instalações Elétricas):** Presença de fiação exposta, cabos sem conduíte ou quadro de comando desprotegido.")
        recomendacoes.append("• Reorganizar o cabeamento elétrico em eletrodutos blindados e fechar tampas de proteção de quadros.")

    if row['casa_maquinas_obstruida']:
        infracoes.append("• **NR-12 / ABNT NBR 14518:** Obstrução na casa de máquinas ou falta de proteção em partes móveis (correias/polias).")
        recomendacoes.append("• Promover a desobstrução imediata do local e instalar carenagens de proteção nos exaustores.")

    if row['vazamento_dutos']:
        infracoes.append("• **ABNT NBR 14518:** Estanqueidade comprometida com vazamento/gotejamento de óleo lipídico em junções de dutos.")
        recomendacoes.append("• Aplicar vedação adequada com silicone de alta temperatura ou reajustar flanges e juntas de estanqueidade.")

    if not infracoes:
        status_texto = "A operação apresenta excelente nível de conformidade técnica. Não foram identificadas infrações graves durante esta vistoria."
        plano_acao = "Manter o cronograma preventivo de limpeza e manutenção rotineira."
    else:
        status_texto = "\n".join(infracoes)
        plano_acao = "\n".join(recomendacoes)

    parecer_md = f"""
    ### 🛡️ Parecer de Engenharia — {loja}
    **Classificação de Risco:** `{criticidade.upper()}` | **Pontuação ICL:** `{icl}%`

    #### 🔴 Inconformidades e Riscos Normativos Identificados:
    {status_texto}

    #### 🛠️ Plano de Ação & Recomendações Corretivas:
    {plano_acao}

    ---
    *Parecer automatizado pela CSA Engenharia fundamentado nas diretrizes ABNT NBR 14518, NFPA 96, NR-10 e NR-12.*
    """
    return parecer_md

# --- CABEÇALHO ---
st.markdown("""
    <div class="csa-header">
        <h1>CSA ENGENHARIA</h1>
        <p>Plataforma Técnica de Gestão e Auditoria de Exaustão Comercial — Shopping Guararapes</p>
    </div>
""", unsafe_allow_html=True)

df = carregar_dados()

if df.empty:
    st.error("Nenhum registro encontrado no Supabase. Certifique-se de executar o script SQL no Supabase.")
    st.stop()

# --- BARRA LATERAL ---
st.sidebar.title("Navegação Estratégica")
modulo = st.sidebar.radio("Selecione o Módulo:", [
    "📊 Dashboard Global de Riscos",
    "🏪 Análise Detalhada por Loja",
    "📐 Metodologia ICL & Normas Técnicas",
    "🤖 Agente de IA (Diagnóstico)",
    "📄 Upload de Laudos (PDF/OCR)",
    "📋 Matriz Completa de Dados"
])

meses = df["mes_referencia"].unique().tolist()
mes_sel = st.sidebar.selectbox("Ciclo da Vistoria:", meses)
df_filtrado = df[df["mes_referencia"] == mes_sel].copy()

# --- MÓDULO 1: DASHBOARD GLOBAL DE RISCOS ---
if modulo == "📊 Dashboard Global de Riscos":
    c1, c2, c3, c4 = st.columns(4)
    total = len(df_filtrado)
    criticas = len(df_filtrado[df_filtrado["criticidade"].isin(["Crítico", "Severo"])])
    eletrica = (df_filtrado["eletrica_exposta"].sum() / total) * 100 if total > 0 else 0
    intertrav = ((~df_filtrado["intertravamento_ok"]).sum() / total) * 100 if total > 0 else 0

    c1.markdown(f'<div class="metric-card"><div class="metric-title">Operações Auditadas</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card" style="border-top-color: #EF4444;"><div class="metric-title">Grau Crítico / Severo</div><div class="metric-value" style="color: #EF4444;">{criticas}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card" style="border-top-color: #F97316;"><div class="metric-title">Risco Elétrico (NR-10)</div><div class="metric-value" style="color: #F97316;">{eletrica:.0f}%</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="metric-card" style="border-top-color: #3B82F6;"><div class="metric-title">Falha Intertravamento</div><div class="metric-value" style="color: #3B82F6;">{intertrav:.0f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("### 🎯 Distribuição de Criticidade (ICL)")
        fig_pie = px.pie(
            df_filtrado, names="criticidade", color="criticidade", hole=0.4,
            color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("### 📈 Ranking de Risco Por Unidade (ICL %)")
        df_sort = df_filtrado.sort_values(by="icl_score", ascending=True)
        fig_bar = px.bar(
            df_sort, y="loja", x="icl_score", orientation="h", color="criticidade",
            color_discrete_map={"Controlado": "#22C55E", "Atenção": "#3B82F6", "Relevante": "#F97316", "Crítico": "#EF4444", "Severo": "#0F172A"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# --- MÓDULO 2: ANÁLISE DETALHADA POR LOJA ---
elif modulo == "🏪 Análise Detalhada por Loja":
    st.markdown("### 🏪 Painel Individual da Unidade")
    loja_sel = st.selectbox("Selecione a Operação:", df_filtrado["loja"].unique())
    dados_loja = df_filtrado[df_filtrado["loja"] == loja_sel].iloc[0]

    col_l1, col_l2 = st.columns([1, 2])

    with col_l1:
        st.markdown(f"#### Status: **{dados_loja['criticidade']}**")
        st.metric("Pontuação ICL", f"{dados_loja['icl_score']}%")
        
        st.write("**Checklist de Conformidade:**")
        st.write(f"{'✅' if dados_loja['incendio_conforme'] else '❌'} Combate a Incêndio / NFPA 96")
        st.write(f"{'✅' if dados_loja['intertravamento_ok'] else '❌'} Intertravamento de Gás")
        st.write(f"{'❌' if dados_loja['eletrica_exposta'] else '✅'} Fiação Isolada (NR-10)")
        st.write(f"{'❌' if dados_loja['casa_maquinas_obstruida'] else '✅'} Casa de Máquinas Desobstruída")
        st.write(f"{'❌' if dados_loja['vazamento_dutos'] else '✅'} Ausência de Vazamento nos Dutos")

    with col_l2:
        # Gráfico Radar de Riscos
        categorias = ['Incêndio', 'Intertravamento', 'Elétrica', 'Acesso/NR12', 'Estanqueidade']
        valores = [
            100 if dados_loja['incendio_conforme'] else 20,
            100 if dados_loja['intertravamento_ok'] else 20,
            20 if dados_loja['eletrica_exposta'] else 100,
            20 if dados_loja['casa_maquinas_obstruida'] else 100,
            20 if dados_loja['vazamento_dutos'] else 100
        ]

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=valores,
            theta=categorias,
            fill='toself',
            marker_color='#0D3B66'
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=f"Perfil de Seguridade Técnica — {loja_sel}"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("<div class='ia-card'>", unsafe_allow_html=True)
    st.markdown(gerar_parecer_ia_local(dados_loja))
    st.markdown("</div>", unsafe_allow_html=True)

# --- MÓDULO 3: METODOLOGIA ICL & NORMAS TÉCNICAS ---
elif modulo == "📐 Metodologia ICL & Normas Técnicas":
    st.markdown("### 📐 Fundamentação Técnica e Cálculo do ICL")
    
    st.markdown("""
    O **ICL (Índice de Criticidade de Loja)** é uma métrica ponderada desenvolvida pela **CSA Engenharia** para mensurar o nível de exposição ao risco de incêndio, colapso operacional e autuações fiscalizatórias em praças de alimentação de shoppings centers.

    #### 🧮 Fórmula do ICL:
    $$ICL = (P_{INC} \times 0.35) + (P_{INT} \times 0.25) + (P_{ELE} \times 0.20) + (P_{OBS} \times 0.10) + (P_{VAZ} \times 0.10)$$

    * **Combate a Incêndio ($P_{INC}$):** Peso 35% — Avalia extintores saponificantes e dampers corta-fogo (**NFPA 96**).
    * **Intertravamento de Gás ($P_{INT}$):** Peso 25% — Valida o desligamento automático do combustível (**ABNT NBR 14518**).
    * **Segurança Elétrica ($P_{ELE}$):** Peso 20% — Avalia quadros elétricos e fiação (**NR-10**).
    * **Acesso & Casa de Máquinas ($P_{OBS}$):** Peso 10% — Avalia obstruções e proteções móveis (**NR-12**).
    * **Vazamentos em Dutos ($P_{VAZ}$):** Peso 10% — Avalia acúmulo e gotejamento de gordura lipídica.

    #### 🚦 Tabela de Enquadramento de Risco:
    * **0% a 25% — Controlado (Verde):** Operação em conformidade com manutenção preventiva em dia.
    * **26% a 50% — Atenção (Azul):** Pendências leves que não impedem o funcionamento imediato.
    * **51% a 70% — Relevante (Laranja):** Necessidade de intervenção em até 15 dias.
    * **71% a 85% — Crítico (Vermelho):** Alto risco de sinistro. Regularização necessária em até 48 horas.
    * **86% a 100% — Severo (Preto):** Risco iminente de incêndio/acidente. Recomendada a paralisação do equipamento.
    """)

# --- MÓDULO 4: AGENTE DE IA (DIAGNÓSTICO) ---
elif modulo == "🤖 Agente de IA (Diagnóstico)":
    st.markdown("### 🤖 Diagnóstico Automatizado de Riscos")
    loja_ia = st.selectbox("Selecione a Loja para Gerar o Laudo:", df_filtrado["loja"].unique())
    dados_ia = df_filtrado[df_filtrado["loja"] == loja_ia].iloc[0]

    st.markdown("<div class='ia-card'>", unsafe_allow_html=True)
    st.markdown(gerar_parecer_ia_local(dados_ia))
    st.markdown("</div>", unsafe_allow_html=True)

# --- MÓDULO 5: UPLOAD DE LAUDOS (PDF/OCR) ---
elif modulo == "📄 Upload de Laudos (PDF/OCR)":
    st.markdown("### 📄 Processamento Automático de PDF")
    pdf_file = st.file_uploader("Envie o relatório em PDF:", type=["pdf"])

    if pdf_file:
        reader = PdfReader(io.BytesIO(pdf_file.read()))
        texto = "".join([page.extract_text() or "" for page in reader.pages])
        st.success("Texto extraído com sucesso!")
        st.text_area("Prévia:", texto[:500], height=120)

        with st.form("salvar_pdf_form"):
            f_loja = st.text_input("Nome da Loja:")
            f_mes = st.text_input("Mês:", value="2026-06")
            f_icl = st.slider("ICL (%):", 0, 100, 50)
            f_crit = st.selectbox("Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
            
            f_eletrica = st.checkbox("Fiação Exposta (NR-10)")
            f_inter = st.checkbox("Intertravamento OK")
            f_incendio = st.checkbox("Incêndio Conforme (NFPA 96)")
            
            f_obs = st.text_area("Observações:", value=texto[:300])

            if st.form_submit_button("Salvar Registro"):
                novo = {
                    "loja": f_loja, "mes_referencia": f_mes, "icl_score": f_icl,
                    "criticidade": f_crit, "eletrica_exposta": f_eletrica,
                    "intertravamento_ok": f_inter, "incendio_conforme": f_incendio,
                    "observacoes": f_obs
                }
                supabase.table("vistorias_exaustao").insert(novo).execute()
                st.success("Salvo com sucesso no Supabase!")

# --- MÓDULO 6: MATRIZ COMPLETA DE DADOS ---
elif modulo == "📋 Matriz Completa de Dados":
    st.markdown("### 📋 Visão Tabular e Matriz de Riscos")
    st.dataframe(df_filtrado, use_container_width=True)
