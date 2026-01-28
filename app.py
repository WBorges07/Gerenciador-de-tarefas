import streamlit as st
import httpx

# --- 1. CONFIGURAÇÃO DE ACESSO (SECRETS) ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Erro: Credenciais não encontradas nos Secrets do Streamlit.")
    st.stop()

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Configuração da página
st.set_page_config(page_title="WN tarefas", page_icon="📝", layout="centered")

# --- 2. ESTILIZAÇÃO PERSONALIZADA (CSS PRO - LOGO AMPLIADO) ---
st.markdown("""
    <style>
    /* Logotipo WN tarefas Ampliado e Centralizado */
    .logo-container {
        display: flex;
        justify-content: center;
        padding: 20px 0 40px 0;
    }
    .logo-text {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 900;
        font-size: 64px; /* Aumentado de 42px para 64px */
        letter-spacing: -2px;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    
    /* Botão Salvar Principal */
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }

    /* Botão de Excluir (Lixeira) */
    .stButton button[kind="secondary"] {
        background-color: transparent;
        color: #EF4444;
        border: 1px solid #EF4444;
        border-radius: 6px;
    }
    .stButton button[kind="secondary"]:hover {
        background-color: #EF4444;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Título Estilizado e Gigante
st.markdown('<div class="logo-container"><p class="logo-text">WN tarefas</p></div>', unsafe_allow_html=True)

# --- 3. INTERFACE DE ENTRADA ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("Tarefa", placeholder="O que vamos realizar agora?")
    col1, col2 = st.columns(2)
    # Seleção de 5 em 5 minutos
    ini = col1.time_input("Início", step=300)
    fim = col2.time_input("Fim", step=300)
    enviar = st.form_submit_button("Salvar", use_container_width=True)

    if enviar and nome:
        horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
        payload = {"nome": nome, "horario": horario, "feita": False}
        try:
            httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            st.rerun()
        except:
            st.error("Erro na conexão com o banco.")

st.divider()

# --- 4. BUSCA E EXIBIÇÃO ---
try:
    busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = busca.json() if busca.status_code == 200 else []
except:
    tarefas = []

if tarefas:
    # Progresso e Barra
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    
    st.subheader(f"Progresso: {int(percentual * 100)}%")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
        
        # Checkbox de status
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        # Texto da Tarefa
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")
            
        # Excluir Item por Item
        if c3.button("🗑️", key=f"del_{t['id']}"):
            httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
            st.rerun()

    st.write("")
    if st.button("🗑️ Limpar Lista Completa", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Nenhuma tarefa cadastrada.")