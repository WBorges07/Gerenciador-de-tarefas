import streamlit as st
import httpx

# --- 1. CONFIGURAÇÃO DE ACESSO (SECRETS) ---
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

# Configuração da página
st.set_page_config(page_title="WN tarefas", page_icon="📝", layout="centered")

# --- 2. ESTILIZAÇÃO PERSONALIZADA (CSS LOGO MASTER) ---
st.markdown("""
    <style>
    /* Reset de margens superiores do Streamlit */
    .block-container { padding-top: 2rem; }
    
    /* Logotipo WN tarefas - Estilo Imponente */
    .logo-master {
        font-family: 'Arial Black', Gadget, sans-serif;
        font-weight: 900;
        font-size: 110px; /* Tamanho Extremo */
        line-height: 0.9;
        letter-spacing: -6px;
        text-align: center;
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 4px 8px rgba(0,0,0,0.2));
        margin: 40px 0;
        text-transform: uppercase;
    }
    
    /* Ajuste para telas pequenas (Mobile) */
    @media (max-width: 640px) {
        .logo-master { font-size: 60px; letter-spacing: -3px; }
    }

    /* Botão Salvar Estilizado */
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 12px;
        height: 3.5rem;
        font-weight: bold;
        font-size: 1.2rem;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# Exibição do Logotipo Master
st.markdown('<h1 class="logo-master">WN<br>TAREFAS</h1>', unsafe_allow_html=True)

# --- 3. INTERFACE DE ENTRADA ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("O que vamos realizar agora?", placeholder="Digite aqui...")
    col1, col2 = st.columns(2)
    # Seleção de 5 em 5 minutos
    ini = col1.time_input("Início", step=300)
    fim = col2.time_input("Fim", step=300)
    enviar = st.form_submit_button("Salvar", use_container_width=True)

    if enviar and nome:
        horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
        payload = {"nome": nome, "horario": horario, "feita": False}
        try:
            res = httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            if res.status_code in [200, 201]: st.rerun()
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
    
    # Barra de Progresso
    st.markdown(f"### Progresso: **{int(percentual * 100)}%**")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
        
        # Checkbox
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")
            
        # Excluir individual
        if c3.button("🗑️", key=f"del_{t['id']}"):
            httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
            st.rerun()

    st.write("")
    if st.button("🗑️ Limpar Lista Completa", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Nenhuma tarefa cadastrada.")