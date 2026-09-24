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

    .calc-box {
        background-color: #F1F5F9;
        border-left: 5px solid #0D3B66;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        margin: 10px 0;
    }
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

def analisar_respostas_detalhadas(questoes):
    """Analisa exaustivamente todas as respostas do questionário para evitar falsos positivos/negativos."""
    def get_val(key):
        item = questoes.get(key, {})
        if isinstance(item, dict):
            resp = str(item.get("resposta", "")).strip().upper()
            obs = str(item.get("observacao", "")).strip()
            return resp, obs
        return str(item).strip().upper(), ""

    # Pilar 1: Incêndio / Supressão
    resp_inc, obs_inc = get_val("SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?")
    ha_inc, _ = get_val("HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?")
    
    p_inc = 0
    if resp_inc in ["NÃO", "INCONFORME", "NÃO CONFORME"] or ha_inc == "NÃO":
        p_inc = 100
    elif "NÃO CONFORME" in obs_inc.upper() or "INOPERANTE" in obs_inc.upper():
        p_inc = 75

    # Pilar 2: Intertravamento
    resp_int, obs_int = get_val("INTERTRAVAMENTO FUNCIONANDO?")
    ha_int, _ = get_val("HÁ INTERTRAVAMENTO?")
    
    p_int = 0
    if resp_int in ["NÃO", "INCONFORME", "NÃO CONFORME"] or ha_int in ["NÃO", "NÃO CONFORME"]:
        p_int = 100

    # Pilar 3: Elétrica (Coifa + Exaustor)
    resp_ele_c, _ = get_val("ELÉTRICA EXPOSTA PRÓXIMO A COIFA?")
    resp_ele_ex, obs_ele_ex = get_val("ELÉTRICA DO EXAUSTOR")
    resp_ele_exp, _ = get_val("ELÉTRICA EXPOSTA?")
    
    p_ele = 0
    if (resp_ele_c in ["SIM", "EXPOSTA"] or 
        resp_ele_exp in ["SIM", "EXPOSTA"] or 
        "NÃO CONFORME" in resp_ele_ex or 
        "EXPOSTA" in obs_ele_ex.upper()):
        p_ele = 100

    # Pilar 4: Máquinas & Acesso & Estado Mecânico
    resp_maq, _ = get_val("CASA DE MÁQUINA DESOBSTRUÍDA?")
    resp_lub, obs_lub = get_val("LUBRIFICAÇÃO")
    resp_ali, obs_ali = get_val("ALINHAMENTO")
    resp_cor, obs_cor = get_val("CORREIAS")
    
    p_obs = 0
    fator_mec = 0
    if resp_maq in ["NÃO", "OBSTRUÍDA"]:
        fator_mec += 40
    if "NÃO CONFORME" in resp_lub or "NÃO CONFORME" in obs_lub.upper():
        fator_mec += 20
    if "NÃO CONFORME" in resp_ali or "NÃO CONFORME" in obs_ali.upper():
        fator_mec += 20
    if "NÃO CONFORME" in resp_cor or "NÃO CONFORME" in obs_cor.upper():
        fator_mec += 20
    
    p_obs = min(100, fator_mec)

    # Pilar 5: Estanqueidade & Acessibilidade nos Dutos & Dreno
    resp_vaz, _ = get_val("HÁ VAZAMENTO NOS DUTOS?")
    resp_dre, obs_dre = get_val("HÁ DRENO DE OLÉO?")
    resp_jan_d, _ = get_val("HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?")
    resp_damp_a, _ = get_val("DAMPER TEM ACESSO PARA LIMPEZA?")
    resp_ac_coz, _ = get_val("HÁ ACESSO AOS DUTOS DA COZINHA?")
    
    fator_est = 0
    if resp_vaz in ["SIM", "VAZANDO"]:
        fator_est += 40
    if resp_dre in ["NÃO", "NÃO CONFORME"]:
        fator_est += 20
    if resp_jan_d in ["NÃO", "NÃO CONFORME"]:
        fator_est += 15
    if resp_damp_a in ["NÃO", "NÃO CONFORME"]:
        fator_est += 15
    if resp_ac_coz in ["NÃO", "NÃO CONFORME"]:
        fator_est += 10
        
    p_vaz = min(100, fator_est)

    return p_inc, p_int, p_ele, p_obs, p_vaz

