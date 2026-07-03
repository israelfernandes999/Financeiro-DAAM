import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURAÇÃO DA API DO GOOGLE SHEETS ---
escopo = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    credenciais = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", escopo)
    cliente = gspread.authorize(credenciais)
except Exception as e:
    st.error(f"Erro nas credenciais: {e}")
    st.stop()

NOME_PLANILHA = "Fluxo de Caixa - Diretório Acadêmico"

try:
    planilha = cliente.open(NOME_PLANILHA)
    aba_estoque = planilha.worksheet("Entradas")
    aba_fechamento = planilha.worksheet("Fechamentos")
except Exception as e:
    st.error(f"Erro ao conectar com as abas do Sheets: {e}")
    st.stop()


# --- INTERFACE VIZUAL ---
st.set_page_config(page_title="Finanças DAAM", page_icon="💰", layout="centered")

st.markdown("<h1 style='text-align: center; color: #4CAF50;'> Sistema de Caixa DAAM</h1>", unsafe_allow_html=True)
st.markdown("---")

aba_prod, aba_fech = st.tabs([" Entrada de Mercadorias", " Fechamento Semanal"])

# --- ABA 1: REGISTRAR PRODUTOS ---
with aba_prod:
    st.markdown("### Cadastrar Nova Compra")
    
    with st.form("form_estoque", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            operador_prod = st.selectbox("Operador responsável:", ["Israel", "Membro 2", "Membro 3", "Membro 4"])
        with c2:
            produto = st.selectbox("Produto adquirido:", ["Trufa", "Pirulito", "Nucita", "Pipoca", "Jujuba", "Outro"])
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            quantidade = st.number_input("Quantidade (Unidades)", min_value=1, step=1, value=100)
        with col2:
            custo_unitario = st.number_input("Custo Unitário (R$)", min_value=0.01, format="%.2f", value=1.50)
        with col3:
            preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.01, format="%.2f", value=3.00)
        
        # NOVA FUNCIONALIDADE: Campo para custo de Uber/Logística
        custo_operacional = st.number_input("Custo Operacional / Uber (R$)", min_value=0.0, format="%.2f", value=0.0, help="Gasto com transporte para buscar os doces")
        
        st.markdown("<br>", unsafe_allow_html=True)
        botao_salvar_estoque = st.form_submit_button(" Gravar e Atualizar Planilha", use_container_width=True)

    if botao_salvar_estoque:
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Mapeamento dinâmico da linha atual para as fórmulas do Sheets
        proxima_linha = len(aba_estoque.get_all_values()) + 1
        
        # Fórmulas baseadas na nova estrutura de colunas (A até I)
        formula_custo_total = f"=D{proxima_linha}*E{proxima_linha}"
        # Faturamento Líquido = (Quantidade * Venda) - Custo Operacional (Coluna G)
        formula_faturamento_liquido = f"=(D{proxima_linha}*H{proxima_linha})-G{proxima_linha}"
        
        nova_linha_estoque = [
            data_atual, 
            operador_prod, 
            produto, 
            int(quantidade), 
            float(custo_unitario), 
            formula_custo_total,         # Coluna F
            float(custo_operacional),    # Coluna G (Uber)
            float(preco_venda),          # Coluna H
            formula_faturamento_liquido  # Coluna I
        ]
        
        with st.spinner("Salvando na nuvem..."):
            try:
                aba_estoque.append_row(nova_linha_estoque, value_input_option="USER_ENTERED")
                st.balloons()
                st.success(f"✅ Registrado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar na planilha: {e}")

# --- ABA 2: FECHAMENTO SEMANAL ---
with aba_fech:
    st.markdown("### Fechamento de Caixa Semanal")
    
    with st.form("form_fechamento", clear_on_submit=True):
        operador_fech = st.selectbox("Quem está fechando o caixa?", ["Israel", "Membro 2", "Membro 3", "Membro 4"])
        
        col4, col5 = st.columns(2)
        with col4:
            valor_especie = st.number_input("Total em Dinheiro Físico (R$)", min_value=0.0, format="%.2f", value=0.0)
        with col5:
            valor_banco = st.number_input("Total no Banco Virtual / Pix (R$)", min_value=0.0, format="%.2f", value=0.0)
            
        botao_salvar_fechamento = st.form_submit_button(" Registrar Fechamento", use_container_width=True)

    if botao_salvar_fechamento:
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        nova_linha_fechamento = [
            data_atual,
            operador_fech,
            float(valor_especie),
            float(valor_banco)
        ]
        
        with st.spinner("Registrando fechamento..."):
            try:
                aba_fechamento.append_row(nova_linha_fechamento, value_input_option="USER_ENTERED")
                st.success(" Dados de fechamento arquivados com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar na planilha: {e}")