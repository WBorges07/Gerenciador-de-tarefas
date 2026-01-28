import streamlit as st
import httpx
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib

# --- CONFIGURAÇÃO ---
SUPABASE_URL = st.secrets["SUPABASE_URL"].strip("/")
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="WN Tarefas Pro", page_icon="🎯", layout="centered")

# --- FUNÇÕES DE SEGURANÇA ---
def hash_senha(senha):
    return hashlib.sha256(str.encode(senha)).hexdigest()

def realizar_login(email, senha):
    res = httpx.get(f"{SUPABASE_URL}/rest/v1/perfis?email=eq.{email}&senha=eq.{hash_senha(senha)}", headers=headers)
    usuarios = res.json()
    return usuarios[0] if usuarios else None

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .logo-box { background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); padding: 10px 25px; border-radius: 15px; text-align: center; }
    .logo-text { color: white !important; font-weight: 800; font-size: 30px; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- GERENCIAMENTO DE SESSÃO (LOGIN) ---
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.markdown('<div class="logo-box"><p class="logo-text">🎯 WN LOGIN</p></div>', unsafe_allow_html=True)
    tab_login, tab_cad = st.tabs(["Acessar", "Criar Conta"])
    
    with tab_login:
        with st.form("login"):
            e = st.text_input("E-mail")
            s = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                u = realizar_login(e, s)
                if u:
                    st.session_state.usuario = u
                    st.rerun()
                else: st.error("Usuário ou senha inválidos")

    with tab_cad:
        with st.form("cadastro"):
            novo_e = st.text_input("E-mail")
            novo_s = st.text_input("Senha", type="password")
            zap = st.text_input("WhatsApp (Ex: 5511999999999)")
            if st.form_submit_button("Cadastrar"):
                payload = {"email": novo_e, "senha": hash_senha(novo_s), "whatsapp": zap}
                httpx.post(f"{SUPABASE_URL}/rest/v1/perfis", headers=headers, json=payload)
                st.success("Conta criada! Acesse a aba de Login.")
    st.stop()

# --- APP LOGADO ---
u_id = st.session_state.usuario['email']
u_zap = st.session_state.usuario.get('whatsapp', '')

st.sidebar.write(f"Logado como: **{u_id}**")
if st.sidebar.button("Sair"):
    st.session_state.usuario = None
    st.rerun()

st.markdown('<div class="logo-box"><p class="logo-text">🎯 WN TAREFAS</p></div>', unsafe_allow_html=True)
aba1, aba2 = st.tabs(["🚀 HOJE", "📊 HISTÓRICO"])

with aba1:
    with st.form("nova_tarefa"):
        nome = st.text_input("O que vamos fazer?")
        c1, c2 = st.columns(2)
        ini = c1.time_input("Início")
        fim = c2.time_input("Fim")
        
        st.write("---")
        col_zap, col_rep = st.columns(2)
        avisar = col_zap.checkbox("🔔 Notificar no WhatsApp (15min antes)")
        repetir = col_rep.checkbox("🔁 Repetir Diariamente")
        
        if st.form_submit_button("Agendar", use_container_width=True):
            horario_ini = ini.strftime('%H:%M')
            payload = {
                "nome": nome, "horario": f"{horario_ini} - {fim.strftime('%H:%M')}",
                "feita": False, "data": str(date.today()), "repetir": repetir,
                "usuario_id": u_id, "avisar_zap": avisar
            }
            httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            # DICA: Aqui você enviaria o payload para um serviço como o n8n para agendar o Zap
            st.rerun()

    # Listagem (Filtrada por usuário)
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_id}&data=eq.{date.today()}&order=horario.asc", headers=headers)
        tarefas = res.json()
        for t in tarefas:
            c1, c2, c3 = st.columns([0.1, 0.7, 0.2])
            f = c1.checkbox("", value=t['feita'], key=t['id'])
            if f != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": f})
                st.rerun()
            zap_icon = "🔔" if t.get('avisar_zap') else ""
            c2.write(f"{zap_icon} **{t['nome']}** ({t['horario']})")
            if c3.button("🗑️", key=f"del_{t['id']}"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    except: st.write("Inicie sua jornada!")

with aba2:
    st.subheader("Seu Histórico")
    # Gráfico simples de barras
    res_hist = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?usuario_id=eq.{u_id}&feita=eq.true", headers=headers)
    df = pd.DataFrame(res_hist.json())
    if not df.empty:
        df_count = df.groupby('data').size()
        st.bar_chart(df_count)
    else: st.write("Sem dados para exibir ainda.")