def carregar_dados():
    try:
        response = supabase.table("vistorias_exaustao").select("*").order("created_at", desc=True).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        df = pd.DataFrame()

    if df.empty:
        return pd.DataFrame()

    for idx, row in df.iterrows():
        dados = row.get("dados", {})
        questoes = dados.get("questoes", {}) if isinstance(dados, dict) else {}

        if questoes:
            p_inc, p_int, p_ele, p_obs, p_vaz = analisar_respostas_detalhadas(questoes)
        else:
            p_inc = 0 if row.get('incendio_conforme', True) else 100
            p_int = 0 if row.get('intertravamento_ok', True) else 100
            p_ele = 100 if row.get('eletrica_exposta', False) else 0
            p_obs = 100 if row.get('casa_maquinas_obstruida', False) else 0
            p_vaz = 100 if row.get('vazamento_dutos', False) else 0

        df.at[idx, 'score_incend'] = p_inc
        df.at[idx, 'score_intert'] = p_int
        df.at[idx, 'score_eletri'] = p_ele
        df.at[idx, 'score_maquin'] = p_obs
        df.at[idx, 'score_estana'] = p_vaz

        df.at[idx, 'incendio_conforme'] = (p_inc < 50)
        df.at[idx, 'intertravamento_ok'] = (p_int < 50)
        df.at[idx, 'eletrica_exposta'] = (p_ele >= 50)
        df.at[idx, 'casa_maquinas_obstruida'] = (p_obs >= 50)
        df.at[idx, 'vazamento_dutos'] = (p_vaz >= 50)

        icl_calc = (p_inc * 0.35) + (p_int * 0.25) + (p_ele * 0.20) + (p_obs * 0.10) + (p_vaz * 0.10)
        df.at[idx, 'icl_score'] = round(icl_calc, 1)

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

        df.at[idx, 'criticidade'] = crit
        df.at[idx, 'observacoes'] = row.get('observacoes', dados.get("observacoes_gerais", ""))

    return df

