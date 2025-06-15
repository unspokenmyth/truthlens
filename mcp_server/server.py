from flask import Flask, jsonify, request
import sqlite3
from .scrapers import scrape_allsides_rating, scrape_mbfc_rating, scrape_factcheck_claim, get_reddit_sentiment
from .analyzers import analyze_content
import socket

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

@app.route('/mcp/social-sentiment/<article_hash>', methods=['GET'])
def social_sentiment(article_hash):
    conn = get_db_connection()
    article = conn.execute('SELECT url FROM articles_cache WHERE url_hash = ?', (article_hash,)).fetchone()
    if article:
        sentiment = get_reddit_sentiment(article['url'])
        conn.execute('INSERT INTO social_sentiment (article_hash, platform, sentiment_score, engagement_metrics) VALUES (?, ?, ?, ?)',
                     (article_hash, 'reddit', sentiment['sentiment_score'], str(sentiment['comment_count'])))
        conn.commit()
        conn.close()
        return jsonify(sentiment)
    conn.close()
    return jsonify({'error': 'Article not found'})

if __name__ == '__main__':
    port = 5000
    # Check if the port is already in use
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
    except socket.error as e:
        print(f"Port {port} is already in use. Please stop the other process using this port.")
        exit(1)
    finally:
        sock.close()
    app.run(host='0.0.0.0', port=port, debug=True)