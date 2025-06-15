import spacy
from textblob import TextBlob
from textstat import flesch_reading_ease
from .scrapers import extract_article_content, scrape_allsides_rating, scrape_mbfc_rating
import requests
from dotenv import load_dotenv
import os
import hashlib
import sqlite3

load_dotenv()
nlp = spacy.load('en_core_web_sm')

def extract_claims(text):
    try:
        doc = nlp(text)
        claims = [sent.text for sent in doc.sents if any(token.dep_ == 'ROOT' for token in sent)]
        return claims[:5]
    except:
        return []

def detect_emotional_language(text):
    try:
        blob = TextBlob(text)
        return blob.sentiment.polarity
    except:
        return 0

def check_citation_quality(text):
    try:
        return len([ent for ent in nlp(text).ents if ent.label_ in ['ORG', 'PERSON', 'GPE']]) > 0
    except:
        return False

def calculate_readability(text):
    try:
        return flesch_reading_ease(text)
    except:
        return 0

def detect_logical_fallacies(text):
    fallacies = []
    if 'everyone agrees' in text.lower():
        fallacies.append('Bandwagon')
    return fallacies

import requests
from dotenv import load_dotenv
import os

load_dotenv()

def query_llm(article_text, context):
    headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
    payload = {
        "inputs": f"""
        You are a news credibility analyst. Analyze this article using the provided context:

        ARTICLE: {article_text}

        CONTEXT:
        - Source: {context['domain']} (Bias: {context['bias_rating']}, Credibility: {context['credibility_score']}/10)
        - Fact-checks: {context['fact_check_results']}
        - Social sentiment: {context['sentiment_data']}
        - Content analysis: {context['content_metrics']}

        Provide JSON response with:
        1. credibility_score (1-10)
        2. bias_indicators (list)
        3. fact_check_alerts (list)
        4. explanation (human-readable)
        5. recommendation (trust/verify/reject)
        """
    }
    response = requests.post("https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct", json=payload, headers=headers)
    return response.json()

def analyze_content(article_text, url):
    claims = extract_claims(article_text)
    emotional_score = detect_emotional_language(article_text)
    has_citations = check_citation_quality(article_text)
    readability = calculate_readability(article_text)
    fallacies = detect_logical_fallacies(article_text)
    # Fetch social sentiment
    url_hash = hashlib.md5(url.encode()).hexdigest()
    # Cache article in SQLite for social sentiment endpoint
    conn = sqlite3.connect('data/news_context.db')
    conn.execute('INSERT OR IGNORE INTO articles_cache (url_hash, url, title, content, created_at) VALUES (?, ?, ?, ?, ?)',
                 (url_hash, url, 'Unknown', article_text, '2025-06-15'))
    conn.commit()
    conn.close()
    # Call social sentiment endpoint
    try:
        sentiment_response = requests.get(f'http://localhost:5000/mcp/social-sentiment/{url_hash}').json()
    except:
        sentiment_response = {'sentiment_score': 0, 'comment_count': 0}
    context = {
        'domain': url.split('/')[2],
        'bias_rating': scrape_allsides_rating(url.split('/')[2]),
        'credibility_score': scrape_mbfc_rating(url.split('/')[2]),
        'fact_check_results': 'None',
        'sentiment_data': sentiment_response,
        'content_metrics': {'claims': claims, 'emotional_score': emotional_score}
    }
    llm_result = query_llm(article_text, context)
    return {
        'claims': claims,
        'emotional_score': emotional_score,
        'has_citations': has_citations,
        'readability': readability,
        'fallacies': fallacies,
        'llm_analysis': llm_result,
        'url_hash': url_hash,
        'social_sentiment': sentiment_response
    }

def fetch_news(query='news'):
    api_key = os.getenv('NEWSAPI_KEY')
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}"
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return [extract_article_content(article['url']) for article in articles[:5]]