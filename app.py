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
    /* Estilização do botão Salvar */
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
        border-color: #4338CA;
        transform: translateY(-1px);
    }
    /* Estilização da Barra de Progresso */
    .stProgress > div > div > div > div {
        background-color: #10B981;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("☁️ TaskFlow Pro")

# --- 3. INTERFACE DE ENTRADA ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("Tarefa", placeholder="O que precisa ser feito?")
    col1, col2 = st.columns(2)
    
    # Horários com intervalo de 5 minutos
    ini = col1.time_input("Início", step=300)
    fim = col2.time_input("Fim", step=300)
    
    # Botão renomeado para "Salvar" com estilo profissional
    enviar = st.form_submit_button("Salvar", use_container_width=True)

    if enviar and nome:
        horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
        payload = {"nome": nome, "horario": horario, "feita": False}
        
        try:
            res = httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            if res.status_code in [200, 201]:
                st.rerun()
        except Exception:
            st.error("Erro ao conectar ao banco de dados.")

st.divider()

# --- 4. BUSCA E EXIBIÇÃO ---
try:
    busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = busca.json() if busca.status_code == 200 else []
except:
    tarefas = []

if tarefas:
    # Cálculo de progresso
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    
    st.subheader(f"Progresso: {int(percentual * 100)}%")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        c1, c2 = st.columns([0.1, 0.9])
        
        # Checkbox moderno
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")

    st.write("")
    # Botão de limpeza secundário
    if st.button("🗑️ Limpar Lista Completa", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Sua lista está vazia! Adicione uma tarefa acima.")