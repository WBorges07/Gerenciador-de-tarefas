import streamlit as st
import httpx
from datetime import datetime, date

# --- 1. CONFIGURAÇÃO (SECRETS) ---
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

st.set_page_config(page_title="WN Tarefas", page_icon="🎯", layout="centered")

# --- 2. CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .logo-container { display: flex; justify-content: center; padding: 10px 0 30px 0; }
    .logo-box { background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%); padding: 10px 25px; border-radius: 15px; }
    .logo-text { color: white !important; font-weight: 800; font-size: 32px; text-transform: uppercase; margin: 0; }
    div.stButton > button { border-radius: 10px; font-weight: 600; }
    .task-row { background: #f9f9f9; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 5px solid #4F46E5; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="logo-container"><div class="logo-box"><p class="logo-text">🎯 WN Tarefas</p></div></div>', unsafe_allow_html=True)

# --- 3. LÓGICA DE EDIÇÃO ---
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

# --- 4. ABAS ---
aba_hoje, aba_calendario = st.tabs(["🚀 HOJE", "📅 HISTÓRICO"])

with aba_hoje:
    # FORMULÁRIO (CADASTRO / EDIÇÃO)
    titulo_form = "✏️ Editar Tarefa" if st.session_state.edit_id else "🆕 Nova Tarefa"
    with st.form("form_tarefa", clear_on_submit=True):
        st.subheader(titulo_form)
        nome = st.text_input("O que vamos realizar?", key="input_nome")
        c1, c2 = st.columns(2)
        ini = c1.time_input("Início", step=300)
        fim = c2.time_input("Fim", step=300)
        repetir = st.checkbox("Repetir diariamente esta tarefa")
        
        col_btn1, col_btn2 = st.columns(2)
        submetido = col_btn1.form_submit_button("Salvar")
        cancelar = col_btn2.form_submit_button("Cancelar Edição")

        if cancelar:
            st.session_state.edit_id = None
            st.rerun()

        if submetido and nome:
            horario = f"{ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            payload = {
                "nome": nome, "horario": horario, "feita": False,
                "data": str(date.today()), "repetir": repetir
            }
            
            if st.session_state.edit_id:
                httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{st.session_state.edit_id}", headers=headers, json=payload)
                st.session_state.edit_id = None
            else:
                httpx.post(f"{SUPABASE_URL}/rest/v1/tarefas", headers=headers, json=payload)
            st.rerun()

    st.divider()

    # BUSCA E ORDENAÇÃO POR HORÁRIO
    hoje_str = str(date.today())
    # Filtro: tarefas de hoje OU tarefas que se repetem
    try:
        url_busca = f"{SUPABASE_URL}/rest/v1/tarefas?or=(data.eq.{hoje_str},repetir.eq.true)&order=horario.asc"
        res = httpx.get(url_busca, headers=headers)
        tarefas = res.json()
    except:
        tarefas = []

    if tarefas:
        for t in tarefas:
            with st.container():
                col_check, col_txt, col_ops = st.columns([0.1, 0.65, 0.25])
                
                # Checkbox
                feita = col_check.checkbox("", value=t['feita'], key=f"check_{t['id']}", label_visibility="collapsed")
                if feita != t['feita']:
                    httpx.patch(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers, json={"feita": feita})
                    st.rerun()
                
                # Texto e Ícone de Repetição
                rep_icon = "🔁 " if t.get('repetir') else ""
                if t['feita']:
                    col_txt.markdown(f"~~{rep_icon}{t['nome']}~~ <br><small>{t['horario']}</small>", unsafe_allow_html=True)
                else:
                    col_txt.markdown(f"**{rep_icon}{t['nome']}** <br><small>⏰ {t['horario']}</small>", unsafe_allow_html=True)
                
                # BOTÕES DE OPERAÇÃO (Lápis e Lixeira)
                btn_edit, btn_del = col_ops.columns(2)
                if btn_edit.button("✏️", key=f"ed_{t['id']}"):
                    st.session_state.edit_id = t['id']
                    st.rerun()
                
                if btn_del.button("🗑️", key=f"dl_{t['id']}"):
                    httpx.delete(f"{SUPABASE_URL}/rest/v1/tarefas?id=eq.{t['id']}", headers=headers)
                    st.rerun()
    else:
        st.info("Nada agendado para agora.")

with aba_calendario:
    data_sel = st.date_input("Consultar histórico", value=date.today())
    res_hist = httpx.get(f"{SUPABASE_URL}/rest/v1/tarefas?data=eq.{str(data_sel)}&order=horario.asc", headers=headers)
    for t in res_hist.json():
        status = "✅" if t['feita'] else "⏳"
        st.write(f"{status} **{t['horario']}** - {t['nome']}")