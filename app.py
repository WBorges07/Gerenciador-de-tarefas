import streamlit as st
import httpx

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

# Configuração da página
st.set_page_config(page_title="WN tarefas", page_icon="📝", layout="centered")

# --- 2. ESTILIZAÇÃO PERSONALIZADA (CSS PARA LOGO GIGANTE) ---
st.markdown("""
    <style>
    /* Container para dar espaço ao logo */
    .main-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 60px 0; /* Aumenta o respiro em volta do logo */
    }
    
    /* WN tarefas em tamanho máximo */
    .massive-logo {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        font-size: 85px; /* Tamanho massivo para impacto total */
        letter-spacing: -4px;
        line-height: 1;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        text-transform: uppercase; /* Deixa o logo mais robusto */
    }

    /* Botão Salvar Estilizado */
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 12px;
        border: none;
        height: 50px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# Aplicação do Logotipo Gigante
st.markdown('<div class="main-logo-container"><h1 class="massive-logo">WN TAREFAS</h1></div>', unsafe_allow_html=True)

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
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    
    st.subheader(f"Progresso: {int(percentual * 100)}%")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
        
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")
            
        # Excluir individualmente
        if c3.button("🗑️", key=f"del_{t['id']}"):
            httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
            st.rerun()

    st.write("")
    if st.button("🗑️ Limpar Lista Completa", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Nenhuma tarefa cadastrada.")