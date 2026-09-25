import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client, Client
import re

st.set_page_config(page_title="CSA Engenharia | Gestão do Sistema de Exaustão", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
.stApp{background:#F8FAFC;font-family:Inter,-apple-system,BlinkMacSystemFont,sans-serif}
.csa-hero{background:linear-gradient(135deg,#0D3B66,#002855);padding:28px 30px;border-radius:18px;color:#fff;margin-bottom:22px;border-bottom:5px solid #FF6B35}
.csa-hero h1{color:#fff!important;font-size:2.15rem;font-weight:800;margin:0}.csa-hero p{color:#E2E8F0;margin:8px 0 0}
.kpi{background:#fff;padding:18px;border-radius:16px;border:1px solid #E2E8F0;border-left:6px solid #0D3B66;height:100%}
.kpi.red{border-left-color:#E53E3E}.kpi.orange{border-left-color:#FF6B35}.kpi.green{border-left-color:#38A169}.kpi.blue{border-left-color:#3182CE}
.kpi-label{font-size:.76rem;color:#64748B;font-weight:800;text-transform:uppercase}.kpi-value{font-size:1.8rem;color:#0D3B66;font-weight:800}.kpi-sub{font-size:.76rem;color:#94A3B8}
.note{background:#EFF6FF;border-left:5px solid #3182CE;padding:14px;border-radius:9px;margin:12px 0}
.warn{background:#FFF7ED;border-left:5px solid #FF6B35;padding:14px;border-radius:9px;margin:12px 0}
.finding{background:#fff;border:1px solid #E2E8F0;border-left:5px solid #E53E3E;border-radius:12px;padding:14px;margin:7px 0}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def db() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase=db()

WEIGHTS={"Segurança Contra Incêndio":.30,"Desempenho":.15,"Integridade Mecânica":.15,"Elétrica":.20,"Manutenibilidade":.10,"Conservação":.10}

PILLARS={
"Segurança Contra Incêndio":["HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?","SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?","HÁ DAMPER CORTA FOGO?","DAMPER EM BOM ESTADO E OPERANTE?","HÁ SISTEMA DE COMBATE A INCÊNDIO (CO2)?","SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE (CO2)?","INTERTRAVAMENTO FUNCIONANDO?"],
"Desempenho":["VAZÃO DE EXAUSTÃO","VIBRAÇÃO E RUÍDOS NORMAIS?","SISTEMA LAVATÓRIO OPERANTE?","BOMBA DE ÁGUA ESTÁ OPERANTE?","DOSADOR OPERANTE?","QUANTIDADE DE JANELAS SUFICIENTE NA SUCÇÃO?","QUANTIDADE DE JANELAS SUFICIENTE NA DESCARGA?"],
"Integridade Mecânica":["LUBRIFICAÇÃO","ALINHAMENTO","BALACEAMENTO","CORREIAS","MANCAIS","POLIAS","ROLAMENTOS","BASE DO EXAUSTOR","DUTOS EM BOM ESTADO DE CONSERVAÇÃO?","HÁ VAZAMENTO NOS DUTOS?","LONA DE ACOPLAMENTO"],
"Elétrica":["ELÉTRICA DO EXAUSTOR","ELÉTRICA EXPOSTA?","ELÉTRICA EXPOSTA PRÓXIMO A COIFA?","QUADRO DE AUTOMAÇÃO COM ACESSO E OPERANTE?"],
"Manutenibilidade":["ACESSO PARA MANUTENÇÃO?","HÁ JANELA DE INSPEÇÃO NO EXAUSTOR?","HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA SUCÇÃO?","HÁ JANELAS DE INSPEÇÃO NOS DUTOS DA DESCARGA?","DAMPER ESTÁ ACESSÍVEL?","DAMPER TEM ACESSO PARA LIMPEZA?","HÁ ACESSO AOS DUTOS DA COZINHA?","EXISTE DUTO SEM ACESSO?","HÁ ALÇAPÃO NA COZINHA?","HÁ DRENO DE OLÉO?"],
"Conservação":["MATERIAIS DA INFRA HIDRÁULICA APROPRIADOS?","A INFRA HIDRÁULICA DA COIFA ESTÁ PRÓXIMO A EQUIPAMENTOS DE FRITURA?","OS FILTROS ESTÃO COMPLETOS?","OS FILTROS ESTÃO DANIFICADOS?","PINTURA","TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? SUCÇÃO","TEM ISOLAMENTO TÉRMICO E ESTÁ EM BOM ESTADO? DESCARGA"]
}

RISK_IF={"HÁ SISTEMA COMBATE A INCÊNDIO (SAPONIFICANTE)?":"NÃO","SISTEMA DE COMBATE A INCÊNDIO EM CONFORMIDADE?":"NÃO","ELÉTRICA EXPOSTA PRÓXIMO A COIFA?":"SIM","ELÉTRICA EXPOSTA?":"SIM","HÁ INTERTRAVAMENTO?":"NÃO","INTERTRAVAMENTO FUNCIONANDO?":"NÃO","HÁ VAZAMENTO NOS DUTOS?":"SIM","DAMPER ESTÁ ACESSÍVEL?":"NÃO","DAMPER TEM ACESSO PARA LIMPEZA?":"NÃO","HÁ ACESSO AOS DUTOS DA COZINHA?":"NÃO","EXISTE DUTO SEM ACESSO?":"SIM","HÁ DRENO DE OLÉO?":"NÃO","HÁ PROTETOR DE CORREIA?":"NÃO"}

def norm(x): return re.sub(r"\s+"," ",str(x or "").strip().upper())
def questions(row):
    d=row.get("dados",{})
    return d.get("questoes",{}) if isinstance(d,dict) else {}
def q(row,key):
    x=questions(row).get(key,{})
    return (norm(x.get("resposta")),str(x.get("observacao","") or "").strip()) if isinstance(x,dict) else (norm(x),"")
def severity(key,resp,obs):
    if not resp or resp in {"(SEM PREENCHIMENTO)","N/A","NA","NÃO INFORMADO","NÃO APLICÁVEL"}: return None,"Não informado"
    t=norm(resp+" "+obs)
    if "INOPERANTE" in t or "SEVERO" in t: return 100,"Severo"
    if "NÃO CONFORME" in t or "INCONFORME" in t or "CRÍTICO" in t: return 75,"Não conforme"
    if key in RISK_IF: return (75,"Desvio") if norm(resp)==RISK_IF[key] else (0,"Conforme")
    if resp=="NÃO": return 75,"Desvio"
    if resp=="SIM" or "CONFORME" in t or "OK" in t: return 0,"Conforme"
    if "ATENÇÃO" in t or "PARCIAL" in t: return 25,"Atenção"
    if "RELEVANTE" in t: return 50,"Relevante"
    return None,"Não classificado"

def calc(row):
    out=[]
    for p,qs in PILLARS.items():
        for key in qs:
            r,o=q(row,key);s,status=severity(key,r,o)
            out.append({"Pilar":p,"Item":key,"Resposta":r,"Observação":o,"Severidade":s,"Status":status})
    d=pd.DataFrame(out); pr=[]
    for p,w in WEIGHTS.items():
        x=d[d.Pilar==p]; known=x[x.Severidade.notna()]
        exp=float(known.Severidade.mean()) if len(known) else 0
        pr.append({"Pilar":p,"Exposição":exp,"Peso":w,"Não conformidades":int((known.Severidade>0).sum()),"Não informados":int(x.Severidade.isna().sum()),"Cobertura":len(known)/len(x)*100 if len(x) else 0})
    p=pd.DataFrame(pr); active=p[p.Cobertura>0]
    icl=float((active.Exposição*active.Peso).sum()/active.Peso.sum()) if len(active) else None
    return d,p,icl

def grade(x):
    if x is None:return "Sem classificação"
    return "Severo" if x>=70 else "Crítico" if x>=50 else "Relevante" if x>=35 else "Atenção" if x>=20 else "Controlado"

def load():
    try:r=supabase.table("vistorias_exaustao").select("*").order("created_at",desc=True).execute();df=pd.DataFrame(r.data)
    except Exception:return pd.DataFrame()
    if df.empty:return df
    if "shopping" not in df:df["shopping"]="Guararapes"
    df["shopping"]=df["shopping"].fillna("Guararapes")
    df["ano_referencia"]=df.get("ano_referencia",df.get("mes_referencia","").astype(str).str[:4]).fillna("").astype(str)
    df["mes_numero"]=df.get("mes_numero",df.get("mes_referencia","").astype(str).str[-2:]).fillna("").astype(str)
    vals=[]
    for _,r in df.iterrows():
        d,p,i=calc(r); vals.append((i,grade(i),int((d.Severidade.fillna(0)>0).sum()),int(d.Severidade.isna().sum())))
    df["icl_score"]=[x[0] for x in vals];df["criticidade"]=[x[1] for x in vals];df["nao_conformidades"]=[x[2] for x in vals];df["nao_informados"]=[x[3] for x in vals]
    return df

def card(label,value,sub="",cls=""):
    st.markdown(f'<div class="kpi {cls}"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',unsafe_allow_html=True)

st.markdown('<div class="csa-hero"><h1>CSA ENGENHARIA</h1><p>Plataforma Técnica de Auditoria, Risco, Conformidade e Desempenho — Sistemas de Exaustão Comercial</p></div>',unsafe_allow_html=True)
df=load()
if df.empty: st.info("Nenhuma vistoria encontrada no Supabase."); st.stop()

st.sidebar.markdown("### 🛡️ Navegação")
module=st.sidebar.radio("Visão",["🌐 Panorama Executivo","🏪 Diagnóstico por Loja","📐 Matriz de Criticidade & Risco","🤖 Análise Técnica Assistida","📋 Nova Vistoria","📋 Matriz de Dados","🗑️ Gerenciar Vistorias"])

shops=sorted(df.shopping.astype(str).unique());shop=st.sidebar.selectbox("Shopping",shops)
years=sorted(df[df.shopping==shop].ano_referencia.unique(),reverse=True);year=st.sidebar.selectbox("Ano",years) if years else ""
view=df[(df.shopping==shop)&(df.ano_referencia==year)].copy()
months=sorted(view.mes_referencia.dropna().astype(str).unique(),reverse=True);month=st.sidebar.selectbox("Mês / ciclo",["Todos"]+months)
if month!="Todos":view=view[view.mes_referencia.astype(str)==month].copy()

if module=="🌐 Panorama Executivo":
    st.markdown(f"## 🌐 Panorama Executivo — {shop} · {year}")
    n=len(view); mean=view.icl_score.mean(); high=int(view.criticidade.isin(["Crítico","Severo"]).sum()); nc=int(view.nao_conformidades.sum()); ni=int(view.nao_informados.sum())
    c=st.columns(5)
    for col,args in zip(c,[("Lojas auditadas",n,"escopo atual",""),("ICL médio",f"{mean:.1f}%","exposição agregada","orange"),("Crítico/Severo",high,"não significa 'lojas seguras'","red"),("Não conformidades",nc,"achados individuais","red"),("Itens não informados",ni,"lacunas de evidência","blue")]):
        with col:card(*args)
    st.markdown('<div class="note"><b>Regra de leitura:</b> o ICL é um índice agregado de exposição. Ele <b>não certifica segurança</b>. Uma loja com ICL baixo pode ter uma não conformidade específica importante; por isso o painel mantém contagem, severidade, pilar e evidência de cada item.</div>',unsafe_allow_html=True)
    rows=[]
    for _,r in view.iterrows():
        _,p,_=calc(r);rows.append(p)
    pp=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame()
    if not pp.empty:
        g=pp.groupby("Pilar").agg(Exposição=("Exposição","mean"),Não_conformidades=("Não conformidades","sum"),Cobertura=("Cobertura","mean")).reset_index()
        a,b=st.columns(2)
        with a:
            f=px.bar(g,x="Exposição",y="Pilar",orientation="h",text="Exposição",title="Exposição técnica média por pilar");f.update_traces(texttemplate="%{text:.1f}",textposition="outside");f.update_layout(xaxis_range=[0,100]);st.plotly_chart(f,use_container_width=True)
        with b:
            f=px.bar(g,x="Não_conformidades",y="Pilar",orientation="h",text="Não_conformidades",title="Não conformidades por pilar");f.update_traces(textposition="outside");st.plotly_chart(f,use_container_width=True)
        f=px.bar(g,x="Cobertura",y="Pilar",orientation="h",text="Cobertura",title="Cobertura das respostas — ausência de dado é incerteza");f.update_traces(texttemplate="%{text:.0f}%",textposition="outside");f.update_layout(xaxis_range=[0,100]);st.plotly_chart(f,use_container_width=True)
    st.markdown("### 🏪 Visão comparativa das lojas")
    st.dataframe(view[["loja","icl_score","criticidade","nao_conformidades","nao_informados"]].rename(columns={"loja":"Loja","icl_score":"ICL","criticidade":"Grau ICL","nao_conformidades":"Não conformidades","nao_informados":"Não informados"}),use_container_width=True,hide_index=True)

elif module=="🏪 Diagnóstico por Loja":
    loja=st.selectbox("Selecione a operação",sorted(view.loja.unique()));r=view[view.loja==loja].iloc[0];d,p,icl=calc(r);g=grade(icl);nc=d[d.Severidade.fillna(0)>0];unk=d[d.Severidade.isna()]
    st.markdown(f"## 🏪 Diagnóstico técnico — {loja}")
    c=st.columns(4)
    for col,args in zip(c,[("ICL",f"{icl:.1f}%","índice agregado","orange"),("Grau ICL",g,"não é certificação","red" if g in ["Crítico","Severo"] else "blue"),("Não conformidades",len(nc),"todos os itens permanecem visíveis","red" if len(nc) else "green"),("Não informados",len(unk),"não tratados como conformes","blue")]):
        with col:card(*args)
    st.markdown('<div class="warn"><b>Conclusão:</b> o diagnóstico desta loja não é reduzido ao ICL. Cada desvio é contabilizado individualmente e os itens sem resposta permanecem como lacunas de evidência.</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        f=go.Figure(go.Indicator(mode="gauge+number",value=icl or 0,number={"suffix":"%"},gauge={"axis":{"range":[0,100]},"steps":[{"range":[0,20],"color":"#E8F5E9"},{"range":[20,35],"color":"#E3F2FD"},{"range":[35,50],"color":"#FFF3E0"},{"range":[50,70],"color":"#FFEBEE"},{"range":[70,100],"color":"#ECEFF1"}]}));f.update_layout(height=240);st.plotly_chart(f,use_container_width=True)
    with b:
        f=px.bar(p,x="Exposição",y="Pilar",orientation="h",color="Exposição",range_color=[0,100],text="Exposição",title="Exposição por pilar");f.update_traces(textposition="outside");f.update_layout(xaxis_range=[0,100]);st.plotly_chart(f,use_container_width=True)
    st.markdown("### 🚨 Achados e não conformidades")
    for _,x in nc.sort_values("Severidade",ascending=False).iterrows():
        st.markdown(f'<div class="finding"><b>{x.Pilar}</b> · {x.Item}<br><b>Resposta:</b> {x.Resposta} · <b>Severidade:</b> {x.Severidade}/100<br><span style="color:#64748B">{x.Observação or "Sem observação adicional."}</span></div>',unsafe_allow_html=True)
    st.markdown("### ⚠️ Itens sem informação")
    st.dataframe(unk[["Pilar","Item","Resposta"]],use_container_width=True,hide_index=True)
    st.markdown("### ✅ Itens conformes")
    st.dataframe(d[d.Severidade==0][["Pilar","Item","Resposta"]],use_container_width=True,hide_index=True)

elif module=="📐 Matriz de Criticidade & Risco":
    st.markdown("## 📐 Matriz de Criticidade & Risco")
    st.markdown('<div class="note"><b>Separação conceitual:</b> peso = importância do pilar; severidade = intensidade do desvio; cobertura = quantidade de evidência disponível; ICL = síntese agregada. Nenhuma dessas métricas substitui a leitura dos achados.</div>',unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{"Pilar":p,"Peso":f"{w*100:.0f}%"} for p,w in WEIGHTS.items()]),use_container_width=True,hide_index=True)
    st.markdown("### Escala de severidade")
    st.dataframe(pd.DataFrame([["0","Conforme"],["25","Atenção / parcial"],["50","Relevante"],["75","Não conforme / crítico"],["100","Severo / inoperante"]],columns=["Nota","Conceito"]),use_container_width=True,hide_index=True)
    st.markdown("### Matriz de risco")
    rr=pd.DataFrame([(p,c,p*c) for p in range(1,6) for c in range(1,6)],columns=["Probabilidade","Consequência","Risco"])
    f=px.scatter(rr,x="Probabilidade",y="Consequência",size="Risco",color="Risco",text="Risco",title="Risco = Probabilidade × Consequência (1–25)");f.update_traces(textposition="middle center");st.plotly_chart(f,use_container_width=True)
    st.caption("A matriz de risco é independente do ICL. Um achado pode ter alta consequência mesmo quando seu impacto ponderado sobre o ICL total é pequeno.")

elif module=="🤖 Análise Técnica Assistida":
    st.markdown("## 🤖 Análise Técnica Assistida")
    st.markdown('<div class="note"><b>Arquitetura futura do agente:</b> regras determinísticas calculam resultados; a IA apenas interpreta fatos, indicadores e referências aprovadas e redige o parecer. Ela não escolhe pesos nem inventa criticidade.</div>',unsafe_allow_html=True)
    loja=st.selectbox("Loja",sorted(view.loja.unique()));r=view[view.loja==loja].iloc[0];d,p,icl=calc(r)
    st.json({"shopping":shop,"ano":str(year),"loja":loja,"icl":icl,"criticidade":grade(icl),"achados":d[d.Severidade.fillna(0)>0].to_dict("records")})

elif module=="📋 Nova Vistoria":
    st.markdown("## 📋 Nova Vistoria")
    st.info("A entrada continua sendo manual. O PDF não é mais usado como módulo de importação.")
    with st.form("new"):
        shop=st.text_input("Shopping *","Guararapes");loja=st.text_input("Loja / operação *");mes=st.text_input("Mês de referência *","2026-09");data=st.text_input("Data/hora *")
        qs={}
        for p,items in PILLARS.items():
            st.markdown(f"### {p}")
            for i,key in enumerate(items):
                a,b=st.columns([1,2]);resp=a.text_input(key,key=f"r{i}");obs=b.text_input("Observação",key=f"o{i}");qs[key]={"resposta":resp or "(Sem preenchimento)","observacao":obs}
        geral=st.text_area("Observações gerais");ok=st.form_submit_button("💾 Salvar")
    if ok:
        if not shop or not loja or not mes or not data:st.error("Preencha Shopping, Loja, Mês e Data/Hora.")
        else:
            payload={"shopping":shop,"loja":loja,"mes_referencia":mes,"data_hora":data,"dados":{"shopping":shop,"questoes":qs,"observacoes_gerais":geral}}
            try:supabase.table("vistorias_exaustao").insert(payload).execute();st.success("Vistoria salva.");st.rerun()
            except Exception as e:st.error(str(e))

elif module=="📋 Matriz de Dados":
    st.markdown("## 📋 Matriz de Dados")
    st.dataframe(view[["loja","mes_referencia","icl_score","criticidade","nao_conformidades","nao_informados"]].rename(columns={"loja":"Loja","mes_referencia":"Mês","icl_score":"ICL","criticidade":"Grau ICL","nao_conformidades":"Não conformidades","nao_informados":"Não informados"}),use_container_width=True,hide_index=True)

elif module=="🗑️ Gerenciar Vistorias":
    st.markdown("## 🗑️ Gerenciar Vistorias")
    labels=[f"{r.id} | {r.loja} | {r.mes_referencia}" for _,r in df.iterrows()];sel=st.selectbox("Registro",labels);rid=sel.split("|")[0].strip()
    if st.button("❌ Excluir"):
        try:supabase.table("vistorias_exaustao").delete().eq("id",rid).execute();st.success("Excluído.");st.rerun()
        except Exception as e:st.error(str(e))
