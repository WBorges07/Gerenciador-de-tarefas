import streamlit as st
import httpx

# Tenta pegar dos Secrets, se falhar, usa o texto direto (para teste)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].strip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    SUPABASE_URL = "https://jwbzparfvgifpenxanfw.supabase.co"
    SUPABASE_KEY = "SUA_CHAVE_AQUI"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.title("☁️ TaskFlow Pro")

# --- ENTRADA ---
with st.form("nova_tarefa", clear_on_submit=True):
    nome = st.text_input("Tarefa")
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
                st.success("Salvo!")
                st.rerun()
            else:
                st.error(f"Erro no Banco: {res.text}")
        except Exception as e:
            st.error(f"Erro de Conexão: Verifique se a URL nos Secrets está correta.")

# --- LISTA ---
try:
    busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", headers=headers)
    tarefas = busca.json() if busca.status_code == 200 else []
except:
    tarefas = []

if tarefas:
    for t in tarefas:
        col_c, col_t = st.columns([0.1, 0.9])
        if col_c.checkbox("", value=t['feita'], key=str(t['id'])):
            if not t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": True})
                st.rerun()
        col_t.write(f"{t['nome']} ({t['horario']})")
    
    if st.button("🗑️ Limpar Tudo"):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=not.is.null", headers=headers)
        st.rerun()
else:
    st.info("Sua lista está vazia!")