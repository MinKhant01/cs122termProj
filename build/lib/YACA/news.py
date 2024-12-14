import requests
import os
from dotenv import load_dotenv
load_dotenv()

def get_nytimes_top_stories():
    headlines = []
    try:
        nytimes_key = os.getenv('NYTimesAPIKey')
        if not nytimes_key:
            raise ValueError("NYTimes API key is missing")
        
        nytimes_url = f"https://api.nytimes.com/svc/topstories/v2/home.json?api-key={nytimes_key}"
        nytimes_response = requests.get(nytimes_url)
        
        if nytimes_response.status_code == 200:
            nytimes_data = nytimes_response.json()
            for article in nytimes_data['results'][:5]:
                if 'title' in article and 'abstract' in article and 'url' in article:
                    headlines.append({
                        'title': article['title'],
                        'abstract': article['abstract'],
                        'url': article['url'],
                        'source': 'NYTimes',
                        'report_date': article['published_date']
                    })
        else:
            raise ValueError(f"NYTimes API request failed with status code {nytimes_response.status_code}")
    except Exception as e:
        headlines.append({
            'title': 'Error fetching NYTimes news',
            'abstract': str(e),
            'url': '',
            'source': 'NYTimes',
            'report_date': ''
        })
    
    return headlines

def get_newsapi_top_stories():
    headlines = []
    try:
        newsapi_key = os.getenv('NewsAPIKey')
        newsapi_url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi_key}"
        newsapi_response = requests.get(newsapi_url)
        
        if newsapi_response.status_code == 200:
            newsapi_data = newsapi_response.json()
            for article in newsapi_data['articles'][:5]:
                if 'title' in article and 'description' in article and 'url' in article:
                    headlines.append({
                        'title': article['title'],
                        'abstract': article['description'],
                        'url': article['url'],
                        'source': article['source']['name'],
                        'report_date': article['publishedAt']
                    })
    except Exception as e:
        headlines.append({
            'title': 'Error fetching NewsAPI news',
            'abstract': str(e),
            'url': '',
            'source': 'NewsAPI',
            'report_date': ''
        })
    
    return headlines

def get_top_headlines():
    headlines = []
    headlines.extend(get_nytimes_top_stories())
    headlines.extend(get_newsapi_top_stories())
    return headlines
