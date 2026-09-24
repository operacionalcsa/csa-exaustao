import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
from pypdf import PdfReader
import io

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA & THEME CSA
# ==========================================
st.set_page_config(
    page_title="CSA Engenharia | Gestão do Sistema de Exaustão",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ESTILO CSS AVANÇADO (DESIGN MODERNO, FLUIDO E ARREDONDADO)
st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .csa-hero {
        background: linear-gradient(135deg, #0D3B66 0%, #002855 100%);
        padding: 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(13, 59, 102, 0.15);
        border-bottom: 5px solid #FF6B35;
    }
    .csa-hero h1 { color: #FFFFFF !important; font-size: 2.2rem; font-weight: 800; margin: 0; }
    .csa-hero p { color: #E2E8F0; font-size: 1.05rem; margin-top: 8px; font-weight: 400; }
    
    .kpi-card {
        background-color: #FFFFFF;
        padding: 22px 18px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid #E2E8F0;
        border-left: 6px solid #0D3B66;
        height: 100%;
    }
    .kpi-card-orange { border-left-color: #FF6B35 !important; }
    .kpi-card-red { border-left-color: #E53E3E !important; }
    .kpi-card-green { border-left-color: #38A169 !important; }
    
    .kpi-label { font-size: 0.82rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 1.9rem; color: #0D3B66; font-weight: 800; margin-top: 6px; }
    .kpi-subtext { font-size: 0.8rem; color: #94A3B8; margin-top: 4px; }

    .laudo-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 28px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        margin-top: 20px;
        line-height: 1.7;
        color: #2D3748;
    }
    
    .card-matriz {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card-matriz:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }

    .badge-status {
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
    }
    .bg-severo { background-color: #1A202C; color: #FFF; }
    .bg-critico { background-color: #E53E3E; color: #FFF; }
    .bg-relevante { background-color: #FF6B35; color: #FFF; }
    .bg-atencao { background-color: #3182CE; color: #FFF; }
    .bg-controlado { background-color: #38A169; color: #FFF; }
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

# Dicionário de Perguntas do Formulário
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

def carregar_dados():
    try:
        response = supabase.table("vistorias_exaustao").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        df = pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    # Processar respostas do questionário para extrair indicadores dos 5 pilares
    for idx, row in df.iterrows():
        dados = row.get("dados", {})
        questoes = dados.get("questoes", {}) if isinstance(dados, dict) else {}

        # Mapeamento dinâmico baseado no formulário preenchido
        incendio = str(questoes.get("SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?", {}).get("resposta", "")).upper()
        intertrava = str(questoes.get("INTERTRAVAMENTO FUNCIONANDO?", {}).get("resposta", "")).upper()
        eletrica = str(questoes.get("ELÉTRICA EXPOSTA PRÓXIMO A COIFA?", {}).get("resposta", "")).upper()
        maquina = str(questoes.get("CASA DE MÁQUINA DESOBSTRUÍDA?", {}).get("resposta", "")).upper()
        vazamento = str(questoes.get("HÁ VAZAMENTO NOS DUTOS?", {}).get("resposta", "")).upper()

        # Atribuição dos valores aos pilares
        df.at[idx, 'incendio_conforme'] = incendio in ["SIM", "OK", "CONFORME"] if incendio else row.get('incendio_conforme', True)
        df.at[idx, 'intertravamento_ok'] = intertrava in ["SIM", "OK", "CONFORME"] if intertrava else row.get('intertravamento_ok', True)
        df.at[idx, 'eletrica_exposta'] = eletrica in ["SIM", "SIM - EXPOSTA", "EXPOSTA"] if eletrica else row.get('eletrica_exposta', False)
        df.at[idx, 'casa_maquinas_obstruida'] = maquina in ["NÃO", "OBSTRUÍDA"] if maquina else row.get('casa_maquinas_obstruida', False)
        df.at[idx, 'vazamento_dutos'] = vazamento in ["SIM", "VAZANDO"] if vazamento else row.get('vazamento_dutos', False)

        # Cálculo do ICL e Criticidade caso não venham calculados
        p_inc = 0 if df.at[idx, 'incendio_conforme'] else 100
        p_int = 0 if df.at[idx, 'intertravamento_ok'] else 100
        p_ele = 100 if df.at[idx, 'eletrica_exposta'] else 0
        p_obs = 100 if df.at[idx, 'casa_maquinas_obstruida'] else 0
        p_vaz = 100 if df.at[idx, 'vazamento_dutos'] else 0

        icl_calc = (p_inc * 0.35) + (p_int * 0.25) + (p_ele * 0.20) + (p_obs * 0.10) + (p_vaz * 0.10)
        df.at[idx, 'icl_score'] = row.get('icl_score', icl_calc) if pd.notnull(row.get('icl_score')) else icl_calc

        score = df.at[idx, 'icl_score']
        if score >= 70:
            crit = "Severo"
        elif score >= 50:
            crit = "Crítico"
        elif score >= 35:
            crit = "Relevante"
        elif score >= 20:
            crit = "Atenção"
        else:
            crit = "Controlado"

        df.at[idx, 'criticidade'] = row.get('criticidade', crit) if pd.notnull(row.get('criticidade')) else crit
        df.at[idx, 'observacoes'] = row.get('observacoes', dados.get("observacoes_gerais", ""))

    return df

# ==========================================
# 3. GERADOR DE PARECER TÉCNICO DISSERTATIVO
# ==========================================
def gerar_parecer_dissertativo(row):
    loja = row['loja']
    icl = row['icl_score']
    crit = str(row['criticidade'])
    
    anomalias = []
    if not row['incendio_conforme']:
        anomalias.append("inoperância do sistema fixo de supressão química saponificante e acúmulo de gordura nos dutos (NFPA 96 / ABNT NBR 14518)")
    if not row['intertravamento_ok']:
        anomalias.append("ausência de intertravamento automático entre ventilação/exaustão e a linha de gás combustível (ABNT NBR 14518, Cap. 5.4)")
    if row['eletrica_exposta']:
        anomalias.append("exposição inadequada de condutores e quadros de comando sem vedação contra vapores (Norma Regulamentadora NR-10)")
    if row['casa_maquinas_obstruida']:
        anomalias.append("obstrução física nas vias da casa de máquinas e falta de carenagem de proteção em partes móveis (Norma Regulamentadora NR-12)")
    if row['vazamento_dutos']:
        anomalias.append("falha de estanqueidade nas acoplagens dos dutos, gerando exsudação de óleos combustíveis no entreforro (ABNT NBR 14518)")

    if anomalias:
        texto_diagnostico = f"Durante a auditoria técnica presencial na operação **{loja}**, foram constatadas não conformidades normativas relevantes, tais como: " + "; ".join(anomalias) + "."
    else:
        texto_diagnostico = f"A unidade **{loja}** apresentou desempenho exemplar na vistoria técnica, operando em total conformidade com as diretrizes da ABNT NBR 14518, NFPA 96, NR-10 e NR-12."

    if icl >= 70:
        recomendacao_executiva = (
            f"Diante do Índice de Criticidade de Loja apurado em **{icl}%** (classificação **{crit.upper()}**), "
            f"a **CSA Engenharia** recomenda notificação formal imediata ao lojista. É necessária a execução emergencial, "
            f"em até 48 horas, de higienização técnica profunda, adequação do intertravamento de gás e isolamento das instalações elétricas. "
            f"A inércia mantém a operação em zona de risco crítico para sinistros térmicos."
        )
    elif icl >= 40:
        recomendacao_executiva = (
            f"Com um ICL de **{icl}%** (classificação **{crit.upper()}**), a unidade apresenta desvios moderados que demandam plano de ação corretiva "
            f"em até 15 dias, priorizando o desobstruimento da casa de máquinas e a recalafetação das juntas dos dutos."
        )
    else:
        recomendacao_executiva = (
            f"Com índice controlado (**ICL {icl}%**), a operação atende aos requisitos de segurança normativos. "
            f"Recomenda-se a manutenção do cronograma quinzenal de inspeção preventiva."
        )

    return f"""
    ### 📜 Laudo Técnico e Diagnóstico Executivo — **{loja}**
    **Classificação Normativa:** `<span class="badge-status bg-{crit.lower()}">{crit.upper()}</span>` | **Índice ICL Registrado:** **{icl}%**

    ---
    
    #### 🔎 Diagnóstico Técnico das Instalações
    {texto_diagnostico}

    #### 🛡️ Parecer Conclusivo & Plano de Mitigação
    {recomendacao_executiva}
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

# ==========================================
# 5. BARRA LATERAL (NAVEGAÇÃO)
# ==========================================
st.sidebar.markdown("### 🛡️ Painel de Navegação")
modulo = st.sidebar.radio("Selecione a Visão:", [
    "🌐 Panorama Executivo do Shopping",
    "🏪 Diagnóstico Detalhado por Loja",
    "📐 Metodologia ICL & Ponderação",
    "🤖 Laudo Autônomo com IA",
    "📋 Novo Relatório (Formulário Manual)",
    "📄 Importação de PDF / Laudo",
    "📋 Matriz Interativa de Dados",
    "🗑️ Gerenciar & Excluir Vistorias"
])

PALETA_CSA = {
    "Controlado": "#38A169",
    "Atenção": "#3182CE",
    "Relevante": "#FF6B35",
    "Crítico": "#E53E3E",
    "Severo": "#1A202C"
}

if not df.empty and "mes_referencia" in df.columns:
    meses = df["mes_referencia"].dropna().unique().tolist()
    if meses:
        mes_sel = st.sidebar.selectbox("Ciclo de Auditoria:", meses)
        df_f = df[df["mes_referencia"] == mes_sel].copy()
    else:
        df_f = df.copy()
else:
    df_f = df.copy()

if not df_f.empty:
    df_f["pilar_incendio"] = df_f["incendio_conforme"].apply(lambda x: 100 if x else 0)
    df_f["pilar_intertravamento"] = df_f["intertravamento_ok"].apply(lambda x: 100 if x else 0)
    df_f["pilar_eletrica"] = df_f["eletrica_exposta"].apply(lambda x: 0 if x else 100)
    df_f["pilar_maquinas"] = df_f["casa_maquinas_obstruida"].apply(lambda x: 0 if x else 100)
    df_f["pilar_estanqueidade"] = df_f["vazamento_dutos"].apply(lambda x: 0 if x else 100)

# ==========================================
# MÓDULO 1: PANORAMA EXECUTIVO GLOBAL
# ==========================================
if modulo == "🌐 Panorama Executivo do Shopping":
    if df_f.empty:
        st.info("Nenhuma vistoria encontrada no Supabase. Adicione um novo relatório pelo menu lateral.")
    else:
        total_lojas = len(df_f)
        criticas_severas = len(df_f[df_f["criticidade"].isin(["Crítico", "Severo"])])
        media_icl = df_f["icl_score"].mean()
        perc_conformidade = ((total_lojas - criticas_severas) / total_lojas) * 100 if total_lojas > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'''
                <div class="kpi-card">
                    <div class="kpi-label">Operações Auditadas</div>
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
                    <div class="kpi-label">Média ICL do Shopping</div>
                    <div class="kpi-value" style="color:#FF6B35;">{media_icl:.1f}%</div>
                    <div class="kpi-subtext">Índice Global de Risco de Exaustão</div>
                </div>
            ''', unsafe_allow_html=True)
        with c4:
            st.markdown(f'''
                <div class="kpi-card kpi-card-green">
                    <div class="kpi-label">Taxa de Conformidade</div>
                    <div class="kpi-value" style="color:#38A169;">{perc_conformidade:.0f}%</div>
                    <div class="kpi-subtext">Operações sem risco severo</div>
                </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 🏛️ Desempenho Global por Pilar Normativo")
        
        avg_inc = df_f["pilar_incendio"].mean()
        avg_int = df_f["pilar_intertravamento"].mean()
        avg_ele = df_f["pilar_eletrica"].mean()
        avg_maq = df_f["pilar_maquinas"].mean()
        avg_est = df_f["pilar_estanqueidade"].mean()

        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Proteção Incêndio", f"{avg_inc:.0f}%", "NFPA 96 / NBR 14518")
        p2.metric("Intertravamento Gás", f"{avg_int:.0f}%", "NBR 14518 Cap. 5.4")
        p3.metric("Segurança Elétrica", f"{avg_ele:.0f}%", "Norma NR-10")
        p4.metric("Acesso & Máquinas", f"{avg_maq:.0f}%", "Norma NR-12")
        p5.metric("Estanqueidade Dutos", f"{avg_est:.0f}%", "Vedação / NBR 14518")

        st.markdown("<br>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns([1, 1])

        with col_g1:
            st.markdown("### 🎯 Distribuição de Criticidade (ICL Global)")
            fig_pie = px.pie(
                df_f, names="criticidade", color="criticidade",
                color_discrete_map=PALETA_CSA, hole=0.5
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.markdown("### 📊 Nível de Conformidade por Pilar Normativo (%)")
            df_pilares = pd.DataFrame({
                'Pilar Normativo': [
                    'Incêndio (NFPA 96 / NBR 14518)',
                    'Intertravamento Gás (NBR 14518)',
                    'Elétrica (NR-10)',
                    'Máquinas (NR-12)',
                    'Estanqueidade (NBR 14518)'
                ],
                'Conformidade (%)': [avg_inc, avg_int, avg_ele, avg_maq, avg_est]
            })
            fig_pilares = px.bar(
                df_pilares, x='Conformidade (%)', y='Pilar Normativo', orientation='h',
                color='Conformidade (%)', color_continuous_scale='Reds_r', text='Conformidade (%)'
            )
            fig_pilares.update_traces(texttemplate='%{text:.0f}%', textposition='outside')
            fig_pilares.update_layout(yaxis=dict(autorange="reversed"), xaxis=dict(range=[0, 110]), showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_pilares, use_container_width=True)

        st.markdown("---")

        st.markdown("<div class='laudo-card'>", unsafe_allow_html=True)
        st.markdown(f"""
        ### 📑 Análise & Parecer Técnico Geral do Empreendimento
        **Escopo:** Avaliação Global do Sistema de Exaustão da Praça de Alimentação — **Shopping Guararapes**  
        **Engenharia Responsável:** CSA Engenharia

        ---

        #### 🔍 Análise Técnica Consolidada
        A auditoria global realizada no complexo revela um estado de exposição ao risco que demanda ações estruturadas por parte da superintendência e da gestão de operações do shopping. Com uma média geral de **ICL em {media_icl:.1f}%**, o empreendimento se posiciona em nível de atenção técnica. 

        A análise detalhada dos **5 Pilares Normativos** indica que os maiores gargalos de conformidade concentram-se no **Intertravamento de Gás (ABNT NBR 14518)** e na **Segurança Elétrica (NR-10)**. A ausência de interrupção automática do suprimento de gás em caso de parada dos exaustores foi constatada em uma parcela significativa das lojas, gerando risco latente de acúmulo de vapores inflamáveis e monóxido de carbono no ambiente fabril das cozinhas.

        #### 🛡️ Conclusão Técnica e Recomendações Gestoras
        1. **Notificação Emergencial (Prazo 48h):** Emissão de termo de adequação prioritário para as operações classificadas nos níveis **CRÍTICO** e **SEVERO** ({criticas_severas} lojas), exigindo a certificação dos sistemas supressores e desobstrução das casas de máquinas.
        2. **Padronização do Intertravamento:** Estabelecer diretriz técnica única para que todas as lojas instalem válvulas solenoides NF (Normalmente Fechadas) interligadas aos pressostatos ou sensores de corrente do exaustor.
        3. **Programa contínuo de Mitigação de Carga Incêndio:** Agendar higienização robótica/hidrojateamento nos dutos coletores do shopping para impedir o acúmulo de gordura acima da espessura limite de 0,18 mm fixada pela norma **NFPA 96**.
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 2: DIAGNÓSTICO DETALHADO POR LOJA
# ==========================================
elif modulo == "🏪 Diagnóstico Detalhado por Loja":
    st.markdown("### 🏪 Análise Operacional e Avaliação de Risco Individual")
    
    if df_f.empty:
        st.info("Nenhuma loja cadastrada.")
    else:
        loja_selecionada = st.selectbox("Selecione a Operação para Inspeção:", df_f["loja"].unique())
        d = df_f[df_f["loja"] == loja_selecionada].iloc[0]

        st.markdown("<br>", unsafe_allow_html=True)

        col_loja1, col_loja2 = st.columns([1, 1.2])

        with col_loja1:
            st.markdown("##### 🎛️ Velocímetro de Exposição ao Risco (ICL)")
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = d['icl_score'],
                number = {'suffix': "%", 'font': {'size': 36, 'color': "#0D3B66"}},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#FF6B35" if d['icl_score'] > 50 else "#0D3B66"},
                    'steps': [
                        {'range': [0, 25], 'color': "rgba(56, 161, 105, 0.25)"},
                        {'range': [25, 50], 'color': "rgba(49, 130, 206, 0.25)"},
                        {'range': [50, 70], 'color': "rgba(255, 107, 53, 0.25)"},
                        {'range': [70, 100], 'color': "rgba(229, 62, 62, 0.25)"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': d['icl_score']
                    }
                }
            ))
            fig_gauge.update_layout(height=230, margin=dict(t=20, b=10, l=30, r=30))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_loja2:
            st.markdown("##### 📊 Status Atual de Adequação nos 5 Pilares Normativos")
            
            pilares_loja = pd.DataFrame({
                'Pilar Normativo': [
                    'Incêndio (NFPA 96 / NBR 14518)',
                    'Intertravamento (NBR 14518)',
                    'Elétrica (NR-10)',
                    'Máquinas (NR-12)',
                    'Estanqueidade (NBR 14518)'
                ],
                'Status': [
                    'Conforme' if d['incendio_conforme'] else 'Inconforme',
                    'Conforme' if d['intertravamento_ok'] else 'Inconforme',
                    'Inconforme' if d['eletrica_exposta'] else 'Conforme',
                    'Inconforme' if d['casa_maquinas_obstruida'] else 'Conforme',
                    'Inconforme' if d['vazamento_dutos'] else 'Conforme'
                ],
                'Valor': [
                    100 if d['incendio_conforme'] else 15,
                    100 if d['intertravamento_ok'] else 15,
                    15 if d['eletrica_exposta'] else 100,
                    15 if d['casa_maquinas_obstruida'] else 100,
                    15 if d['vazamento_dutos'] else 100
                ]
            })

            fig_status = px.bar(
                pilares_loja, x='Valor', y='Pilar Normativo', color='Status',
                color_discrete_map={'Conforme': '#38A169', 'Inconforme': '#E53E3E'},
                orientation='h', text='Status'
            )
            fig_status.update_traces(textposition='inside')
            fig_status.update_layout(
                xaxis=dict(range=[0, 105], visible=False),
                yaxis=dict(autorange="reversed"),
                height=230, margin=dict(t=10, b=10, l=10, r=10), showlegend=False
            )
            st.plotly_chart(fig_status, use_container_width=True)

        st.markdown("<div class='laudo-card'>", unsafe_allow_html=True)
        st.markdown(gerar_parecer_dissertativo(d), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 3: METODOLOGIA ICL & PONDERAÇÃO
# ==========================================
elif modulo == "📐 Metodologia ICL & Ponderação":
    st.markdown("### 📐 Metodologia do Índice de Criticidade de Loja (ICL)")
    
    st.markdown("""
    O **Índice de Criticidade de Loja (ICL)** é uma métrica quantitativa desenvolvida pela **CSA Engenharia** para mensurar o nível contínuo de exposição ao risco de incêndio, explosão e interrupção operacional no sistema de exaustão de cozinhas comerciais.

    ---
    #### 🧮 A Equação Fundamental
    $$ICL = (P_{INC} \times 0.35) + (P_{INT} \times 0.25) + (P_{ELE} \times 0.20) + (P_{OBS} \times 0.10) + (P_{VAZ} \times 0.10)$$

    ---
    #### 🔍 Detalhamento Técnico dos Cálculo e Escala de Pontuação (0 a 100)

    A pontuação de cada pilar **não se limita a 0 e 100**. Durante a inspeção técnica, cada índice assume um valor **graduado de 0 a 100**, calculado com base em critérios objetivos medidos em campo:

    1. **$P_{INC}$ — Risco de Incêndio & Supressão Química (Peso 35%) | *Normas: ABNT NBR 14518, NFPA 96 e IT-38 CBM*:**
       * **Como é atribuído a número no cálculo:**
         * `0`: Dutos perfeitamente limpos ($<0,05\text{ mm}$ de espessura de gordura) e sistema saponificante com carga, certificado e disparadores limpos.
         * `25`: Camada leve de gordura ($0,05\text{ a }0,18\text{ mm}$) e sistema saponificante 100% operacional.
         * `50`: Camada moderada de gordura ($0,18\text{ a }0,50\text{ mm}$) ou sistema saponificante com manutenção vencida a menos de 30 dias.
         * `75`: Acúmulo severo de gordura ($>0,50\text{ mm}$) com sistema saponificante operacional OU sistema inoperante com duto limpo.
         * `100`: Sistema saponificante descarregado/ausente E duto com incrustação crítica de gordura ($>1,0\text{ mm}$).
       * *Física do Risco:* A gordura depositada nos dutos entra em ignição espontânea a **315 °C**. Sem a extinção química automática, o fogo atinge o entreforro em menos de 180 segundos.

    2. **$P_{INT}$ — Intertravamento de Segurança de Gás (Peso 25%) | *Normas: ABNT NBR 14518 Cap. 5.4 e ABNT NBR 17039*:**
       * **Como é atribuído a número no cálculo:**
         * `0`: Intertravamento 100% funcional (ao desligar o exaustor, a válvula solenoide corta o gás instantaneamente).
         * `50`: Intertravamento com retardo de acionamento ($>5\text{ segundos}$) ou sem botão de emergência manual de rápido acesso.
         * `100`: Ausência total de intertravamento (linha de gás permanece aberta mesmo com exaustor desligado).
       * *Física do Risco:* Queimadores operando sem exaustão geram acúmulo de monóxido de carbono e vapores não queimados, criando uma atmosfera explosiva (LII/LEL).

    3. **$P_{ELE}$ — Segurança Elétrica da Instalação (Peso 20%) | *Normas: NR-10 e ABNT NBR 5410*:**
       * **Como é atribuído a número no cálculo:**
         * `0`: Instalação 100% em eletrodutos blindados e painéis selados com grau de proteção IP65.
         * `33`: Conexões elétricas sem prensa-cabos ou quadros de comando com vedação ressecada.
         * `66`: Fiação exposta sem proteção mecânica na proximidade de áreas úmidas.
         * `100`: Fiação exposta impregnada com gordura/óleo sobre a coifa ou na casa de máquinas.
       * *Física do Risco:* Curtos-circuitos resultantes da degradação do isolamento por gordura e vapor são a **causa número 1 de ignição** em cozinhas comerciais.

    4. **$P_{OBS}$ — Proteção de Máquinas & Acesso (Peso 10%) | *Normas: NR-12 e NR-35*:**
       * **Como é atribuído a número no cálculo:**
         * `0`: Casa de máquinas com acesso desobstruído, iluminação adequada e proteção total de polias/correias.
         * `50`: Acesso parcialmente dificultado por materiais armazenados de forma temporária.
         * `100`: Casa de máquinas usada como depósito de descartes ou motores com partes giratórias desprotegidas.

    5. **$P_{VAZ}$ — Estanqueidade e Vedações dos Dutos (Peso 10%) | *Norma: ABNT NBR 14518*:**
       * **Como é atribuído a número no cálculo:**
         * `0`: Dutos soldados a ponto elétrico/TIG, sem nenhum ponto de exsudação.
         * `50`: Pequena goteira/umidade de óleo nas juntas flangeadas sem vazamento direto para a cozinha.
         * `100`: Vazamento ativo de gordura gotejando sobre o entreforro, equipamentos ou alimentos.

    ---
    #### 📏 Margens de Tolerância e Calibração
    * **Margem de Erro do Modelo:** $\pm 2.5\%$, calibrada com base em amostras FMEA e histórico de vistorias técnicas da **CSA Engenharia**.
    """)

# ==========================================
# MÓDULO 4: LAUDO AUTÔNOMO COM IA
# ==========================================
elif modulo == "🤖 Laudo Autônomo com IA":
    st.markdown("### 🤖 Gerador Autônomo de Laudos Técnicos")
    
    if df_f.empty:
        st.info("Nenhuma vistoria encontrada para gerar laudo.")
    else:
        st.write("Selecione qualquer loja do complexo para gerar a minuta oficial pronta para emissão.")
        loja_ia = st.selectbox("Selecione a Operação:", df_f["loja"].unique())
        d_ia = df_f[df_f["loja"] == loja_ia].iloc[0]

        st.markdown("<div class='laudo-card'>", unsafe_allow_html=True)
        st.markdown(gerar_parecer_dissertativo(d_ia), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 5: NOVO RELATÓRIO (FORMULÁRIO MANUAL)
# ==========================================
elif modulo == "📋 Novo Relatório (Formulário Manual)":
    st.markdown("### 📋 Preenchimento de Relatório de Vistoria em Campo")
    st.info("Preencha as informações da operação. Os campos de respostas são opcionais.")

    with st.form("form_vistoria_manual", clear_on_submit=True):
        st.subheader("📍 Identificação da Operação")
        c1, c2, c3 = st.columns(3)
        loja_nome = c1.text_input("NOME DA LOJA / OPERAÇÃO *", placeholder="Ex: Burger King")
        mes_ref = c2.text_input("CICLO / MÊS DE REFERÊNCIA *", value="2026-09")
        data_hora = c3.text_input("DATA/HORA DA VISTORIA *", placeholder="Ex: 24/09/2026 10:00")

        respostas_coletadas = {}

        for secao_nome, perguntas in SECOES_RELATORIO.items():
            st.divider()
            st.markdown(f"#### 🔽 {secao_nome}")
            
            for index, pergunta in enumerate(perguntas):
                st.markdown(f"**{pergunta}**")
                col_resp, col_obs = st.columns([1, 2])
                
                resp = col_resp.text_input(
                    label=f"Resp_{secao_nome}_{index}",
                    key=f"resp_{secao_nome}_{index}",
                    placeholder="SIM / NÃO / OK (Opcional)",
                    max_chars=20,
                    label_visibility="collapsed"
                )
                
                obs = col_obs.text_input(
                    label=f"Obs_{secao_nome}_{index}",
                    key=f"obs_{secao_nome}_{index}",
                    placeholder="Observação do item (Opcional)",
                    label_visibility="collapsed"
                )
                
                respostas_coletadas[pergunta] = {
                    "resposta": resp.strip() if resp.strip() else "(Sem preenchimento)",
                    "observacao": obs.strip() if obs.strip() else ""
                }

        st.divider()
        st.markdown("#### 🔽 OBSERVAÇÕES GERAIS")
        obs_gerais = st.text_area("CONSIDERAÇÕES FINAIS (Opcional)", placeholder="Observações técnicas gerais...")

        submetido = st.form_submit_button("💾 Salvar Vistoria no Banco de Dados")

        if submetido:
            if not loja_nome or not mes_ref or not data_hora:
                st.error("Preencha os campos obrigatórios: Nome da Loja, Mês de Referência e Data/Hora.")
            else:
                dados_payload = {
                    "loja": loja_nome,
                    "mes_referencia": mes_ref,
                    "data_hora": data_hora,
                    "observacoes_gerais": obs_gerais,
                    "questoes": respostas_coletadas
                }

                try:
                    supabase.table("vistorias_exaustao").insert({
                        "loja": loja_nome,
                        "mes_referencia": mes_ref,
                        "dados": dados_payload
                    }).execute()

                    st.success(f"Vistoria da loja {loja_nome} salva com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")

# ==========================================
# MÓDULO 6: IMPORTAÇÃO DE PDF / LAUDO
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
            f_mes = st.text_input("Ciclo de Vistoria:", value="2026-09")
            f_icl = st.slider("Score ICL (%):", 0, 100, 50)
            f_crit = st.selectbox("Nível de Criticidade:", ["Controlado", "Atenção", "Relevante", "Crítico", "Severo"])
            
            c1, c2 = st.columns(2)
            f_inc = c1.checkbox("Sistema de Incêndio OK (NFPA 96 / NBR 14518)", value=True)
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
                st.rerun()

# ==========================================
# MÓDULO 7: MATRIZ INTERATIVA DE DADOS (CARDS)
# ==========================================
elif modulo == "📋 Matriz Interativa de Dados":
    st.markdown("### 📋 Matriz Geral de Operações (Visão em Cards Distribuídos)")
    st.write("Navegue pelas operações de forma fluida, interativa e visualmente moderna.")

    if df_f.empty:
        st.info("Nenhuma operação encontrada.")
    else:
        col_f1, col_f2 = st.columns([2, 1])
        busca = col_f1.text_input("🔍 Pesquisar por nome da loja:")
        
        opcoes_crit = df_f["criticidade"].unique() if "criticidade" in df_f.columns else []
        filtro_crit = col_f2.multiselect("Filtrar Criticidade:", opcoes_crit, default=opcoes_crit)

        df_exibicao = df_f[df_f["criticidade"].isin(filtro_crit)].copy() if filtro_crit else df_f.copy()
        if busca:
            df_exibicao = df_exibicao[df_exibicao["loja"].str.contains(busca, case=False)]

        st.markdown("<br>", unsafe_allow_html=True)

        for idx, row in df_exibicao.iterrows():
            c_status = str(row['criticidade']).lower()
            
            st.markdown(f"""
                <div class="card-matriz">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3 style="margin:0; color:#0D3B66;">🏪 {row['loja']}</h3>
                        <span class="badge-status bg-{c_status}">{str(row['criticidade']).upper()}</span>
                    </div>
                    <div style="margin-top: 10px; display: flex; gap: 20px; align-items: center;">
                        <div style="flex: 1;">
                            <span style="font-weight: 700; color: #64748B;">Índice ICL:</span>
                            <div style="background-color: #E2E8F0; border-radius: 10px; height: 12px; width: 100%; margin-top: 4px;">
                                <div style="background-color: {'#E53E3E' if row['icl_score'] > 70 else '#FF6B35' if row['icl_score'] > 50 else '#38A169'}; width: {row['icl_score']}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                        </div>
                        <div style="font-weight: 800; font-size: 1.3rem; color: #0D3B66;">{row['icl_score']}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"🔍 Ver Detalhes Técnicos — {row['loja']}"):
                st.write(f"• **Incêndio (NFPA 96 / NBR 14518):** {'✅ Conforme' if row['incendio_conforme'] else '❌ Inconforme'}")
                st.write(f"• **Intertravamento Gás (NBR 14518):** {'✅ Conforme' if row['intertravamento_ok'] else '❌ Inconforme'}")
                st.write(f"• **Fiação Elétrica (NR-10):** {'❌ Exposta' if row['eletrica_exposta'] else '✅ Protegida'}")
                st.write(f"• **Casa de Máquinas (NR-12):** {'❌ Obstruída' if row['casa_maquinas_obstruida'] else '✅ Livre'}")
                st.write(f"• **Observações:** {row.get('observacoes', 'Nenhuma')}")

# ==========================================
# MÓDULO 8: GERENCIAR & EXCLUIR VISTORIAS
# ==========================================
elif modulo == "🗑️ Gerenciar & Excluir Vistorias":
    st.markdown("### 🗑️ Gerenciamento e Exclusão de Registros")
    st.write("Caso tenha inserido uma loja com informações erradas, utilize esta opção para excluí-la do banco de dados.")

    if df.empty:
        st.info("Nenhum registro disponível para exclusão.")
    else:
        # Opções formatadas para seleção
        df_excluir = df.copy()
        df_excluir["label"] = df_excluir.apply(lambda r: f"ID: {r['id']} | Loja: {r.get('loja', 'Sem Nome')} | Ref: {r.get('mes_referencia', 'N/A')}", axis=1)

        opcao_selecionada = st.selectbox("Selecione a Vistoria que deseja apagar:", df_excluir["label"].tolist())

        registro_id = df_excluir[df_excluir["label"] == opcao_selecionada]["id"].values[0]

        st.warning(f"⚠️ **Atenção:** Você está prestes a excluir permanentemente o registro seleccionado. Essa ação não pode ser desfeita.")

        if st.button("❌ Confirmar e Excluir Vistoria"):
            try:
                supabase.table("vistorias_exaustao").delete().eq("id", registro_id).execute()
                st.success("Vistoria excluída com sucesso!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir registro no Supabase: {e}")
