import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib

# --- 1. CONFIGURAÇÃO DE ACESSO ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Erro: Credenciais não encontradas.")
    st.stop()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="WN Tarefas Pro", page_icon="🎯", layout="centered")

# --- 2. DEFINIÇÃO DE CATEGORIAS E CORES ---
CATEGORIAS = {
    "Reunião": "#EF4444",           # Vermelho
    "Retorno de reunião": "#F59E0B", # Âmbar
    "Rotina diária": "#10B981",      # Verde
    "Entreterimento": "#8B5CF6",     # Roxo
    "Foco": "#3B82F6",               # Azul
    "Livre": "#6B7280"               # Cinza
}

# --- 3. FUNÇÕES DE SEGURANÇA ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def realizar_login(email, senha):
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/perfis?email=eq.{email}&senha=eq.{hash_senha(senha)}", headers=headers)
        usuarios = res.json()
        return usuarios[0] if usuarios else None
    except: return None

# --- 4. ESTILIZAÇÃO CSS ---
st.markdown(f"""
    <style>
    .logo-box {{ background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); padding: 10px 25px; border-radius: 15px; text-align: center; margin-bottom: 20px; }}
    .logo-text {{ color: white !important; font-weight: 800; font-size: 30px; margin: 0; text-transform: uppercase; }}
    .task-card {{ padding: 10px; border-radius: 8px; border-left: 6px solid; background: #fdfdfd; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
    div.stButton > button {{ border-radius: 8px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 5. GERENCIAMENTO DE SESSÃO ---
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# --- 6. TELA DE ACESSO ---
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
                else: st.error("Dados incorretos.")
    with tab_c:
        with st.form("cadastro"):
            ne = st.text_input("Novo E-mail")
            ns = st.text_input("Nova Senha", type="password")
            if st.form_submit_button("Cadastrar", use_container_width=True):
                httpx.post(f"{SUPABASE_URL}/rest/v1/perfis", headers=headers, json={"email": ne, "senha": hash_senha(ns)})
                st.success("Conta criada!")
    st.stop()

# --- 7. APP LOGADO ---
u_email = st.session_state.usuario['email']
st.sidebar.subheader(f"Olá, {u_email.split('@')[0]}!")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.rerun()

st.markdown('<div class="logo-box"><p class="logo-text">🎯 WN TAREFAS</p></div>', unsafe_allow_html=True)
aba1, aba2 = st.tabs(["🚀 HOJE", "📊 ANÁLISE"])

with aba1:
    titulo_f = "✏️ Editar Tarefa" if st.session_state.edit_id else "🆕 Nova Tarefa"
    with st.form("form_tarefa", clear_on_submit=True):
        st.write(f"### {titulo_f}")
        nome = st.text_input("O que vamos realizar?")
        cat = st.selectbox("Categoria", list(CATEGORIAS.keys()))
        c1, c2 = st.columns(2)
        ini = c1.time_input("Início", step=300)
        fim = c2.time_input("Fim", step=300)
        rep = st.checkbox("Repetir diariamente")
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.form_submit_button("Salvar", use_container_width=True):
            if nome:
                horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
                payload = {
                    "nome": nome, "horario": horario, "feita": False,
                    "data": str(date.today()), "repetir": rep,
                    "usuario_id": u_email, "categoria": cat
                }
                if st.session_state.edit_id:
                    httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{st.session_state.edit_id}", headers=headers, json=payload)
                    st.session_state.edit_id = None
                else:
                    httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
                st.rerun()
        if st.session_state.edit_id and col_b2.form_submit_button("Cancelar"):
            st.session_state.edit_id = None
            st.rerun()

    st.divider()

    # LISTAGEM
    try:
        query = f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&or=(data.eq.{date.today()},repetir.eq.true)&order=horario.asc"
        tarefas = httpx.get(query, headers=headers).json()
        
        for t in tarefas:
            cor = CATEGORIAS.get(t.get('categoria', 'Livre'), "#6B7280")
            
            # Card Customizado com Borda da Categoria
            st.markdown(f"""
                <div style="border-left: 6px solid {cor}; padding: 10px; background: #f9f9f9; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 12px; font-weight: bold; color: {cor}; text-transform: uppercase;">{t.get('categoria', 'Livre')}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([0.1, 0.65, 0.25])
            status = c1.checkbox("", value=t['feita'], key=f"c_{t['id']}", label_visibility="collapsed")
            if status != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": status})
                st.rerun()
            
            txt = f"~~{t['nome']}~~" if t['feita'] else f"**{t['nome']}**"
            c2.markdown(f"{txt}<br><small>⏰ {t['horario']}</small>", unsafe_allow_html=True)
            
            b_ed, b_de = c3.columns(2)
            if b_ed.button("✏️", key=f"e_{t['id']}"):
                st.session_state.edit_id = t['id']
                st.rerun()
            if b_de.button("🗑️", key=f"d_{t['id']}"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    except: st.info("Sem tarefas.")

with aba2:
    st.subheader("📊 Resumo de Esforço")
    res_g = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&feita=eq.true", headers=headers).json()
    if res_g:
        df = pd.DataFrame(res_g)
        st.write("Tarefas concluídas por categoria:")
        cat_count = df['categoria'].value_counts()
        st.bar_chart(cat_count)
    
    st.divider()
    dt_f = st.date_input("Histórico por data", value=date.today())
    res_h = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_email}&data=eq.{dt_f}&order=horario.asc", headers=headers).json()
    for t in res_h:
        st.write(f"{'✅' if t['feita'] else '⏳'} **{t['horario']}** - {t['nome']} ({t['categoria']})")