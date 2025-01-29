import streamlit as st
import requests
from PyPDF2 import PdfReader
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Função para autenticar e conectar com o Google Sheets
def conectar_google_sheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Erro na autenticação com Google Sheets: {e}")
        return None

# Função para salvar dados na planilha
def salvar_na_planilha(sheet_name, dados):
    client = conectar_google_sheets()
    if client:
        try:
            # Abrir ou criar a planilha
            try:
                sheet = client.open(sheet_name).sheet1
            except gspread.exceptions.SpreadsheetNotFound:
                sheet = client.create(sheet_name).sheet1
            # Adicionar os dados
            sheet.append_row(dados)
            st.success(f"Dados salvos na planilha '{sheet_name}' com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar os dados na planilha: {e}")

# Função para usar a API da OpenAI para processar texto com prompt personalizado
def processar_texto_com_openai(api_key, texto_pdf, prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4",  # Ou "gpt-3.5-turbo"
        "messages": [
            {"role": "system", "content": "Você é um assistente especializado em análise de textos."},
            {"role": "user", "content": f"{prompt}\n\nTexto do PDF:\n{texto_pdf}"}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        resultado = response.json()
        return resultado['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao processar o texto com a OpenAI: {e}")
        return None

# Função para leitura completa ou rápida do PDF
def ler_pdf(arquivo_pdf, leitura_rapida=False, paginas_para_ler=5):
    try:
        pdf_reader = PdfReader(arquivo_pdf)
        texto = []
        total_paginas = len(pdf_reader.pages)
        paginas = paginas_para_ler if leitura_rapida else total_paginas

        for pagina_num in range(min(paginas, total_paginas)):
            texto.append(pdf_reader.pages[pagina_num].extract_text())
        return " ".join(texto)
    except Exception as e:
        st.error(f"Erro ao ler o PDF: {e}")
        return None

# Interface gráfica com Streamlit
def main():
    st.title("Leitor de PDF com OpenAI ")
    
    # Gerenciar várias chaves de API
    st.sidebar.subheader("Configurações de API")
    api_keys = st.sidebar.text_area("Insira as chaves de API separadas por vírgula", 
                                    "API_KEY_1,API_KEY_2")
    api_key_list = [key.strip() for key in api_keys.split(",") if key.strip()]

    # Selecionar qual chave de API usar
    if api_key_list:
        api_key_selecionada = st.sidebar.selectbox("Selecione uma chave de API", api_key_list)
    else:
        st.sidebar.error("Insira pelo menos uma chave de API.")
        return

    # Upload de vários PDFs
    st.subheader("Fazer Upload de PDFs")
    arquivos_pdf = st.file_uploader("Faça o upload de um ou mais arquivos PDF", type=["pdf"], accept_multiple_files=True)

    # Configuração de leitura rápida
    leitura_rapida = st.checkbox("Ativar leitura rápida (primeiras 5 páginas)", value=True)
    
    # Campo para inserir o prompt personalizado
    prompt_personalizado = st.text_area("Insira o prompt para análise do texto do PDF", 
                                        "Resuma o texto fornecido de forma clara e objetiva.")
    
    # Nome da planilha
    nome_planilha = st.text_input("Nome da Planilha no Google Sheets", "Análise de PDFs")

    if arquivos_pdf:
        st.write(f"{len(arquivos_pdf)} arquivo(s) PDF carregado(s) com sucesso!")
        
        for arquivo_pdf in arquivos_pdf:
            st.write(f"Processando arquivo: {arquivo_pdf.name}")
            
            # Ler o PDF (rápido ou completo)
            st.write("Lendo o PDF...")
            texto_pdf = ler_pdf(arquivo_pdf, leitura_rapida=leitura_rapida, paginas_para_ler=5)
            
            if texto_pdf:
                st.write(f"Texto extraído do PDF {arquivo_pdf.name}:")
                st.text_area(f"Conteúdo do PDF ({arquivo_pdf.name})", texto_pdf[:5000], height=200)
                
                # Processar o texto com a OpenAI
                if st.button(f"Processar com OpenAI - {arquivo_pdf.name}", key=f"processar_{arquivo_pdf.name}"):
                    if api_key_selecionada:
                        resultado = processar_texto_com_openai(api_key_selecionada, texto_pdf, prompt_personalizado)
                        
                        if resultado:
                            st.write(f"Resultado da análise do arquivo {arquivo_pdf.name}:")
                            st.text_area(f"Resultado gerado ({arquivo_pdf.name})", resultado, height=200)
                            
                            # Salvar na planilha
                            if st.button(f"Salvar na Planilha - {arquivo_pdf.name}", key=f"salvar_{arquivo_pdf.name}"):
                                salvar_na_planilha(
                                    nome_planilha,
                                    [arquivo_pdf.name, resultado]
                                )
                    else:
                        st.error("Por favor, insira uma chave de API válida.")

if __name__ == "__main__":
    main()
