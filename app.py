import re
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="CSA Engenharia | Sistema de Exaustão", page_icon="🛡️", layout="wide")

# =========================================================
# VISUAL — preserva a linguagem do painel anterior, mas
# privilegia cartões, gráficos simples, acordeões e textos.
# =========================================================
st.markdown("""
<style>
.stApp{background:#F7F9FC;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.block-container{padding-top:1.1rem;padding-bottom:2rem}
.csa-hero{background:linear-gradient(135deg,#0D3B66 0%,#07305A 65%,#0B477C 100%);padding:28px 30px;border-radius:20px;color:#fff;margin-bottom:20px;border-bottom:5px solid #FF6B35;box-shadow:0 8px 25px rgba(13,59,102,.12)}
.csa-hero h1{color:#fff!important;font-size:2.1rem;font-weight:850;margin:0}.csa-hero p{color:#DDEAF5;margin:7px 0 0;font-size:.98rem}
.kpi{background:#fff;padding:16px 18px;border-radius:16px;border:1px solid #E2E8F0;height:100%;box-shadow:0 3px 12px rgba(15,23,42,.04)}
.kpi.red{border-left:6px solid #E53E3E}.kpi.orange{border-left:6px solid #FF6B35}.kpi.green{border-left:6px solid #38A169}.kpi.blue{border-left:6px solid #3182CE}.kpi.dark{border-left:6px solid #0D3B66}
.kpi-label{font-size:.72rem;color:#64748B;font-weight:800;text-transform:uppercase;letter-spacing:.03em}.kpi-value{font-size:1.65rem;color:#0D3B66;font-weight:850;line-height:1.2}.kpi-sub{font-size:.74rem;color:#94A3B8;margin-top:4px}
.note{background:#EFF6FF;border-left:5px solid #3182CE;padding:14px 16px;border-radius:10px;margin:12px 0;color:#17324D}
.warn{background:#FFF7ED;border-left:5px solid #FF6B35;padding:14px 16px;border-radius:10px;margin:12px 0;color:#5A2B0C}
.good{background:#F0FDF4;border-left:5px solid #38A169;padding:14px 16px;border-radius:10px;margin:12px 0;color:#14532D}
.finding{background:#fff;border:1px solid #E2E8F0;border-left:5px solid #E53E3E;border-radius:12px;padding:13px 15px;margin:7px 0;box-shadow:0 2px 8px rgba(15,23,42,.03)}
.finding.att{border-left-color:#FF6B35}.finding.info{border-left-color:#3182CE}.finding.ok{border-left-color:#38A169}
.section-card{background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:18px;margin:10px 0;box-shadow:0 3px 12px rgba(15,23,42,.03)}
.small{font-size:.84rem;color:#64748B}.big-text{font-size:1.02rem;line-height:1.65;color:#243B53}
.pill{display:inline-block;padding:5px 9px;border-radius:999px;background:#EEF2FF;color:#334155;font-size:.75rem;font-weight:750;margin-right:5px}
.method-box{background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:18px;height:100%}
.stTabs [data-baseweb="tab"]{font-weight:750}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def db() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = db()

# =========================================================
# FORMULÁRIO — baseado exatamente nos campos apresentados
# nos relatórios de input enviados pelo usuário.
# =========================================================
YESNO = ["SIM", "NÃO", "N/A"]
CONFORME = ["Conforme", "Não conforme", "N/A"]

FORM_SECTIONS = {
"DADOS DA COIFA": [
 ("FABRICANTE", "text", None),
 ("TIPO", "select", ["PAREDE", "CENTRAL", "LAVATÓRIA", "OUTRO", "N/A"]),
 ("VAZÃO DE EXAUSTÃO", "text", None),
 ("HÁ LAVADOR DE GASES?", "select", YESNO),
 ("HÁ LUMINÁRIA NA COIFA", "select", YESNO),
 ("MATERIAL DA LUMINÁRIA EM CONFORMIDADE?", "select", YESNO),
 ("HÁ ALÇAPÃO NA COZINHA?", "select", YESNO),
 ("EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)", "select", YESNO),
 ("ELÉTRICA EXPOSTA PRÓXIMO A COIFA?", "select", YESNO),
 ("HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?", "select", YESNO),
 ("SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?", "select", YESNO),
 ("EXISTEM FILTROS?", "select", YESNO),
 ("QUAL O TIPO DE FILTROS?", "select", ["INERCIAL", "OUTROS", "N/A"]),
 ("OS FILTROS ESTÃO COMPLETOS?", "select", YESNO),
 ("OS FILTROS ESTÃO DANIFICADOS?", "select", YESNO),
 ("SISTEMA LAVATÓRIO OPERANTE?", "select", YESNO),
 ("QUADRO DE AUTOMAÇÃO COM ACESSO E OPERANTE?", "select", YESNO),
 ("MATERIAIS DA INFRA HIDRÁULICA APROPRIADOS?", "select", YESNO),
 ("A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?", "select", YESNO),
 ("BICOS INJETORES EM CONFORMIDADE?", "select", YESNO),
 ("FLAUTA DA COIFA EM CONFORMIDADE?", "select", YESNO),
 ("BOIA DA COIFA EM CONFORMIDADE?", "select", YESNO),
 ("BOMBA DE ÁGUA ESTÁ OPERANTE?", "select", YESNO),
 ("HÁ PRODUTO NO RESERVATÓRIO?", "select", YESNO),
 ("DOSADOR OPERANTE?", "select", YESNO),
],
"DADOS DO EXAUSTOR": [
 ("CASA DE MÁQUINA DESOBSTRUÍDA?", "select", YESNO),
 ("FABRICANTE DO EXAUSTOR", "text", None),
 ("TIPO", "select", ["LIMIT-LOAD", "CENTRÍFUGO", "AXIAL", "OUTRO", "N/A"]),
 ("LUBRIFICAÇÃO", "select", CONFORME),
 ("ALINHAMENTO", "select", CONFORME),
 ("BALACEAMENTO", "select", CONFORME),
 ("CORREIAS", "select", CONFORME),
 ("REFERÊNCIA DA CORREA", "text", None),
 ("HÁ PROTETOR DE CORREIA?", "select", YESNO),
 ("MANCAIS", "select", CONFORME),
 ("REFERÊNCIA DOS MANCAIS", "text", None),
 ("POLIAS", "select", CONFORME),
 ("REFERÊNCIA DAS POLIA MOTORA", "text", None),
 ("REFERÊNCIA DAS POLIA MOVIDA", "text", None),
 ("ROLAMENTOS", "select", CONFORME),
 ("ELÉTRICA DO EXAUSTOR", "select", CONFORME),
 ("ELÉTRICA EXPOSTA?", "select", YESNO),
 ("ACESSO PARA MANUTENÇÃO?", "select", YESNO),
 ("HÁ JANELA DE INSPEÇÃO NO EXAUSTOR?", "select", YESNO),
 ("HÁ DRENO DE OLÉO?", "select", YESNO),
 ("BASE DO EXAUSTOR", "select", CONFORME),
 ("VIBRAÇÃO E RUÍDOS NORMAIS?", "select", YESNO),
 ("PINTURA", "select", CONFORME),
 ("HÁ LAVADOR DE GASES?", "select", YESNO),
 ("HÁ INTERTRAVAMENTO?", "select", YESNO),
 ("INTERTRAVAMENTO FUNCIONANDO?", "select", YESNO),
],
"DUTOS DE EXAUSTÃO": [
 ("DUTOS EM BOM ESTADO DE CONSERVAÇÃO?", "select", YESNO),
 ("HÁ VAZAMENTO NOS DUTOS?", "select", YESNO),
 ("TIPO DA CHAPA DO DUTO", "select", ["AÇO CARBONO", "GALVANIZADO", "INOX", "OUTRO", "N/A"]),
 ("TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? SUCÇÃO", "select", YESNO),
 ("TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? DESCARGA", "select", YESNO),
 ("TIPO DO ISOLAMENTO", "select", ["LÃ DE CERÂMICA", "CERÂMICA", "LÃ MINERAL", "OUTRO", "N/A"]),
 ("EXISTE DUTO SEM ACESSO?", "select", YESNO),
 ("HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA SUCÇÃO?", "select", YESNO),
 ("QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?", "select", YESNO),
 ("HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?", "select", YESNO),
 ("QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?", "select", YESNO),
 ("ONDE NECESSITA DE JANELAS?", "text", None),
 ("HÁ DAMPER CORTA FOGO?", "select", YESNO),
 ("TIPO DO DAMPER (MECÂNICO/ELÉTRICO)", "select", ["MECÂNICO", "ELÉTRICO", "N/A"]),
 ("DAMPER EM BOM ESTADO E OPERANTE?", "select", YESNO),
 ("DAMPER ESTÁ ACESSÍVEL?", "select", YESNO),
 ("DAMPER TEM ACESSO PARA LIMPEZA?", "select", YESNO),
 ("HÁ SISTEMA DE COMBATE A INCÊNDIO (CO2)?", "select", YESNO),
 ("SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE (CO2)?", "select", YESNO),
 ("HÁ ACESSO AOS DUTOS DA COZINHA?", "select", YESNO),
 ("HÁ LONA DE ACOPLAMENTO?", "select", YESNO),
 ("LONA DE ACOPLAMENTO", "select", CONFORME),
],
}

# Compatibilidade com versões anteriores do formulário/JSON.
# Os nomes acima são preservados; nenhuma pergunta antiga é descartada.
ALL_QUESTIONS = [(sec, q, typ, opts) for sec, items in FORM_SECTIONS.items() for q, typ, opts in items]

PILLARS = {
 "Segurança Contra Incêndio": [
  "HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?", "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?",
  "ELÉTRICA EXPOSTA PRÓXIMO A COIFA?", "EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)",
  "HÁ DAMPER CORTA FOGO?", "DAMPER EM BOM ESTADO E OPERANTE?", "HÁ SISTEMA DE COMBATE A INCÊNDIO (CO2)?",
  "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE (CO2)?", "INTERTRAVAMENTO FUNCIONANDO?"
 ],
 "Desempenho": [
  "VAZÃO DE EXAUSTÃO", "SISTEMA LAVATÓRIO OPERANTE?", "BOMBA DE ÁGUA ESTÁ OPERANTE?", "DOSADOR OPERANTE?",
  "VIBRAÇÃO E RUÍDOS NORMAIS?", "QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?", "QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?"
 ],
 "Integridade Mecânica": [
  "LUBRIFICAÇÃO", "ALINHAMENTO", "BALACEAMENTO", "CORREIAS", "HÁ PROTETOR DE CORREIA?", "MANCAIS", "POLIAS", "ROLAMENTOS",
  "BASE DO EXAUSTOR", "DUTOS EM BOM ESTADO DE CONSERVAÇÃO?", "HÁ VAZAMENTO NOS DUTOS?", "LONA DE ACOPLAMENTO"
 ],
 "Elétrica": [
  "ELÉTRICA DO EXAUSTOR", "ELÉTRICA EXPOSTA?", "ELÉTRICA EXPOSTA PRÓXIMO A COIFA?", "QUADRO DE AUTOMAÇÃO COM ACESSO E OPERANTE?"
 ],
 "Manutenibilidade": [
  "ACESSO PARA MANUTENÇÃO?", "HÁ JANELA DE INSPEÇÃO NO EXAUSTOR?", "HÁ DRENO DE OLÉO?", "EXISTE DUTO SEM ACESSO?",
  "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA SUCÇÃO?", "QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?", "HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?",
  "QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?", "DAMPER ESTÁ ACESSÍVEL?", "DAMPER TEM ACESSO PARA LIMPEZA?", "HÁ ACESSO AOS DUTOS DA COZINHA?", "HÁ ALÇAPÃO NA COZINHA?"
 ],
 "Conservação": [
  "MATERIAIS DA INFRA HIDRÁULICA APROPRIADOS?", "A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?",
  "OS FILTROS ESTÃO COMPLETOS?", "OS FILTROS ESTÃO DANIFICADOS?", "PINTURA",
  "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? SUCÇÃO", "TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? DESCARGA"
 ]
}
WEIGHTS = {"Segurança Contra Incêndio":.30,"Desempenho":.15,"Integridade Mecânica":.15,"Elétrica":.20,"Manutenibilidade":.10,"Conservação":.10}

# Cada regra tem rastreabilidade. Os pesos abaixo são uma escala operacional do motor,
# não uma "nota da ABNT". A norma é usada como referência técnica aplicável, não como fonte
# de números inventados.
RULES = {
 "HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?": (100,"Crítica","Proteção contra incêndio; verificar aplicabilidade ao sistema/projeto.","ABNT NBR 14518:2019; NFPA 96, capítulo 10, quando aplicável."),
 "SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?": (100,"Crítica","Sistema de proteção contra incêndio declarado não conforme.","ABNT NBR 14518:2019; sistema aprovado/projeto e requisitos da autoridade competente."),
 "ELÉTRICA EXPOSTA PRÓXIMO A COIFA?": (90,"Crítica","Exposição elétrica próxima à área de cocção/exaustão.","ABNT NBR 14518:2019; requisitos elétricos e de segurança aplicáveis."),
 "EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)": (80,"Alta","Equipamento de cocção fora da área de captação informada no checklist.","ABNT NBR 14518:2019; projeto e dimensionamento do sistema."),
 "HÁ VAZAMENTO NOS DUTOS?": (85,"Alta","Vazamento de gordura/efluente nos dutos pode comprometer estanqueidade, conservação e segurança.","ABNT NBR 14518:2019; NFPA 96, capítulo 7, quando aplicável."),
 "CASA DE MÁQUINA DESOBSTRUÍDA?": (65,"Alta","Obstrução prejudica acesso, inspeção e manutenção e pode ampliar exposição a incêndio.","ABNT NBR 14518:2019, requisitos de acessibilidade e manutenção."),
 "ELÉTRICA DO EXAUSTOR": (75,"Alta","Condição elétrica declarada não conforme.","ABNT NBR 14518:2019 e requisitos elétricos aplicáveis."),
 "INTERTRAVAMENTO FUNCIONANDO?": (90,"Crítica","Intertravamento declarado inoperante compromete a lógica de proteção/controle do sistema.","ABNT NBR 14518:2019; NFPA 96, requisitos de controles/intertravamentos quando aplicáveis."),
 "VIBRAÇÃO E RUÍDOS NORMAIS?": (55,"Relevante","Vibração/ruído anormal indica necessidade de investigação mecânica.","Boas práticas de manutenção e instruções do fabricante."),
 "LUBRIFICAÇÃO": (45,"Relevante","Lubrificação não conforme pode acelerar desgaste e reduzir confiabilidade.","Instruções do fabricante e boas práticas de manutenção."),
 "ALINHAMENTO": (45,"Relevante","Desalinhamento pode elevar esforços e desgaste.","Instruções do fabricante e boas práticas de manutenção."),
 "BALACEAMENTO": (50,"Relevante","Balanceamento não conforme pode elevar vibração e esforços.","Instruções do fabricante e boas práticas de manutenção."),
 "CORREIAS": (45,"Relevante","Condição não conforme pode provocar perda de transmissão e falha operacional.","Instruções do fabricante e boas práticas de manutenção."),
 "HÁ PROTETOR DE CORREIA?": (55,"Alta","Ausência de proteção mecânica deve ser avaliada quanto ao risco de contato/acidente.","Requisitos de segurança de máquinas e projeto/manutenção aplicáveis."),
 "HÁ DRENO DE OLÉO?": (35,"Atenção","Ausência pode dificultar drenagem/manutenção, mas a aplicabilidade deve ser confirmada pelo projeto.","Projeto do equipamento e instruções do fabricante."),
 "DAMPER EM BOM ESTADO E OPERANTE?": (80,"Alta","Damper declarado inoperante pode comprometer a função prevista de proteção/controle.","ABNT NBR 14518:2019; projeto do sistema."),
 "DAMPER ESTÁ ACESSÍVEL?": (55,"Alta","Acessibilidade insuficiente prejudica inspeção e manutenção.","ABNT NBR 14518:2019."),
 "DAMPER TEM ACESSO PARA LIMPEZA?": (55,"Alta","Acesso insuficiente prejudica manutenção e limpeza.","ABNT NBR 14518:2019."),
 "EXISTE DUTO SEM ACESSO?": (65,"Alta","Trecho sem acesso dificulta inspeção e limpeza do sistema.","ABNT NBR 14518:2019, acessibilidade da rede de dutos."),
 "HÁ ACESSO AOS DUTOS DA COZINHA?": (65,"Alta","Acesso insuficiente dificulta inspeção, limpeza e manutenção.","ABNT NBR 14518:2019."),
 "LONA DE ACOPLAMENTO": (45,"Relevante","Lona declarada não conforme requer correção para preservar o acoplamento e o desempenho do conjunto.","Projeto do equipamento e boas práticas de manutenção."),
}


def norm(v): return re.sub(r"\s+", " ", str(v or "").strip().upper())

def questions(row):
    d=row.get("dados",{})
    if isinstance(d,dict): return d.get("questoes",{}) or {}
    return {}

def get_q(row,key):
    x=questions(row).get(key,{})
    if isinstance(x,dict): return str(x.get("resposta","") or ""), str(x.get("observacao","") or "")
    return str(x or ""), ""

def pillar_for(key):
    for p,qs in PILLARS.items():
        if key in qs:return p
    return "Conservação"

def classify(key,resp,obs):
    r=norm(resp); o=norm(obs); t=f"{r} {o}".strip()
    if not r or r in {"(SEM PREENCHIMENTO)","SEM PREENCHIMENTO","NÃO INFORMADO"}:
        return {"status":"Não informado","severity":None,"nivel":"Sem evidência","rule":"DADO-001"}
    if r in {"N/A","NA","NÃO APLICÁVEL"}:
        return {"status":"Não aplicável","severity":None,"nivel":"N/A","rule":"APLIC-001"}
    if "INOPERANTE" in t or "NÃO CONFORME" in t or "INCONFORME" in t:
        base=RULES.get(key,(55,"Relevante","Desvio técnico identificado no item.","Critério técnico aplicável."))
        return {"status":"Não conforme","severity":base[0],"nivel":base[1],"rule":key}
    if key in RULES:
        bad=False
        # Explicit negative conditions observed in the checklist.
        if key in {"ELÉTRICA EXPOSTA PRÓXIMO A COIFA?","HÁ VAZAMENTO NOS DUTOS?","EXISTE DUTO SEM ACESSO?","OS FILTROS ESTÃO DANIFICADOS?","ELÉTRICA EXPOSTA?","A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?"}:
            bad = r=="SIM"
        elif key in {"SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?","INTERTRAVAMENTO FUNCIONANDO?","DAMPER EM BOM ESTADO E OPERANTE?","HÁ ACESSO AOS DUTOS DA COZINHA?"}:
            bad = r=="NÃO"
        elif key=="HÁ DRENO DE OLÉO?": bad = r=="NÃO"
        elif key=="LONA DE ACOPLAMENTO": bad = r=="NÃO CONFORME"
        elif key in {"LUBRIFICAÇÃO","ALINHAMENTO","BALACEAMENTO","CORREIAS","ELÉTRICA DO EXAUSTOR"}: bad = r=="NÃO CONFORME"
        elif key=="VIBRAÇÃO E RUÍDOS NORMAIS?": bad = r=="NÃO"
        elif key=="CASA DE MÁQUINA DESOBSTRUÍDA?": bad = r=="NÃO"
        elif key=="HÁ PROTETOR DE CORREIA?": bad = r=="NÃO"
        elif key=="EQUIPAMENTOS DE COCÇÃO ESTÃO TODOS LOCALIZADOS NO INTERIOR DA COIFA (15CM)": bad = r=="NÃO"
        if bad:
            base=RULES[key]; return {"status":"Não conforme","severity":base[0],"nivel":base[1],"rule":key}
        # Presence questions (HÁ/EXISTEM) are not automatically nonconformities when the answer is NO.
        if key.startswith("HÁ ") or key.startswith("EXISTEM "):
            return {"status":"Condição registrada","severity":0,"nivel":"Informativo / aplicabilidade","rule":key}
        return {"status":"Conforme","severity":0,"nivel":"Conforme","rule":key}
    # Generic interpretation for all remaining checklist fields.
    if "NÃO CONFORME" in t or "INCONFORME" in t:
        return {"status":"Não conforme","severity":55,"nivel":"Relevante","rule":key}
    if "DANIFICAD" in key and r=="SIM":
        return {"status":"Não conforme","severity":55,"nivel":"Relevante","rule":key}
    if any(word in key for word in ["EM CONFORMIDADE","OPERANTE","BOM ESTADO","SUFICIENTE","COMPLETOS","NORMAL","APROPRIADOS","DESOBSTRUÍDA"]) and r=="NÃO":
        return {"status":"Não conforme","severity":55,"nivel":"Relevante","rule":key}
    if r in {"CONFORME","OK"} or "CONFORME" in t:
        return {"status":"Conforme","severity":0,"nivel":"Conforme","rule":key}
    if r in {"SIM","NÃO"}:
        return {"status":"Condição registrada","severity":0,"nivel":"Informativo / aplicabilidade","rule":key}
    return {"status":"Informação registrada","severity":0,"nivel":"Informativo","rule":key}

def analyze(row):
    records=[]
    for sec,key,typ,opts in ALL_QUESTIONS:
        resp,obs=get_q(row,key)
        c=classify(key,resp,obs)
        records.append({"Seção":sec,"Pilar":pillar_for(key),"Item":key,"Resposta":resp or "(Sem preenchimento)","Observação":obs,"Status":c["status"],"Severidade":c["severity"],"Nível":c["nivel"],"Regra":c["rule"]})
    d=pd.DataFrame(records)
    pillar=[]
    for p,w in WEIGHTS.items():
        x=d[d.Pilar==p]; known=x[x.Severidade.notna()]; evaluated=len(known); total=len(x)
        exposure=float((known.Severidade.fillna(0)).mean()) if evaluated else 0
        pillar.append({"Pilar":p,"Peso":w,"Exposição":exposure,"Avaliados":evaluated,"Total":total,"Cobertura":(evaluated/total*100 if total else 0),"Não conformidades":int((known.Severidade>0).sum()),"Críticos":int((known.Severidade>=80).sum())})
    p=pd.DataFrame(pillar)
    active=p[p.Cobertura>0]
    icl=float((active.Exposição*active.Peso).sum()/active.Peso.sum()) if len(active) else 0
    evaluated=int(d.Severidade.notna().sum()); total=len(d); missing=int(d.Severidade.isna().sum()); nc=int((d.Severidade.fillna(0)>0).sum()); critical=int((d.Severidade.fillna(0)>=80).sum())
    coverage=evaluated/total*100 if total else 0
    return d,p,icl,{"total":total,"avaliados":evaluated,"faltantes":missing,"nao_conformidades":nc,"criticos":critical,"cobertura":coverage}

def grade(icl):
    if icl>=70:return "Severo"
    if icl>=50:return "Crítico"
    if icl>=35:return "Relevante"
    if icl>=20:return "Atenção"
    return "Controlado"

def load():
    try:
        r=supabase.table("vistorias_exaustao").select("*").order("created_at",desc=True).execute()
        df=pd.DataFrame(r.data)
    except Exception as e:
        st.error("Não foi possível ler o Supabase. Verifique os Secrets e a tabela vistorias_exaustao.")
        return pd.DataFrame()
    if df.empty:return df
    # Old Guararapes records remain untouched in the DB. These defaults are only in-memory.
    if "shopping" not in df.columns: df["shopping"]="Guararapes"
    df["shopping"]=df["shopping"].fillna("").replace("","Guararapes")
    if "ano_referencia" not in df.columns: df["ano_referencia"]=""
    if "mes_numero" not in df.columns: df["mes_numero"]=""
    if "mes_referencia" not in df.columns: df["mes_referencia"]=""
    df["ano_referencia"]=df["ano_referencia"].fillna("").astype(str)
    mask=df["ano_referencia"].eq("")
    df.loc[mask,"ano_referencia"]=df.loc[mask,"mes_referencia"].astype(str).str[:4]
    vals=[]
    for _,r in df.iterrows():
        d,p,icl,stats=analyze(r); vals.append((icl,grade(icl),stats["nao_conformidades"],stats["faltantes"],stats["criticos"],stats["cobertura"]))
    df["icl_score"]=[x[0] for x in vals];df["criticidade"]=[x[1] for x in vals];df["nao_conformidades"]=[x[2] for x in vals];df["nao_informados"]=[x[3] for x in vals];df["criticos"]=[x[4] for x in vals];df["cobertura"]=[x[5] for x in vals]
    return df

def card(label,value,sub="",cls=""):
    st.markdown(f'<div class="kpi {cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',unsafe_allow_html=True)

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def narrative(loja,d,p,icl,stats):
    bad=d[d.Severidade.fillna(0)>0].sort_values("Severidade",ascending=False)
    crit=bad[bad.Severidade>=80]
    parts=[]
    parts.append(f"A vistoria da operação {loja} apresentou ICL de {icl:.1f}%, calculado a partir das evidências disponíveis nos itens avaliados. O ICL representa uma medida agregada de exposição técnica e não constitui, isoladamente, declaração de conformidade ou certificado de segurança. Foram avaliados {stats['avaliados']} de {stats['total']} itens, com cobertura de {stats['cobertura']:.0f}%.")
    if crit.shape[0]:
        nomes=", ".join(crit.Item.head(4).tolist())
        parts.append(f"A leitura individual dos achados identifica {len(crit)} ocorrência(s) de maior severidade, entre elas: {nomes}. Essas ocorrências devem permanecer visíveis mesmo quando a contribuição matemática de cada item não altera significativamente o ICL global.")
    if len(bad):
        top=bad.Item.head(5).tolist()
        parts.append("Os principais pontos de atenção concentram-se em " + ", ".join(top) + ". A priorização deve considerar a consequência do desvio, sua exposição, a possibilidade de recorrência e a aplicabilidade do requisito técnico ao sistema instalado.")
    if stats['faltantes']:
        parts.append(f"Há ainda {stats['faltantes']} item(ns) sem evidência suficiente. Ausência de resposta não é tratada como conformidade; ela reduz a cobertura e deve ser considerada uma lacuna de informação para a tomada de decisão.")
    parts.append("Como encaminhamento, recomenda-se atuar primeiro sobre os desvios de maior severidade e sobre aqueles relacionados à segurança contra incêndio, integridade dos dutos, operação dos dispositivos de proteção e condições elétricas, sempre confrontando o sistema real com projeto, fabricante, requisitos normativos aplicáveis e condições observadas em campo.")
    return " ".join(parts)

# =========================================================
# INTERFACE
# =========================================================
st.markdown('<div class="csa-hero"><h1>CSA ENGENHARIA</h1><p>Plataforma Técnica de Auditoria, Risco, Conformidade e Desempenho — Sistemas de Exaustão Comercial</p></div>',unsafe_allow_html=True)
df=load()
if df.empty:
    st.info("Nenhuma vistoria encontrada no Supabase.")
    st.stop()

st.sidebar.markdown("### 🛡️ Navegação")
module=st.sidebar.radio("Visão",["🌐 Panorama Executivo","🏪 Diagnóstico por Loja","📐 Metodologia ICL & Risco","🤖 Análise Técnica Assistida","📋 Nova Vistoria","📋 Matriz de Dados","🗑️ Gerenciar Vistorias"])
shops=sorted(df.shopping.astype(str).unique())
shop=st.sidebar.selectbox("Shopping",shops)
years=sorted(df[df.shopping==shop].ano_referencia.astype(str).unique(),reverse=True)
year=st.sidebar.selectbox("Ano",years) if years else ""
view=df[(df.shopping==shop)&(df.ano_referencia.astype(str)==str(year))].copy()
months=sorted(view.mes_referencia.dropna().astype(str).unique(),reverse=True)
month=st.sidebar.selectbox("Mês / ciclo",["Todos"]+months)
if month!="Todos":view=view[view.mes_referencia.astype(str)==month].copy()

# =========================================================
# PANORAMA
# =========================================================
if module=="🌐 Panorama Executivo":
    st.markdown(f"## 🌐 Panorama Executivo — {shop} · {year}")
    n=len(view); mean=float(view.icl_score.mean()) if n else 0; nc=int(view.nao_conformidades.sum()) if n else 0; crit=int(view.criticos.sum()) if n else 0; miss=int(view.nao_informados.sum()) if n else 0; cov=float(view.cobertura.mean()) if n else 0
    cols=st.columns(5)
    for col,args in zip(cols,[("Lojas auditadas",n,"escopo selecionado","dark"),("ICL médio",f"{mean:.1f}%","exposição agregada","orange"),("Achados críticos",crit,"itens individuais ≥ 80","red"),("Não conformidades",nc,"todos os desvios encontrados","red"),("Cobertura média",f"{cov:.0f}%","qualidade da evidência","blue")]):
        with col:card(*args)
    st.markdown('<div class="note"><b>Como ler:</b> o ICL é uma síntese matemática da exposição técnica dos itens avaliados. Ele não diz sozinho se uma loja está "segura". Por isso o painel mostra separadamente severidade, não conformidades, cobertura, pilares e evidências.</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        fig=px.histogram(view,x="icl_score",nbins=8,title="Distribuição do ICL entre as lojas",labels={"icl_score":"ICL (%)"});fig.update_layout(showlegend=False);st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.bar(view.sort_values("icl_score"),x="icl_score",y="loja",orientation="h",text="icl_score",title="ICL por loja — leitura rápida");fig.update_traces(texttemplate="%{text:.1f}%",textposition="outside");fig.update_layout(xaxis_range=[0,max(100,float(view.icl_score.max()+10))]);st.plotly_chart(fig,use_container_width=True)
    rows=[]
    for _,r in view.iterrows():
        d,p,icl,stats=analyze(r); p=p.copy();p["Loja"]=r.loja;rows.append(p)
    pp=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    if not pp.empty:
        g=pp.groupby("Pilar").agg(Exposição=("Exposição","mean"),Não_conformidades=("Não conformidades","sum"),Cobertura=("Cobertura","mean")).reset_index()
        a,b=st.columns(2)
        with a:
            fig=px.bar(g,x="Exposição",y="Pilar",orientation="h",text="Exposição",title="Exposição técnica média por pilar");fig.update_traces(texttemplate="%{text:.1f}",textposition="outside");fig.update_layout(xaxis_range=[0,100]);st.plotly_chart(fig,use_container_width=True)
        with b:
            fig=px.bar(g,x="Não_conformidades",y="Pilar",orientation="h",text="Não_conformidades",title="Não conformidades por pilar");fig.update_traces(textposition="outside");st.plotly_chart(fig,use_container_width=True)
    st.markdown("### 🔎 O que está gerando os desvios?")
    all_bad=[]
    for _,r in view.iterrows():
        d,_,_,_=analyze(r); x=d[d.Severidade.fillna(0)>0].copy();x["Loja"]=r.loja;all_bad.append(x)
    bad=pd.concat(all_bad,ignore_index=True) if all_bad else pd.DataFrame()
    if not bad.empty:
        pareto=bad.groupby("Item").size().reset_index(name="Ocorrências").sort_values("Ocorrências",ascending=False).head(10)
        fig=px.bar(pareto.sort_values("Ocorrências"),x="Ocorrências",y="Item",orientation="h",text="Ocorrências",title="Principais achados recorrentes — Top 10");fig.update_traces(textposition="outside");st.plotly_chart(fig,use_container_width=True)
    st.markdown("### 🧭 Leitura executiva")
    st.markdown(f'<div class="section-card"><div class="big-text">No período selecionado, foram analisadas <b>{n}</b> operação(ões). O ICL médio foi de <b>{mean:.1f}%</b>, enquanto a cobertura média dos dados foi de <b>{cov:.0f}%</b>. O painel separa exposição agregada de achados individuais para evitar que uma média baixa esconda uma condição pontual relevante. A priorização deve ser feita pelos achados, sua severidade, sua aplicabilidade e sua consequência técnica.</div></div>',unsafe_allow_html=True)

# =========================================================
# DIAGNÓSTICO POR LOJA
# =========================================================
elif module=="🏪 Diagnóstico por Loja":
    st.markdown("## 🏪 Diagnóstico técnico por loja")
    loja=st.selectbox("Selecione a operação",sorted(view.loja.dropna().astype(str).unique()))
    r=view[view.loja.astype(str)==loja].iloc[0];d,p,icl,stats=analyze(r);g=grade(icl)
    cols=st.columns(5)
    for col,args in zip(cols,[("ICL",f"{icl:.1f}%","exposição agregada","orange"),("Grau do ICL",g,"não substitui os achados","dark"),("Não conformidades",stats['nao_conformidades'],"itens com desvio","red"),("Críticos",stats['criticos'],"severidade elevada","red"),("Cobertura",f"{stats['cobertura']:.0f}%","evidência disponível","blue")]):
        with col:card(*args)
    st.markdown(f'<div class="warn"><b>Leitura obrigatória:</b> esta loja possui ICL de <b>{icl:.1f}%</b>, porém o ICL não é um certificado de segurança. Os {stats["nao_conformidades"]} desvios encontrados são analisados individualmente, e {stats["faltantes"]} item(ns) sem evidência não são convertidos em conformidade.</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        fig=go.Figure(go.Indicator(mode="gauge+number",value=icl,number={"suffix":"%"},title={"text":"Índice de Exposição Agregada"},gauge={"axis":{"range":[0,100]},"steps":[{"range":[0,20],"color":"#E8F5E9"},{"range":[20,35],"color":"#E3F2FD"},{"range":[35,50],"color":"#FFF3E0"},{"range":[50,70],"color":"#FFEBEE"},{"range":[70,100],"color":"#ECEFF1"}]}));fig.update_layout(height=280);st.plotly_chart(fig,use_container_width=True)
    with b:
        fig=px.bar(p,x="Exposição",y="Pilar",orientation="h",text="Exposição",title="Condição agregada por pilar");fig.update_traces(texttemplate="%{text:.1f}",textposition="outside");fig.update_layout(xaxis_range=[0,100]);st.plotly_chart(fig,use_container_width=True)
    st.markdown("### 📊 Composição do cálculo desta loja")
    # Transparência: mostra exatamente como cada pilar contribuiu.
    p2=p.copy();p2["Contribuição ICL"]=p2["Exposição"]*p2["Peso"]
    for _,x in p2.iterrows():
        st.markdown(f'<div class="section-card"><b>{esc(x.Pilar)}</b><br><span class="small">Exposição do pilar: {x.Exposição:.1f} × Peso: {x.Peso*100:.0f}% = <b>{x["Contribuição ICL"]:.1f} pontos</b> · Cobertura: {x.Cobertura:.0f}% · Não conformidades: {int(x["Não conformidades"])}.</span></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="note"><b>Resultado matemático:</b> ICL = soma das contribuições ponderadas dos pilares com evidência disponível, normalizada pelos pesos ativos. Resultado desta loja: <b>{icl:.1f}%</b>.</div>',unsafe_allow_html=True)
    st.markdown("### 🚨 Achados individuais")
    bad=d[d.Severidade.fillna(0)>0].sort_values("Severidade",ascending=False)
    if bad.empty: st.markdown('<div class="good"><b>Nenhum desvio foi classificado pelo motor.</b> Isso não elimina a necessidade de análise das observações e da aplicabilidade dos requisitos.</div>',unsafe_allow_html=True)
    for _,x in bad.iterrows():
        nivel=x.Nível; cls="finding" if x.Severidade>=80 else "finding att"
        base=RULES.get(x.Item,(0,"Informativo","Critério técnico aplicável.","Referência técnica aplicável."))
        st.markdown(f'<div class="{cls}"><b>{esc(x.Item)}</b><br><span class="pill">{esc(x.Pilar)}</span><span class="pill">{esc(nivel)}</span><span class="pill">{int(x.Severidade)}/100</span><br><b>Evidência:</b> {esc(x.Resposta)}. {esc(x.Observação or "Sem observação adicional.")}<br><b>Leitura técnica:</b> {esc(base[2])}<br><b>Base de referência:</b> {esc(base[3])}</div>',unsafe_allow_html=True)
    st.markdown("### 📝 Diagnóstico técnico e mitigação")
    st.markdown(f'<div class="section-card"><div class="big-text">{esc(narrative(loja,d,p,icl,stats))}</div></div>',unsafe_allow_html=True)
    st.markdown("### 📚 Evidências completas da vistoria")
    # Acordeão para não transformar o painel em uma tabela gigantesca.
    for sec in FORM_SECTIONS:
        with st.expander(f"{sec} — {sum(1 for s,_,_,_ in ALL_QUESTIONS if s==sec)} itens"):
            x=d[d.Seção==sec]
            for _,z in x.iterrows():
                icon="🟢" if z.Status=="Conforme" else "🔴" if z.Status=="Não conforme" else "🔵" if z.Status=="Não informado" else "⚪"
                st.markdown(f"{icon} **{z.Item}** — `{z.Resposta}`" + (f"\n\n_{z.Observação}_" if z.Observação else ""))

# =========================================================
# METODOLOGIA — restaurada, explicativa e com exemplo.
# =========================================================
elif module=="📐 Metodologia ICL & Risco":
    st.markdown("## 📐 Metodologia ICL, criticidade e risco")
    st.markdown('<div class="note"><b>Princípio central:</b> a metodologia não transforma uma vistoria em uma simples "nota". O motor separa evidência, condição, severidade, peso do pilar, cobertura e risco. O ICL é uma síntese; a decisão técnica continua dependente dos achados individuais e da aplicabilidade do requisito.</div>',unsafe_allow_html=True)
    a,b,c=st.columns(3)
    with a:
        st.markdown('<div class="method-box"><h4>1. Evidência</h4><p>Resposta do checklist + observação de campo. Resposta ausente permanece como <b>não informado</b>.</p></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="method-box"><h4>2. Condição</h4><p>O motor interpreta a resposta segundo uma regra documentada: conforme, não conforme, atenção ou ausência de evidência.</p></div>',unsafe_allow_html=True)
    with c:
        st.markdown('<div class="method-box"><h4>3. Síntese</h4><p>As condições são agrupadas em seis pilares e ponderadas para formar o ICL, sem apagar os achados individuais.</p></div>',unsafe_allow_html=True)
    st.markdown("### ⚖️ Pesos dos pilares")
    fig=px.pie(pd.DataFrame({"Pilar":list(WEIGHTS.keys()),"Peso":[v*100 for v in WEIGHTS.values()]}),names="Pilar",values="Peso",hole=.55,title="Peso relativo usado na síntese do ICL");fig.update_traces(textinfo="label+percent");st.plotly_chart(fig,use_container_width=True)
    st.markdown("### 🧮 Como o cálculo é feito")
    st.markdown("""<div class="section-card"><div class="big-text"><b>Passo 1:</b> cada item recebe uma condição técnica. <br><b>Passo 2:</b> os itens avaliados formam a exposição média de cada pilar. <br><b>Passo 3:</b> cada exposição é multiplicada pelo peso do respectivo pilar. <br><b>Passo 4:</b> as contribuições são somadas e normalizadas pelos pesos dos pilares que possuem evidência. <br><br><b>Fórmula:</b> ICL = Σ (Exposição do Pilar × Peso do Pilar) ÷ Σ Pesos Ativos.</div></div>""",unsafe_allow_html=True)
    st.markdown("### 🔢 Exemplo simples")
    ex=pd.DataFrame({"Pilar":["Incêndio","Elétrica","Mecânica"],"Exposição":[60,20,40],"Peso":[30,20,15]})
    ex["Contribuição"]=ex.Exposição*ex.Peso/100
    st.dataframe(ex,use_container_width=True,hide_index=True)
    st.markdown('<div class="note"><b>Exemplo:</b> se os três pilares acima fossem os únicos com evidência, o resultado seria a soma das contribuições dividida pela soma dos pesos ativos. O número final representa exposição agregada; não significa que 35%, por exemplo, corresponda a "35% de segurança".</div>',unsafe_allow_html=True)
    st.markdown("### 🚦 Severidade dos achados")
    sev=pd.DataFrame([[0,"Conforme / sem desvio"],[35,"Atenção"],[45,"Relevante"],[65,"Alta"],[80,"Crítica"],[100,"Crítica máxima / regra específica"]],columns=["Referência operacional","Leitura"])
    st.dataframe(sev,use_container_width=True,hide_index=True)
    st.caption("Os valores de severidade são parâmetros operacionais do motor desta plataforma. Eles não são percentuais publicados pela ABNT. A referência normativa entra na regra técnica do item, enquanto a escala serve para mensuração e priorização.")
    st.markdown("### 🧩 ICL × não conformidade × risco")
    a,b,c=st.columns(3)
    with a:st.markdown('<div class="method-box"><h4>ICL</h4><p>Síntese da exposição agregada dos pilares.</p></div>',unsafe_allow_html=True)
    with b:st.markdown('<div class="method-box"><h4>Não conformidade</h4><p>Achado individual que permanece visível e mensurado independentemente do ICL.</p></div>',unsafe_allow_html=True)
    with c:st.markdown('<div class="method-box"><h4>Risco</h4><p>Leitura de consequência e probabilidade/exposição. Não é a mesma coisa que o ICL.</p></div>',unsafe_allow_html=True)
    st.markdown("### 📚 Base técnica utilizada")
    st.markdown("""<div class="section-card"><div class="big-text"><b>ABNT NBR 14518</b> — Sistemas de ventilação para cozinhas profissionais: referência principal para projeto, instalação, operação, inspeção, manutenção, acessibilidade e segurança do sistema de exaustão. <br><br><b>NFPA 96</b> — referência internacional complementar para ventilação, remoção de gordura e proteção contra incêndio em operações de cocção comercial, quando adotada/aplicável. <br><br><b>Projeto, fabricante e autoridade competente</b> — a avaliação de conformidade depende também do projeto específico, das instruções do fabricante e dos requisitos legais/da autoridade competente. A plataforma não considera automaticamente que toda ausência de determinado equipamento seja não conformidade; a aplicabilidade deve ser verificada.</div></div>""",unsafe_allow_html=True)

# =========================================================
# ANÁLISE ASSISTIDA — texto para leigos, sem código Python.
# =========================================================
elif module=="🤖 Análise Técnica Assistida":
    st.markdown("## 🤖 Análise Técnica Assistida")
    st.markdown('<div class="note"><b>Como funciona:</b> esta área transforma os resultados objetivos da vistoria em uma leitura técnica dissertativa. A IA, quando integrada futuramente, deverá receber somente os fatos, indicadores e referências aprovadas pelo motor; ela não poderá escolher pesos nem inventar criticidade.</div>',unsafe_allow_html=True)
    loja=st.selectbox("Loja",sorted(view.loja.dropna().astype(str).unique()))
    r=view[view.loja.astype(str)==loja].iloc[0];d,p,icl,stats=analyze(r)
    st.markdown(f"### Parecer técnico assistido — {loja}")
    st.markdown(f'<div class="section-card"><div class="big-text">{esc(narrative(loja,d,p,icl,stats))}</div></div>',unsafe_allow_html=True)
    bad=d[d.Severidade.fillna(0)>0].sort_values("Severidade",ascending=False)
    if not bad.empty:
        st.markdown("### 🔎 Base objetiva utilizada para o parecer")
        for _,x in bad.head(10).iterrows():
            st.markdown(f'<div class="finding"><b>{esc(x.Item)}</b><br><span class="small">Resposta: {esc(x.Resposta)} · Severidade operacional: {int(x.Severidade)}/100 · Pilar: {esc(x.Pilar)}</span></div>',unsafe_allow_html=True)
    st.markdown("### 📚 Referências técnicas")
    st.markdown('<div class="section-card"><div class="big-text">A análise deve ser lida em conjunto com a <b>ABNT NBR 14518</b>, requisitos específicos do projeto e fabricante e, quando aplicável, referências internacionais como a <b>NFPA 96</b>. A indicação de não conformidade depende da aplicabilidade do requisito ao sistema efetivamente instalado.</div></div>',unsafe_allow_html=True)

# =========================================================
# NOVA VISTORIA — TODOS os campos do input, sem índice duplicado.
# =========================================================
elif module=="📋 Nova Vistoria":
    st.markdown("## 📋 Nova Vistoria")
    st.markdown('<div class="note"><b>Formulário integral:</b> os campos abaixo reproduzem os itens dos relatórios de input enviados. O motor utiliza chaves únicas por seção e por pergunta para evitar o erro StreamlitDuplicateElementKey. Nenhuma pergunta é omitida.</div>',unsafe_allow_html=True)
    with st.form("nova_vistoria_integral", clear_on_submit=False):
        c1,c2,c3=st.columns(3)
        with c1: shopping_new=st.text_input("Shopping *",value=shop)
        with c2: loja_new=st.text_input("LOJA *")
        with c3: data_new=st.text_input("DATA/HORA *",value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        mes_new=st.text_input("MÊS / CICLO DE REFERÊNCIA *",value=f"{datetime.now().year}-{datetime.now().month:02d}")
        qs={}
        for sec,items in FORM_SECTIONS.items():
            st.markdown(f"### {sec}")
            for idx,(key,typ,opts) in enumerate(items):
                unique=f"{sec}_{idx}_{re.sub(r'[^A-Za-z0-9]+','_',key)}"
                a,b=st.columns([1.05,1.95])
                with a:
                    if typ=="select": resp=st.selectbox(key,opts,key=f"r_{unique}")
                    else: resp=st.text_input(key,key=f"r_{unique}")
                with b:
                    obs=st.text_input("Observação",key=f"o_{unique}")
                qs[key]={"resposta":resp,"observacao":obs}
        geral=st.text_area("OBSERVAÇÕES GERAIS",key="obs_gerais_nova")
        salvar=st.form_submit_button("💾 Salvar vistoria",type="primary")
    if salvar:
        if not shopping_new or not loja_new or not mes_new or not data_new: st.error("Preencha Shopping, LOJA, MÊS/CICLO e DATA/HORA.")
        else:
            ano=mes_new[:4] if len(mes_new)>=4 else str(datetime.now().year)
            mes_num=mes_new[-2:] if len(mes_new)>=2 else ""
            payload={"shopping":shopping_new,"loja":loja_new,"mes_referencia":mes_new,"ano_referencia":ano,"mes_numero":mes_num,"data_hora":data_new,"dados":{"shopping":shopping_new,"loja":loja_new,"data_hora":data_new,"questoes":qs,"observacoes_gerais":geral}}
            try:
                supabase.table("vistorias_exaustao").insert(payload).execute(); st.success("Vistoria salva com todos os campos."); st.rerun()
            except Exception as e: st.error(f"Não foi possível salvar: {e}")

# =========================================================
# MATRIZ DE DADOS — mantida apenas como apoio, não como tela principal.
# =========================================================
elif module=="📋 Matriz de Dados":
    st.markdown("## 📋 Matriz de Dados")
    st.markdown('<div class="note">Esta tela é administrativa. O usuário final deve priorizar o Panorama, o Diagnóstico por Loja e a Metodologia; a matriz existe para conferência e exportação rápida.</div>',unsafe_allow_html=True)
    st.dataframe(view[[c for c in ["loja","mes_referencia","icl_score","criticidade","nao_conformidades","criticos","nao_informados","cobertura"] if c in view.columns]].rename(columns={"loja":"Loja","mes_referencia":"Mês","icl_score":"ICL","criticidade":"Grau ICL","nao_conformidades":"Não conformidades","criticos":"Críticos","nao_informados":"Não informados","cobertura":"Cobertura"}),use_container_width=True,hide_index=True)

# =========================================================
# GERENCIAR
# =========================================================
elif module=="🗑️ Gerenciar Vistorias":
    st.markdown("## 🗑️ Gerenciar Vistorias")
    st.warning("A exclusão é permanente. Use somente para corrigir um registro criado por engano.")
    labels=[f"{r.id} | {r.loja} | {r.mes_referencia}" for _,r in df.iterrows()]
    sel=st.selectbox("Registro",labels); rid=sel.split("|")[0].strip()
    if st.button("❌ Excluir vistoria"):
        try:supabase.table("vistorias_exaustao").delete().eq("id",rid).execute();st.success("Excluído.");st.rerun()
        except Exception as e:st.error(str(e))
