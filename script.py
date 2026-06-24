import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. CONFIGURAÇÕES DOS CANAIS E PALAVRAS-CHAVE
KEYWORDS_SCI = ["cannabidiol", "cannabis", "endocannabinoid"]
KEYWORDS_REG = ["cannabis", "medicinal", "RDC"]
KEYWORDS_MKT = ["cannabis", "market", "medical"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

html_conteudo = "<h2>🚀 Relatório Semanal de Dados - Agência Weedoo</h2>"

# --- FRENTE 1: CIENTÍFICA (PubMed, Nature, The Lancet via Europe PMC) ---
html_conteudo += "<h3>🔬 FRENTE CIENTÍFICA (PubMed, Nature, The Lancet)</h3>"
for query in KEYWORDS_SCI:
    encoded_query = urllib.parse.quote(query)
    # URL corrigida com o caminho completo da API estável
    sci_url = f"https://ebi.ac.uk{encoded_query}%20AND%20(SRC:MED%20OR%20JOURNAL:%22Nature%22%20OR%20JOURNAL:%22The%20Lancet%22)&format=json&pageSize=2"
    try:
        res = requests.get(sci_url, headers=headers).json()
        results = res.get("resultList", {}).get("result", [])
        for art in results:
            title = art.get("title", "Sem título")
            journal = art.get("journalTitle", "Periódico Não Identificado")
            pmid = art.get("pmid", "")
            link = f"https://nih.gov{pmid}/" if pmid else "#"
            html_conteudo += f"<p><b>[{journal}]</b> {title}<br><a href='{link}'>Acessar artigo</a></p>"
    except:
        pass

# --- FRENTE 2: REGULATÓRIA (Anvisa Notícias) ---
html_conteudo += "<h3>⚖️ FRENTE REGULATÓRIA (Anvisa)</h3>"
try:
    # URL corrigida para apontar direto para o feed de notícias regulatórias
    anvisa_res = requests.get("https://www.gov.br", headers=headers, timeout=15)
    soup = BeautifulSoup(anvisa_res.content, "html.parser")
    articles = soup.find_all("article", class_="tileItem")
    found_any = False
    for art in articles[:5]:
        title_tag = art.find("h2", class_="tileHeadline")
        if title_tag:
            title_text = title_tag.get_text().strip()
            if any(key.lower() in title_text.lower() for key in KEYWORDS_REG):
                link = title_tag.find("a")["href"] if title_tag.find("a") else "#"
                html_conteudo += f"<p>🚨 <b>Anvisa:</b> {title_text}<br><a href='{link}'>Ver notícia</a></p>"
                found_any = True
    if not found_any:
        html_conteudo += "<p>Sem novidades críticas na Anvisa hoje.</p>"
except:
    html_conteudo += "<p>Erro temporário ao acessar o portal da Anvisa.</p>"

# --- FRENTE 3: MERCADO GLOBAL (MJBizDaily) ---
html_conteudo += "<h3>📈 FRENTE DE MERCADO (MJBizDaily)</h3>"
try:
    # URL corrigida para varrer o feed de notícias de mercado
    mjbiz_res = requests.get("https://mjbizdaily.com", headers=headers, timeout=15)
    soup = BeautifulSoup(mjbiz_res.content, "html.parser")
    posts = soup.find_all("article")
    found_mkt = False
    for post in posts[:5]:
        title_tag = post.find("h2") or post.find("h3")
        if title_tag:
            title_text = title_tag.get_text().strip()
            if any(key.lower() in title_text.lower() for key in KEYWORDS_MKT):
                link = post.find("a")["href"] if post.find("a") else "#"
                html_conteudo += f"<p>🌐 <b>Tendência:</b> {title_text}<br><a href='{link}'>Ler análise</a></p>"
                found_mkt = True
    if not found_mkt:
        html_conteudo += "<p>Estabilidade no mercado global de Cannabis.</p>"
except:
    html_conteudo += "<p>Erro temporário ao acessar o MJBizDaily.</p>"

# ==============================================================================
# ENVIO DE E-MAIL AUTOMÁTICO (Variáveis de Ambiente e Indentação Corrigidas)
# ==============================================================================
EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

if EMAIL_REMETENTE and EMAIL_SENHA and EMAIL_DESTINATARIO:
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = "🌿 [Weedoo Data Hub] Relatório Semanal de Atualizações"
    
    msg.attach(MIMEText(html_conteudo, 'html'))
    
    try:
        print("🔗 Conectando ao servidor SMTP do Gmail...")
        # Correção Crítica do Host e Porta SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        print("🔐 Fazendo login com a Senha de App...")
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()
        print("📧 E-mail semanal enviado com sucesso para o CEO!")
    except Exception as e:
        print(f"❌ Erro crítico no disparo do e-mail: {str(e)}")
        raise e
else:
    print("⚠️ Configurações de e-mail ausentes no GitHub Secrets.")
