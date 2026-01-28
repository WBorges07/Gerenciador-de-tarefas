import streamlit as st
import httpx

# --- CONFIGURAÇÃO DE ACESSO SEGURO ---
# O Streamlit vai buscar estes dados na aba 'Settings > Secrets' do seu painel online
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # Caso você esteja rodando localmente e ainda não configurou secrets
    SUPABASE_URL = "https://jwbzparfvgifpenxanfw.supabase.co"
    SUPABASE_KEY = "SUA_CHAVE_ANON_AQUI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# Configuração visual da página
st.set_page_config(page_title="TaskFlow Pro", page_icon="☁️", layout="centered")

st.markdown("""
    <style>
    .stCheckbox { font-size: 22px; }
    div[data-testid="stMetricValue"] { color: #4ade80; }
    </style>
    """, unsafe_allow_html=True)

st.title("☁️ TaskFlow Pro")

# --- 1. INTERFACE DE ENTRADA ---
with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    nome = col1.text_input("Tarefa", placeholder="Ex: Academia")
    ini = col2.time_input("Início")
    fim = col3.time_input("Fim")

    if st.button("🚀 Agendar na Nuvem", use_container_width=True):
        if nome:
            horario_formatado = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            dados_tarefa = {"nome": nome, "horario": horario_formatado, "feita": False}
            
            envio = httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=dados_tarefa)
            if envio.status_code in [200, 201]:
                st.rerun()
        else:
            st.warning("Digite o nome da tarefa.")

st.divider()

# --- 2. BUSCA DE DADOS NO SUPABASE ---
try:
    response = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = response.json() if response.status_code == 200 else []
except:
    tarefas = []

# --- 3. EXIBIÇÃO E PROGRESSO ---
if tarefas:
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    
    st.subheader(f"Progresso de Hoje: {int(percentual * 100)}%")
    st.progress(percentual)
    
    for t in tarefas:
        c1, c2 = st.columns([0.1, 0.9])
        
        # Checkbox para atualizar status
        feita = c1.checkbox("", value=t['feita'], key=f"check_{t['id']}", label_visibility="collapsed")
        
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        # Texto riscado se concluído
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~", unsafe_allow_html=True)
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")

    st.write("")
    # --- 4. BOTÃO DE LIMPAR (CORRIGIDO) ---
    if st.button("🗑️ Limpar todas as tarefas", use_container_width=False):
        # Usamos id=not.is.null para o Supabase aceitar o DELETE em massa
        limpeza = httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        if limpeza.status_code in [200, 204]:
            st.success("Lista limpa!")
            st.rerun()
        else:
            st.error("Erro ao limpar banco. Verifique o SQL Editor.")
else:
    st.info("Sua lista está vazia! Adicione uma tarefa acima.")