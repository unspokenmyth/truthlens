import sqlite3

conn = sqlite3.connect('data/news_context.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS source_ratings
             (domain TEXT PRIMARY KEY, bias_rating TEXT, credibility_score REAL, factual_reporting TEXT, notes TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS fact_checks
             (claim_hash TEXT PRIMARY KEY, claim TEXT, status TEXT, explanation TEXT, sources TEXT, confidence REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS articles_cache
             (url_hash TEXT PRIMARY KEY, url TEXT, title TEXT, content TEXT, analysis TEXT, created_at TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS social_sentiment
             (article_hash TEXT, platform TEXT, sentiment_score REAL, engagement_metrics TEXT)''')
conn.commit()
conn.close()