import requests
from bs4 import BeautifulSoup
from newspaper import Article
import hashlib
import praw
from dotenv import load_dotenv
import os
from textblob import TextBlob

load_dotenv()

def scrape_allsides_rating(domain):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(f"https://www.allsides.com/media-bias/{domain.replace('.', '-')}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        bias = soup.find('span', class_='bias-text') or 'Unknown'
        return bias.text.strip() if bias else 'Unknown'
    except:
        return 'Unknown'

def scrape_mbfc_rating(domain):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(f"https://mediabiasfactcheck.com/{domain.replace('.', '-')}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        credibility = soup.find('span', class_='credibility-score') or '5'
        return float(credibility.text.strip()) if credibility else 5.0
    except:
        return 5.0

def scrape_factcheck_claim(claim):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(f"https://www.snopes.com/?s={claim}", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        result = soup.find('div', class_='fact-check-result') or {'status': 'Unknown', 'explanation': 'No data'}
        return {'status': result.get('status', 'Unknown'), 'explanation': result.get('explanation', 'No data')}
    except:
        return {'status': 'Unknown', 'explanation': 'No data found'}

def extract_article_content(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return {
            'title': article.title or 'Unknown',
            'content': article.text or '',
            'url_hash': hashlib.md5(url.encode()).hexdigest()
        }
    except:
        return {'title': 'Unknown', 'content': '', 'url_hash': hashlib.md5(url.encode()).hexdigest()}

def get_reddit_sentiment(article_url):
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
        search_results = reddit.subreddit('all').search(article_url, limit=10)
        comments = []
        for submission in search_results:
            submission.comments.replace_more(limit=0)
            comments.extend([comment.body for comment in submission.comments.list()])
        sentiment = TextBlob(' '.join(comments)).sentiment.polarity if comments else 0
        return {'sentiment_score': sentiment, 'comment_count': len(comments)}
    except:
        return {'sentiment_score': 0, 'comment_count': 0}