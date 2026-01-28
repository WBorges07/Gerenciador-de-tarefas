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
st.set_page_config(page_title="TaskFlow Pro", page_icon="☁️", layout="centered")

# --- 2. ESTILIZAÇÃO PERSONALIZADA (CSS) ---
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        transform: translateY(-1px);
    }
    /* Estilo para o botão de excluir unitário */
    .stButton button[kind="secondary"] {
        background-color: transparent;
        color: #EF4444;
        border: 1px solid #EF4444;
        padding: 0.2rem 0.5rem;
    }
    .stButton button[kind="secondary"]:hover {
        background-color: #EF4444;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("☁️ TaskFlow Pro")

# --- 3. INTERFACE DE ENTRADA ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("Tarefa", placeholder="O que precisa ser feito?")
    col1, col2 = st.columns(2)
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
            st.error("Erro ao conectar ao banco.")

st.divider()

# --- 4. BUSCA E EXIBIÇÃO ---
try:
    busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = busca.json() if busca.status_code == 200 else []
except:
    tarefas = []

if tarefas:
    # Barra de Progresso
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    st.subheader(f"Progresso: {int(percentual * 100)}%")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        # Criamos 3 colunas: Checkbox, Texto da Tarefa e Botão de Excluir
        c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
        
        # Checkbox de status
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        # Nome da tarefa
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")
            
        # Botão de Excluir individual
        if c3.button("🗑️", key=f"del_{t['id']}", help="Excluir esta tarefa"):
            httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
            st.rerun()

    st.write("")
    if st.button("🗑️ Limpar Lista Completa", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Sua lista está vazia!")