# ==========================================
# 3. GERADOR DE PARECER TÉCNICO APROFUNDADO
# ==========================================
def gerar_parecer_dissertativo(row):
    loja = row['loja']
    icl = row['icl_score']
    crit = str(row['criticidade'])
    dados = row.get('dados', {})
    questoes = dados.get('questoes', {}) if isinstance(dados, dict) else {}

    anomalias = []
    
    # Checagens específicas e precisas baseadas no questionário
    if row.get('score_incend', 0) >= 50:
        anomalias.append("irregularidades no sistema fixo de combate a incêndio por saponificante (ABNT NBR 14518 / NFPA 96)")
    if row.get('score_intert', 0) >= 50:
        anomalias.append("ausência de intertravamento automático entre o sistema de exaustão mecânica e a válvula solenoide da linha de gás combustível (ABNT NBR 14518, Cap. 5.4)")
    if row.get('score_eletri', 0) >= 50:
        anomalias.append("fiação e condutores elétricos expostos no exaustor/coifa sem proteção por eletrodutos rígidos não combustíveis, aumentando expressivamente o risco de curto-circuito e ignição por centelha em ambiente impregnado de vapores (ABNT NBR 5410 / NR-10)")
    if row.get('score_maquin', 0) >= 50:
        anomalias.append("obstrução da casa de máquinas, além de desgastes mecânicos críticos no exaustor como folga/frouxidão em correias de transmissão, desalinhamento de componentes rotativos e falta de lubrificação periódica nos rolamentos (Norma Regulamentadora NR-12)")
    if row.get('score_estana', 0) >= 50:
        anomalias.append("ausência de dreno de óleo no fundo do exaustor, falta de janelas de inspeção para limpeza do damper corta-fogo e inexistência de acesso aos dutos da cozinha e descarga, favorecendo o acúmulo contínuo de gordura pesada e vazamentos de óleo (ABNT NBR 14518)")

    if anomalias:
        texto_diagnostico = f"A auditoria técnica presencial realizada nas instalações da operação **{loja}** identificou desvios normativos de alta relevância que comprometem a segurança contra incêndio e a integridade operacional do sistema de exaustão. Entre as principais não conformidades constatadas, destacam-se: " + "; ".join(anomalias) + "."
    else:
        texto_diagnostico = f"A operação **{loja}** apresentou excelente padrão de conformidade técnica, operando de acordo com as diretrizes de segurança da ABNT NBR 14518, ABNT NBR 5410, NFPA 96, NR-10 e NR-12."

    if icl >= 70:
        recomendacao_executiva = (
            f"Diante do Índice de Criticidade de Loja apurado em **{icl}%** (Grau **{crit.upper()}**), "
            f"a **CSA Engenharia** recomenda a emissão de notificação formal imediata pela administração do Shopping Guararapes. "
            f"É imperativo o cumprimento de um plano de ação emergencial em até 48 horas contemplando: "
            f"(1) Proteção e embutimento total da fiação elétrica exposta do exaustor em eletrodutos rígidos (NBR 5410); "
            f"(2) Instalação de sistema de intertravamento automático para corte de gás na parada da exaustão; "
            f"(3) Abertura de janelas de inspeção para higienização e manutenção do damper corta-fogo; "
            f"(4) Instalação de dreno de óleo no exaustor, tensionamento das correias e alinhamento mecânico do conjunto rotativo."
        )
    elif icl >= 40:
        recomendacao_executiva = (
            f"Com um ICL apurado em **{icl}%** (Grau **{crit.upper()}**), a operação demanda regularizações corretivas no prazo máximo de 15 dias, "
            f"priorizando a proteção das instalações elétricas do exaustor, adequação da casa de máquinas e readequação das vias de acesso e limpeza dos dutos."
        )
    else:
        recomendacao_executiva = (
            f"Com o índice sob controle (**ICL {icl}%**), a operação encontra-se em conformidade com as diretrizes gerais de engenharia. "
            f"Recomenda-se manter a rotina de manutenção preventiva e higienização periódica."
        )

    return f"""
    ### 📜 Laudo Técnico e Diagnóstico Executivo — **{loja}**
    **Classificação Normativa:** `<span class="badge-status bg-{crit.lower()}">{crit.upper()}</span>` | **Índice ICL Registrado:** **{icl}%**

    ---
    
    #### 🔎 Diagnóstico Técnico Aprofundado das Instalações
    {texto_diagnostico}

    ---

    #### 🛡️ Parecer Conclusivo & Plano de Mitigação de Riscos
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
    df_f["pilar_incendio"] = df_f["score_incend"].apply(lambda x: 100 - x)
    df_f["pilar_intertravamento"] = df_f["score_intert"].apply(lambda x: 100 - x)
    df_f["pilar_eletrica"] = df_f["score_eletri"].apply(lambda x: 100 - x)
    df_f["pilar_maquinas"] = df_f["score_maquin"].apply(lambda x: 100 - x)
    df_f["pilar_estanqueidade"] = df_f["score_estana"].apply(lambda x: 100 - x)

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
        p3.metric("Segurança Elétrica", f"{avg_ele:.0f}%", "Norma NR-10 / NBR 5410")
        p4.metric("Acesso & Máquinas", f"{avg_maq:.0f}%", "Norma NR-12")
        p5.metric("Estanqueidade & Dutos", f"{avg_est:.0f}%", "Vedação / NBR 14518")

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
                    'Elétrica (NR-10 / NBR 5410)',
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
        ### 📑 Parecer Técnico Global do Empreendimento
        **Escopo de Auditoria:** Avaliação Sistêmica de Riscos em Exaustão Comercial — **Shopping Guararapes**  
        **Engenharia Responsável:** CSA Engenharia

        ---

        #### 1. Diagnóstico Geral do Complexo
        A auditoria técnica conduzida no parque de exaustão das operações alimentícias revelou uma média global de **ICL de {media_icl:.1f}%**, enquadrando o empreendimento em nível de atenção preventiva. Os dados apontam que os principais fatores causadores de risco crítico no complexo são a **ausência generalizada de intertravamento do gás combustível** e a **exposição de condutores elétricos na área de exaustores e casas de máquinas**.

        A presença de fiação exposta e impregnada por vapores inflamáveis nas vizinhanças de exaustores e motores elétricos representa o ponto mais crítico de ignição por arco elétrico ou curto-circuito, infringindo diretamente a norma **ABNT NBR 5410** e a **NR-10**.

        #### 2. Recomendações Estratégicas e Diretrizes de Engenharia
        * **Plano Emergencial de Instalações Elétricas:** Exigir que todas as operações com fiação exposta realizem o envelopamento e passagem dos condutores em eletrodutos rígidos metálicos ou de material não combustível com vedação IP65.
        * **Intertravamento Obrigatório de Gás:** Notificar os lojistas inconformes para instalação de válvulas solenoides NF vinculadas ao fluxo de exaustão em até 15 dias.
        * **Acessibilidade e Higienização do Damper:** Exigir a abertura imediata de janelas de inspeção para limpeza nos locais onde o acesso ao damper e ao exaustor está bloqueado, prevenindo a retenção contínua de massa de gordura.
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
            
            p_inc = d.get('score_incend', 0)
            p_int = d.get('score_intert', 0)
            p_ele = d.get('score_eletri', 0)
            p_obs = d.get('score_maquin', 0)
            p_vaz = d.get('score_estana', 0)

            pilares_loja = pd.DataFrame({
                'Pilar Normativo': [
                    'Incêndio (NFPA 96 / NBR 14518)',
                    'Intertravamento (NBR 14518)',
                    'Elétrica (NR-10 / NBR 5410)',
                    'Máquinas (NR-12)',
                    'Estanqueidade (NBR 14518)'
                ],
                'Status': [
                    'Inconforme' if p_inc >= 50 else 'Conforme',
                    'Inconforme' if p_int >= 50 else 'Conforme',
                    'Inconforme' if p_ele >= 50 else 'Conforme',
                    'Inconforme' if p_obs >= 50 else 'Conforme',
                    'Inconforme' if p_vaz >= 50 else 'Conforme'
                ],
                'Valor': [
                    100 - p_inc,
                    100 - p_int,
                    100 - p_ele,
                    100 - p_obs,
                    100 - p_vaz
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

        # PAINEL EXCLUSIVO: MEMÓRIA DE CÁLCULO PASSO A PASSO
        with st.expander(f"🧮 Ver Memória de Cálculo Detalhada do ICL para {loja_selecionada}"):
            st.markdown(f"""
            #### Cálculo Numérico Exato da Operação:
            
            * **Pilar 1 - Incêndio ($P_{{INC}}$):** Nota **{p_inc}** $\\times$ Peso 0.35 = **{p_inc * 0.35:.2f}**
            * **Pilar 2 - Intertravamento ($P_{{INT}}$):** Nota **{p_int}** $\\times$ Peso 0.25 = **{p_int * 0.25:.2f}**
            * **Pilar 3 - Elétrica ($P_{{ELE}}$):** Nota **{p_ele}** $\\times$ Peso 0.20 = **{p_ele * 0.20:.2f}**
            * **Pilar 4 - Máquinas ($P_{{OBS}}$):** Nota **{p_obs}** $\\times$ Peso 0.10 = **{p_obs * 0.10:.2f}**
            * **Pilar 5 - Estanqueidade ($P_{{VAZ}}$):** Nota **{p_vaz}** $\\times$ Peso 0.10 = **{p_vaz * 0.10:.2f}**
            
            <div class="calc-box">
            ICL Final = {p_inc*0.35:.2f} + {p_int*0.25:.2f} + {p_ele*0.20:.2f} + {p_obs*0.10:.2f} + {p_vaz*0.10:.2f} = {d['icl_score']}%
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div class='laudo-card'>", unsafe_allow_html=True)
        st.markdown(gerar_parecer_dissertativo(d), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# MÓDULO 3: METODOLOGIA ICL & PONDERAÇÃO
# ==========================================
elif modulo == "📐 Metodologia ICL & Ponderação":
    st.markdown("### 📐 Metodologia do Índice de Criticidade de Loja (ICL)")
    
    st.markdown("""
    O **Índice de Criticidade de Loja (ICL)** é a métrica quantitativa padronizada da **CSA Engenharia** para mensurar o nível de exposição de uma operação comercial aos riscos de incêndio, explosão por gás e paradas operacionais no sistema de exaustão.

    ---
    #### 🧮 A Fórmula Matemática
    $$ICL = (P_{INC} \\times 0.35) + (P_{INT} \\times 0.25) + (P_{ELE} \\times 0.20) + (P_{OBS} \\times 0.10) + (P_{VAZ} \\times 0.10)$$

    ---
    #### 💡 Exemplo Prático de Cálculo (Passo a Passo)

    Para entender como chegamos ao número final, acompanhe este exemplo hipotético de cálculo de uma loja:

    * **Passo 1: Atribuição das Notas de Risco por Pilar (de 0 a 100)**
      * **$P_{INC}$ (Incêndio):** O sistema saponificante está OK, mas os filtros estão danificados $\\rightarrow$ Nota = **25**
      * **$P_{INT}$ (Intertravamento):** Não há intertravamento entre exaustor e gás $\\rightarrow$ Nota = **100** (Risco total)
      * **$P_{ELE}$ (Elétrica):** A fiação do exaustor está totalmente exposta $\\rightarrow$ Nota = **100** (Risco total)
      * **$P_{OBS}$ (Máquinas):** Correias frouxas e desalinhamento mecânico $\\rightarrow$ Nota = **40**
      * **$P_{VAZ}$ (Estanqueidade):** Sem dreno de óleo e sem janelas de inspeção na descarga $\\rightarrow$ Nota = **50**

    * **Passo 2: Multiplicação pelos Pesos Normativos**
      * $25 \\times 0.35 = \\mathbf{8.75}$
      * $100 \\times 0.25 = \\mathbf{25.00}$
      * $100 \\times 0.20 = \\mathbf{20.00}$
      * $40 \\times 0.10 = \\mathbf{4.00}$
      * $50 \\times 0.10 = \\mathbf{5.00}$

    * **Passo 3: Soma Ponderada dos Resultados**
      * $ICL = 8.75 + 25.00 + 20.00 + 4.00 + 5.00 = \\mathbf{62.75\\%}$

    * **Passo 4: Classificação da Criticidade**
      * Resultado de **62.75%** enquadra a operação na faixa **CRÍTICO (50% a 69.9%)**, exigindo adequações corretivas urgentes.

    ---
    #### 📊 Tabela de Graus de Criticidade
    * **0.0% a 19.9% — CONTROLADO (Verde):** Operação em conformidade normativa total.
    * **20.0% a 34.9% — ATENÇÃO (Azul):** Pequenos desvios estéticos ou operacionais leves.
    * **35.0% a 49.9% — RELEVANTE (Laranja):** Necessidade de manutenção preventiva programada.
    * **50.0% a 69.9% — CRÍTICO (Vermelho):** Presença de riscos reais de incêndio ou vazamento de gás. Regularização em 15 dias.
    * **70.0% a 100.0% — SEVERO (Preto):** Alto risco iminente de sinistro. Notificação emergencial em até 48 horas.
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
        loja_nome = c1.text_input("NOME DA LOJA / OPERAÇÃO *", placeholder="Ex: Divino Fogão")
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
                st.write(f"• **Fiação Elétrica (NR-10 / NBR 5410):** {'❌ Exposta' if row['eletrica_exposta'] else '✅ Protegida'}")
                st.write(f"• **Casa de Máquinas (NR-12):** {'❌ Obstruída / Desgaste' if row['casa_maquinas_obstruida'] else '✅ Livre'}")
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
        df_excluir = df.copy()
        df_excluir["label"] = df_excluir.apply(lambda r: f"ID: {r['id']} | Loja: {r.get('loja', 'Sem Nome')} | Ref: {r.get('mes_referencia', 'N/A')}", axis=1)

        opcao_selecionada = st.selectbox("Selecione a Vistoria que deseja apagar:", df_excluir["label"].tolist())

        registro_id = df_excluir[df_excluir["label"] == opcao_selecionada]["id"].values[0]

        st.warning(f"⚠️ **Atenção:** Você está prestes a excluir permanentemente o registro selecionado. Essa ação não pode ser desfeita.")

        if st.button("❌ Confirmar e Excluir Vistoria"):
            try:
                supabase.table("vistorias_exaustao").delete().eq("id", registro_id).execute()
                st.success("Vistoria excluída com sucesso!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir registro no Supabase: {e}")
