from flask import Flask, render_template, request
from mcp_server.server import app as mcp_app
from mcp_server.scrapers import extract_article_content
from mcp_server.analyzers import analyze_content
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form['url']
    article = extract_article_content(url)
    analysis = analyze_content(article['content'], url)
    domain = url.split('/')[2]
    credibility = requests.get(f'http://localhost:5000/mcp/source-credibility/{domain}').json()
    return render_template('analysis.html', article=article, analysis=analysis, credibility=credibility)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)