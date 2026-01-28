import streamlit as st
import httpx
from datetime import datetime, date

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

# --- 2. ESTILIZAÇÃO CSS (LOGO MASTER E BOTÕES) ---
st.markdown("""
    <style>
    .logo-master {
        font-family: 'Arial Black', sans-serif;
        font-weight: 900;
        font-size: 100px;
        line-height: 0.8;
        letter-spacing: -5px;
        text-align: center;
        background: linear-gradient(135deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 40px 0;
        text-transform: uppercase;
    }
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 12px;
        height: 3rem;
        font-weight: bold;
        border: none;
    }
    /* Estilo mobile para o logo */
    @media (max-width: 640px) { .logo-master { font-size: 60px; } }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="logo-master">WN<br>TAREFAS</h1>', unsafe_allow_html=True)

# --- 3. NAVEGAÇÃO POR ABAS ---
aba_hoje, aba_calendario = st.tabs(["🚀 HOJE", "📅 CALENDÁRIO"])

# --- ABA 1: TAREFAS DE HOJE ---
with aba_hoje:
    with st.form("nova_tarefa", clear_on_submit=True):
        nome = st.text_input("O que vamos realizar agora?", placeholder="Digite a tarefa...")
        col1, col2 = st.columns(2)
        # Seleção de 5 em 5 minutos
        ini = col1.time_input("Início", step=300)
        fim = col2.time_input("Fim", step=300)
        enviar = st.form_submit_button("Salvar", use_container_width=True)

        if enviar and nome:
            horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            # Salvando com a data de hoje por padrão
            payload = {
                "nome": nome, 
                "horario": horario, 
                "feita": False, 
                "data": str(date.today())
            }
            try:
                httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
                st.rerun()
            except:
                st.error("Erro ao salvar.")

    st.divider()

    # Busca tarefas apenas do dia de hoje
    hoje_str = str(date.today())
    try:
        busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{hoje_str}&order=created_at", headers=headers)
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
        
        for t in tarefas:
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
            # Checkbox de status
            feita = c1.checkbox("", value=t['feita'], key=f"hoje_{t['id']}", label_visibility="collapsed")
            if feita != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
                st.rerun()
            
            texto = f"~~{t['nome']}~~" if t['feita'] else f"**{t['nome']}**"
            c2.markdown(f"{texto} — ⏰ {t['horario']}")
            
            # Excluir individual
            if c3.button("🗑️", key=f"del_{t['id']}"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    else:
        st.info("Nenhuma tarefa para hoje. Comece agendando acima!")

# --- ABA 2: CALENDÁRIO / HISTÓRICO ---
with aba_calendario:
    st.subheader("Consultar Histórico")
    data_consulta = st.date_input("Escolha um dia", value=date.today())
    
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{str(data_consulta)}&order=created_at", headers=headers)
        tarefas_hist = res.json()
    except:
        tarefas_hist = []

    if tarefas_hist:
        for t in tarefas_hist:
            status = "✅" if t['feita'] else "⏳"
            st.write(f"{status} **{t['nome']}** | {t['horario']}")
    else:
        st.warning(f"Sem tarefas registradas em {data_consulta.strftime('%d/%m/%Y')}.")