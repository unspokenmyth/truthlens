from flask import Flask, render_template, request
from mcp_server.scrapers import extract_article_content
from mcp_server.analyzers import analyze_content, fetch_news
import requests

app = Flask(__name__)

@app.route('/')
def index():
    articles = fetch_news('news')  # Fetch recent news
    return render_template('index.html', articles=articles)

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form['url']
    try:
        article = extract_article_content(url)
        analysis = analyze_content(article['content'], url)
        domain = url.split('/')[2]
        credibility = requests.get(f'http://localhost:5000/mcp/source-credibility/{domain}').json()
        return render_template('analysis.html', article=article, analysis=analysis, credibility=credibility)
    except Exception as e:
        return render_template('analysis.html', error=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # Enable debug mode for better error messages