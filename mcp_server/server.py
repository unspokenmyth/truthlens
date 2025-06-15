from flask import Flask, jsonify, request
import sqlite3
from .scrapers import scrape_allsides_rating, scrape_mbfc_rating, scrape_factcheck_claim
from .analyzers import analyze_content

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('data/news_context.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/mcp/source-credibility/<domain>', methods=['GET'])
def source_credibility(domain):
    conn = get_db_connection()
    source = conn.execute('SELECT * FROM source_ratings WHERE domain = ?', (domain,)).fetchone()
    if source:
        return jsonify(dict(source))
    else:
        bias = scrape_allsides_rating(domain)
        credibility = scrape_mbfc_rating(domain)
        conn.execute('INSERT INTO source_ratings (domain, bias_rating, credibility_score) VALUES (?, ?, ?)',
                     (domain, bias, credibility))
        conn.commit()
        conn.close()
        return jsonify({'domain': domain, 'bias_rating': bias, 'credibility_score': credibility})

@app.route('/mcp/fact-check', methods=['POST'])
def fact_check():
    data = request.json
    claim = data.get('claim')
    result = scrape_factcheck_claim(claim)
    conn = get_db_connection()
    conn.execute('INSERT INTO fact_checks (claim, status, explanation) VALUES (?, ?, ?)',
                 (claim, result['status'], result['explanation']))
    conn.commit()
    conn.close()
    return jsonify(result)

@app.route('/mcp/analyze-content', methods=['POST'])
def analyze_content_endpoint():
    data = request.json
    article_text = data.get('article_text')
    url = data.get('url')
    analysis = analyze_content(article_text, url)
    return jsonify(analysis)