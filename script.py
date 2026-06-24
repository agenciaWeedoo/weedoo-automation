import os
import smtplib
import time
import urllib.parse
import xml.etree.ElementTree as ET  # CORREÇÃO 4: biblioteca padrão, sem depender de lxml
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup

# ==============================================================================
# 1. CONFIGURAÇÕES DOS CANAIS E PALAVRAS-CHAVE
# ==============================================================================
KEYWORDS_SCI = [
    "cannabinoid", "cbd", "thc", "medical cannabis",
    "endocannabinoid system", "endocannabinoid receptors",
]
KEYWORDS_REG = [
    "cannabis", "medicinal", "anvisa", "regulamentação",
    "rdc", "stj", "hc para cultivo",
]
# CORREÇÃO 6: Removidas palavras-chave em português — o MJBizDaily é em inglês
KEYWORDS_MKT = [
    "cannabis", "hemp", "business", "industry",
    "market", "growth", "medicinal cannabis",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

html_conteudo = "<h2>🚀 Relatório Semanal de Dados - Agência Weedoo</h2>"


# ==============================================================================
# FRENTE 1: CIENTÍFICA (Europe PMC → PubMed, Nature, The Lancet)
# ==============================================================================
html_conteudo += "<h3>🔬 FRENTE CIENTÍFICA (PubMed, Nature, The Lancet)</h3>"
found_sci = False

for query in KEYWORDS_SCI:
    encoded_query = urllib.parse.quote(query)

    # CORREÇÃO 1: URL da API estava incompleta — faltava o caminho
    # "/europepmc/webservices/rest/search?query=" e o domínio correto "www.ebi.ac.uk"
    sci_url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query={encoded_query}"
        "%20AND%20(SRC:MED%20OR%20JOURNAL:%22Nature%22%20OR%20JOURNAL:%22The%20Lancet%22)"
        "&format=json&pageSize=2&sort=P_PDATE_D%20desc"
    )

    try:
        res = requests.get(sci_url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        results = res.json().get("resultList", {}).get("result", [])

        for art in results:
            title   = art.get("title", "Sem título")
            journal = art.get("journalTitle", "Periódico Não Identificado")
            pmid    = art.get("pmid", "")
            doi     = art.get("doi", "")

            # CORREÇÃO 2: Link do PubMed estava malformado ("https://nih.gov{pmid}/")
            if pmid:
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            elif doi:
                link = f"https://doi.org/{doi}"
            else:
                link = "#"

            html_conteudo += (
                f"<p><b>[{journal}]</b> {title}<br>"
                f"<a href='{link}'>Acessar artigo científico</a></p>"
            )
            found_sci = True

    except Exception as e:
        print(f"⚠️  Erro na busca científica para '{query}': {e}")

if not found_sci:
    html_conteudo += (
        "<p>Nenhum artigo científico encontrado nos periódicos "
        "monitorados esta semana.</p>"
    )


# ==============================================================================
# FRENTE 2: REGULATÓRIA (Anvisa 2026 + Backup Google News RSS)
# ==============================================================================
html_conteudo += "<h3>⚖️ FRENTE REGULATÓRIA (Anvisa & Clipping Nacional)</h3>"
found_reg = False

# --- Tentativa 1: Site Oficial da Anvisa 2026 ---
try:
    url_anvisa = "https://www.gov.br/anvisa/pt-br/assuntos/noticias-anvisa/2026"
    anvisa_res = requests.get(url_anvisa, headers=HEADERS, timeout=15)

    if anvisa_res.status_code == 200:
        soup = BeautifulSoup(anvisa_res.content, "html.parser")
        for art in soup.find_all("article", class_="tileItem"):
            title_tag = art.find("h2", class_="tileHeadline")
            if not title_tag:
                continue
            title_text = title_tag.get_text().strip()
            if not any(k.lower() in title_text.lower() for k in KEYWORDS_REG):
                continue

            link_tag     = title_tag.find("a")
            link_href    = link_tag["href"] if link_tag else "#"
            link_completo = (
                f"https://www.gov.br{link_href}"
                if link_href.startswith("/") else link_href
            )
            desc_tag  = art.find("span", class_="description")
            desc_text = desc_tag.get_text().strip() if desc_tag else "Ver nota técnica completa."

            html_conteudo += (
                f"<p>🚨 <b>Anvisa 2026 (Oficial):</b> {title_text}<br>"
                f"<i>{desc_text}</i><br>"
                f"<a href='{link_completo}'>Acessar Notícia</a></p>"
            )
            found_reg = True

except Exception as e:
    print(f"⚠️  Portal da Anvisa instável: {e}")

# --- Tentativa 2 / Backup: Google News RSS ---
if not found_reg:
    html_conteudo += (
        "<p><i>Nota: Portal oficial da Anvisa sem novas ocorrências diretas. "
        "Ativando redundância via Google News...</i></p>"
    )
    try:
        termo_busca  = "anvisa cannabis rdc regulamentação"
        encoded_term = urllib.parse.quote(termo_busca)

        # CORREÇÃO 3: URL corrigida para o endpoint RSS (/rss/search em vez de /search)
        gn_url = (
            f"https://news.google.com/rss/search"
            f"?q={encoded_term}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )

        gn_res = requests.get(gn_url, headers=HEADERS, timeout=15)
        gn_res.raise_for_status()

        # CORREÇÃO 4: xml.etree.ElementTree — sem dependência de lxml
        root    = ET.fromstring(gn_res.content)
        channel = root.find("channel")
        items   = channel.findall("item") if channel is not None else []

        count = 0
        for item in items:
            if count >= 5:
                break
            title      = item.findtext("title", "Notícia sem título")
            link       = item.findtext("link", "#")
            source_tag = item.find("source")
            source     = source_tag.text if source_tag is not None else "Imprensa"
            pub_date   = item.findtext("pubDate", "")

            date_html = f"<br><small>{pub_date}</small>" if pub_date else ""
            html_conteudo += (
                f"<p>📰 <b>{source}:</b> {title}"
                f"{date_html}<br>"
                f"<a href='{link}'>Ler matéria na íntegra</a></p>"
            )
            found_reg = True
            count += 1

    except Exception as e:
        html_conteudo += f"<p>Erro ao carregar contingência do Google News: {e}</p>"
        print(f"⚠️  Erro Google News RSS: {e}")

if not found_reg:
    html_conteudo += (
        "<p>Nenhuma atualização regulatória encontrada nos canais "
        "oficiais ou na imprensa esta semana.</p>"
    )


# ==============================================================================
# FRENTE 3: MERCADO GLOBAL (MJBizDaily)
# CORREÇÃO 5: Seção duplicada removida — aparecia duas vezes no código original
# ==============================================================================
html_conteudo += "<h3>📈 FRENTE DE MERCADO (MJBizDaily)</h3>"
try:
    mjbiz_res = requests.get("https://mjbizdaily.com", headers=HEADERS, timeout=15)
    soup      = BeautifulSoup(mjbiz_res.content, "html.parser")
    posts     = soup.find_all("article")
    found_mkt = False

    for post in posts[:10]:
        title_tag = post.find("h2") or post.find("h3")
        if not title_tag:
            continue
        title_text = title_tag.get_text().strip()
        if not any(k.lower() in title_text.lower() for k in KEYWORDS_MKT):
            continue

        link_tag = post.find("a", href=True)
        link     = link_tag["href"] if link_tag else "#"

        html_conteudo += (
            f"<p>🌐 <b>Tendência Global:</b> {title_text}<br>"
            f"<a href='{link}'>Ler análise de mercado</a></p>"
        )
        found_mkt = True

    if not found_mkt:
        html_conteudo += (
            "<p>Estabilidade detectada no monitoramento do mercado "
            "global de Cannabis.</p>"
        )

except Exception as e:
    html_conteudo += "<p>Erro temporário ao acessar o feed do MJBizDaily.</p>"
    print(f"⚠️  Erro MJBizDaily: {e}")


# ==============================================================================
# ENVIO DE E-MAIL AUTOMÁTICO (com reconexão automática para falhas de rede)
# ==============================================================================
EMAIL_REMETENTE    = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA        = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

if EMAIL_REMETENTE and EMAIL_SENHA and EMAIL_DESTINATARIO:
    msg            = MIMEMultipart()
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINATARIO
    msg["Subject"] = "🌿 [Weedoo Data Hub] Relatório Semanal de Atualizações"
    msg.attach(MIMEText(html_conteudo, "html"))

    max_tentativas = 3

    for tentativa in range(1, max_tentativas + 1):
        try:
            print(
                f"🔗 [Tentativa {tentativa}/{max_tentativas}] "
                "Conectando ao servidor SMTP do Gmail..."
            )
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.ehlo()
            server.starttls()
            server.ehlo()
            print("🔐 Fazendo login com a Senha de App...")
            server.login(EMAIL_REMETENTE, EMAIL_SENHA)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
            server.quit()
            print("📧 E-mail semanal enviado com sucesso!")
            break

        except Exception as e:
            print(f"⚠️  Alerta: Conexão falhou na tentativa {tentativa}. Motivo: {e}")
            if tentativa < max_tentativas:
                print("⏳ Aguardando 5 segundos para tentar novamente...")
                time.sleep(5)
            else:
                print("❌ Todas as tentativas de conexão falharam.")
                raise e
else:
    print("⚠️  Configurações de e-mail ausentes no GitHub Secrets.")
