import streamlit as st
import httpx

# --- CONFIGURAÇÃO DE ACESSO (Substitua pelos seus dados) ---
# Certifique-se de que a URL comece com https://
SUPABASE_URL = "https://jwbzparfvgifpenxanfw.supabase.co" 
# Use a sua chave 'anon' public do painel API Keys
SUPABASE_KEY = "sb_publishable_8CT2OX2RrjepZ1yQHIpBDA_d43P66k-" 

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Configuração da página
st.set_page_config(page_title="TaskFlow Pro", page_icon="✅", layout="centered")

# Estilo visual moderno
st.markdown("""
    <style>
    .stCheckbox { font-size: 20px; }
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { color: #4ade80; }
    </style>
    """, unsafe_allow_html=True)

st.title("☁️ TaskFlow Pro")

# --- ÁREA DE ENTRADA DE TAREFAS ---
with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    nome = col1.text_input("Tarefa", placeholder="Ex: Academia")
    ini = col2.time_input("Início")
    fim = col3.time_input("Fim")

    if st.button("🚀 Agendar na Nuvem", use_container_width=True):
        if nome:
            horario_formatado = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            dados_tarefa = {
                "nome": nome, 
                "horario": horario_formatado, 
                "feita": False
            }
            
            try:
                # Envia para a tabela 'tarefas' no Supabase
                envio = httpx.post(
                    f"{SUPABASE_URL}/rest/v1/tarefas", 
                    headers=headers, 
                    json=dados_tarefa
                )
                
                if envio.status_code in [200, 201]:
                    st.success("Tarefa salva com sucesso!")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {envio.text}")
            except Exception as e:
                st.error(f"Erro de conexão: {e}")
        else:
            st.warning("Por favor, digite o nome da tarefa.")

st.divider()

# --- BUSCA E EXIBIÇÃO DAS TAREFAS ---
try:
    response = httpx.get(
        f"{SUPABASE_URL}/rest/v1/tarefas?select=*&order=created_at", 
        headers=headers
    )
    tarefas = response.json() if response.status_code == 200 else []
except Exception as e:
    st.error(f"Não foi possível carregar as tarefas: {e}")
    tarefas = []

# --- LÓGICA DA BARRA DE PROGRESSO ---
if tarefas:
    total = len(tarefas)
    concluidas = sum(1 for t in tarefas if t.get('feita') is True)
    percentual = concluidas / total
    
    st.subheader(f"Progresso de Hoje: {int(percentual * 100)}%")
    st.progress(percentual)
    
    st.write("") # Espaçamento visual

    for t in tarefas:
        c1, c2 = st.columns([0.1, 0.9])
        
        status_atual = t.get('feita', False)
        # Checkbox para marcar como feita
        check = c1.checkbox("", value=status_atual, key=str(t['id']), label_visibility="collapsed")
        
        # Se o usuário clicar no checkbox, atualiza o banco de dados
        if check != status_atual:
            httpx.patch(
                f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", 
                headers=headers, 
                json={"feita": check}
            )
            st.rerun()
            
        # Texto da tarefa (Riscado se estiver pronta)
        if status_atual:
            c2.markdown(f"<span style='color: gray; text-decoration: line-through;'>{t['nome']} ({t['horario']})</span>", unsafe_allow_html=True)
        else:
            c2.markdown(f"**{t['nome']}** — ⏰ {t['horario']}")
            
    # Botão para limpar o banco de dados
    if st.button("🗑️ Limpar todas as tarefas"):
        httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?select=*", headers=headers)
        st.rerun()
else:
    st.info("Sua lista está vazia! Adicione uma tarefa acima para começar.")