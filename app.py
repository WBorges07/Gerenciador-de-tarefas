import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, date, timedelta

# --- 1. CONFIGURAÇÃO DE ACESSO (SECRETS) ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Erro: Credenciais não encontradas nos Secrets.")
    st.stop()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="WN Tarefas", page_icon="🎯", layout="centered")

# --- 2. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .logo-container { display: flex; justify-content: center; padding: 10px 0 30px 0; }
    .logo-box { background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); padding: 10px 25px; border-radius: 15px; }
    .logo-text { color: white !important; font-weight: 800; font-size: 32px; text-transform: uppercase; margin: 0; }
    div.stButton > button { border-radius: 10px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="logo-container"><div class="logo-box"><p class="logo-text">🎯 WN Tarefas</p></div></div>', unsafe_allow_html=True)

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# --- 3. ABAS ---
aba_hoje, aba_historico = st.tabs(["🚀 HOJE", "📊 HISTÓRICO & ANÁLISE"])

# --- ABA HOJE ---
with aba_hoje:
    with st.form("form_tarefa", clear_on_submit=True):
        st.subheader("✏️" if st.session_state.edit_id else "🆕 Tarefa")
        nome = st.text_input("O que vamos realizar?", key="input_nome")
        c1, c2 = st.columns(2)
        ini = c1.time_input("Início", value=datetime.now().time(), step=300)
        fim = c2.time_input("Fim", value=datetime.now().time(), step=300)
        repetir = st.checkbox("Repetir diariamente")
        
        btn_salvar = st.form_submit_button("Salvar Tarefa", use_container_width=True)
        if btn_salvar and nome:
            horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            payload = {"nome": nome, "horario": horario, "feita": False, "data": str(date.today()), "repetir": repetir}
            if st.session_state.edit_id:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{st.session_state.edit_id}", headers=headers, json=payload)
                st.session_state.edit_id = None
            else:
                httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            st.rerun()

    st.divider()
    
    hoje_str = str(date.today())
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?or=(data.eq.{hoje_str},repetir.eq.true)&order=horario.asc", headers=headers)
        tarefas = res.json()
    except: tarefas = []

    if tarefas:
        for t in tarefas:
            col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
            feita = col1.checkbox("", value=t['feita'], key=f"h_{t['id']}", label_visibility="collapsed")
            if feita != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
                st.rerun()
            
            label = f"~~{t['nome']}~~" if t['feita'] else f"**{t['nome']}**"
            col2.markdown(f"{label} <br><small>⏰ {t['horario']}</small>", unsafe_allow_html=True)
            
            b_edit, b_del = col3.columns(2)
            if b_edit.button("✏️", key=f"ed_{t['id']}"):
                st.session_state.edit_id = t['id']
                st.rerun()
            if b_del.button("🗑️", key=f"dl_{t['id']}"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    else:
        st.info("Nenhuma tarefa para hoje.")

# --- ABA HISTÓRICO & ANÁLISE ---
with aba_historico:
    # 1. GRÁFICO DE PRODUTIVIDADE (Últimos 7 dias)
    st.subheader("📈 Produtividade da Semana")
    try:
        data_limite = str(date.today() - timedelta(days=7))
        res_graph = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=gte.{data_limite}&feita=eq.true", headers=headers)
        dados_brutos = res_graph.json()
        
        if dados_brutos:
            df = pd.DataFrame(dados_brutos)
            df['data'] = pd.to_datetime(df['data']).dt.strftime('%d/%m')
            contagem = df.groupby('data').size().reset_index(name='Concluídas')
            st.bar_chart(contagem.set_index('data'), color="#4F46E5")
        else:
            st.write("Ainda não há dados suficientes para o gráfico.")
    except:
        st.write("Erro ao carregar gráfico.")

    st.divider()

    # 2. BUSCA E FILTROS
    st.subheader("🔍 Encontrar Tarefas")
    col_busca, col_data = st.columns([0.6, 0.4])
    termo_busca = col_busca.text_input("Pesquisar por nome...", placeholder="Ex: Academia")
    data_pesquisa = col_data.date_input("Filtrar por data", value=date.today())

    try:
        query_url = f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{str(data_pesquisa)}&order=horario.asc"
        res_hist = httpx.get(query_url, headers=headers)
        tarefas_hist = res_hist.json()

        # Filtragem em tempo real (Search)
        if termo_busca:
            tarefas_hist = [t for t in tarefas_hist if termo_busca.lower() in t['nome'].lower()]

        if tarefas_hist:
            for t in tarefas_hist:
                status = "✅" if t['feita'] else "⏳"
                st.write(f"{status} **{t['horario']}** - {t['nome']}")
        else:
            st.warning("Nenhuma tarefa encontrada com esses critérios.")
    except:
        st.error("Erro ao buscar histórico.")