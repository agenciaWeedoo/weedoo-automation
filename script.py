import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. CONFIGURAÇÕES DOS CANAIS E PALAVRAS-CHAVE
KEYWORDS_SCI = ["cannabinoid", "cbd", "thc", "medical cannabis", "canabinoide", "canabinóide", "cannabis medicinal", "canabis medicinal", "sistema endocanabinoide", "receptores endocanabinoide"]
KEYWORDS_REG = ["cannabis", "medicinal", "anvisa", "regulamentação", "rdc", "stj", "hc para cultivo"]
KEYWORDS_MKT = ["business", "industry", "market", "growth", "cannabis", "ciência endocanabinoide", "medicina endocanabinoide", "medicinal cannabis"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

html_conteudo = "<h2>🚀 Relatório Semanal de Dados - Agência Weedoo</h2>"

# --- FRENTE 1: CIENTÍFICA (PubMed, Nature, The Lancet via Europe PMC) ---
html_conteudo += "<h3>🔬 FRENTE CIENTÍFICA (PubMed, Nature, The Lancet)</h3>"
for query in KEYWORDS_SCI:
    encoded_query = urllib.parse.quote(query)
    sci_url = f"https://ebi.ac.uk{encoded_query}%20AND%20(SRC:MED%20OR%20JOURNAL:%22Nature%22%20OR%20JOURNAL:%22The%20Lancet%22)&format=json&pageSize=2"
    try:
        res = requests.get(sci_url, headers=headers, timeout=15).json()
        results = res.get("resultList", {}).get("result", [])
        for art in results:
            title = art.get("title", "Sem título")
            journal = art.get("journalTitle", "Periódico Não Identificado")
            pmid = art.get("pmid", "")
            link = f"https://nih.gov{pmid}/" if pmid else "#"
            html_conteudo += f"<p><b>[{journal}]</b> {title}<br><a href='{link}'>Acessar artigo</a></p>"
    except:
        pass

# --- FRENTE 2: REGULATÓRIA (Anvisa 2026 + Backup Google News) ---
html_conteudo += "<h3>⚖️ FRENTE REGULATÓRIA (Anvisa & Clipping Nacional)</h3>"
found_reg = False

# Tentativa 1: Site Oficial da Anvisa 2026
try:
    url_anvisa_2026 = "https://www.gov.br"
    anvisa_res = requests.get(url_anvisa_2026, headers=headers, timeout=15)
    if anvisa_res.status_code == 200:
        soup = BeautifulSoup(anvisa_res.content, "html.parser")
        articles = soup.find_all("article", class_="tileItem")
        for art in articles:
            title_tag = art.find("h2", class_="tileHeadline")
            if title_tag:
                title_text = title_tag.get_text().strip()
                if any(key.lower() in title_text.lower() for key in KEYWORDS_REG):
                    link_href = title_tag.find("a")["href"] if title_tag.find("a") else "#"
                    link_completo = f"https://www.gov.br{link_href}" if link_href.startswith("/") else link_href
                    desc_tag = art.find("span", class_="description")
                    desc_text = desc_tag.get_text().strip() if desc_tag else "Ver nota técnica completa."
                    
                    html_conteudo += f"<p>🚨 <b>Anvisa 2026 (Oficial):</b> {title_text}<br><i>{desc_text}</i><br><a href='{link_completo}'>Acessar Notícia</a></p>"
                    found_reg = True
except Exception as e:
    print(f"⚠️ Portal da Anvisa instável. Ativando plano de contingência Google News...")

# Tentativa 2 / Backup: Google News (Acionado se a Anvisa falhar ou não trouxer resultados)
if not found_reg:
    html_conteudo += "<p><i>Nota: Portal oficial da Anvisa sem novas ocorrências diretas. Ativando redundância via Google News...</i></p>"
    try:
        # Busca no Google News focada em termos regulatórios do Brasil
        termo_busca = "Anvisa Cannabis RDC"
        encoded_term = urllib.parse.quote(termo_busca)
        gn_url = f"https://google.com{encoded_term}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        
        gn_res = requests.get(gn_url, headers=headers, timeout=15)
        soup = BeautifulSoup(gn_res.content, "xml") # Processa o feed RSS em formato XML
        items = soup.find_all("item")
        
        for item in items[:4]: # Captura as 4 principais notícias da imprensa nacional
            title = item.find("title").text if item.find("title") else "Notícia sem título"
            link = item.find("link").text if item.find("link") else "#"
            pub_date = item.find("pubDate").text[:16] if item.find("pubDate") else ""
            source = item.find("source").text if item.find("source") else "Imprensa"
            
            html_conteudo += f"<p>📰 <b>{source} ({pub_date}):</b> {title}<br><a href='{link}'>Ler matéria na íntegra</a></p>"
            found_reg = True
    except Exception as e:
        html_conteudo += f"<p>Erro ao carregar contingência do Google News: {str(e)}</p>"

if not found_reg:
    html_conteudo += "<p>Nenhuma atualização regulatória encontrada nos canais oficiais ou na imprensa esta semana.</p>"

# --- FRENTE 3: MERCADO GLOBAL (MJBizDaily) ---
html_conteudo += "<h3>📈 FRENTE DE MERCADO (MJBizDaily)</h3>"
try:
    mjbiz_res = requests.get("https://mjbizdaily.com", headers=headers, timeout=15)
    soup = BeautifulSoup(mjbiz_res.content, "html.parser")
    posts = soup.find_all("article")
    found_mkt = False
    for post in posts[:6]:
        title_tag = post.find("h2") or post.find("h3")
        if title_tag:
            title_text = title_tag.get_text().strip()
            if any(key.lower() in title_text.lower() for key in KEYWORDS_MKT):
                link = post.find("a")["href"] if post.find("a") else "#"
                html_conteudo += f"<p>🌐 <b>Tendência Global:</b> {title_text}<br><a href='{link}'>Ler análise de mercado</a></p>"
                found_mkt = True
    if not found_mkt:
        html_conteudo += "<p>Estabilidade detectada no monitoramento do mercado global de Cannabis.</p>"
except:
    html_conteudo += "<p>Erro temporário ao acessar o feed do MJBizDaily.</p>"

# ==============================================================================
# ENVIO DE E-MAIL AUTOMÁTICO (Com trava de reconexão automática para falhas de rede)
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
    
    import time
    max_tentativas = 3
    conectado = False
    
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"🔗 [Tentativa {tentativa}/{max_tentativas}] Conectando ao servidor SMTP do Gmail...")
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("🔐 Fazendo login com a Senha de App...")
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
            server.quit()
            print("📧 E-mail semanal enviado com sucesso para o CEO!")
            conectado = True
            break
        except Exception as e:
            print(f"⚠️ Alerta: Conexão falhou na tentativa {tentativa}. Motivo: {str(e)}")
            if tentativa < max_tentativas:
                print("⏳ Aguardando 5 segundos para tentar novamente...")
                time.sleep(5)
            else:
                print("❌ Todas as tentativas de conexão de rede falharam.")
                raise e
else:
    print("⚠️ Configurações de e-mail ausentes no GitHub Secrets.")
