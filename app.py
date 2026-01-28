import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib

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

st.set_page_config(page_title="WN Tarefas Pro", page_icon="🎯", layout="centered")

# --- 2. FUNÇÕES DE SEGURANÇA ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def realizar_login(email, senha):
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/perfis?email=eq.{email}&senha=eq.{hash_senha(senha)}", headers=headers)
        usuarios = res.json()
        return usuarios[0] if usuarios else None
    except: return None

# --- 3. ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .logo-box { background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); padding: 10px 25px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .logo-text { color: white !important; font-weight: 800; font-size: 30px; margin: 0; text-transform: uppercase; letter-spacing: -1px; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    div.stButton > button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. GERENCIAMENTO DE SESSÃO ---
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# --- 5. TELA DE ACESSO (LOGIN/CADASTRO) ---
if st.session_state.usuario is None:
    st.markdown('<div class="logo-box"><p class="logo-text">🎯 WN LOGIN</p></div>', unsafe_allow_html=True)
    tab_l, tab_c = st.tabs(["Acessar", "Criar Conta"])
    
    with tab_l:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                u = realizar_login(e, s)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else: st.error("E-mail ou senha incorretos.")
    
    with tab_c:
        with st.form("cadastro"):
            ne = st.text_input("Novo E-mail")
            ns = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Cadastrar Conta", use_container_width=True):
                payload = {"email": ne, "senha": hash_senha(ns)}
                httpx.post(f"{SUPABASE_URL}/rest/v1/perfis", headers=headers, json=payload)
                st.success("Conta criada com sucesso! Acesse a aba 'Acessar'.")
    st.stop()

# --- 6. APP LOGADO ---
u_email = st.session_state.usuario['email']
st.sidebar.subheader(f"Olá, {u_email.split('@')[0]}!")
if st.sidebar.button("Sair do Sistema"):
    st.session_state.usuario = None
    st.rerun()

st.markdown('<div class="logo-box"><p class="logo-text">🎯 WN TAREFAS</p></div>', unsafe_allow_html=True)
aba1, aba2 = st.tabs(["🚀 HOJE", "📊 ANÁLISE & BUSCA"])

# --- ABA HOJE ---
with aba1:
    titulo_f = "✏️ Editar Tarefa" if st.session_state.edit_id else "🆕 Nova Tarefa"
    with st.form("form_tarefa", clear_on_submit=True):
        st.write(f"### {titulo_f}")
        nome = st.text_input("O que vamos realizar?", placeholder="Ex: Academia, Reunião...")
        c1, c2 = st.columns(2)
        # Intervalo de 5 em 5 minutos
        ini = c1.time_input("Início", step=300)
        fim = c2.time_input("Fim", step=300)
        
        rep = st.checkbox("🔁 Repetir esta tarefa diariamente")
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.form_submit_button("Salvar", use_container_width=True):
            if nome:
                horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
                payload = {
                    "nome": nome, "horario": horario, "feita": False,
                    "data": str(date.today()), "repetir": rep,
                    "usuario_id": u_email
                }
                if st.session_state.edit_id:
                    httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{st.session_state.edit_id}", headers=headers, json=payload)
                    st.session_state.edit_id = None
                else:
                    httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
                st.rerun()

        if st.session_state.edit_id:
            if col_b2.form_submit_button("Cancelar Edição", use_container_width=True):
                st.session_state.edit_id = None
                st.rerun()

    st.divider()

    # Listagem de Hoje organizada por horário
    try:
        query = f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&or=(data.eq.{date.today()},repetir.eq.true)&order=horario.asc"
        tarefas = httpx.get(query, headers=headers).json()
        
        for t in tarefas:
            col_f, col_t, col_o = st.columns([0.1, 0.6, 0.3])
            
            # Checkbox Status
            status = col_f.checkbox("", value=t['feita'], key=f"check_{t['id']}", label_visibility="collapsed")
            if status != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": status})
                st.rerun()
            
            # Texto da Tarefa
            txt = f"~~{t['nome']}~~" if t['feita'] else f"**{t['nome']}**"
            rep_icon = "🔁" if t.get('repetir') else ""
            col_t.markdown(f"{txt} {rep_icon} <br><small>⏰ {t['horario']}</small>", unsafe_allow_html=True)
            
            # Operações
            b_ed, b_de = col_o.columns(2)
            if b_ed.button("✏️", key=f"ed_{t['id']}"):
                st.session_state.edit_id = t['id']
                st.rerun()
            if b_de.button("🗑️", key=f"del_{t['id']}"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    except:
        st.info("Nenhuma tarefa para exibir.")

# --- ABA ANÁLISE & BUSCA ---
with aba2:
    st.subheader("🔍 Localizar Tarefas")
    c_busca, c_data = st.columns([0.6, 0.4])
    termo = c_busca.text_input("Pesquisar nome...")
    dt_f = c_data.date_input("Filtrar por dia", value=date.today())
    
    try:
        res_h = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&data=eq.{dt_f}&order=horario.asc", headers=headers).json()
        if termo:
            res_h = [t for t in res_h if termo.lower() in t['nome'].lower()]
        
        if res_h:
            for t in res_h:
                status = "✅" if t['feita'] else "⏳"
                st.write(f"{status} **{t['horario']}** - {t['nome']}")
        else:
            st.write("Nenhum registro encontrado.")
    except: pass

    st.divider()
    st.subheader("📈 Produtividade Semanal")
    try:
        limite = str(date.today() - timedelta(days=7))
        res_g = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&data=gte.{limite}&feita=eq.true", headers=headers).json()
        if res_g:
            df = pd.DataFrame(res_g)
            df['data'] = pd.to_datetime(df['data']).dt.strftime('%d/%m')
            st.bar_chart(df.groupby('data').size(), color="#4F46E5")
    except:
        st.write("Ainda não há dados suficientes para gerar o gráfico.")