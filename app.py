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
st.set_page_config(page_title="WN Tarefas", page_icon="🎯", layout="centered")

# --- 2. ESTILIZAÇÃO CSS PROFISSIONAL ---
st.markdown("""
    <style>
    /* Esconder menu padrão para um look mais clean */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Logotipo Personalizado e Reduzido */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 10px 0 30px 0;
    }
    .logo-box {
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        padding: 10px 25px;
        border-radius: 15px;
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.2);
    }
    .logo-text {
        font-family: 'Inter', sans-serif;
        color: white !important;
        font-weight: 800;
        font-size: 32px;
        letter-spacing: -1px;
        margin: 0;
        text-transform: uppercase;
    }

    /* Botões Modernos */
    div.stButton > button {
        background: linear-gradient(90deg, #4F46E5, #4338CA);
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(79, 70, 229, 0.4);
        color: white;
    }

    /* Estilização dos Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# Exibição do Logotipo Customizado
st.markdown("""
    <div class="logo-container">
        <div class="logo-box">
            <p class="logo-text">🎯 WN Tarefas</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. NAVEGAÇÃO POR ABAS ---
aba_hoje, aba_calendario = st.tabs(["🚀 HOJE", "📅 HISTÓRICO"])

# --- ABA 1: TAREFAS DE HOJE ---
with aba_hoje:
    with st.container():
        with st.form("nova_tarefa", clear_on_submit=True):
            nome = st.text_input("O que vamos realizar?", placeholder="Ex: Reunião de Planejamento")
            col1, col2 = st.columns(2)
            ini = col1.time_input("Início", step=300)
            fim = col2.time_input("Fim", step=300)
            enviar = st.form_submit_button("Agendar Tarefa", use_container_width=True)

            if enviar and nome:
                horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
                payload = {
                    "nome": nome, 
                    "horario": horario, 
                    "feita": False, 
                    "data": str(date.today())
                }
                try:
                    res = httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload, timeout=10.0)
                    st.rerun()
                except:
                    st.rerun()

    st.write("")
    
    hoje_str = str(date.today())
    try:
        busca = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{hoje_str}&order=created_at", headers=headers)
        tarefas = busca.json() if busca.status_code == 200 else []
    except:
        tarefas = []

    if tarefas:
        total = len(tarefas)
        concluidas = sum(1 for t in tarefas if t.get('feita'))
        percentual = concluidas / total
        
        # Barra de Progresso Estilizada
        st.markdown(f"**Sua Meta de Hoje: {int(percentual * 100)}%**")
        st.progress(percentual)
        st.write("")
        
        for t in tarefas:
            c1, c2, c3 = st.columns([0.1, 0.75, 0.15])
            
            # Checkbox
            feita = c1.checkbox("", value=t['feita'], key=f"h_{t['id']}", label_visibility="collapsed")
            if feita != t['feita']:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
                st.rerun()
            
            # Conteúdo da tarefa
            if t['feita']:
                c2.markdown(f"<span style='color: gray; text-decoration: line-through;'>{t['nome']} ({t['horario']})</span>", unsafe_allow_html=True)
            else:
                c2.markdown(f"**{t['nome']}** <br> <small>⏰ {t['horario']}</small>", unsafe_allow_html=True)
            
            # Botão de deletar minimalista
            if c3.button("🗑️", key=f"del_{t['id']}", help="Excluir tarefa"):
                httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                st.rerun()
    else:
        st.info("Você ainda não tem tarefas para hoje. Que tal planejar seu dia?")

# --- ABA 2: CALENDÁRIO ---
with aba_calendario:
    st.markdown("### 🔍 Consultar Datas Anteriores")
    data_consulta = st.date_input("Selecione o dia", value=date.today())
    
    try:
        res = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{str(data_consulta)}&order=created_at", headers=headers)
        tarefas_hist = res.json()
    except:
        tarefas_hist = []

    st.divider()

    if tarefas_hist:
        for t in tarefas_hist:
            status = "✅" if t['feita'] else "⏳"
            st.write(f"{status} **{t['nome']}** — {t['horario']}")
    else:
        st.warning(f"Não encontramos tarefas registradas para o dia {data_consulta.strftime('%d/%m/%Y')}.")