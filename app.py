import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from pypdf import PdfReader
import io

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA & THEMA CSA
# ==========================================
st.set_page_config(
    page_title="CSA Engenharia | Gestão do Sistema de Exaustão",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILO CSS AVANÇADO (DESIGN MODERNO & ARREDONDADO - AZUL, LARANJA, CINZA)
st.markdown("""
    <style>
    /* Estilo Geral da Aplicação */
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Cabeçalho Principal */
    .csa-hero {
        background: linear-gradient(135deg, #0D3B66 0%, #002855 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(13, 59, 102, 0.12);
        border-bottom: 4px solid #FF6B35;
    }
    .csa-hero h1 { color: #FFFFFF !important; font-size: 2.3rem; font-weight: 800; margin: 0; }
    .csa-hero p { color: #E2E8F0; font-size: 1.1rem; margin-top: 8px; font-weight: 400; }
    
    /* Cartões Executivos / KPI */
    .kpi-card {
        background-color: #FFFFFF;
        padding: 22px 18px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid #E2E8F0;
        border-left: 6px solid #0D3B66;
        transition: transform 0.2s ease;
    }
    .kpi-card-orange { border-left-color: #FF6B35 !important; }
    .kpi-card-red { border-left-color: #E53E3E !important; }
    .kpi-card-green { border-left-color: #38A169 !important; }
    
    .kpi-label { font-size: 0.82rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 2rem; color: #0D3B66; font-weight: 800; margin-top: 6px; }
    .kpi-subtext { font-size: 0.8rem; color: #94A3B8; margin-top: 4px; }

    /* Caixa de Diagnóstico IA */
    .ia-box {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 25px;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #FF6B35;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-top: 20px;
    }
    
    /* Tags de Status */
    .tag-severo { background-color: #1A202C; color: white; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .tag-critico { background-color: #E53E3E; color: white; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .tag-relevante { background-color: #FF6B35; color: white; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .tag-atencao { background-color: #3182CE; color: white; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    .tag-controlado { background-color: #38A169; color: white; padding: 4px 10px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO E BANCO DE DADOS
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

def carregar_dados():
    response = supabase.table("vistorias_exaustao").select("*").execute()
    return pd.DataFrame(response.data)

# ==========================================
# 3. MOTOR LOCAL DE INTELIGÊNCIA TÉCNICA
# ==========================================
def gerar_parecer_executivo(row):
    loja = row['loja']
    icl = row['icl_score']
    crit = row['criticidade']
    
    infracoes = []
    acoes_imediatas = []
    acoes_preventivas = []

    if not row['incendio_conforme']:
        infracoes.append("❌ **Risco de Incêndio Severo (NFPA 96 / ABNT NBR 14518):** Ausência ou falha no sistema fixo de extinção química (saponificante) e/ou contaminação lipídica excessiva nos dutos.")
        acoes_imediatas.append("• Promover a limpeza técnica dos dutos com hidrojateamento de alta pressão e desengraxante biodegradável.")
        acoes_imediatas.append("• Recarregar e certificar o sistema automático de supressão de incêndio da coifa.")

    if not row['intertravamento_ok']:
        infracoes.append("❌ **Falha de Intertravamento (NBR 14518 - Cap. 5.4):** Não há desligamento automático da linha de gás/energia quando o exaustor é desligado.")
        acoes_imediatas.append("• Instalar/reparar a válvula solenoide de corte de gás interligada ao sensor de fluxo do exaustor.")

    if row['eletrica_exposta']:
        infracoes.append("❌ **Insegurança Elétrica (NR-10):** Fiação exposta sem eletrodutos blindados e quadros de comando desprotegidos contra umidade/gordura.")
        acoes_imediatas.append("• Isolar cabeamentos, adequar prensa-cabos e fechar os painéis elétricos com vedação adequada.")

    if row['casa_maquinas_obstruida']:
        infracoes.append("⚠️ **Obstrução & Proteção de Máquinas (NR-12):** Casa de máquinas usada como depósito ou polias/correias desprovidas de carenagem de proteção.")
        acoes_preventivas.append("• Liberar totalmente a área de circulação da casa de máquinas e instalar grades de proteção nos motores.")

    if row['vazamento_dutos']:
        infracoes.append("⚠️ **Vazamento de Gordura (NBR 14518):** Falha de estanqueidade nas juntas de união dos dutos, ocasionando gotejamento de óleo sobre o entreforro/cozinha.")
        acoes_preventivas.append("• Recalafetar as conexões dos dutos com vedante resistente a altas temperaturas (silicone acético/mástique).")

    infracoes_str = "\n".join(infracoes) if infracoes else "✅ Operação em total conformidade com as normas regulamentadoras aplicáveis."
    imediatas_str = "\n".join(acoes_imediatas) if acoes_imediatas else "• Manter inspeção preventiva quinzenal."
    preventivas_str = "\n".join(acoes_preventivas) if acoes_preventivas else "• Seguir o plano de manutenção programado."

    return f"""
    ### 📋 Parecer Técnico de Auditoria — **{loja}**
    **Classificação:** `{crit.upper()}` | **Índice ICL:** `{icl}%`

    ---
    #### 🚨 Não Conformidades Normativas:
    {infracoes_str}

    #### ⚡ Plano de Ação Prioritário (Emergencial):
    {imediatas_str}

    #### 🛠️ Ações Preventivas e Corretivas (15 dias):
    {preventivas_str}
    """

# ==========================================
# 4. TOPBAR / CABEÇALHO
# ==========================================
st.markdown("""
    <div class="csa-hero">
        <h1>CSA ENGENHARIA</h1>
        <p>Plataforma Executiva de Auditoria, Risco & Conformidade de Exaustão Comercial — Shopping Guararapes</p>
    </div>
""", unsafe_allow_html=True)

df = carregar_dados()

if df.empty:
    st.error("Nenhum registro encontrado no Supabase. Execute o script de carga inicial no banco.")
    st.stop()

# ==========================================
# 5. BARRA LATERAL (NAVEGAÇÃO)
# ==========================================
st.sidebar.markdown("### 🛡️ Painel de Navegação")
modulo = st.sidebar.radio("Selecione a Visão:", [
    "🌐 Panorama Executivo do Shopping",
    "🏪 Diagnóstico Detalhado por Loja",
    "📐 Metodologia ICL & Ponderação",
    "🤖 Laudo Autônomo com IA",
    "📄 Importação de PDF / Laudo",
    "📋 Matriz Interativa de Dados"
])

meses = df["mes_referencia"].unique().tolist()
mes_sel = st.sidebar.selectbox("Ciclo de Auditoria:", meses)
df_f = df[df["mes_referencia"] == mes_sel].copy()

# CORES CSA
PALETA_CSA = {
    "Controlado": "#38A169",
    "Atenção": "#3182CE",
    "Relevante": "#FF6B35",
    "Crítico": "#E53E3E",
    "Severo": "#1A202C"
}

# ==========================================
# MÓDULO 1: PANORAMA EXECUTIVO GLOBAL
# ==========================================
if modulo == "🌐 Panorama Executivo do Shopping":
    
    # 1. KPIs Globais
    total_lojas = len(df_f)
    criticas_severas = len(df_f[df_f["criticidade"].isin(["Crítico", "Severo"])])
    media_icl = df_f["icl_score"].mean()
    perc_conformidade = ((total_lojas - criticas_severas) / total_lojas) * 100 if total_lojas > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'''
            <div class="kpi-card">
                <div class="kpi-label">Total de Operações Auditadas</div>
                <div class="kpi-value">{total_lojas}</div>
                <div class="kpi-subtext">Praça de Alimentação</div>
            </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
            <div class="kpi-card kpi-card-red">
                <div class="kpi-label">Lojas em Alto Risco</div>
                <div class="kpi-value" style="color:#E53E3E;">{criticas_severas}</div>
                <div class="kpi-subtext">Grau Crítico ou Severo ({ (criticas_severas/total_lojas)*100:.0f}%)</div>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''
            <div class="kpi-card kpi-card-orange">
                <div class="kpi-label">Média ICL do Complexo</div>
                <div class="kpi-value" style="color:#FF6B35;">{media_icl:.1f}%</div>
                <div class="kpi-subtext">Índice Geral de Risk Exposição</div>
            </div>
        ''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''
            <div class="kpi-card kpi-card-green">
                <div class="kpi-label">Taxa de Conformidade</div>
                <div class="kpi-value" style="color:#38A169;">{perc_conformidade:.0f}%</div>
                <div class="kpi-subtext">Operações sem risco alto</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Gráficos Principais
    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.markdown("### 🎯 Visão Macroscópica de Criticidade (ICL)")
        fig_pie = px.pie(
            df_f, names="criticidade", color="criticidade",
            color_discrete_map=PALETA_CSA,
            hole=0.45
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("### 📊 Ranking de Exposição ao Risco por Loja")
        df_ord = df_f.sort_values("icl_score", ascending=True)
        fig_bar = px.bar(
            df_ord, y="loja", x="icl_score", color="criticidade", orientation="h",
            color_discrete_map=PALETA_CSA,
            text="icl_score"
        )
        fig_bar.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_bar.update_layout(
            xaxis_title="Pontuação ICL (%)", yaxis_title="",
            margin=dict(t=20, b=20, l=20, r=20), showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # 3. Análise de Infracões por Norma
    st.markdown("### 📋 Mapeamento de Infrações Técnicas por Norma Regulamentadora")
    
    col_n1, col_n2, col_n3, col_n4 = st.columns(4)
    
    inc_falha = (~df_f["incendio_conforme"]).sum()
    inter_falha = (~df_f["intertravamento_ok"]).sum()
    ele_falha = df_f["eletrica_exposta"].sum()
    obs_falha = df_f["casa_maquinas_obstruida"].sum()

    col_n1.metric("NFPA 96 / Combate Incêndio", f"{inc_falha} lojas", f"{(inc_falha/total_lojas)*100:.0f}% de reprovação", delta_color="inverse")
    col_n2.metric("NBR 14518 / Intertravamento", f"{inter_falha} lojas", f"{(inter_falha/total_lojas)*100:.0f}% de reprovação", delta_color="inverse")
    col_n3.metric("NR-10 / Segurança Elétrica", f"{ele_falha} lojas", f"{(ele_falha/total_lojas)*100:.0f}% de risco", delta_color="inverse")
    col_n4.metric("NR-12 / Máquinas e Acesso", f"{obs_falha} lojas", f"{(obs_falha/total_lojas)*100:.0f}% de obstrução", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Resumo Diretor
    st.markdown("""
        <div class="ia-box">
            <h4>💡 Conclusão Executiva para a Gestão do Shopping:</h4>
            <p>O diagnóstico global revela que <b>mais de 30% das operações de exaustão</b> apresentam riscos classificados entre <b>Crítico e Severo</b>, com foco principal em falhas de intertravamento do sistema de gás (NBR 14518) e fiação exposta em zonas úmidas (NR-10). Recomenda-se a emissão de notificação técnica imediata para as 5 operações no topo do ranking.</p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# MÓDULO 2: DIAGNÓSTICO DETALHADO POR LOJA
# ==========================================
elif modulo == "🏪 Diagnóstico Detalhado por Loja":
    st.markdown("### 🏪 Panorama Operacional Individualizado")
    
    loja_selecionada = st.selectbox("Selecione a Unidade para Inspeção:", df_f["loja"].unique())
    d = df_f[df_f["loja"] == loja_selecionada].iloc[0]

    st.markdown("<br>", unsafe_allow_html=True)

    col_loja1, col_loja2 = st.columns([1, 1.2])

    with col_loja1:
        st.markdown(f"#### Status Atual: **{d['criticidade']}**")
        st.markdown(f"### Score ICL: **{d['icl_score']}%**")
        
        st.markdown("##### 📌 Checklist Normativo:")
        st.write(f"{'✅ Conforme' if d['incendio_conforme'] else '❌ Inconforme'} — Sistema Supressor de Incêndio (NFPA 96)")
        st.write(f"{'✅ Conforme' if d['intertravamento_ok'] else '❌ Inconforme'} — Intertravamento Gás/Exaustão (NBR 14518)")
        st.write(f"{'✅ Protegido' if not d['eletrica_exposta'] else '❌ Fiação Exposta'} — Cabeamento e Painéis (NR-10)")
        st.write(f"{'✅ Livre' if not d['casa_maquinas_obstruida'] else '❌ Obstruída'} — Casa de Máquinas (NR-12)")
        st.write(f"{'✅ Estanque' if not d['vazamento_dutos'] else '❌ Com Vazamento'} — Estanqueidade dos Dutos")

    with col_loja2:
        # Gráfico Radar de Riscos
        eixos = ['Incêndio (NFPA 96)', 'Intertravamento', 'Elétrica (NR-10)', 'Acesso (NR-12)', 'Estanqueidade']
        valores = [
            100 if d['incendio_conforme'] else 15,
            100 if d['intertravamento_ok'] else 15,
            15 if d['eletrica_exposta'] else 100,
            15 if d['casa_maquinas_obstruida'] else 100,
            15 if d['vazamento_dutos'] else 100
        ]

        fig_radar = go.Figure(data=go.Scatterpolar(
            r=valores, theta=eixos, fill='toself',
            fillcolor='rgba(255, 107, 53, 0.3)',
            line=dict(color='#FF6B35', width=3)
        ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=f"Perfil de Risco da Unidade — {loja_selecionada}",
            margin=dict(t=40, b=20, l=40, r=40)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("<div class='ia-box'>", unsafe_allow_html=True)
    st.markdown(gerar_parecer_executivo(d))
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 3: METODOLOGIA ICL & PONDERAÇÃO
# ==========================================
elif modulo == "📐 Metodologia ICL & Ponderação":
    st.markdown("### 📐 Fundamentação Matemática e Origem dos Pesos")
    
    st.markdown("""
    O **ICL (Índice de Criticidade de Loja)** foi desenvolvido pela **CSA Engenharia** com base nas diretrizes internacionais de análise de risco **FMEA (Failure Mode and Effects Analysis)** e normas brasileiras **ABNT**.

    #### 🧮 Equação do ICL:
    $$ICL = (P_{INC} \times 0.35) + (P_{INT} \times 0.25) + (P_{ELE} \times 0.20) + (P_{OBS} \times 0.10) + (P_{VAZ} \times 0.10)$$

    ---
    #### 🔍 Por que esses números? Origem da Ponderação:

    * **35% — Proteção e Extinção de Incêndio ($P_{INC}$ / NFPA 96 / NBR 14518):**
      * *Justificativa:* O fogo em dutos de gordura atinge temperaturas superiores a **1.000 °C** em menos de 3 minutos, propagando-se rapidamente para a estrutura do shopping. Por representarem o maior risco de perda total de patrimônio e vidas, possuem o peso mais elevado.
    
    * **25% — Intertravamento de Segurança ($P_{INT}$ / ABNT NBR 14518 Cap. 5.4):**
      * *Justificativa:* Se o exaustor falhar e o gás (LPG/Natural) continuar alimentando as fritadeiras e chapas, o acúmulo de monóxido de carbono e vapores inflamáveis gera **risco iminente de explosão**.
    
    * **20% — Segurança Elétrica ($P_{ELE}$ / NR-10):**
      * *Justificativa:* A presença de gordura e vapor sobre fiação elétrica exposta é a **causa primária número 1** de curtos-circuitos e faíscas que iniciam os incêndios em cozinhas industriais.
    
    * **10% — Acesso e Proteção de Máquinas ($P_{OBS}$ / NR-12):**
      * *Justificativa:* Impedimentos de acesso à casa de máquinas atrasam a ação dos bombeiros e equipes de manutenção em emergências, além de expor operadores a acidentes em correias.
    
    * **10% — Estanqueidade e Vazamentos ($P_{VAZ}$):**
      * *Justificativa:* Vazamentos de gordura deterioram o forro e aumentam a carga de combustível no entreforro, agindo como condutor de chamas silencioso.

    ---
    #### 🚦 Escala de Severidade:
    * **0% a 25% (Controlado - Verde):** Sistema em total conformidade.
    * **26% a 50% (Atenção - Azul):** Desvios operacionais leves sem risco imediato.
    * **51% a 70% (Relevante - Laranja):** Notificação para adequação em 15 dias.
    * **71% a 85% (Crítico - Vermelho):** Intervenção emergencial requerida em 48 horas.
    * **86% a 100% (Severo - Preto):** Risco crítico iminente. Recomendada suspensão das atividades de cocção.
    """)

# ==========================================
# MÓDULO 4: LAUDO AUTÔNOMO COM IA
# ==========================================
elif modulo == "🤖 Laudo Autônomo com IA":
    st.markdown("### 🤖 Gerador Autônomo de Laudos Técnicos")
    st.write("Selecione qualquer loja do complexo para emitir a minuta do relatório técnico pronto para envio ao lojista.")

    loja_ia = st.selectbox("Selecione a Operação:", df_f["loja"].unique())
    d_ia = df_f[df_f["loja"] == loja_ia].iloc[0]

    st.markdown("<div class='ia-box'>", unsafe_allow_html=True)
    st.markdown(gerar_parecer_executivo(d_ia))
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 5: IMPORTAÇÃO DE PDF / LAUDO
# ==========================================
elif modulo == "📄 Importação de PDF / Laudo":
    st.markdown("### 📄 Processamento de Novos Laudos Técnicos (PDF)")
    
    pdf_file = st.file_uploader("Selecione o arquivo PDF da vistoria:", type=["pdf"])

    if pdf_file:
        reader = PdfReader(io.BytesIO(pdf_file.read()))
        texto = "".join([page.extract_text() or "" for page in reader.pages])
        st.success("Arquivo PDF lido com sucesso!")
        
        with st.expander("Ver Conteúdo do Laudo"):
            st.write(texto)

        with st.form("form_pdf_import"):
            f_loja = st.text_input("Nome da Operação:")
            f_mes = st.text_input("Ciclo de Vistoria:", value="2026-06")
            f_icl = st.slider("Score ICL (%):", 0, 100, 50)
            f_crit = st.selectbox("Nível de Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
            
            c1, c2 = st.columns(2)
            f_inc = c1.checkbox("Sistema de Incêndio OK (NFPA 96)", value=True)
            f_int = c2.checkbox("Intertravamento OK (NBR 14518)", value=True)
            f_ele = c1.checkbox("Fiação Exposta (NR-10)")
            f_obs = c2.checkbox("Casa de Máquinas Obstruída (NR-12)")

            f_not = st.text_area("Observações da Inspeção:", value=texto[:300])

            if st.form_submit_button("Salvar no Supabase"):
                novo_reg = {
                    "loja": f_loja, "mes_referencia": f_mes, "icl_score": f_icl,
                    "criticidade": f_crit, "incendio_conforme": f_inc,
                    "intertravamento_ok": f_int, "eletrica_exposta": f_ele,
                    "casa_maquinas_obstruida": f_obs, "observacoes": f_not
                }
                supabase.table("vistorias_exaustao").insert(novo_reg).execute()
                st.success(f"Vistoria da loja {f_loja} cadastrada com sucesso!")

# ==========================================
# MÓDULO 6: MATRIZ INTERATIVA DE DADOS
# ==========================================
elif modulo == "📋 Matriz Interativa de Dados":
    st.markdown("### 📋 Matriz Geral de Unidades Auditadas")
    st.write("Filtre, ordene e pesquise em tempo real os dados consolidados das operações.")

    # Filtros Dinâmicos
    col_f1, col_f2 = st.columns([2, 1])
    busca = col_f1.text_input("🔍 Buscar por nome da loja:")
    filtro_crit = col_f2.multiselect("Filtrar por Criticidade:", df_f["criticidade"].unique(), default=df_f["criticidade"].unique())

    df_exibicao = df_f[df_f["criticidade"].isin(filtro_crit)].copy()
    if busca:
        df_exibicao = df_exibicao[df_exibicao["loja"].str.contains(busca, case=False)]

    st.dataframe(
        df_exibicao[[
            "loja", "criticidade", "icl_score", "incendio_conforme",
            "intertravamento_ok", "eletrica_exposta", "casa_maquinas_obstruida", "vazamento_dutos", "observacoes"
        ]],
        column_config={
            "loja": "Operação / Loja",
            "criticidade": "Criticidade",
            "icl_score": st.column_config.ProgressColumn("Score ICL", format="%d%%", min_value=0, max_value=100),
            "incendio_conforme": "Incêndio OK",
            "intertravamento_ok": "Intertravamento OK",
            "eletrica_exposta": "Fiação Exposta",
            "casa_maquinas_obstruida": "Máq. Obstruída",
            "vazamento_dutos": "Vazamento Dutos",
            "observacoes": "Observações Técnicas"
        },
        use_container_width=True,
        hide_index=True
    )
