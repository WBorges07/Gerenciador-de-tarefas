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
st.set_page_config(page_title="TaskFlow Pro", page_icon="☁️")
st.title("☁️ TaskFlow Pro")

# --- 2. INTERFACE DE ENTRADA (FORMULÁRIO) ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("Tarefa", placeholder="Ex: Academia")
    col1, col2 = st.columns(2)
    ini = col1.time_input("Início")
    fim = col2.time_input("Fim")
    enviar = st.form_submit_button("🚀 Agendar na Nuvem", use_container_width=True)

    if enviar and nome:
        horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
        payload = {"nome": nome, "horario": horario, "feita": False}
        
        try:
            res = httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            if res.status_code in [200, 201]:
                st.rerun()
        except Exception as e:
            st.error("Erro ao conectar ao banco de dados.")

st.divider()

# --- 3. BUSCA E EXIBIÇÃO DE TAREFAS ---
try:
    busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = busca.json() if busca.status_code == 200 else []
except:
    tarefas = []

# --- 4. LÓGICA DA BARRA DE PROGRESSO ---
if tarefas:
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita'))
    percentual = concluidas / total
    
    # Exibe a barra e o texto que haviam sumido
    st.subheader(f"Progresso de Hoje: {int(percentual * 100)}%")
    st.progress(percentual)
    st.write("")

    for t in tarefas:
        c1, c2 = st.columns([0.1, 0.9])
        
        # Checkbox para atualizar o status
        feita = c1.checkbox("", value=t['feita'], key=f"id_{t['id']}", label_visibility="collapsed")
        
        if feita != t['feita']:
            httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
            st.rerun()
            
        if t['feita']:
            c2.markdown(f"~~{t['nome']} ({t['horario']})~~")
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")

    st.write("")
    # Botão de limpeza corrigido
    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Sua lista está vazia! Adicione uma tarefa acima.")