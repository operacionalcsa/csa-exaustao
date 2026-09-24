import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

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
# Função para Carregar Vistorias da Tabela "vistorias_exaustao"
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
    st.info("Preencha os dados da loja vistoriada. O campo de resposta aceita até duas palavras. O campo de anotações é opcional.")

    with st.form("form_vistoria", clear_on_submit=True):
        st.subheader("📍 Identificação Geral")
        col_loja, col_data = st.columns(2)
        loja_nome = col_loja.text_input("LOJA *", placeholder="Ex: Loja 01 - Centro")
        data_hora = col_data.text_input("DATA/HORA *", value=datetime.now().strftime("%Y-%m-%d %H:%M"))

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
                    placeholder="Ex: Sim / Não / Inox",
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
                    "resposta": resp.strip(),
                    "observacao": obs.strip()
                }

        st.divider()
        st.markdown("### 🔽 OBSERVAÇÕES GERAIS")
        obs_gerais = st.text_area("OBSERVAÇÕES GERAIS", placeholder="Digite considerações gerais sobre a vistoria técnica...")

        submetido = st.form_submit_button("💾 Salvar Relatório de Vistoria")

        if submetido:
            if not loja_nome or not data_hora:
                st.error("Por favor, preencha o nome da LOJA e DATA/HORA antes de salvar.")
            else:
                dados_payload = {
                    "loja": loja_nome,
                    "data_hora": data_hora,
                    "status": "Concluída",
                    "observacoes_gerais": obs_gerais,
                    "questoes": respostas_coletadas,
                    "created_at": datetime.now().isoformat()
                }

                try:
                    supabase.table("vistorias_exaustao").insert({
                        "loja": loja_nome,
                        "data_hora": data_hora,
                        "status": "Concluída",
                        "dados": dados_payload
                    }).execute()

                    st.success(f"Relatório da {loja_nome} salvo com sucesso no banco de dados!")
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
        c1.metric("Total de Vistorias Salvas", len(df))
        
        if "loja" in df.columns:
            lojas_unicas = df["loja"].dropna().nunique()
            c2.metric("Lojas Cadastradas", lojas_unicas)
        
        c3.metric("Norma de Referência", "ABNT NBR 14518:2019")

        st.divider()
        st.subheader("Registros Recentes")
        
        col_tabela, col_grafico = st.columns([2, 1])
        with col_tabela:
            exibir_df = df[["loja", "data_hora", "status", "created_at"]] if "loja" in df.columns else df
            st.dataframe(exibir_df, use_container_width=True)

        with col_grafico:
            if "loja" in df.columns and not df["loja"].isnull().all():
                fig = px.bar(df, x="loja", title="Vistorias por Loja", color="loja")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma vistoria cadastrada até o momento. Acesse o menu 'Novo Relatório' para preencher o formulário.")

# -----------------------------------------------------------------------------
# MÓDULO 3: Análise Detalhada das Lojas
# -----------------------------------------------------------------------------
elif menu == "🔍 Análise Detalhada das Lojas":
    st.header("Análise Detalhada")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas_validas = df["loja"].dropna().unique()
        loja_sel = st.selectbox("Selecione a Loja para visualizar o checklist completo:", lojas_validas)
        
        registro = df[df["loja"] == loja_sel].iloc[0]
        dados_json = registro.get("dados", {})

        st.write(f"**Data da Vistoria:** {registro.get('data_hora', 'N/A')}")
        
        if isinstance(dados_json, dict) and "questoes" in dados_json:
            questoes = dados_json["questoes"]
            
            itens = []
            for q, val in questoes.items():
                itens.append({
                    "Item / Pergunta": q,
                    "Resposta (Até 2 Palavras)": val.get("resposta", ""),
                    "Anotações / Observações": val.get("observacao", "")
                })
            
            st.dataframe(pd.DataFrame(itens), use_container_width=True)
            
            if "observacoes_gerais" in dados_json and dados_json["observacoes_gerais"]:
                st.subheader("Observações Gerais")
                st.info(dados_json["observacoes_gerais"])
        else:
            st.warning("Selecione um registro salvo através do novo formulário.")
    else:
        st.info("Nenhum dado cadastrado para análise.")

# -----------------------------------------------------------------------------
# MÓDULO 4: Diagnósticos e Laudos Técnicos
# -----------------------------------------------------------------------------
elif menu == "📄 Diagnósticos e Laudos Técnicos":
    st.header("Diagnósticos e Pareceres Dissertativos Ricos")

    if not df.empty and "loja" in df.columns and df["loja"].notnull().any():
        lojas_validas = df["loja"].dropna().unique()
        loja_laudo = st.selectbox("Selecione a Loja para Gerar o Laudo:", lojas_validas)
        
        if st.button("📄 Gerar Laudo Técnico Completo"):
            registro = df[df["loja"] == loja_laudo].iloc[0]
            dados_json = registro.get("dados", {})
            questoes = dados_json.get("questoes", {}) if isinstance(dados_json, dict) else {}

            st.markdown(f"## 📋 PARECER TÉCNICO DE VISTORIA - {str(loja_laudo).upper()}")
            st.markdown(f"**Norma de Referência:** ABNT NBR 14518:2019 (Sistemas de Exaustão para Cozinhas Profissionais)")
            st.markdown(f"**Data/Hora do Levantamento:** {registro.get('data_hora', 'N/A')}")
            st.divider()

            st.markdown("### 1. DIAGNÓSTICO DO SISTEMA DE COIFA")
            for p in SECOES_RELATORIO["DADOS DA COIFA"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "Não informado")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Anotação: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.markdown("### 2. DIAGNÓSTICO DO EXAUSTOR E CASA DE MÁQUINAS")
            for p in SECOES_RELATORIO["DADOS DO EXAUSTOR"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "Não informado")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Anotação: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.markdown("### 3. DIAGNÓSTICO DOS DUTOS DE EXAUSTÃO")
            for p in SECOES_RELATORIO["DUTOS DE EXAUSTÃO"]:
                if p in questoes:
                    r = questoes[p].get("resposta", "Não informado")
                    o = questoes[p].get("observacao", "")
                    obs_str = f" _(Anotação: {o})_" if o else ""
                    st.markdown(f"- **{p}:** {r}{obs_str}")

            st.divider()
            st.markdown("### 4. PARECER DISSERTATIVO FINAL E RECOMENDAÇÕES")
            obs_g = dados_json.get("observacoes_gerais", "") if isinstance(dados_json, dict) else ""
            st.write(f"""
            O sistema de exaustão da unidade **{loja_laudo}** foi inspecionado em conformidade com as diretrizes da norma ABNT NBR 14518:2019. 
            Com base nos dados inseridos, recomenda-se a execução regular das rotinas de manutenção preventiva e corretiva nos pontos observados.
            
            **Observações Gerais da Vistoria:**
            {obs_g if obs_g else 'Nenhuma observação geral registrada.'}
            """)
    else:
        st.info("Cadastre ao menos uma loja no formulário para gerar o laudo técnico.")

# -----------------------------------------------------------------------------
# MÓDULO 5: Configurações
# -----------------------------------------------------------------------------
elif menu == "⚙️ Configurações":
    st.header("Configurações e Banco de Dados")
    st.success("Conexão ativada com o Supabase (Tabela: vistorias_exaustao).")
    if st.button("🔄 Atualizar Cache de Dados"):
        st.cache_data.clear()
        st.success("Dados recarregados com sucesso!")
